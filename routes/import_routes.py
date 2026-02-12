from flask import Blueprint, request, redirect, url_for, flash
from flask_login import current_user, login_required
from services.csv_service import process_eight_csv

import_bp = Blueprint("import", __name__)

@import_bp.route("/import/eight", methods=["POST"])
@login_required
def import_eight():
    if "csv_file" not in request.files:
        flash("ファイルが選択されていません", "error")
        return redirect(url_for("cards.show_cards"))
    
    file = request.files["csv_file"]
    if file.filename == "":
        flash("ファイル名が空です", "error")
        return redirect(url_for("cards.show_cards"))

    if not file.filename.endswith(".csv"):
        flash("CSVファイルを選択してください", "error")
        return redirect(url_for("cards.show_cards"))

    try:
        content = file.read()
        count_success, count_updated = process_eight_csv(content, current_user.id)
        flash(f"インポート完了: {count_success}件を新規登録、{count_updated}件を更新しました。", "success")
    except Exception as e:
        flash(f"エラーが発生しました: {str(e)}", "error")

    return redirect(url_for("cards.show_cards"))
