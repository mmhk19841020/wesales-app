import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask settings
    SECRET_KEY = os.environ.get("SECRET_KEY", "fallback-secret-key-for-dev")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Path settings
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "users.db")
    UPLOAD_FOLDER = os.path.join("static", "uploads", "cards")

    # AI settings
    VISION_KEY = os.environ.get("VISION_KEY", "")
    VISION_ENDPOINT = os.environ.get("VISION_ENDPOINT", "")
    OPENAI_KEY = os.environ.get("OPENAI_KEY", "")
    OPENAI_ENDPOINT = os.environ.get("OPENAI_ENDPOINT", "")
    OPENAI_DEPLOYMENT = os.environ.get("OPENAI_DEPLOYMENT", "")
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
    AI_ENGINE_TYPE = os.environ.get("AI_ENGINE_TYPE", "azure").lower()

    # Email settings
    RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")

    # Security settings (Session)
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
