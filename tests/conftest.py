import pytest
from app import create_app
from extensions import db
from models import User, Card
from flask_bcrypt import generate_password_hash
from flask_login import login_user

class TestConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = False
    SECRET_KEY = "test-secret-key-for-testing"
    
    # Session settings
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Disable login manager's redirect
    LOGIN_DISABLED = False
    
    # AI settings (ダミー値)
    VISION_KEY = ""
    VISION_ENDPOINT = ""
    OPENAI_KEY = ""
    OPENAI_ENDPOINT = ""
    OPENAI_DEPLOYMENT = ""
    GEMINI_API_KEY = ""
    AI_ENGINE_TYPE = "azure"
    
    # Email settings
    RESEND_API_KEY = ""
    
    # Path settings
    UPLOAD_FOLDER = "static/uploads/cards"

@pytest.fixture(scope='function')
def app():
    app = create_app(TestConfig)
    
    with app.app_context():
        db.create_all()
        
        # テスト用の一般ユーザー作成
        user = User(
            username="testuser",
            password=generate_password_hash("testpassword").decode('utf-8'),
            is_admin=False
        )
        # 管理者ユーザー作成
        admin = User(
            username="admin",
            password=generate_password_hash("adminpassword").decode('utf-8'),
            is_admin=True
        )
        db.session.add(user)
        db.session.add(admin)
        db.session.commit()
        
        yield app
        
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """テストクライアントを返す"""
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()

@pytest.fixture
def auth_client(app):
    """一般ユーザーでログイン済みのクライアント
    
    Flask-Loginのセッション管理を正しく扱うため、
    実際のログインエンドポイントを使用します。
    """
    client = app.test_client()
    
    # ログインリクエストを送信（follow_redirectsなしで）
    response = client.post("/login", data={
        "username": "testuser",
        "password": "testpassword"
    })
    
    # ログインが成功したことを確認（リダイレクトされる）
    assert response.status_code == 302
    
    return client

@pytest.fixture
def admin_client(app):
    """管理者ユーザーでログイン済みのクライアント"""
    client = app.test_client()
    
    response = client.post("/login", data={
        "username": "admin",
        "password": "adminpassword"
    })
    
    assert response.status_code == 302
    
    return client
