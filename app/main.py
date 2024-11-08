from fastapi import FastAPI, HTTPException, Depends
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


# Регистрация админа
@app.post("/login-admin")
async def register_admin(admin: UserCreate, db: Session = Depends(get_db)):
    print(admin.login, admin.password)
    new_admin = Admin(login=admin.login, password=admin.password)
    db.add(new_admin)
    try:
        db.commit()
        db.refresh(new_admin)
        return {"message": "Admin created successfully!"}
    except exc.IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Username already exists")


# Вход админа
@app.post("/admin/login")
async def login_admin(admin: UserLogin, db: Session = Depends(get_db)):
    user = db.query(Admin).filter(Admin.username == admin.username).first()
    if not user or not verify_password(user.password, admin.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"message": "Login successful", "user_id": user.id}


# Создание категории
@app.post("/category/")
async def create_category(category: CategoryCreate, db: Session = Depends(get_db)):
    new_category = Category(name=category.name, color=category.color)
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return {"message": "Category created successfully!", "category_id": new_category.id}


# Создание набора
@app.post("/set/")
async def create_set(set_data: SetCreate, db: Session = Depends(get_db)):
    new_set = Set(name=set_data.name, category_id=set_data.category_id)
    db.add(new_set)
    db.commit()
    db.refresh(new_set)
    return {"message": "Set created successfully!", "set_id": new_set.id}


# Создание карточки
@app.post("/card/")
async def create_card(card_data: CardCreate, db: Session = Depends(get_db)):
    new_card = Card(
        number=card_data.number,
        description=card_data.description,
        hashtags=",".join(card_data.hashtags),
        set_id=card_data.set_id
    )
    db.add(new_card)
    db.commit()
    db.refresh(new_card)
    return {"message": "Card created successfully!", "card_id": new_card.id}


# Создание игры
@app.post("/game/start")
async def start_game(game_data: GameCreate, db: Session = Depends(get_db)):
    game_code = str(uuid.uuid4())  # Генерация уникального кода игры
    new_game = Game(game_code=game_code, host_id=game_data.host_id)
    db.add(new_game)
    db.commit()
    db.refresh(new_game)
    return {"message": "Game started successfully!", "game_code": game_code}


# Генерация QR-кода
@app.get("/game/{game_code}/qr")
async def generate_qr(game_code: str):
    qr = qrcode.make(game_code)
    qr.save(f"C:\\Users\\Venya\\PycharmProjects\\backend\\{game_code}.png")
    return {"message": f"QR code generated for game {game_code}", "qr_code_path": f"qr_codes/{game_code}.png"}
