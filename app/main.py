from sqlalchemy.orm import Session
from sqlalchemy import exc
import uuid
from fastapi.responses import FileResponse
from fastapi import FastAPI, Depends, HTTPException, status
from app.models import Admin, Host, Category, Set, Card, Game, Base
from app.database import SessionLocal, engine
from app.schemas import UserLogin, CategoryCreate, SetCreate, CardCreate, GameCreate

from app.utils import create_access_token

app = FastAPI()

# Инициализация базы данных
Base.metadata.create_all(bind=engine)


# Получение сессии базы данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/HomePage")
async def root():
    return FileResponse("C:\\Users\\Venya\\PycharmProjects\\backend\\index.html")


# Вход админа
@app.post("/admin-login")
async def admin_login(admin: UserLogin, db: Session = Depends(get_db)):
    adm = db.query(Admin).filter(Admin.login == admin.login).first()
    if not adm:
        raise HTTPException(status_code=401, detail="Incorrect user")
    if admin.password != adm.password:
        raise HTTPException(status_code=401, detail="Incorrect password")

    # Генерация JWT токена
    access_token = create_access_token(data={"sub": adm.login})
    return {"access_token": access_token, "token_type": "bearer"}


# Вход ведущего
@app.post("/host-login")
async def register_admin(host: UserLogin, db: Session = Depends(get_db)):
    h = db.query(Host).filter(Host.login == host.login).first()
    if not h:
        raise HTTPException(status_code=401, detail="Incorrect user")
    return {"message": "Login successful", "user_id": h.id}


# Изменение категории
@app.post("/admin/category")
async def edit_category(category_id: int, category: CategoryCreate, db: Session = Depends(get_db)):
    # Поиск категории по ID
    db_category = db.query(Category).filter(Category.id == category_id).first()

    # Проверка, существует ли категория
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")

    # Проверка на уникальность названия
    existing_category = db.query(Category).filter(Category.name == category.name).first()
    if existing_category and existing_category.id != category_id:
        raise HTTPException(status_code=400, detail="Category name must be unique")

    # Обновление названия и цвета категории
    db_category.name = category.name
    db_category.color = category.color

    # Применение изменений
    db.commit()
    db.refresh(db_category)

    return {"message": "Category updated successfully!", "category_id": db_category.id}


# Создание игры
@app.post("/admin/new-game")
async def new_game(game_data: GameCreate, db: Session = Depends(get_db)):
    # Генерация уникального кода для игры
    game_code = str(uuid.uuid4())  # Генерация уникального кода игры

    # Создание нового игрового объекта
    new_game = Game(
        game_code=game_code,  # Уникальный код игры
        host_id=game_data.host_id  # ID ведущего (хоста)
    )

    # Добавление игры в базу данных
    db.add(new_game)

    try:
        db.commit()  # Сохранение изменений
        db.refresh(new_game)  # Обновление объекта после коммита
    except exc.IntegrityError:  # Обработка ошибок, если возникнут проблемы с уникальностью или другими ограничениями
        db.rollback()  # Откатываем изменения, если возникла ошибка
        raise HTTPException(status_code=400, detail="Error occurred while creating the game")

    # Возвращаем информацию о созданной игре (код игры и ID хоста)
    return {
        "message": "Game created successfully!",
        "game_code": new_game.game_code,
        "host_id": new_game.host_id
    }


# Получение списка категорий
@app.get("/admin/getCategories")
async def get_categories(db: Session = Depends(get_db)):
    categories = db.query(Category).all()
    return [{"id": category.id, "name": category.name, "color": category.color} for category in categories]


# Создание категории
@app.post("/admin/createCategory")
async def create_category(category: CategoryCreate, db: Session = Depends(get_db)):
    new_category = Category(name=category.name, color=category.color)
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return {"message": "Category created successfully!", "category_id": new_category.id}


# Получение информации о наборе
@app.post("/admin/getSetInfo")
async def get_set_info(set_id: int, db: Session = Depends(get_db)):
    set_info = db.query(Set).filter(Set.id == set_id).first()
    if not set_info:
        raise HTTPException(status_code=404, detail="Set not found")

    # Получаем карточки
    cards = db.query(Card).filter(Card.set_id == set_id).all()

    set_data = {
        "name": set_info.name,
        "cards": [{"id": card.number, "description": card.description, "hashtags": card.hashtags} for card in cards]
    }

    return set_data


# Создание карточки
@app.post("/admin/addCardToCategoryID")
async def add_card_to_category(category_id: int, card_data: CardCreate, db: Session = Depends(get_db)):
    # Проверка существования категории
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    # Создание нового набора (если не существует)
    main_set = db.query(Set).filter(Set.category_id == category_id).first()
    if not main_set:
        main_set = Set(name="Main Set", category_id=category_id)
        db.add(main_set)
        db.commit()
        db.refresh(main_set)

    # Создание новой карточки
    new_card = Card(
        number=card_data.number,
        description=card_data.description,
        hashtags=",".join(card_data.hashtags),
        set_id=main_set.id
    )
    db.add(new_card)
    db.commit()
    db.refresh(new_card)

    return {"message": "Card added successfully!", "card_id": new_card.number}


# Удаление категории
@app.post("/admin/deleteCategory")
async def delete_category(category_id: int, db: Session = Depends(get_db)):
    # Получаем категорию по id
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    # Удаляем все наборы, связанные с категорией
    sets = db.query(Set).filter(Set.category_id == category_id).all()
    for set_ in sets:
        # Удаляем все карточки, связанные с набором
        cards = db.query(Card).filter(Card.set_id == set_.id).all()
        for card in cards:
            db.delete(card)
        db.delete(set_)

    # Удаляем категорию
    db.delete(category)
    db.commit()

    return {"message": "Category and all associated sets and cards deleted successfully!"}


# Удаление карточки
@app.post("/admin/deleteCard")
async def delete_card(card_id: int, db: Session = Depends(get_db)):
    # Находим карточку по id
    card = db.query(Card).filter(Card.number == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    # Удаляем карточку
    db.delete(card)
    db.commit()

    return {"message": "Card deleted successfully!"}


# Удаление набора
@app.post("/admin/deleteSet")
async def delete_set(set_id: int, db: Session = Depends(get_db)):
    # Находим набор по id
    db_set = db.query(Set).filter(Set.id == set_id).first()
    if not db_set:
        raise HTTPException(status_code=404, detail="Set not found")

    # Удаляем все карточки, связанные с набором
    cards = db.query(Card).filter(Card.set_id == set_id).all()
    for card in cards:
        db.delete(card)

    # Удаляем набор
    db.delete(db_set)
    db.commit()

    return {"message": "Set and all associated cards deleted successfully!"}
