import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException, Security
from fastapi.security import OAuth2PasswordBearer
from typing import Optional

from sqlalchemy.orm import Session

# Секретный ключ для подписывания токенов
SECRET_KEY = "9d5f2b2e6f5a2e7b788d9e4e7e07c4b3a6a01f44b5e74fb87a8232c2f4ab27a1"
ALGORITHM = "HS256"

# OAuth2PasswordBearer - стандартная схема для получения токена из заголовков
#oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/admin-login")


# Функция для создания JWT токена
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=1)  # по умолчанию срок жизни токена 1 час
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# Функция для проверки и декодирования токена
def verify_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        print(username)
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    return username


'''def get_current_user(token: str = Security(oauth2_scheme)):
    try:
        payload = verify_access_token(token)
        return payload  # Возвращаем данные о пользователе
    except HTTPException:
        raise HTTPException(status_code=401, detail="Invalid or expired token")'''
