import os
import resend
import smtplib
import uuid
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import Config
from models import History
from datetime import date

resend.api_key = Config.RESEND_API_KEY

def get_monthly_sent_count(user_id):
    """ユーザーの今月のメール送信数を取得する"""
    first_day = date(date.today().year, date.today().month, 1)
    count = History.query.filter(
        History.user_id == user_id,
        History.sent_at >= first_day
    ).count()
    return count

def get_resend_metrics():
    """Resend APIから送信済みメールのメトリクスを取得する"""
    try:
        if not resend.api_key:
            return None
            
        emails = resend.Emails.list()
        
        counts = {
            "delivered": 0, "opened": 0, "clicked": 0,
            "bounced": 0, "complained": 0, "sent": 0
        }
        
        email_data = getattr(emails, "data", []) if not isinstance(emails, dict) else emails.get("data", [])
        total = len(email_data)
        
        for email in email_data:
            status = getattr(email, "last_event", None) if not isinstance(email, dict) else email.get("last_event")
            if status and status in counts:
                counts[status] += 1
            else:
                counts["sent"] += 1
                
        metrics = {
            "counts": counts,
            "total": total,
            "rates": {
                "delivered": round(counts["delivered"] * 100.0 / total, 1) if total > 0 else 0.0,
                "opened": round(counts["opened"] * 100.0 / total, 1) if total > 0 else 0.0,
                "clicked": round(counts["clicked"] * 100.0 / total, 1) if total > 0 else 0.0,
            }
        }
        return metrics
    except Exception:
        return None

def send_email(user, data):
    """メールを送信する (Gmail SMTP or Resend)"""
    email_provider = user.email_provider or "resend"
    
    if email_provider == "gmail" and user.email_address and user.gmail_app_password:
        return _send_via_gmail(user, data)
    else:
        return _send_via_resend(user, data)

def _send_via_gmail(user, data):
    sender_email = user.email_address
    sender_pass = user.gmail_app_password
    
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = data.get("to")
    msg["Subject"] = data.get("subject")
    msg.attach(MIMEText(data.get("body"), "plain"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, sender_pass)
        server.send_message(msg)
    
    return "gmail-smtp", "自身のGmail経由で送信に成功しました！"

def _send_via_resend(user, data):
    sender_email = "info@email.we-sales.com" 
    
    params = {
        "from": f"{user.real_name or 'WeSales User'} <{sender_email}>",
        "to": [data.get("to")],
        "subject": data.get("subject"),
        "text": data.get("body"),
        "headers": {
            "X-Entity-Ref-ID": str(uuid.uuid4())
        }
    }
    response = resend.Emails.send(params)
    return response.get("id"), "Resend経由で送信に成功しました！"
