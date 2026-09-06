import json
import logging

import redis

from app.core.config import settings

logger = logging.getLogger(__name__)

_client: redis.Redis | None = None
_connection_failed = False


def _get_client() -> redis.Redis | None:
    """Lazy connect - và QUAN TRỌNG: nếu Redis không kết nối được, không raise
    exception làm sập cả app. Cache là tối ưu, không phải phụ thuộc cứng - Redis
    chết thì fallback về query DB thẳng, chậm hơn nhưng vẫn đúng và vẫn chạy được.
    _connection_failed chỉ set 1 lần để tránh retry connect ở MỌI request sau đó
    (mỗi lần thử connect lại tốn thời gian timeout) - chấp nhận phải restart app
    nếu Redis phục hồi giữa chừng, đổi lại tránh làm chậm mọi request khi Redis
    đang down kéo dài."""
    global _client, _connection_failed
    if _connection_failed:
        return None
    if _client is None:
        try:
            _client = redis.from_url(settings.redis_url, socket_connect_timeout=1, socket_timeout=1)
            _client.ping()
        except Exception:  # noqa: BLE001 - chủ đích bắt rộng, xem comment dưới
            # Bắt Exception RỘNG (không chỉ redis.RedisError) có chủ đích: lỗi kết
            # nối thực tế lúc này có thể là bất kỳ loại nào (DNS fail, connection
            # refused ở tầng OS, timeout...) không nhất thiết kế thừa RedisError.
            # Đây là ranh giới với 1 hạ tầng ngoài (Redis) - đúng chỗ nên bắt rộng,
            # vì mục tiêu tuyệt đối là "Redis lỗi kiểu gì cũng không được sập app".
            logger.warning("Không kết nối được Redis - cache sẽ bị bỏ qua, fallback về DB.")
            _connection_failed = True
            return None
    return _client


def get_cached(key: str) -> dict | list | None:
    """Trả None nếu cache miss HOẶC Redis lỗi - caller không cần phân biệt 2
    trường hợp này, đều xử lý giống nhau (query DB)."""
    client = _get_client()
    if client is None:
        return None
    try:
        raw = client.get(key)
        return json.loads(raw) if raw else None
    except redis.RedisError:
        logger.warning(f"Lỗi đọc cache key={key} - bỏ qua, coi như cache miss.")
        return None


def set_cached(key: str, value: dict | list, ttl_seconds: int = 300) -> None:
    """Lỗi ghi cache KHÔNG được raise ra ngoài - request chính (đã query DB xong)
    vẫn phải trả kết quả đúng cho client dù ghi cache thất bại."""
    client = _get_client()
    if client is None:
        return
    try:
        client.set(key, json.dumps(value), ex=ttl_seconds)
    except redis.RedisError:
        logger.warning(f"Lỗi ghi cache key={key} - bỏ qua, không ảnh hưởng response chính.")


def delete_cached(key: str) -> None:
    client = _get_client()
    if client is None:
        return
    try:
        client.delete(key)
    except redis.RedisError:
        logger.warning(f"Lỗi xoá cache key={key}.")