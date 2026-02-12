import io
import pytest
from services.csv_service import process_eight_csv
from models import Card, User
from extensions import db

def test_process_eight_csv_success(app):
    with app.app_context():
        user = User.query.filter_by(username="testuser").first()
        
        # Eight形式のサンプルCSVデータ (UTF-8 with BOM or CP932)
        csv_content = (
            "姓,名,会社名,部署名,役職,e-mail,TEL会社,携帯電話,会社URL\n"
            "山田,太郎,株式会社テスト,開発部,マネージャー,yamada@example.com,03-1234-5678,090-1234-5678,https://example.com\n"
            "佐藤,花子,テスト株式会社,,主任,sato@example.com,03-8765-4321,,https://test.co.jp\n"
        ).encode("utf-8-sig")
        
        success, updated = process_eight_csv(csv_content, user.id)
        db.session.commit()
        
        assert success == 2
        assert updated == 0
        
        # 登録内容の確認
        card1 = Card.query.filter_by(email="yamada@example.com").first()
        assert card1 is not None
        assert card1.person_name == "山田 太郎"
        assert card1.company_name == "株式会社テスト"
        assert card1.phone_number == "090-1234-5678"
        
        card2 = Card.query.filter_by(email="sato@example.com").first()
        assert card2 is not None
        assert card2.person_name == "佐藤 花子"
        assert card2.phone_number == "03-8765-4321"

def test_process_eight_csv_update(app):
    with app.app_context():
        user = User.query.filter_by(username="testuser").first()
        
        # 事前に1件登録
        existing_card = Card(
            user_id=user.id,
            email="update@example.com",
            person_name="旧 氏名",
            company_name="旧 会社"
        )
        db.session.add(existing_card)
        db.session.commit()
        
        # 同じEmailの新データ
        csv_content = (
            "姓,名,会社名,e-mail\n"
            "新,氏名,新 会社,update@example.com\n"
        ).encode("utf-8-sig")
        
        success, updated = process_eight_csv(csv_content, user.id)
        db.session.commit()
        
        assert success == 0
        assert updated == 1
        
        card = Card.query.filter_by(email="update@example.com").first()
        assert card.person_name == "新 氏名"
        assert card.company_name == "新 会社"
