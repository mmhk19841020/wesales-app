import pytest
from unittest.mock import patch, MagicMock
from datetime import date, datetime
from services.mail_service import (
    get_monthly_sent_count,
    get_resend_metrics,
    send_email,
    _send_via_gmail,
    _send_via_resend
)
from models import User, History
from extensions import db


class TestMailService:
    """メールサービスのテスト"""
    
    def test_get_monthly_sent_count(self, app):
        """今月の送信数カウントのテスト"""
        with app.app_context():
            user = User.query.filter_by(username="testuser").first()
            
            # 今月の履歴を3件追加
            for i in range(3):
                history = History(
                    user_id=user.id,
                    customer_name=f"顧客{i}",
                    email=f"customer{i}@example.com",
                    mail_subject="テスト件名",
                    mail_body="テスト本文",
                    sent_at=datetime.now()
                )
                db.session.add(history)
            db.session.commit()
            
            # カウントを確認
            count = get_monthly_sent_count(user.id)
            assert count == 3
    
    @patch("services.mail_service.resend.Emails.list")
    def test_get_resend_metrics(self, mock_list):
        """Resend メトリクス取得のテスト"""
        # モックデータの設定
        mock_list.return_value = {
            "data": [
                {"last_event": "delivered"},
                {"last_event": "delivered"},
                {"last_event": "opened"},
                {"last_event": "sent"},
            ]
        }
        
        metrics = get_resend_metrics()
        
        assert metrics is not None
        assert metrics["total"] == 4
        assert metrics["counts"]["delivered"] == 2
        assert metrics["counts"]["opened"] == 1
        assert metrics["counts"]["sent"] == 1
        assert metrics["rates"]["delivered"] == 50.0
    
    @patch("services.mail_service.resend.Emails.send")
    def test_send_via_resend(self, mock_send, app):
        """Resend 経由のメール送信テスト"""
        with app.app_context():
            user = User.query.filter_by(username="testuser").first()
            user.real_name = "テスト太郎"
            
            # モックの設定
            mock_send.return_value = {"id": "test-email-id-123"}
            
            # メール送信データ
            data = {
                "to": "recipient@example.com",
                "subject": "テスト件名",
                "body": "テスト本文です。"
            }
            
            # 送信実行
            email_id, message = _send_via_resend(user, data)
            
            # 検証
            assert email_id == "test-email-id-123"
            assert "Resend経由" in message
            
            # モックが正しい引数で呼ばれたか確認
            mock_send.assert_called_once()
            call_args = mock_send.call_args[0][0]
            assert call_args["to"] == ["recipient@example.com"]
            assert call_args["subject"] == "テスト件名"
            assert call_args["text"] == "テスト本文です。"
            assert "テスト太郎" in call_args["from"]
    
    @patch("services.mail_service.smtplib.SMTP_SSL")
    def test_send_via_gmail(self, mock_smtp, app):
        """Gmail SMTP 経由のメール送信テスト"""
        with app.app_context():
            user = User.query.filter_by(username="testuser").first()
            user.email_address = "test@gmail.com"
            user.gmail_app_password = "test-app-password"
            
            # モックの設定
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server
            
            # メール送信データ
            data = {
                "to": "recipient@example.com",
                "subject": "Gmail テスト",
                "body": "Gmail 経由のテストです。"
            }
            
            # 送信実行
            provider, message = _send_via_gmail(user, data)
            
            # 検証
            assert provider == "gmail-smtp"
            assert "Gmail経由" in message
            
            # SMTP接続が正しく呼ばれたか確認
            mock_smtp.assert_called_once_with("smtp.gmail.com", 465)
            mock_server.login.assert_called_once_with("test@gmail.com", "test-app-password")
            mock_server.send_message.assert_called_once()
    
    @patch("services.mail_service._send_via_resend")
    def test_send_email_defaults_to_resend(self, mock_resend, app):
        """send_email がデフォルトで Resend を使用することを確認"""
        with app.app_context():
            user = User.query.filter_by(username="testuser").first()
            user.email_provider = None  # デフォルト
            
            mock_resend.return_value = ("test-id", "成功")
            
            data = {"to": "test@example.com", "subject": "テスト", "body": "本文"}
            send_email(user, data)
            
            mock_resend.assert_called_once_with(user, data)
    
    @patch("services.mail_service._send_via_gmail")
    def test_send_email_uses_gmail_when_configured(self, mock_gmail, app):
        """Gmail が設定されている場合に Gmail を使用することを確認"""
        with app.app_context():
            user = User.query.filter_by(username="testuser").first()
            user.email_provider = "gmail"
            user.email_address = "test@gmail.com"
            user.gmail_app_password = "password"
            
            mock_gmail.return_value = ("gmail-id", "成功")
            
            data = {"to": "test@example.com", "subject": "テスト", "body": "本文"}
            send_email(user, data)
            
            mock_gmail.assert_called_once_with(user, data)
