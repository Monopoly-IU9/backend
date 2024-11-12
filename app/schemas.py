# schemas.py

from pydantic import BaseModel
from typing import List, Optional


class UserBase(BaseModel):
    login: str
    password: str


class UserCreate(UserBase):
    pass


class UserLogin(BaseModel):
    login: str
    password: str


class CategoryCreate(BaseModel):
    name: str
    color: str


class SetCreate(BaseModel):
    name: str
    category_id: int


class CardCreate(BaseModel):
    number: int
    description: str
    hashtags: List[str]
    set_id: int


class GameCreate(BaseModel):
    host_id: int
    game_code: str