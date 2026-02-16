from datetime import datetime
from flask_login import UserMixin
from extensions import db

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    company_name = db.Column(db.String(100))
    job_title = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    first_name = db.Column(db.String(100))
    phone_number = db.Column(db.String(20))
    email_address = db.Column(db.String(120))
    company_url = db.Column(db.String(200))
    business_summary = db.Column(db.Text)
    gmail_app_password = db.Column(db.String(100))
    email_provider = db.Column(db.String(20), default="resend") # gmail or resend
    monthly_limit = db.Column(db.Integer, default=100) # 月間送信上限

    @property
    def real_name(self):
        return f"{self.last_name or ''} {self.first_name or ''}".strip()
    
    @real_name.setter
    def real_name(self, value):
        if value:
            parts = value.strip().replace('　', ' ').split(' ', 1)
            self.last_name = parts[0]
            self.first_name = parts[1] if len(parts) > 1 else ""
        else:
            self.last_name = ""
            self.first_name = ""

class History(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    customer_name = db.Column(db.String(100))
    company_name = db.Column(db.String(100))
    email = db.Column(db.String(120))
    mail_subject = db.Column(db.String(200))
    mail_body = db.Column(db.Text)
    sent_at = db.Column(db.DateTime, default=datetime.now)
    user = db.relationship("User", backref=db.backref("histories", lazy=True))

class Card(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    image_path = db.Column(db.String(200))
    company_name = db.Column(db.String(100))
    department_name = db.Column(db.String(100))
    job_title = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    first_name = db.Column(db.String(100))
    phone_number = db.Column(db.String(20))
    email = db.Column(db.String(120))
    url = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.now)
    user = db.relationship("User", backref=db.backref("cards", lazy=True))

    @property
    def person_name(self):
        return f"{self.last_name or ''} {self.first_name or ''}".strip()

    @person_name.setter
    def person_name(self, value):
        if value:
            parts = value.strip().replace('　', ' ').split(' ', 1)
            self.last_name = parts[0]
            self.first_name = parts[1] if len(parts) > 1 else ""
        else:
            self.last_name = ""
            self.first_name = ""
