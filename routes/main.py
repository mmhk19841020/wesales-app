from flask import Blueprint, render_template, redirect, url_for, request, jsonify
from flask_login import current_user, login_required
from extensions import db
from models import Card, History
from services.mail_service import get_monthly_sent_count, send_email

main_bp = Blueprint("main", __name__)

# ... (index and profile remains)

@main_bp.route("/send", methods=["POST"])
@login_required
def send():
    try:
        sent_count = get_monthly_sent_count(current_user.id)
        limit = current_user.monthly_limit or 100
        if sent_count >= limit:
            return jsonify({"message": f"今月の送信上限（{limit}件）に達したため、送信できません。"}), 403

        data = request.json
        res_id, msg_text = send_email(current_user, data)

        new_history = History(
            user_id=current_user.id,
            customer_name=data.get("customer_name", "氏名不明"),
            company_name=data.get("company_name", "会社名不明"),
            email=data.get("to"),
            mail_subject=data.get("subject", "件名なし"),
            mail_body=data.get("body"),
        )
        db.session.add(new_history)
        db.session.commit()

        return jsonify({
            "message": f"{msg_text} 履歴に保存しました。",
            "id": res_id
        })
    except Exception as e:
        return jsonify({"message": f"送信失敗: {str(e)}"}), 500


@main_bp.route("/")
@login_required
def index():
    if current_user.is_admin:
        return redirect(url_for("admin.admin_users"))

    sent_count = get_monthly_sent_count(current_user.id)
    limit_info = {
        "sent": sent_count,
        "limit": current_user.monthly_limit or 100
    }

    recent_cards = (
        Card.query.filter_by(user_id=current_user.id)
        .order_by(Card.created_at.desc())
        .limit(5)
        .all()
    )
    recent_histories = (
        History.query.filter_by(user_id=current_user.id)
        .order_by(History.sent_at.desc())
        .limit(5)
        .all()
    )
    return render_template("index.html", recent_cards=recent_cards, recent_histories=recent_histories, limit_info=limit_info)

@main_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        current_user.company_name = request.form.get("company_name")
        current_user.job_title = request.form.get("job_title")
        current_user.real_name = request.form.get("real_name")
        current_user.phone_number = request.form.get("phone_number")
        current_user.email_address = request.form.get("email_address")
        current_user.company_url = request.form.get("company_url")
        current_user.business_summary = request.form.get("business_summary")
        current_user.gmail_app_password = request.form.get("gmail_app_password")
        current_user.email_provider = request.form.get("email_provider", "resend")

        db.session.commit()
        return redirect(url_for("main.index"))

    return render_template("profile.html", user=current_user)
