import os
from dotenv import load_dotenv
from datetime import timedelta

# Load the environment variable from .env file
load_dotenv()

class Config:
    _raw_database_url = os.getenv('DATABASE_URL')

    if not _raw_database_url:
        raise ValueError("DATABASE_URL is not configure in .env file!")

    if _raw_database_url.startswith("postgres://"):
        _raw_database_url = _raw_database_url.replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_DATABASE_URI = _raw_database_url

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 280,
        "pool_size": 5,
        "max_overflow": 2,
    }


    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')

    if not JWT_SECRET_KEY:
        raise ValueError("JWT_SECRET_KEY is not configured in .env file!")

    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)

    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*')