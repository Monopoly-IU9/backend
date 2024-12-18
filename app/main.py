from datetime import datetime, timedelta
from typing import List
import random

from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Depends, HTTPException
from app.models import Admin, Host, Category, Set, Card, Game, Base, GameCategoryAssociation, SetCardAssociation, \
    GameSetAssociation
from app.database import SessionLocal, engine
from app.schemas import UserLogin, CategoryCreate, CardCreate, GameCreate, UserCreate, SetCreate, CardInSet, HostCreate, \
    Card_add, SetEdit, CardEdit, GameEdit
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


# Создание категории
@app.post("/admin/createCategory")
async def create_category(category: CategoryCreate, db: Session = Depends(get_db)):
    # Проверка на уникальность названия
    existing_category = db.query(Category).filter(Category.name == category.name).first()
    if existing_category:
        raise HTTPException(status_code=400, detail="Category name must be unique")

    # Создание
    new_category = Category(name=category.name, color=category.color)
    db.add(new_category)
    db.commit()
    db.refresh(new_category)

    # Создание main_set для новой категории
    main_set = Set(name=f'Main Set ({category.name})', category_id=new_category.id)
    db.add(main_set)
    db.commit()
    db.refresh(main_set)

    return {"message": "Category created successfully!", "category_id": new_category.id}


# Редактирование категории
@app.post("/admin/editCategory")
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


# Данные о всех категориях
@app.get("/admin/getCategories")
async def get_categories(db: Session = Depends(get_db)):
    # Получение всех категорий
    categories = db.query(Category).all()
    return [{"id": category.id, "name": category.name, "color": category.color} for category in categories]


#
@app.post("/admin/deleteCategory")
async def delete_category(category_id: int, db: Session = Depends(get_db)):
    # Получаем категорию по id
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    # Удаляем все наборы, связанные с категорией
    sets = db.query(Set).filter(Set.category_id == category_id).all()
    for set_ in sets:
        # Удаляем все карточки, связанные с набором через промежуточную таблицу
        set_card_associations = db.query(SetCardAssociation).filter(SetCardAssociation.set_id == set_.id).all()
        for association in set_card_associations:
            db.delete(association)
        # Удаляем набор
        db.delete(set_)
    cards = db.query(Card).filter(Card.category_id == category_id).all()
    for card in cards:
        db.delete(card)

    # Удаляем категорию
    db.delete(category)
    db.commit()

    return {"message": "Category and all associated sets and cards deleted successfully!"}


@app.get("/admin/getCategoryData")
async def get_category_data(category_id: int, db: Session = Depends(get_db)):
    category_data = db.query(Category).filter(category_id == Category.id).first()
    cards = category_data.cards
    sets = category_data.sets
    card_data = []
    set_data = []
    for card in cards:
        card_data.append({
            "id": card.id,
            "description": card.description,
            "tags": card.hashtags.split(',')
        })

    for set in sets:
        if not (set.name.startswith("Main Set")):
            set_data.append({
                "id": set.id,
                "name": set.name,
            })
    return {"name": category_data.name, "color": category_data.color, "cards": card_data, "sets": set_data}


# Функции для работы с наборами
@app.post("/admin/addSetByCategoryID")
async def addSetByCategoryID(set_data: SetCreate, db: Session = Depends(get_db)):
    # Проверка существования категории
    category = db.query(Category).filter(Category.id == set_data.category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    # Проверка на уникальность названия
    existing_set = db.query(Set).filter(Set.name == set_data.name).first()
    if existing_set:
        raise HTTPException(status_code=400, detail="Set name must be unique")

    # Создание нового набора
    new_set = Set(name=set_data.name, category_id=set_data.category_id)
    db.add(new_set)
    db.commit()
    db.refresh(new_set)

    # Добавление карточек в набор
    for card_id in set_data.cards:
        card = db.query(Card).filter(Card.id == card_id).first()
        if not card:
            raise HTTPException(status_code=404, detail=f"Card with id {card_id} not found")
        new_set.cards.append(card)

    db.commit()
    db.refresh(new_set)

    return {"message": "Set created successfully!", "set_id": new_set.id}


@app.post("/admin/editSetByID")
async def edit_set_by_id(set_id: int, set: SetEdit, db: Session = Depends(get_db)):
    db_set = db.query(Set).filter(Set.id == set_id).first()
    if not db_set:
        raise HTTPException(status_code=404, detail="Set not found")

    db_set.name = set.name
    db_set.cards = [db.query(Card).filter(Card.id == card_id).first() for card_id in
                    set.cards]
    db.commit()
    db.refresh(db_set)

    return {"message": "Set updated successfully!", "set_id": db_set.id}


@app.post("/admin/deleteSetByID")
async def delete_set(set_id: int, db: Session = Depends(get_db)):
    db_set = db.query(Set).filter(Set.id == set_id).first()
    if not db_set:
        raise HTTPException(status_code=404, detail="Set not found")
    if db_set.name.startswith("Main Set"):
        raise HTTPException(status_code=400, detail="You cannot delete the main set")

    set_card_associations = db.query(SetCardAssociation).filter(SetCardAssociation.set_id == set_id).all()
    for association in set_card_associations:
        db.delete(association)
    # Удаление всех карточек, связанных с набором
    for card in db_set.cards:
        db.delete(card)

    db.delete(db_set)
    db.commit()

    return {"message": "Set deleted successfully!"}


@app.post("/admin/getSetInfo")
async def get_set_info(set_id: int, db: Session = Depends(get_db)):
    set_info = db.query(Set).filter(Set.id == set_id).first()
    if not set_info:
        raise HTTPException(status_code=404, detail="Set not found")

    # Получаем карточки через промежуточную таблицу SetCardAssociation
    set_card_associations = db.query(SetCardAssociation).filter(SetCardAssociation.set_id == set_id).all()
    cards = [db.query(Card).filter(Card.id == association.card_id).first() for association in set_card_associations]

    set_data = {
        "name": set_info.name,
        "cards": [{"id": card.id, "number": card.number, "description": card.description, "hashtags": card.hashtags} for
                  card in cards]
    }

    return set_data


# Функции для работы с карточками
@app.post("/admin/addCardByCategoryID")
async def add_card_by_category_id(card: Card_add, db: Session = Depends(get_db)):
    category = db.query(Category).filter(Category.id == card.category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    main_set = db.query(Set).filter(Set.category_id == card.category_id, Set.name.startswith("Main Set")).first()
    if not main_set:
        main_set = Set(name="Main Set", category_id=card.category_id)
        db.add(main_set)
        db.commit()
        db.refresh(main_set)

    new_card = Card(
        number=len(category.cards) + 1,
        description=card.description,
        hashtags=",".join(card.hashtags),
        category_id=card.category_id
    )
    db.add(new_card)
    db.commit()
    db.refresh(new_card)

    # Добавление карточки в main_set
    main_set.cards.append(new_card)
    db.commit()

    return {"message": "Card added successfully!", "card_id": new_card.id}


@app.post("/admin/editCardByID")
async def edit_card_by_id(card_id: int, card: CardEdit, db: Session = Depends(get_db)):
    db_card = db.query(Card).filter(Card.id == card_id).first()
    if not db_card:
        raise HTTPException(status_code=404, detail="Card not found")

    db_card.description = card.description
    db_card.hashtags = ",".join(card.hashtags)
    db.commit()
    db.refresh(db_card)

    return {"message": "Card updated successfully!"}


@app.post("/admin/deleteCard")
async def delete_card(card_id: int, db: Session = Depends(get_db)):
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    # Удаление карточки из всех наборов
    for set_ in card.sets:
        set_.cards.remove(card)

    db.delete(card)
    db.commit()

    return {"message": "Card deleted successfully!"}


@app.post("/admin/getCardInfo")
async def get_card_info(card_id: int, db: Session = Depends(get_db)):
    card_info = db.query(Card).filter(Card.id == card_id).first()
    if not card_info:
        raise HTTPException(status_code=404, detail="Card not found")

    card_data = {
        "number": f'{card_info.category_id}.{card_info.number}',
        "description": card_info.description,
    }

    return {"card_data": card_data}


# Функции для работы с ведущими
@app.post("/admin/createHost")
async def create_host(host: UserCreate, db: Session = Depends(get_db)):
    new_host = Host(login=host.login, password=host.password)
    db.add(new_host)
    db.commit()
    db.refresh(new_host)
    return {"message": "Host created successfully!", "host_id": new_host.id}


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


# Функции для работы с админами
@app.get("/admin/logout")
async def admin_logout(token: str):
    blacklist.add(token)
    return {"message": "Admin logged out successfully"}


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


# Эндпоинт для получения токена
@app.post("/token")
async def login(form_data: UserLogin, db: Session = Depends(get_db)):
    # Поиск пользователя в базе данных
    adm = db.query(Admin).filter(Admin.login == form_data.login).first()

    if not adm:
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    access_token = create_access_token(data={"sub": adm.login})
    return {"access_token": access_token, "token_type": "bearer"}


# Функции для работы с играми
@app.post("/admin/new-game")
async def new_game(game_data: GameCreate, db: Session = Depends(get_db)):
    new_game = Game(
        name=game_data.name,
        start_time=None,
        status="waiting",
        initial_deck=None,
        deck=None,
        hashtags=",".join(game_data.hashtags)
    )
    existing_game = db.query(Game).filter(Game.name == game_data.name).first()
    if existing_game:
        raise HTTPException(status_code=400, detail="Game name must be unique")
    # Добавление игры в базу данных
    db.add(new_game)
    db.commit()
    db.refresh(new_game)
    for set_id in game_data.sets:
        s = db.query(Set).filter(Set.id == set_id).first()
        if not s:
            raise HTTPException(status_code=404, detail=f"Set with id {set_id} not found")
        new_game.sets.append(s)

    for category_id in game_data.categories:
        c = db.query(Category).filter(Category.id == category_id).first()
        if not c:
            raise HTTPException(status_code=404, detail=f"Category with id {category_id} not found")
        new_game.categories.append(c)

    db.commit()
    db.refresh(new_game)

    # Возвращаем информацию о созданной игре
    return {
        "message": "Game created successfully!",
        "id": new_game.id
    }


@app.post("/host/start-game/{game_id}")
async def start_game(game_id: int, db: Session = Depends(get_db)):
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    if game.status != "waiting":
        raise HTTPException(status_code=400, detail="Game is already started")
    hashtags_game = game.hashtags.split(",")
    deck = []
    sets = game.sets
    all_cards = set()
    for set_ in sets:
        set_card_associations = db.query(SetCardAssociation).filter(SetCardAssociation.set_id == set_.id).all()
        for association in set_card_associations:
            card = db.query(Card).filter(association.card_id == Card.id).first()
            hashtags_card = card.hashtags.split(",")
            # Проверка на принадлежность хештегов карты в хештегах игры
            for h in hashtags_card:
                if h in hashtags_game:
                    all_cards.add(card.id)
                    break
    all_cards = list(all_cards)
    for a_c_id in all_cards:
        card = db.query(Card).filter(Card.id == a_c_id).first()
        deck.append(f'{str(a_c_id)}.{card.category_id}')

    random.shuffle(deck)

    game.initial_deck = ','.join(deck)
    game.deck = ','.join(deck)
    game.status = "started"
    game.start_time = datetime.utcnow()
    db.commit()
    db.refresh(game)

    return {"message": "Game started successfully!", "game_id": game.id}


@app.post("/game/draw-card/{game_id}")
async def draw_card(game_id: int, category_id: int, db: Session = Depends(get_db)):
    game = db.query(Game).filter(Game.id == game_id).first()
    category = db.query(Category).filter(Category.id == category_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    if game.status != "started":
        raise HTTPException(status_code=400, detail="Game is not started")
    deck = game.deck.split(',')
    found = False
    if deck[0] == '' and len(deck) == 1:
        deck = []
    # Поиск карты из нужной категории
    for d in deck:
        card_id, categ_id = d.split('.')
        if int(categ_id) == category_id:
            found = True
            break
    # Заполнение недостающими картами из категории
    if not found:
        init_deck = game.initial_deck.split(',')
        for i in init_deck:
            card_id, categ_id = i.split('.')
            if int(categ_id) == category_id:
                deck.append(f'{card_id}.{categ_id}')
    random.shuffle(deck)
    c_id = 0
    k = 0
    # Получение id карточки
    for d in deck:
        k += 1
        card_id, categ_id = d.split('.')
        if int(categ_id) == category_id:
            c_id = card_id
            deck.pop(k - 1)
            break
    game.deck = ','.join(deck)
    card = db.query(Card).filter(Card.id == c_id).first()
    card_data = {
        "number": f'{category_id}.{card.number}',
        "description": card.description,
        "color": category.color,
        "name": category.name
    }
    db.commit()
    db.refresh(game)
    return card_data


@app.post("/host/finish-game/{game_id}")
async def finish_game(game_id: int, db: Session = Depends(get_db)):
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    if game.status != "started":
        raise HTTPException(status_code=400, detail="Game is not started")
    game.deck = None
    game.initial_deck = None
    game.status = "waiting"
    game.start_time = None
    db.commit()
    db.refresh(game)

    return {"message": "Game finished successfully!", "game_id": game.id}


@app.get("/admin/check-game-status/{game_id}")
async def check_game_status(game_id: int, db: Session = Depends(get_db)):
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    if game.status == "started" and game.start_time:
        elapsed_time = datetime.utcnow() - game.start_time
        if elapsed_time > timedelta(hours=12):
            game.status = "waiting"
            db.commit()
            db.refresh(game)
    return {"game_id": game.id, "status": game.status}


@app.get("/admin/getGames")
async def admin_get_games(db: Session = Depends(get_db)):
    games = db.query(Game).all()
    return [{"id": game.id, "name": game.name} for game in games]


@app.get("/host/getGames")
async def host_get_games(db: Session = Depends(get_db)):
    games = db.query(Game).all()
    return [{"id": game.id, "name": game.name, "status": game.status} for game in games]


@app.post("/host/getCategoriesByGameID")
@app.post("/admin/getCategoriesByGameID")
async def get_categories_by_game_id(game_id: int, db: Session = Depends(get_db)):
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    # Получаем все категории, связанные с игрой
    categories = game.categories

    category_data = []
    for category in categories:
        category_data.append({
            "id": category.id,
            "name": category.name,
            "color": category.color
        })

    return {"game_id": game.id, "categories": category_data}


@app.get("/admin/getgameInfo/{game_id}")
async def get_game_info(game_id: int, db: Session = Depends(get_db)):
    # название игры, список категорий с флагами, список сетов с флагами, хештеги с флагами
    game = db.query(Game).filter(Game.id == game_id).first()
    # Получение всех категорий в игре
    categories_in_game = db.query(GameCategoryAssociation).filter(GameCategoryAssociation.game_id == game_id).all()
    # Получение всех наборов в игре
    sets_in_game = db.query(GameSetAssociation).filter(GameSetAssociation.game_id == game_id).all()
    # Список id наборов в игре
    id_set_list = [s.set_id for s in sets_in_game]
    # Список id категорий  в игре
    id_category_list = [categ.category_id for categ in categories_in_game]
    # Получение всех категорий (которые вообще существуют)
    all_categories = db.query(Category).all()
    # Получение всех сетов (которые вообще существуют)
    all_sets = db.query(Set).all()
    id_all_sets = [s.id for s in all_sets]
    game_data = dict()
    game_data["name"] = game.name
    category_data = []
    for c in all_categories:
        sets_in_category = db.query(Set).filter(Set.category_id == c.id).all()
        sets_dict = []
        for s in sets_in_category:
            sets_dict.append({
                "id": s.id,
                "name": s.name,
                "in_category": s.id in id_set_list
            })
        category_data.append({
            "id": c.id,
            "name": c.name,
            "in_game": c.id in id_category_list,
            "sets": sets_dict
        })
    game_data["categories"] = category_data
    list_of_all_hashtags = set()
    hash_list = []
    for id_s in id_all_sets:
        cards = db.query(SetCardAssociation).filter(SetCardAssociation.set_id == id_s).all()
        for i in cards:
            card = db.query(Card).filter(Card.id == i.card_id).first()
            for h in card.hashtags.split(','):
                list_of_all_hashtags.add(h)
    for h in list_of_all_hashtags:
        hash_list.append({
            "name": h,
            "in_game": h in game.hashtags.split(',')
        })
    game_data["hashtags"] = hash_list
    return game_data


@app.post("/admin/editGame/{game_id}")
async def edit_game(game_id: int, game: GameEdit, db: Session = Depends(get_db)):
    # Поиск игры по ID
    db_game = db.query(Game).filter(Game.id == game_id).first()
    # Проверка, существует ли игра
    if not db_game:
        raise HTTPException(status_code=404, detail="Game not found")
    # Проверка на уникальность названия
    existing_game = db.query(Game).filter(Game.name == game.name).first()
    if existing_game and existing_game.id != game_id:
        raise HTTPException(status_code=400, detail="Game name must be unique")
    db_game.name = game.name
    db_game.categories = [db.query(Category).filter(Category.id == category_id).first() for category_id in
                          game.categories]
    db_game.sets = [db.query(Set).filter(Set.id == set_id).first() for set_id in game.sets]
    db_game.hashtags = ",".join(game.hashtags)
    # Применение изменений
    db.commit()
    db.refresh(db_game)
    return {"message": "Game updated successfully!", "game_id": db_game.id}


@app.post("/admin/deleteGameByID")
async def delete_game(game_id: int, db: Session = Depends(get_db)):
    # Поиск игры по ID
    db_game = db.query(Game).filter(Game.id == game_id).first()

    # Проверка, существует ли игра
    if not db_game:
        raise HTTPException(status_code=404, detail="Game not found")

    # Удаление игры и всех связанных записей
    db.delete(db_game)
    db.commit()

    return {"message": "Game deleted successfully!", "game_id": game_id}
