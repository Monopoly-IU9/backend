import jwt
from datetime import datetime, timedelta
from typing import Optional
#from passlib.context import CryptContext

# Секретный ключ и алгоритм для подписи токенов
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # Время жизни токена (в минутах)

# Инициализация контекста для хэширования паролей
#pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Функция для создания токена
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = data.copy()
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# Функция для проверки и декодирования токена
def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise Exception("Token has expired")
    except jwt.JWTError:
        raise Exception("Token is invalid")


# Функция для проверки пароля
#def verify_password(plain_password, hashed_password):
   # return pwd_context.verify(plain_password, hashed_password)


# Функция для получения пользователя из "базы данных" (в данном случае просто словарь)
def get_user(db, username: str):
    if username in db:
        return db[username]
    return None
