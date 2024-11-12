from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


# Модель для админов
class Admin(Base):
    __tablename__ = "admins"
    id = Column(Integer, primary_key=True, index=True)
    login = Column(String, unique=True, index=True)
    password = Column(String)  # Пароль будет храниться в хешированном виде

    categories = relationship("Category", back_populates="owner")


# Модель для ведущих
class Host(Base):
    __tablename__ = "hosts"
    id = Column(Integer, primary_key=True, index=True)
    login = Column(String, unique=True, index=True)
    password = Column(String)


# Модель для категорий
class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    color = Column(String)

    owner_id = Column(Integer, ForeignKey("admins.id"))
    owner = relationship("Admin", back_populates="categories")
    sets = relationship("Set", back_populates="category")


# Модель для наборов
class Set(Base):
    __tablename__ = "sets"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    category_id = Column(Integer, ForeignKey("categories.id"))

    category = relationship("Category", back_populates="sets")
    cards = relationship("Card", back_populates="set")


# Модель для карточек
class Card(Base):
    __tablename__ = "cards"
    number = Column(Integer, primary_key=True, index=True)
    description = Column(String)
    hashtags = Column(String)

    set_id = Column(Integer, ForeignKey("sets.id"))
    set = relationship("Set", back_populates="cards")


# Модель для игр
class Game(Base):
    __tablename__ = "games"
    id = Column(Integer, primary_key=True, index=True)
    game_code = Column(String, unique=True, index=True)
    status = Column(String, default="waiting")  # Статус игры (waiting, started, finished)

    host_id = Column(Integer, ForeignKey("hosts.id"))
    host = relationship("Host")