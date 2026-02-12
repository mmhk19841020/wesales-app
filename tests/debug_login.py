"""
デバッグ用スクリプト: テスト環境でのログイン動作を確認
"""
from app import create_app
from extensions import db
from models import User
from flask_bcrypt import generate_password_hash

class TestConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = False
    SECRET_KEY = "test-secret-key-for-testing"
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    VISION_KEY = ""
    VISION_ENDPOINT = ""
    OPENAI_KEY = ""
    OPENAI_ENDPOINT = ""
    OPENAI_DEPLOYMENT = ""
    GEMINI_API_KEY = ""
    AI_ENGINE_TYPE = "azure"
    RESEND_API_KEY = ""
    UPLOAD_FOLDER = "static/uploads/cards"

app = create_app(TestConfig)

with app.app_context():
    db.create_all()
    user = User(
        username="testuser",
        password=generate_password_hash("testpassword").decode('utf-8'),
        is_admin=False
    )
    db.session.add(user)
    db.session.commit()
    
    client = app.test_client()
    
    # ログインテスト
    with client:
        response = client.post("/login", data={
            "username": "testuser",
            "password": "testpassword"
        })
        print(f"Login response status: {response.status_code}")
        print(f"Login response location: {response.location}")
        
        # ログイン後に名刺一覧にアクセス
        response2 = client.get("/cards")
        print(f"Cards list response status: {response2.status_code}")
        print(f"Cards list response location: {response2.location if hasattr(response2, 'location') else 'N/A'}")
        
        if response2.status_code != 200:
            print("Failed to access cards list after login")
        else:
            print("Successfully accessed cards list!")
