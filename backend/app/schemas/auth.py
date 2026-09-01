from pydantic import BaseModel

from app.schemas.user import UserResponse


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user: UserResponse


class RefreshRequest(BaseModel):
    refresh_token: str


class RefreshResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class LogoutRequest(BaseModel):
    refresh_token: str