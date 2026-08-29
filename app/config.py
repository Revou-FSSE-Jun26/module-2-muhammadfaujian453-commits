import os
from dotenv import load_dotenv
from datetime import timedelta

# Load the environment variable from .env file
load_dotenv()

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')

    if not SQLALCHEMY_DATABASE_URI:
        raise ValueError("DATABASE_URL is not configure in .env file!")

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 280,
    }

    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')

    if not JWT_SECRET_KEY:
        raise ValueError("JWT_SECRET_KEY is not configured in .env file!")

    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)

    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*')