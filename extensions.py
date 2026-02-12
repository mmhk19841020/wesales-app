from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_wtf.csrf import CSRFProtect
from flask_talisman import Talisman
from flask_login import LoginManager

db = SQLAlchemy()
bcrypt = Bcrypt()
csrf = CSRFProtect()
talisman = Talisman()
login_manager = LoginManager()

login_manager.login_view = "auth.login" # Updated to blueprint name later
login_manager.login_message = "ログインしてください。"
login_manager.login_message_category = "info"
