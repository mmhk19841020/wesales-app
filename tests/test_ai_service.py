import pytest
import json
from unittest.mock import patch, MagicMock
from services.ai_service import get_ai_completion, analyze_card_image

class TestAIService:
    """AI サービスのモックテスト"""
    
    @patch("services.ai_service.get_openai_client")
    def test_get_ai_completion_azure(self, mock_get_client):
        """Azure OpenAI でのテキスト生成テスト"""
        # モックの設定
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "テスト応答"
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = (mock_client, "gpt-4o-mini")
        
        # テスト実行
        with patch("services.ai_service.Config.AI_ENGINE_TYPE", "azure"):
            result = get_ai_completion("テストプロンプト")
        
        # 検証
        assert result == "テスト応答"
        mock_client.chat.completions.create.assert_called_once()
    
    @patch("services.ai_service.genai.GenerativeModel")
    @patch("services.ai_service.configure_gemini")
    def test_get_ai_completion_gemini(self, mock_configure, mock_model_class):
        """Gemini でのテキスト生成テスト"""
        # モックの設定
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Gemini応答"
        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model
        
        # テスト実行
        with patch("services.ai_service.Config.AI_ENGINE_TYPE", "gemini"):
            result = get_ai_completion("テストプロンプト")
        
        # 検証
        assert result == "Gemini応答"
        mock_configure.assert_called()
        mock_model.generate_content.assert_called_once()
    
    @patch("services.ai_service.genai.GenerativeModel")
    @patch("services.ai_service.configure_gemini")
    def test_analyze_card_image_gemini(self, mock_configure, mock_model_class):
        """Gemini での名刺画像解析テスト"""
        # モックの設定
        mock_model = MagicMock()
        mock_response = MagicMock()
        test_data = {
            "name": "山田 太郎",
            "company": "テスト株式会社",
            "department": "開発部",
            "title": "部長",
            "url": "https://test.example.com",
            "email": "yamada@test.example.com",
            "phone": "03-1234-5678"
        }
        mock_response.text = json.dumps(test_data)
        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model
        
        # テスト実行
        with patch("services.ai_service.Config.AI_ENGINE_TYPE", "gemini"):
            result = analyze_card_image(b"fake-image-data", "test.jpg")
        
        # 検証
        assert result["name"] == "山田 太郎"
        assert result["company"] == "テスト株式会社"
        assert result["email"] == "yamada@test.example.com"
        mock_model.generate_content.assert_called_once()
    
    @patch("services.ai_service.get_openai_client")
    @patch("services.ai_service.get_vision_client")
    def test_analyze_card_image_azure(self, mock_vision_client, mock_openai_client):
        """Azure での名刺画像解析テスト"""
        # Vision API のモック
        mock_vision = MagicMock()
        mock_result = MagicMock()
        mock_block = MagicMock()
        mock_line = MagicMock()
        mock_line.text = "テスト株式会社"
        mock_block.lines = [mock_line]
        mock_result.read.blocks = [mock_block]
        mock_vision.analyze.return_value = mock_result
        mock_vision_client.return_value = mock_vision
        
        # OpenAI のモック
        mock_openai = MagicMock()
        mock_response = MagicMock()
        test_data = {
            "name": "佐藤 花子",
            "company": "テスト株式会社",
            "department": "",
            "title": "課長",
            "url": "",
            "email": "sato@test.example.com",
            "phone": "090-9876-5432"
        }
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(test_data)
        mock_openai.chat.completions.create.return_value = mock_response
        mock_openai_client.return_value = (mock_openai, "gpt-4o-mini")
        
        # テスト実行
        with patch("services.ai_service.Config.AI_ENGINE_TYPE", "azure"):
            result = analyze_card_image(b"fake-image-data", "test.png")
        
        # 検証
        assert result["name"] == "佐藤 花子"
        assert result["email"] == "sato@test.example.com"
        mock_vision.analyze.assert_called_once()
        mock_openai.chat.completions.create.assert_called_once()
