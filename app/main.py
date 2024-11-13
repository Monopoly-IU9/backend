from sqlalchemy.orm import Session
from sqlalchemy import exc
import uuid
from fastapi.responses import FileResponse
from app.models import Admin, Host, Category, Set, Card, Game, Base
from app.database import SessionLocal, engine
from app.schemas import UserLogin, CategoryCreate, SetCreate, CardCreate, GameCreate
from app.utils import create_access_token, get_current_user, oauth2_scheme, verify_access_token
from fastapi import FastAPI, Depends, HTTPException, status

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
    print(host.login, host.password)
    return {"message": "Login successful", "user_id": h.id}


# Изменение категории
@app.post("/admin/category")
async def edit_category(category_id: int, category: CategoryCreate, db: Session = Depends(get_db),
                        current_user: dict = Depends(get_current_user)):
    if not current_user or current_user.get("sub") != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")
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


'''''# Создание набора
@app.post("/admin/set/")
async def create_set(set_data: SetCreate, db: Session = Depends(get_db),
                     current_user: dict = Depends(get_current_user)):
    if not current_user or current_user.get("sub") != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")
    new_set = Set(name=set_data.name, category_id=set_data.category_id)
    db.add(new_set)
    db.commit()
    db.refresh(new_set)
    return {"message": "Set created successfully!", "set_id": new_set.id}'''

''''# Создание карточки
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
'''


# Изменение игры
@app.post("/admin/edit-game")
async def edit_game(game_data: GameCreate, db: Session = Depends(get_db),
                    current_user: dict = Depends(get_current_user)):
    pass


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


# Начало игры
@app.post("/host/game/start")
async def start_game(game_data: GameCreate, db: Session = Depends(get_db),
                     current_user: dict = Depends(get_current_user)):
    if not current_user or current_user.get("sub") != "host":
        raise HTTPException(status_code=403, detail="Permission denied")
    game_code = str(uuid.uuid4())  # Генерация уникального кода игры
    new_game = Game(game_code=game_code, host_id=game_data.host_id)
    db.add(new_game)
    db.commit()
    db.refresh(new_game)
    return {"message": "Game started successfully!", "game_code": game_code}


''''@app.get("/host/game{gameid}/play")
async def play_game(game_data: GameCreate, db: Session = Depends(get_db),
                    current_user: dict = Depends(get_current_user)):
    if not current_user or current_user.get("sub") != "host":
        raise HTTPException(status_code=403, detail="Permission denied")'''

'''# Генерация QR
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
    return JSONResponse(content={"message": "QR code generated", "qr_code": qr_base64})'''


# Получение списка категорий
@app.get("/admin/getCategories")
async def get_categories(db: Session = Depends(get_db)):
    categories = db.query(Category).all()
    return [{"id": category.id, "name": category.name, "color": category.color} for category in categories]


# Создание категории
@app.post("/admin/createCategory")
async def create_category(category: CategoryCreate, db: Session = Depends(get_db),
                          current_user: dict = Depends(get_current_user)):
    if not current_user or current_user.get("sub") != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")

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


# Получение наборов из категории
@app.post("/admin/getSetsByCategoryID")
async def get_sets_by_category(category_id: int, db: Session = Depends(get_db)):
    sets = db.query(Set).filter(Set.category_id == category_id).all()
    return [{"id": set.id, "name": set.name} for set in sets]


# Создание карточки
@app.post("/admin/addCardToCategoryID")
async def add_card_to_category(category_id: int, card_data: CardCreate, db: Session = Depends(get_db)):
    main_set = db.query(Set).filter(Set.category_id == category_id).first()
    if not main_set:
        main_set = Set(name="Main Set", category_id=category_id)
        db.add(main_set)
        db.commit()
        db.refresh(main_set)

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


# Получение карточек из категории
@app.post("/admin/getCardsByCategoryID")
async def get_cards_by_category(category_id: int, db: Session = Depends(get_db)):
    cards = db.query(Card).join(Set).filter(Set.category_id == category_id).all()
    return [{"id": card.number, "description": card.description} for card in cards]


# Создание набора
@app.post("/admin/addSet")
async def add_set(set_data: SetCreate, db: Session = Depends(get_db)):
    # Проверка существования категории по id
    category = db.query(Category).filter(Category.id == set_data.category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    # Создание нового набора
    new_set = Set(name=set_data.name, category_id=set_data.category_id)
    db.add(new_set)
    db.commit()
    db.refresh(new_set)

    # Добавление карточек в набор
    if set_data.card_ids:
        for card_id in set_data.card_ids:
            card = db.query(Card).filter(Card.number == card_id).first()
            if not card:
                raise HTTPException(status_code=404, detail=f"Card with id {card_id} not found")
            card.set_id = new_set.id
            db.commit()

    return {"message": "Set created successfully!", "set_id": new_set.id}


# Изменение набора
@app.post("/admin/editSet")
async def edit_set(set_data: SetCreate, db: Session = Depends(get_db)):
    # Проверка существования набора по id
    db_set = db.query(Set).filter(Set.id == set_data.id).first()
    if not db_set:
        raise HTTPException(status_code=404, detail="Set not found")

    # Обновление информации о наборе
    db_set.name = set_data.name
    db.commit()
    db.refresh(db_set)

    # Обновление списка карточек для набора
    if set_data.card_ids:
        # Очищаем текущие карточки для набора
        for card in db_set.cards:
            card.set_id = None
        db.commit()

        # Добавляем новые карточки в набор
        for card_id in set_data.card_ids:
            card = db.query(Card).filter(Card.number == card_id).first()
            if not card:
                raise HTTPException(status_code=404, detail=f"Card with id {card_id} not found")
            card.set_id = db_set.id
            db.commit()

    return {"message": "Set updated successfully!", "set_id": db_set.id}


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


# Ручка для проверки авторизации ведущего
@app.get("/check-auth")
async def check_auth(token: str = Depends(oauth2_scheme)):
    payload = verify_access_token(token)
    if payload.get("role") != "host":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a host")
    return {"status": "authorized"}


# Ручка для проверки авторизации администратора
@app.get("/check-admin-auth")
async def check_admin_auth(token: str = Depends(oauth2_scheme)):
    payload = verify_access_token(token)
    if payload.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not an admin")
    return {"status": "authorized"}

