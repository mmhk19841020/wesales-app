# Wesales プロジェクト構造

## ディレクトリ構成

```
CardApp/
├── app.py                    # アプリケーションのエントリーポイント
├── config.py                 # 設定ファイル（環境変数の読み込み）
├── extensions.py             # Flask拡張機能の初期化
├── models.py                 # データベースモデル（User, Card, History）
├── requirements.txt          # 依存パッケージ一覧
├── .env                      # 環境変数（APIキーなど）
├── Web.config                # IIS デプロイ用設定
│
├── routes/                   # ルート（Blueprint）
│   ├── auth.py              # 認証（ログイン/ログアウト）
│   ├── main.py              # メインページ
│   ├── cards.py             # 名刺管理
│   ├── history.py           # 送信履歴
│   ├── admin.py             # 管理者機能
│   └── import_routes.py     # CSV インポート
│
├── services/                 # ビジネスロジック
│   ├── ai_service.py        # AI 連携（Azure/Gemini）
│   ├── csv_service.py       # CSV パース処理
│   ├── mail_service.py      # メール送信
│   └── web_service.py       # Web スクレイピング
│
├── templates/                # HTML テンプレート
│   ├── base.html
│   ├── login.html
│   ├── card_list.html
│   ├── create_email.html
│   └── ...
│
├── static/                   # 静的ファイル
│   ├── css/
│   ├── js/
│   └── uploads/
│
└── tests/                    # 自動テスト
    ├── conftest.py          # テスト共通設定
    ├── test_csv_service.py  # CSV テスト
    ├── test_ai_service.py   # AI テスト
    ├── test_routes.py       # ルートテスト
    └── README.md            # テストドキュメント
```

## 主要ファイルの説明

### app.py
アプリケーションのエントリーポイント。`create_app()` 関数で Flask アプリを作成し、
各 Blueprint を登録します。

### config.py
環境変数（`.env`）から設定を読み込み、`Config` クラスとして提供します。

### extensions.py
Flask 拡張機能（SQLAlchemy, Bcrypt, CSRF, Talisman, LoginManager）を初期化します。

### models.py
データベースモデルを定義：
- `User`: ユーザー情報
- `Card`: 名刺情報
- `History`: メール送信履歴

## サービス層の役割

### services/ai_service.py
- Azure OpenAI または Gemini を使用したテキスト生成
- 名刺画像の解析（OCR + 構造化）
- AI エンジンの切り替え対応

### services/csv_service.py
- Eight 形式の CSV ファイルのパース
- データベースへの登録/更新処理

### services/mail_service.py
- Resend API を使用したメール送信
- 送信履歴の記録
- 月間送信数の集計

### services/web_service.py
- 企業 URL からの情報取得（スクレイピング）

## ルート（Blueprint）の役割

### routes/auth.py
- ログイン/ログアウト処理

### routes/main.py
- トップページ
- ユーザー設定

### routes/cards.py
- 名刺一覧表示
- 名刺アップロード
- 名刺編集/削除
- メール作成画面

### routes/history.py
- 送信履歴の表示
- 履歴の削除

### routes/admin.py
- ユーザー管理
- ダッシュボード

### routes/import_routes.py
- Eight CSV インポート

## データフロー

### 名刺登録の流れ
1. ユーザーが画像をアップロード (`routes/cards.py`)
2. AI サービスで画像を解析 (`services/ai_service.py`)
3. 抽出された情報を DB に保存 (`models.py`)

### メール送信の流れ
1. ユーザーが名刺を選択してメール作成画面へ (`routes/cards.py`)
2. AI でメール本文を生成 (`services/ai_service.py`)
3. ユーザーが編集・送信 (`services/mail_service.py`)
4. 送信履歴を記録 (`models.py`)

### CSV インポートの流れ
1. ユーザーが CSV ファイルをアップロード (`routes/import_routes.py`)
2. CSV をパースして構造化 (`services/csv_service.py`)
3. DB に登録/更新 (`models.py`)

## 環境変数（.env）

```env
# Azure AI
VISION_KEY=...
VISION_ENDPOINT=...
OPENAI_KEY=...
OPENAI_ENDPOINT=...
OPENAI_DEPLOYMENT=...

# Gemini
GEMINI_API_KEY=...
AI_ENGINE_TYPE=azure  # または gemini

# Email
RESEND_API_KEY=...

# Security
SECRET_KEY=...
```

## IIS デプロイ

`Web.config` を使用して IIS 上で動作します。
- Python 仮想環境のパスを指定
- ポート番号は環境変数 `PORT` から取得
- ログは `logs/python.log` に出力

## テスト

`tests/` ディレクトリに pytest ベースの自動テストがあります。
詳細は `tests/README.md` を参照してください。

```powershell
# テスト実行
python -m pytest

# 成功しているテストのみ実行
python -m pytest tests/test_csv_service.py tests/test_ai_service.py -v
```

## 開発の流れ

1. **機能追加時**:
   - 必要に応じて `services/` にビジネスロジックを追加
   - `routes/` に新しいエンドポイントを追加
   - `templates/` に HTML を追加
   - `tests/` にテストを追加

2. **AI エンジン切り替え**:
   - `.env` の `AI_ENGINE_TYPE` を変更（`azure` または `gemini`）
   - `services/ai_service.py` が自動的に切り替え

3. **デプロイ**:
   - IIS: `Web.config` を確認
   - 環境変数を設定
   - アプリケーションプールを再起動

## トラブルシューティング

### IIS で動作しない
- `Web.config` のパスを確認
- `logs/python.log` を確認
- 環境変数 `PORT` が正しく渡されているか確認

### AI が動作しない
- `.env` の API キーを確認
- `AI_ENGINE_TYPE` の設定を確認
- ログでエラーメッセージを確認

### テストが失敗する
- 仮想環境がアクティブか確認
- `pytest` がインストールされているか確認
- `tests/README.md` で既知の問題を確認
