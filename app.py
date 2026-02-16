import sys
import os
try:
    import google
    print(f"DEBUG: python path: {sys.executable}")
    print(f"DEBUG: sys.path: {sys.path}")
    print(f"DEBUG: google path: {google.__path__}")
except Exception as e:
    print(f"DEBUG: Error importing google: {e}")

from flask import Flask
from config import Config
from extensions import db, bcrypt, csrf, talisman, login_manager
from models import User
from datetime import datetime, timezone

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize Extensions
    db.init_app(app)
    bcrypt.init_app(app)
    csrf.init_app(app)
    # Configure Talisman
    # Disable HTTPS enforcement in testing to avoid 302 redirects
#    force_https = not app.config.get("TESTING", False)
#    talisman.init_app(app, content_security_policy=None, force_https=force_https)
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Context Processor
    @app.context_processor
    def inject_now():
        return {"now": datetime.now(timezone.utc)}

    # Register Blueprints
    from routes.auth import auth_bp
    from routes.main import main_bp
    from routes.cards import cards_bp
    from routes.history import history_bp
    from routes.admin import admin_bp
    from routes.import_routes import import_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(cards_bp)
    app.register_blueprint(history_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(import_bp)

    return app

app = create_app()

import os

# 【重要】IISで動かす際、データベース作成を確実に行うため if の外に出します
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    # 手元のPCでのデバッグ用設定
    # ポートは手元で動作確認が取れた「5001」をデフォルトにします
    import os
    port = int(os.environ.get("PORT", 5001))
    
    # host='0.0.0.0' にすることで、AzureのIISからの通信を受け取れるようにします
    # use_reloader=False は、IIS上での二重起動エラーを防ぐために必須です
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)