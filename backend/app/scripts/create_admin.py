"""Tạo tài khoản HR Admin đầu tiên - chạy 1 lần khi mới deploy hệ thống.

Mọi API tạo user khác đều yêu cầu đã đăng nhập với role hr_admin (xem
app/api/users.py), nên cần 1 cách tạo tài khoản hr_admin đầu tiên nằm ngoài
luồng API bình thường.

Chạy trong container backend:
    docker compose exec backend python -m app.scripts.create_admin
"""

import getpass

from app.core.db import SessionLocal
from app.core.security import hash_password
from app.models.user import User, UserRole


def main() -> None:
    email = input("Email HR Admin: ").strip()
    full_name = input("Họ tên: ").strip()
    password = getpass.getpass("Mật khẩu (không hiện ra màn hình, tối thiểu 8 ký tự): ")

    if len(password) < 8:
        print("Mật khẩu phải có ít nhất 8 ký tự.")
        return

    db = SessionLocal()
    try:
        if db.query(User).filter(User.email == email).first():
            print(f"Email {email} đã tồn tại.")
            return

        user = User(
            email=email,
            full_name=full_name,
            password_hash=hash_password(password),
            role=UserRole.hr_admin.value,
            is_active=True,
        )
        db.add(user)
        db.commit()
        print(f"Đã tạo HR Admin: {email}")
    finally:
        db.close()


if __name__ == "__main__":
    main()