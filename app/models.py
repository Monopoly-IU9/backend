from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


# Промежуточные модели для связи многие-ко-многим

class SetCardAssociation(Base):
    __tablename__ = "set_card_association"
    set_id = Column(Integer, ForeignKey("sets.id"), primary_key=True)
    card_id = Column(Integer, ForeignKey("cards.id"), primary_key=True)


class GameCategoryAssociation(Base):
    __tablename__ = "game_category_association"
    game_id = Column(Integer, ForeignKey("games.id"), primary_key=True)
    category_id = Column(Integer, ForeignKey("categories.id"), primary_key=True)


class GameSetAssociation(Base):
    __tablename__ = "game_set_association"
    game_id = Column(Integer, ForeignKey("games.id"), primary_key=True)
    set_id = Column(Integer, ForeignKey("sets.id"), primary_key=True)


# Модель для админов
class Admin(Base):
    __tablename__ = "admins"
    id = Column(Integer, primary_key=True, index=True)
    login = Column(String, unique=True, index=True)
    password = Column(String)


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

    sets = relationship("Set", back_populates="category")
    # Связь многие-ко-многим с играми
    games = relationship("Game", secondary=GameCategoryAssociation.__table__, back_populates="categories")
    # Связь один-ко-многим с карточками
    cards = relationship("Card", back_populates="category")


# Модель для наборов
class Set(Base):
    __tablename__ = "sets"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    category_id = Column(Integer, ForeignKey("categories.id"))

    category = relationship("Category", back_populates="sets")
    # Связь многие-ко-многим с карточками
    cards = relationship("Card", secondary=SetCardAssociation.__table__, back_populates="sets")
    # Связь многие-ко-многим с играми
    games = relationship("Game", secondary=GameSetAssociation.__table__, back_populates="sets")


# Модель для карточек
class Card(Base):
    __tablename__ = "cards"
    id = Column(Integer, primary_key=True, index=True)
    number = Column(Integer)
    description = Column(String)
    hashtags = Column(String)

    # Связь многие-ко-одному с категорией
    category_id = Column(Integer, ForeignKey("categories.id"))
    category = relationship("Category", back_populates="cards")

    # Связь многие-ко-многим с наборами
    sets = relationship("Set", secondary=SetCardAssociation.__table__, back_populates="cards")


# Модель для игр
class Game(Base):
    __tablename__ = "games"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    status = Column(String, default="waiting")  # Статус игры (waiting, started, finished)
    start_time = Column(DateTime, nullable=True)
    initial_deck = Column(String, nullable=True)
    deck = Column(String, nullable=True)
    hashtags = Column(String, nullable=True)

    # Связь многие-ко-многим с категориями
    categories = relationship("Category", secondary=GameCategoryAssociation.__table__, back_populates="games")

    # Связь многие-ко-многим с наборами
    sets = relationship("Set", secondary=GameSetAssociation.__table__, back_populates="games")
