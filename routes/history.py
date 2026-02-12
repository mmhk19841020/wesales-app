from flask import Blueprint, render_template, request, jsonify
from flask_login import current_user, login_required
from extensions import db
from models import History, User
from services.mail_service import get_monthly_sent_count

history_bp = Blueprint("history", __name__)

@history_bp.route("/history")
@login_required
def show_history():
    user_id = request.args.get("user_id", type=int)
    
    monthly_sent_count = get_monthly_sent_count(current_user.id)
    monthly_limit = current_user.monthly_limit
    
    if current_user.is_admin:
        query = History.query
        if user_id:
            query = query.filter_by(user_id=user_id)
        histories = query.order_by(History.sent_at.desc()).all()
        users = User.query.all()
        return render_template("history.html", 
                               histories=histories, 
                               users=users, 
                               selected_user_id=user_id,
                               monthly_sent_count=monthly_sent_count,
                               monthly_limit=monthly_limit)
    else:
        histories = (
            History.query.filter_by(user_id=current_user.id)
            .order_by(History.sent_at.desc())
            .all()
        )
        return render_template("history.html", 
                               histories=histories,
                               monthly_sent_count=monthly_sent_count,
                               monthly_limit=monthly_limit)

@history_bp.route("/history/delete", methods=["POST"])
@login_required
def delete_history():
    try:
        data = request.json
        history_ids = data.get("ids", [])
        
        if not history_ids:
            return jsonify({"message": "削除対象が選択されていません"}), 400
            
        if current_user.is_admin:
            histories_to_delete = History.query.filter(History.id.in_(history_ids)).all()
        else:
            histories_to_delete = History.query.filter(
                History.id.in_(history_ids),
                History.user_id == current_user.id
            ).all()
        
        count = len(histories_to_delete)
        for h in histories_to_delete:
            db.session.delete(h)
            
        db.session.commit()
        return jsonify({"message": f"{count}件の履歴を削除しました"})
    except Exception as e:
        return jsonify({"message": f"削除失敗: {str(e)}"}), 500
