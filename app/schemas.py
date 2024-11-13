from pydantic import BaseModel
from typing import List, Optional


# Базовая модель для пользователей (админов и ведущих)
class UserBase(BaseModel):
    login: str
    password: str


# Модель для создания нового пользователя (админа или ведущего)
class UserCreate(UserBase):
    pass


# Модель для логина пользователя
class UserLogin(BaseModel):
    login: str
    password: str


# Модель для создания категории
class CategoryCreate(BaseModel):
    name: str
    color: str


# Модель для создания набора
class SetCreate(BaseModel):
    name: str
    category_id: int  # ID категории, к которой принадлежит набор


# Модель для создания карточки
class CardCreate(BaseModel):
    number: int
    description: str
    hashtags: List[str]  # Список хештегов
    set_id: int  # ID набора, к которому относится карточка


# Модель для создания игры
class GameCreate(BaseModel):
    host_id: int  # ID ведущего
    game_code: str  # Уникальный код игры


# Схема для отображения информации о категории
class Category(BaseModel):
    id: int
    name: str
    color: str
    # Связь один-ко-многим с наборами
    sets: List["Set"] = []  # Возвращаем список наборов, связанных с категорией
    # Связь многие-ко-многим с играми
    games: List["Game"] = []  # Список игр, связанных с категорией
    # Связь один-ко-многим с карточками
    cards: List["Card"] = []  # Список карточек, связанных с категорией

    class Config:
        orm_mode = True


# Схема для отображения набора
class Set(BaseModel):
    id: int
    name: str
    category_id: int
    # Связь с категорией
    category: Category
    # Связь многие-ко-многим с карточками
    cards: List["Card"] = []  # Список карточек, связанных с набором
    # Связь многие-ко-многим с играми
    games: List["Game"] = []  # Список игр, связанных с набором

    class Config:
        orm_mode = True


# Схема для отображения карточки
class Card(BaseModel):
    id: int
    number: int
    description: str
    hashtags: List[str]  # Список хештегов
    # Связь с набором
    set: Set
    # Связь с категорией
    category: Category

    class Config:
        orm_mode = True


# Схема для отображения игры
class Game(BaseModel):
    id: int
    game_code: str
    status: str  # Статус игры (waiting, started, finished)
    # Связь с ведущим
    host_id: int
    host_login: str  # Логин ведущего
    # Связь многие-ко-многим с категориями
    categories: List[Category] = []  # Список категорий, связанных с игрой
    # Связь многие-ко-многим с наборами
    sets: List[Set] = []  # Список наборов, связанных с игрой

    class Config:
        orm_mode = True


# Модель для отображения информации о ведущем
class Host(BaseModel):
    id: int
    login: str
    password: str

    class Config:
        orm_mode = True


# Модель для отображения информации о администраторе
class Admin(BaseModel):
    id: int
    login: str
    password: str

    class Config:
        orm_mode = True
