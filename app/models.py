from sqlalchemy import Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# Вспомогательные таблицы для связи многие-ко-многим

# Связь между Set и Card
set_card_association = Table(
    "set_card_association", Base.metadata,
    Column("set_id", Integer, ForeignKey("sets.id"), primary_key=True),
    Column("card_id", Integer, ForeignKey("cards.id"), primary_key=True)
)

# Связь между Game и Category
game_category_association = Table(
    "game_category_association", Base.metadata,
    Column("game_id", Integer, ForeignKey("games.id"), primary_key=True),
    Column("category_id", Integer, ForeignKey("categories.id"), primary_key=True)
)

# Связь между Game и Set
game_set_association = Table(
    "game_set_association", Base.metadata,
    Column("game_id", Integer, ForeignKey("games.id"), primary_key=True),
    Column("set_id", Integer, ForeignKey("sets.id"), primary_key=True)
)


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
    games = relationship("Game", secondary=game_category_association, back_populates="categories")
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
    cards = relationship("Card", secondary=set_card_association, back_populates="sets")
    # Связь многие-ко-многим с играми
    games = relationship("Game", secondary=game_set_association, back_populates="sets")


# Модель для карточек
class Card(Base):
    __tablename__ = "cards"
    id = Column(Integer, primary_key=True, index=True)
    number = Column(Integer)
    description = Column(String)
    hashtags = Column(String)

    set_id = Column(Integer, ForeignKey("sets.id"))
    set = relationship("Set", back_populates="cards")

    # Связь многие-ко-одному с категорией
    category_id = Column(Integer, ForeignKey("categories.id"))
    category = relationship("Category", back_populates="cards")

    # Связь многие-ко-многим с наборами
    sets = relationship("Set", secondary=set_card_association, back_populates="cards")


# Модель для игр
class Game(Base):
    __tablename__ = "games"
    id = Column(Integer, primary_key=True, index=True)
    game_code = Column(String, unique=True, index=True)
    status = Column(String, default="waiting")  # Статус игры (waiting, started, finished)

    host_id = Column(Integer, ForeignKey("hosts.id"))
    host = relationship("Host")

    # Связь многие-ко-многим с категориями
    categories = relationship("Category", secondary=game_category_association, back_populates="games")

    # Связь многие-ко-многим с наборами
    sets = relationship("Set", secondary=game_set_association, back_populates="games")
