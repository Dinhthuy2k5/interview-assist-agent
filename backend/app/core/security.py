import hashlib
import secrets
from datetime import UTC, datetime, timedelta

import bcrypt
from jose import jwt

from app.core.config import settings

ALGORITHM = "HS256"
REFRESH_TOKEN_BYTES = 32


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def create_access_token(user_id: str, role: str) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.jwt_expire_minutes)
    # jti (JWT ID, RFC 7519) đảm bảo token luôn duy nhất - thiếu claim này, 2 token
    # cấp cho cùng user trong cùng 1 giây (exp chỉ có độ chính xác tới giây) sẽ
    # sinh ra CHUỖI JWT Y HỆT NHAU (payload giống hệt -> chữ ký HMAC deterministic
    # giống hệt) - xảy ra thật khi login rồi refresh ngay sau đó trong cùng 1 giây.
    payload = {
        "sub": user_id,
        "role": role,
        "exp": expire,
        "jti": secrets.token_hex(8),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Ném jose.JWTError nếu token hết hạn, sai chữ ký, hoặc sai định dạng."""
    return jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])


def generate_refresh_token() -> str:
    """Chuỗi random 256-bit (32 byte), KHÔNG phải JWT - refresh token không cần
    tự chứa thông tin (payload), chỉ cần là 1 khoá tra cứu ngẫu nhiên không đoán
    được, đối chiếu với bảng refresh_token trong DB."""
    return secrets.token_urlsafe(REFRESH_TOKEN_BYTES)


def hash_refresh_token(token: str) -> str:
    """sha256, KHÔNG dùng bcrypt như password. Refresh token là chuỗi random
    256-bit entropy cực cao (không phải do người dùng chọn, không đoán được bằng
    dictionary attack) - không cần thuật toán chậm cố ý (bcrypt) để chống
    brute-force như password. sha256 đủ nhanh để tra cứu mỗi lần refresh mà vẫn
    an toàn: kẻ tấn công có DB rò rỉ vẫn không đảo ngược được hash để lấy token gốc."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()