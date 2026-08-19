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

    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'default-secret-key-fallback')
    JWT_ACCESS_TOKEN_EXPIRESS = timedelta(hours=1)