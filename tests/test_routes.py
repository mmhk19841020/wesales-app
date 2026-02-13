import pytest
import io
import json
from unittest.mock import patch
from extensions import db
from models import Card, User

def test_login_page(client):
    """ログイン画面が表示されるか"""
    response = client.get("/login")
    assert response.status_code == 200
    assert "ログイン".encode("utf-8") in response.data

def test_login_success(client):
    """正しくログインできるか"""
    response = client.post("/login", data={
        "username": "testuser",
        "password": "testpassword"
    }, follow_redirects=True)
    assert response.status_code == 200
    assert "testuser".encode("utf-8") in response.data

def test_cards_list_requires_login(client):
    """未ログイン時は一覧にアクセスできないか"""
    response = client.get("/cards", follow_redirects=True)
    assert "ログイン".encode("utf-8") in response.data

def test_cards_list_authenticated(auth_client):
    """ログイン済みなら一覧が表示されるか"""
    response = auth_client.get("/cards")
    assert response.status_code == 200
    assert "名刺一覧".encode("utf-8") in response.data

@patch("routes.cards.analyze_card_image")
def test_upload_card_mocked(mock_analyze, auth_client):
    """名刺アップロードのモックテスト"""
    mock_analyze.return_value = {
        "name": "テスト 太郎",
        "company": "モック株式会社",
        "department": "技術部",
        "title": "技師",
        "url": "https://mock.example.com",
        "email": "test@mock.example.com",
        "phone": "000-0000-0000"
    }
    
    data = {
        "image": (io.BytesIO(b"fake-image-data"), "test.jpg")
    }
    response = auth_client.post("/upload", data=data, content_type="multipart/form-data")
    assert response.status_code == 200
    res_data = json.loads(response.data)
    assert res_data["message"] == "登録完了"
    
    # DBに登録されているか確認
    card = Card.query.filter_by(person_name="テスト 太郎").first()
    assert card is not None
    assert card.company_name == "モック株式会社"

@patch("routes.cards.get_company_info")
@patch("routes.cards.get_ai_completion")
def test_generate_email_mocked(mock_ai, mock_web, auth_client, app):
    """メール生成画面のモックテスト"""
    mock_ai.return_value = json.dumps({
        "subject": "テスト件名",
        "body": "これはモックされたメール本文です。"
    })
    mock_web.return_value = "モックされた企業情報"
    
    with app.app_context():
        user = User.query.filter_by(username="testuser").first()
        # テストデータをクリーンに
        Card.query.filter_by(email="dest@example.com").delete()
        card = Card(user_id=user.id, person_name="送信先様", email="dest@example.com", url="https://example.com")
        db.session.add(card)
        db.session.commit()
        card_id = card.id

    response = auth_client.get(f"/api/generate_initial_email/{card_id}")
    assert response.status_code == 200
    res_data = json.loads(response.data)
    assert "これはモックされたメール本文です。" in res_data["body"]
    assert res_data["subject"] == "テスト件名"
