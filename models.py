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
    real_name = db.Column(db.String(100))
    phone_number = db.Column(db.String(20))
    email_address = db.Column(db.String(120))
    company_url = db.Column(db.String(200))
    business_summary = db.Column(db.Text)
    gmail_app_password = db.Column(db.String(100))
    email_provider = db.Column(db.String(20), default="resend") # gmail or resend
    monthly_limit = db.Column(db.Integer, default=100) # 月間送信上限

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
    person_name = db.Column(db.String(100))
    phone_number = db.Column(db.String(20))
    email = db.Column(db.String(120))
    url = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.now)
    user = db.relationship("User", backref=db.backref("cards", lazy=True))
