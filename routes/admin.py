from flask import Blueprint, render_template, redirect, url_for, request, abort
from flask_login import login_required, current_user
from extensions import db, bcrypt
from models import User
from services.mail_service import get_monthly_sent_count, get_resend_metrics
from config import Config
from functools import wraps

admin_bp = Blueprint("admin", __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route("/admin/users")
@login_required
@admin_required
def admin_users():
    users = User.query.all()
    for user in users:
        user.current_sent = get_monthly_sent_count(user.id)
    return render_template("admin_list.html", users=users)

@admin_bp.route("/admin/dashboard")
@login_required
@admin_required
def admin_dashboard():
    metrics = get_resend_metrics()
    return render_template("admin_dashboard.html", metrics=metrics, ai_engine=Config.AI_ENGINE_TYPE)

@admin_bp.route("/admin/users/add", methods=["GET", "POST"])
@login_required
@admin_required
def admin_add_user():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        company_name = request.form.get("company_name")
        real_name = request.form.get("real_name")
        
        if User.query.filter_by(username=username).first():
            return render_template("admin_form.html", error="このユーザー名は既に使用されています", user={})
        
        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(
            username=username,
            password=hashed_pw,
            company_name=company_name,
            real_name=real_name,
            monthly_limit=int(request.form.get("monthly_limit") or 100)
        )
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for("admin.admin_users"))
        
    return render_template("admin_form.html", user=None)

@admin_bp.route("/admin/users/edit/<int:user_id>", methods=["GET", "POST"])
@login_required
@admin_required
def admin_edit_user(user_id):
    user = User.query.get_or_404(user_id)
    if request.method == "POST":
        user.company_name = request.form.get("company_name")
        user.real_name = request.form.get("real_name")
        user.monthly_limit = int(request.form.get("monthly_limit") or 100)
        
        password = request.form.get("password")
        if password:
            user.password = bcrypt.generate_password_hash(password).decode('utf-8')
            
        db.session.commit()
        return redirect(url_for("admin.admin_users"))
        
    return render_template("admin_form.html", user=user)

@admin_bp.route("/admin/users/delete/<int:user_id>", methods=["POST"])
@login_required
@admin_required
def admin_delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        return "自分自身は削除できません", 400
        
    db.session.delete(user)
    db.session.commit()
    return redirect(url_for("admin.admin_users"))
