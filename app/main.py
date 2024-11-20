from typing import List

from sqlalchemy.orm import Session
from sqlalchemy import exc
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Depends, HTTPException
from app.models import Admin, Host, Category, Set, Card, Game, Base, set_card_association
from app.database import SessionLocal, engine
from app.schemas import UserLogin, CategoryCreate, CardCreate, GameCreate, UserCreate, SetCreate, CardInSet, HostCreate
from app.utils import create_access_token, verify_access_token  # oauth2_scheme,
from fastapi.security import OAuth2PasswordBearer

app = FastAPI()
blacklist = set()
origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Инициализация базы данных
Base.metadata.create_all(bind=engine)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token", scheme_name="JWT")


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
@app.post("/admin/login")
async def admin_login(admin: UserLogin, db: Session = Depends(get_db)):
    adm = db.query(Admin).filter(Admin.login == admin.login).first()
    if not (admin.login == "admin" and admin.password == "12345678"):
        raise HTTPException(status_code=401, detail="Incorrect user")
    if not adm:
        raise HTTPException(status_code=401, detail="Incorrect user")
    if admin.password != adm.password:
        raise HTTPException(status_code=401, detail="Incorrect password")

    # Генерация JWT токена
    while (access_token := create_access_token(data={"sub": adm.login})) in blacklist:
        continue
    return {"access_token": access_token, "token_type": "bearer"}


# Вход ведущего
@app.post("/host/login")
async def register_admin(host: UserLogin, db: Session = Depends(get_db)):
    h = db.query(Host).filter(Host.login == host.login).first()
    if not h:
        raise HTTPException(status_code=401, detail="Incorrect user")
    if h.password != host.password:
        raise HTTPException(status_code=401, detail="Incorrect password")

    # Генерация JWT токена
    while (access_token := create_access_token(data={"sub": h.login})) in blacklist:
        continue
    return {"access_token": access_token, "token_type": "bearer"}


# Изменение категории
@app.post("/admin/editCategory")
async def edit_category(category_id: int, category: CategoryCreate, db: Session = Depends(get_db),
                        token: str = Depends(oauth2_scheme)):
    verify_access_token(token)
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


@app.post("/admin/editSetByID")
async def edit_set_by_id(set_id: int, name: str, cards: List[int], db: Session = Depends(get_db),
                         token: str = Depends(oauth2_scheme)):
    verify_access_token(token)
    db_set = db.query(Set).filter(Set.id == set_id).first()
    if not db_set:
        raise HTTPException(status_code=404, detail="Set not found")

    db_set.name = name
    db_set.cards = cards
    db.commit()
    db.refresh(db_set)

    return {"message": "Set updated successfully!", "set_id": db_set.id}


@app.post("/admin/editCardByID")
async def edit_card_by_id(card_id: int, description: str, tags: List[str], db: Session = Depends(get_db)):
    db_card = db.query(Card).filter(Card.id == card_id).first()
    if not db_card:
        raise HTTPException(status_code=404, detail="Card not found")

    db_card.description = description
    db_card.hashtags = ",".join(tags)
    db.commit()
    db.refresh(db_card)

    return {"message": "Card updated successfully!"}


# Создание игры
@app.post("/admin/new-game")
async def new_game(game_data: GameCreate, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    verify_access_token(token)
    # Создание нового игрового объекта
    new_game = Game(
        name=game_data.name
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
        "name": new_game.name
    }


# Получение списка категорий
@app.get("/admin/getCategories")
async def get_categories(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    verify_access_token(token)
    categories = db.query(Category).all()
    return [{"id": category.id, "name": category.name, "color": category.color} for category in categories]


# Создание категории
@app.post("/admin/createCategory")
async def create_category(category: CategoryCreate, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    verify_access_token(token)
    new_category = Category(name=category.name, color=category.color)
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return {"message": "Category created successfully!", "category_id": new_category.id}


# Получение информации о наборе
@app.post("/admin/getSetInfo")
async def get_set_info(set_id: int, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    verify_access_token(token)
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


@app.post("/admin/addCardByCategoryID")
async def add_card_by_category_id(category_id: int, description: str, tags: List[str], db: Session = Depends(get_db)):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    main_set = db.query(Set).filter(Set.category_id == category_id).first()
    if not main_set:
        main_set = Set(name="Main Set", category_id=category_id)
        db.add(main_set)
        db.commit()
        db.refresh(main_set)

    new_card = Card(
        number=len(category.cards) + 1,
        description=description,
        hashtags=",".join(tags),
        set_id=main_set.id,
        category_id=category_id
    )
    db.add(new_card)
    db.commit()
    db.refresh(new_card)

    return {"message": "Card added successfully!", "card_id": new_card.id}


# Удаление категории
# TODO(исправить category_id)
@app.post("/admin/deleteCategory")
async def delete_category(category_id: int, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    verify_access_token(token)
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
async def delete_card(card_id: int, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    verify_access_token(token)
    # Находим карточку по id
    card = db.query(Card).filter(Card.number == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    # Удаляем карточку
    db.delete(card)
    db.commit()

    return {"message": "Card deleted successfully!"}


# Удаление набора
@app.post("/admin/deleteSetByID")
async def delete_set(set_id: int, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    verify_access_token(token)
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

    return {"message": "Set deleted successfully!"}


# Создание ведущего
@app.post("/admin/createHost")
async def create_host(host: UserCreate, db: Session = Depends(get_db)):
    new_host = Host(login=host.login, password=host.password)
    db.add(new_host)
    db.commit()
    db.refresh(new_host)
    return {"message": "Host created successfully!", "host_id": new_host.id}


# Получение информации о карте
@app.post("/admin/getCardInfo")
async def get_card_info(card_id: int, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    verify_access_token(token)
    card_info = db.query(Card).filter(Card.id == card_id).first()
    if not card_info:
        raise HTTPException(status_code=404, detail="Card not found")

    card_data = {
        "number": f'{card_info.category_id}.{card_info.number}',
        "description": card_info.description,
    }

    return {"card_data": card_data}


@app.get("/admin/getCategoryData")
async def get_category_data(category_id: int, db: Session = Depends(get_db)):
    # verify_access_token(token)
    category_data = db.query(Category).filter(category_id == Category.id).first()
    cards = category_data.cards
    sets = category_data.sets
    card_data = []
    set_data = []
    for card in cards:
        card_data.append({
            "id": card.id,
            "description": card.description,
            "tags": card.hashtags
        })

    for set in sets:
        if not (set.name.startswith("Main Set")):
            set_data.append({
                "id": set.id,
                "name": set.name,
            })
    return {"name": category_data.name, "color": category_data.color, "cards": card_data, "sets": set_data}


@app.post("/admin/editGame")
async def edit_game(db: Session = Depends(get_db)):
    pass


@app.get("/admin/logout")
async def admin_logout(token: str):
    verify_access_token(token)
    blacklist.add(token)
    return {"message": "Admin logged out successfully"}


@app.get("/host/logout")
async def host_logout(token: str):
    verify_access_token(token)
    blacklist.add(token)
    return {"message": "Host logged out successfully"}


@app.post("/admin/checkAuth")
async def check_auth_admin(token: str = Depends(oauth2_scheme)):
    username = verify_access_token(token)
    if username != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return {"message": "Admin is authorized"}


@app.post("/host/checkAuth")
async def check_auth(token: str = Depends(oauth2_scheme)):
    username = verify_access_token(token)
    if username != "host":
        raise HTTPException(status_code=403, detail="Host privileges required")
    return {"message": "Host is authorized"}


from fastapi import Form


# Эндпоинт для получения токена
@app.post("/token")
async def login(form_data: UserLogin, db: Session = Depends(get_db)):
    # Поиск пользователя в базе данных
    adm = db.query(Admin).filter(Admin.login == form_data.login).first()

    if not adm:
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    access_token = create_access_token(data={"sub": adm.login})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/admin/getHosts")
async def get_hosts(db: Session = Depends(get_db)):
    hosts = db.query(Host).all()
    return [{"id": host.id, "login": host.login, "password": host.password} for host in hosts]


@app.post("/admin/editHost")
async def edit_host(host: HostCreate, db: Session = Depends(get_db)):
    db_host = db.query(Host).filter(Host.id == host.id).first()
    if not db_host:
        raise HTTPException(status_code=404, detail="Host not found")

    db_host.login = host.login
    db_host.password = host.password
    db.commit()
    db.refresh(db_host)

    return {"message": "Host updated successfully!"}


@app.post("/admin/deleteHostByID")
async def delete_host_by_id(host_id: int, db: Session = Depends(get_db)):
    db_host = db.query(Host).filter(Host.id == host_id).first()
    if not db_host:
        raise HTTPException(status_code=404, detail="Host not found")

    db.delete(db_host)
    db.commit()

    return {"message": "Host deleted successfully!"}


@app.post("/admin/addSetByCategoryID")
async def add_set_by_category_id(category_id: int, name: str, cards: List[int], db: Session = Depends(get_db)):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    new_set = Set(name=name, category_id=category_id)
    db.add(new_set)
    db.commit()
    db.refresh(new_set)

    # Добавление карточек в набор через промежуточную таблицу
    for card_id in cards:
        card = db.query(Card).filter(Card.id == card_id).first()
        if not card:
            raise HTTPException(status_code=404, detail=f"Card with id {card_id} not found")

        # Проверка, существует ли уже связь между набором и карточкой
        existing_association = db.query(set_card_association).filter(
            set_card_association.c.set_id == new_set.id,
            set_card_association.c.card_id == card.id
        ).first()

        if not existing_association:
            new_set.cards.append(card)

    db.commit()
    db.refresh(new_set)

    return {"message": "Set added successfully!", "set_id": new_set.id}
