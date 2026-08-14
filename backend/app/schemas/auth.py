from pydantic import BaseModel
from pydantic import Field
from pydantic import SecretStr
from pydantic import field_validator


class LoginRequest(BaseModel):
    """演示用户登录请求。"""

    username: str = Field(
        min_length=3,
        max_length=100,
    )

    password: SecretStr

    @field_validator("username")
    @classmethod
    def normalize_username(
        cls,
        value: str,
    ) -> str:
        return value.strip().lower()


class AuthenticatedUser(BaseModel):
    """已经通过认证的用户。"""

    id: int
    username: str
    display_name: str
    role_code: str
    role_name: str
    permissions: list[str]
    is_demo: bool


class LoginResponse(BaseModel):
    """登录成功后返回的令牌。"""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: AuthenticatedUser