"""Settings for each environment: development, testing and production."""
import os
from datetime import timedelta
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))


class Config:
    """Settings shared by every environment, read from .env (never hard-coded)."""
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")
    DEMO_USER = os.getenv("DEMO_USER", "manager")
    DEMO_PASSWORD = os.getenv("DEMO_PASSWORD", "takt2026")
        PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT = int(os.getenv("DB_PORT", "3306"))
    DB_USER = os.getenv("DB_USER", "avnadmin")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "defaultdb")
    DEBUG = False
    TESTING = False


class DevelopmentConfig(Config):
    """Your laptop: debug mode on, so errors show useful details."""
    DEBUG = True


class TestingConfig(Config):
    """Used when running pytest."""
    TESTING = True


class ProductionConfig(Config):
    """A live server: debug stays off, so users never see error details."""


CONFIGS = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}