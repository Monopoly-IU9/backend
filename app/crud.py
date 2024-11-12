from sqlalchemy.orm import Session
from app import models, schemas


# Создание новой категории
def create_category(db: Session, category: schemas.CategoryCreate):
    db_category = models.Category(name=category.name, color=category.color)
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


# Получение админа
def get_admin(db: Session, admin: schemas.UserLogin):
    return db.query(models.Admin).filter(admin.login == models.Admin.login).first()


# Получение всех категорий
def get_categories(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Category).offset(skip).limit(limit).all()


# Получение категории по ID
def get_category(db: Session, category_id: int):
    return db.query(models.Category).filter(models.Category.id == category_id).first()


# Создание новой игры
def create_game(db: Session, game: schemas.GameCreate):
    db_game = models.Game(
        name=game.name,
        host_login=game.host_login,
        host_password=game.host_password,
        sets=game.sets,
        tags=game.tags
    )
    db.add(db_game)
    db.commit()
    db.refresh(db_game)

    # Добавление категорий в игру
    for category_id in game.categories:
        db_category = db.query(models.Category).filter(models.Category.id == category_id).first()
        if db_category:
            db_game.categories.append(db_category)

    db.commit()
    return db_game


# Получение всех игр
def get_games(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Game).offset(skip).limit(limit).all()


# Получение игры по ID
def get_game(db: Session, game_id: int):
    return db.query(models.Game).filter(models.Game.id == game_id).first()
