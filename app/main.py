import base64
import io

from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import exc
# import bcrypt
import uuid
import qrcode
from fastapi.responses import FileResponse
from app.models import Admin, Host, Category, Set, Card, Game, Base
from app.database import SessionLocal, engine
from app.schemas import UserCreate, UserLogin, CategoryCreate, SetCreate, CardCreate, GameCreate

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


# Хэширование пароля
# def hash_password(password: str):
#  return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())


# Проверка пароля
# def verify_password(hashed_password, password):
#  return bcrypt.checkpw(password.encode('utf-8'), hashed_password)

@app.get("/HomePage")
async def root():
    return FileResponse("C:\\Users\\Venya\\PycharmProjects\\backend\\index.html")


# Вход админа
@app.post("/admin-login")
async def admin_login(admin: UserLogin, db: Session = Depends(get_db)):
    adm = db.query(Admin).filter(Admin.login == admin.login).first()
    if not adm:
        raise HTTPException(status_code=401, detail="Incorrect user")
    print(admin.login, admin.password)
    return {"message": "Login successful", "user_id": adm.id}


# Вход ведущего
@app.post("/host-login")
async def register_admin(host: UserLogin, db: Session = Depends(get_db)):
    h = db.query(Admin).filter(Admin.login == host.login).first()
    if not h:
        raise HTTPException(status_code=401, detail="Incorrect user")
    print(host.login, host.password)
    return {"message": "Login successful", "user_id": h.id}


# Создание категории
@app.post("/admin/new-category")
async def create_category(category: CategoryCreate, db: Session = Depends(get_db)):
    new_category = Category(name=category.name, color=category.color)
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return {"message": "Category created successfully!", "category_id": new_category.id}


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


# Создание набора
@app.post("/admin/set/")
async def create_set(set_data: SetCreate, db: Session = Depends(get_db)):
    new_set = Set(name=set_data.name, category_id=set_data.category_id)
    db.add(new_set)
    db.commit()
    db.refresh(new_set)
    return {"message": "Set created successfully!", "set_id": new_set.id}


# Создание карточки
@app.post("/admin/card/")
async def create_card(card_data: CardCreate, db: Session = Depends(get_db)):
    new_card = Card(
        number=card_data.number,
        description=card_data.description,
        hashtags=",".join(card_data.hashtags),
        set_id=card_data.set_id
    )
    db.add(new_card)
    try:
        db.commit()  # Сохранение изменений
        db.refresh(new_card)  # Обновление объекта после коммита
    except exc.IntegrityError:  # Обработка ошибок, если возникнут проблемы с уникальностью или другими ограничениями
        db.rollback()  # Откатываем изменения, если возникла ошибка
        raise HTTPException(status_code=400, detail="Error occurred while creating the card")
    return {"message": "Card created successfully!", "card_id": new_card.number}


# Изменение игры
@app.post("/admin/edit-game")
async def edit_game():
    pass


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


# Создание игры
@app.post("/admin/game/start")
async def start_game(game_data: GameCreate, db: Session = Depends(get_db)):
    game_code = str(uuid.uuid4())  # Генерация уникального кода игры
    new_game = Game(game_code=game_code, host_id=game_data.host_id)
    db.add(new_game)
    db.commit()
    db.refresh(new_game)
    return {"message": "Game started successfully!", "game_code": game_code}


# Генерация QR
@app.get("/admin/game/{game_code}/qr")
async def generate_qr(game_code: str):
    # Генерация QR-кода
    qr = qrcode.make(game_code)

    # Сохраняем изображение QR в памяти (в формате PNG)
    img_io = io.BytesIO()
    qr.save(img_io, format="PNG")

    # Преобразуем изображение в base64
    img_io.seek(0)
    qr_base64 = base64.b64encode(img_io.getvalue()).decode("utf-8")

    # Отправляем на фронтенд
    return JSONResponse(content={"message": "QR code generated", "qr_code": qr_base64})
