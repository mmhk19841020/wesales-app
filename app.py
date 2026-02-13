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
    force_https = not app.config.get("TESTING", False)
    talisman.init_app(app, content_security_policy=None, force_https=force_https)
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

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    
    # IIS (httpPlatformHandler) passes the port via the PORT environment variable
    port_env = os.environ.get("PORT", "5000")
    try:
        port = int(port_env)
    except ValueError:
        port = 5000
        
    # debug=True is okay for error pages, but use_reloader=False is critical on IIS
    # to avoid the reloader spawning a child process that IIS won't manage correctly.
    app.run(host='127.0.0.1', port=port, debug=True, use_reloader=False)

