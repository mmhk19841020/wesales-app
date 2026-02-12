# Wesales 自動テスト環境

## 概要

このプロジェクトでは、pytest を使用した自動テスト環境を構築しています。
リファクタリング後の全機能が正常に動作するかを確認できます。

## テスト構成

```
tests/
├── conftest.py           # テスト用の共通設定（Flask app, DB, ユーザー）
├── test_csv_service.py   # Eight CSV インポート機能のテスト
├── test_ai_service.py    # AI サービス（Azure/Gemini）のモックテスト
└── test_routes.py        # ルート（画面遷移）のテスト
```

## セットアップ

### 必要なライブラリのインストール

```powershell
pip install pytest pytest-flask pytest-mock
```

または

```powershell
pip install -r requirements.txt
```

## テストの実行

### すべてのテストを実行

```powershell
python -m pytest
```

### 詳細表示で実行

```powershell
python -m pytest -v
```

### 特定のテストファイルのみ実行

```powershell
# CSV サービスのテスト
python -m pytest tests/test_csv_service.py -v

# AI サービスのテスト
python -m pytest tests/test_ai_service.py -v

# ルートのテスト
python -m pytest tests/test_routes.py -v
```

### 失敗したテストで停止

```powershell
python -m pytest -x
```

## テスト内容

### 1. CSV サービステスト (`test_csv_service.py`)

- ✅ Eight 形式の CSV が正しくパースされるか
- ✅ 新規データが DB に登録されるか
- ✅ 既存データ（同じEmail）が更新されるか

**ステータス**: ✅ **全テスト成功**

### 2. AI サービステスト (`test_ai_service.py`)

- ✅ Azure OpenAI でのテキスト生成（モック）
- ✅ Gemini でのテキスト生成（モック）
- ✅ Azure での名刺画像解析（モック）
- ✅ Gemini での名刺画像解析（モック）

**ステータス**: ✅ **全テスト成功**

### 3. ルートテスト (`test_routes.py`)

- ⚠️ ログイン画面の表示
- ⚠️ ログイン機能
- ⚠️ 未ログイン時のリダイレクト
- ⚠️ 名刺一覧の表示（ログイン済み）
- ⚠️ 名刺アップロード（モック）
- ⚠️ メール生成（モック）

**ステータス**: ⚠️ **セッション管理の問題により一部失敗**

## モック（Mock）について

テストでは、実際の API（Azure OpenAI、Gemini、Resend）を呼び出さず、
`unittest.mock` を使って「成功したと仮定」してテストを進めます。

これにより：
- ✅ API キーが不要
- ✅ 高速にテスト実行
- ✅ API 使用料金が発生しない
- ✅ ネットワーク不要

## テスト用データベース

テストでは、メモリ内 SQLite データベース（`:memory:`）を使用します。
テスト実行ごとに新しいデータベースが作成され、テスト終了後に自動削除されます。

## 既知の問題と今後の改善

### ルートテストのセッション管理

現在、Flask-Login のセッション管理がテスト環境で正しく動作していません。
これは以下の理由によるものです：

1. テストクライアントのセッション永続化の問題
2. CSRF トークンの扱い
3. Cookie の設定

**解決策（今後の実装）**:
- `flask_login.utils.login_user()` を直接使用
- テストコンテキスト内でのセッション操作
- または、`LOGIN_DISABLED = True` でテスト時のみログインをスキップ

### 推奨される次のステップ

1. **ルートテストの修正**: セッション管理を適切に処理
2. **メールサービステストの追加**: `services/mail_service.py` のテスト
3. **統合テストの追加**: 実際のワークフロー全体をテスト
4. **カバレッジ測定**: `pytest-cov` を使用してテストカバレッジを確認

## 成功しているテストの実行例

```powershell
# CSVとAIサービスのテストのみ実行（すべて成功）
python -m pytest tests/test_csv_service.py tests/test_ai_service.py -v
```

出力例：
```
tests/test_csv_service.py::test_process_eight_csv_success PASSED
tests/test_csv_service.py::test_process_eight_csv_update PASSED
tests/test_ai_service.py::TestAIService::test_get_ai_completion_azure PASSED
tests/test_ai_service.py::TestAIService::test_get_ai_completion_gemini PASSED
tests/test_ai_service.py::TestAIService::test_analyze_card_image_gemini PASSED
tests/test_ai_service.py::TestAIService::test_analyze_card_image_azure PASSED

======================== 6 passed in 2.01s ========================
```

## まとめ

現時点で、**CSV インポート機能**と**AI サービス**の自動テストは完全に動作しています。
これにより、コードを変更した際に、これらの重要な機能が壊れていないことを即座に確認できます。

ルートテストについては、Flask-Login のセッション管理を適切に扱う必要があり、
今後の改善課題となっています。
