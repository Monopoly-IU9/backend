from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
DATABASE_URL = "mysql+pymysql://u2575528_default:xC1hJ2gA4deT0cF2@localhost/u2575528_default"  # Важно, что база данных будет сохраняться в файл

# Создаем подключение к базе данных
engine = create_engine(DATABASE_URL)

# Создаем базовый класс для всех моделей
Base = declarative_base()

# Создаем сессию для работы с базой данных
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
