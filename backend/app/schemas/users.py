from typing import Literal, Optional

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: Optional[str] = None
    role: Literal["member", "chair"]


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    role: Optional[Literal["member", "chair"]] = None


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: Literal["member", "chair"]
