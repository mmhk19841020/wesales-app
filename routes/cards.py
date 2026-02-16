import os
import uuid
import json
import time

from flask import Blueprint, render_template, redirect, url_for, request, jsonify, abort, current_app
from flask_login import current_user, login_required
from extensions import db
from models import Card, User, History
from services.ai_service import analyze_card_image, get_ai_completion
from services.web_service import get_company_info
from services.mail_service import send_email
from config import Config

cards_bp = Blueprint("cards", __name__)

@cards_bp.route("/cards")
@login_required
def show_cards():
    user_id = request.args.get("user_id", type=int)

    if current_user.is_admin:
        query = Card.query
        if user_id:
            query = query.filter_by(user_id=user_id)
        cards = query.order_by(Card.created_at.desc()).all()
        users = User.query.all()
        return render_template("card_list.html", cards=cards, users=users, selected_user_id=user_id)
    else:
        cards = (
            Card.query.filter_by(user_id=current_user.id)
            .order_by(Card.created_at.desc())
            .all()
        )
        return render_template("card_list.html", cards=cards)

@cards_bp.route("/upload", methods=["POST"])
@login_required
def upload():
    try:
        file = request.files["image"]
        filename = str(uuid.uuid4()) + os.path.splitext(file.filename)[1]
        save_dir = current_app.config["UPLOAD_FOLDER"]
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, filename)
        file.save(save_path)
        
        with open(save_path, "rb") as f:
            image_data = f.read()

        info = analyze_card_image(image_data, filename)
        
        new_card = Card(
            user_id=current_user.id,
            image_path=filename, 
            company_name=info.get("company", ""),
            department_name=info.get("department", ""),
            job_title=info.get("title", ""),
            person_name=info.get("name", ""),
            phone_number=info.get("phone", ""),
            email=info.get("email", ""),
            url="http://" + info.get("url", "") if info.get("url", "").startswith("www.") else info.get("url", "")
        )
        db.session.add(new_card)
        db.session.commit()

        return jsonify({"message": "登録完了", "card_id": new_card.id})
    except Exception as e:
        return jsonify({"message": f"エラー: {str(e)}"}), 500

@cards_bp.route("/cards/<int:card_id>")
@login_required
def card_detail(card_id):
    card = db.session.get(Card, card_id)
    if not card:
        abort(404)
    if not current_user.is_admin and card.user_id != current_user.id:
        abort(403)
    return render_template("card_detail.html", card=card)

@cards_bp.route("/cards/<int:card_id>/edit", methods=["GET", "POST"])
@login_required
def card_edit(card_id):
    card = db.session.get(Card, card_id)
    if not card:
        abort(404)
    if not current_user.is_admin and card.user_id != current_user.id:
        abort(403)
        
    if request.method == "POST":
        card.company_name = request.form.get("company_name")
        card.department_name = request.form.get("department_name")
        card.job_title = request.form.get("job_title")
        
        # Name splitting support
        last_name = request.form.get("last_name")
        first_name = request.form.get("first_name")
        
        if last_name or first_name:
            card.last_name = last_name
            card.first_name = first_name
        else:
            # Fallback for old forms if any
            card.person_name = request.form.get("person_name")
            
        card.email = request.form.get("email")
        card.phone_number = request.form.get("phone_number")
        
        url = request.form.get("url")
        if url and url.startswith("www."):
            url = "http://" + url
        card.url = url
        
        db.session.commit()
        return redirect(url_for("cards.card_detail", card_id=card.id))
        
    return render_template("card_edit.html", card=card)

@cards_bp.route("/cards/<int:card_id>/delete", methods=["POST"])
@login_required
def card_delete(card_id):
    card = db.session.get(Card, card_id)
    if not card:
        abort(404)
    if not current_user.is_admin and card.user_id != current_user.id:
        abort(403)
        
    db.session.delete(card)
    db.session.commit()
    return redirect(url_for("cards.show_cards"))

@cards_bp.route("/cards/delete", methods=["POST"])
@login_required
def bulk_delete_cards():
    data = request.get_json()
    card_ids = data.get("ids", [])
    if not card_ids:
        return jsonify({"message": "削除対象が選択されていません"}), 400
        
    try:
        if current_user.is_admin:
            cards_to_delete = Card.query.filter(Card.id.in_(card_ids)).all()
        else:
            cards_to_delete = Card.query.filter(Card.id.in_(card_ids), Card.user_id == current_user.id).all()
            
        count = len(cards_to_delete)
        for card in cards_to_delete:
            db.session.delete(card)
        db.session.commit()
        return jsonify({"message": f"{count}件の名刺を削除しました"})
    except Exception as e:
        return jsonify({"message": f"削除失敗: {str(e)}"}), 500

@cards_bp.route("/create_email/<int:card_id>")
@login_required
def create_email_page(card_id):
    card = db.session.get(Card, card_id)
    if not card:
        abort(404)
    if card.user_id != current_user.id:
        return redirect(url_for('main.index'))
    return render_template("create_email.html", card=card)

@cards_bp.route("/api/generate_initial_email/<int:card_id>")
@login_required
def generate_initial_email(card_id):
    card = db.session.get(Card, card_id)
    if not card:
        abort(404)
    if card.user_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403

    web_info = get_company_info(card.url)
    u = current_user
    
    prompt = f"""
    あなたはプロの営業担当です。以下の情報を元に、名刺交換のお礼メールの件名と本文を作成してください。

    【差出人情報（あなた）】
    会社名: {u.company_name or '（会社名未設定）'}
    氏名: {u.real_name or '（氏名未設定）'}
    事業概要: {u.business_summary or '営業支援'}

    【相手の情報】
    会社名: {card.company_name or '貴社'}
    氏名: {card.person_name or '担当者'}
    相手企業の事業概要: {web_info}

    【出力ルール】
    - 以下のJSON形式のみを出力してください。
    {{
        "subject": "件名",
        "body": "メール本文"
    }}
    """
    
    try:
        result_text = get_ai_completion(prompt, response_format="json_object")
        return jsonify(result_text)  # ⭕️ そのまま渡す
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@cards_bp.route("/api/bulk_send_emails", methods=["POST"])
@login_required
def bulk_send_emails():
    """
    一括メール送信API
    選択された名刺IDに対して、AI生成したメールを送信し、履歴を保存する。
    """
    data = request.get_json()
    card_ids = data.get("ids", [])
    
    if not card_ids:
        return jsonify({"message": "送信対象が選択されていません"}), 400

    # 所有権の確認
    if current_user.is_admin:
        cards_to_send = Card.query.filter(Card.id.in_(card_ids)).all()
    else:
        cards_to_send = Card.query.filter(Card.id.in_(card_ids), Card.user_id == current_user.id).all()
    
    count_success = 0
    count_failed = 0
    
    u = current_user
    sender_info = f"""
    【差出人情報（あなた）】
    会社名: {u.company_name or '（会社名未設定）'}
    氏名: {u.real_name or '（氏名未設定）'}
    事業概要: {u.business_summary or '営業支援'}
    """

    for card in cards_to_send:
        # メールアドレスがない場合はスキップ
        if not card.email:
            count_failed += 1
            print(f"DEBUG: Skipping card {card.id} (No email)")
            continue

        try:
            # 1. AIによるメール内容生成
            prompt = f"""
            あなたはプロの営業担当です。以下の情報を元に、名刺交換のお礼メールの件名と本文を作成してください。
            
            {sender_info}

            【相手の情報】
            会社名: {card.company_name or '貴社'}
            氏名: {card.person_name or '担当者'}
            役職: {card.job_title or ''}
            部署: {card.department_name or ''}
            URL: {card.url or ''}

            【出力ルール】
            - 以下のJSON形式のみを出力してください。
            {{
                "subject": "件名",
                "body": "メール本文"
            }}
            """
            
            ai_result = get_ai_completion(prompt, response_format="json_object")
            # 文字列で返ってきた場合のパース処理
            if isinstance(ai_result, str):
                 try:
                    ai_result = json.loads(ai_result)
                 except json.JSONDecodeError:
                    # JSONデコード失敗時のフォールバック（稀なケース）
                    print(f"DEBUG: AI response not valid JSON: {ai_result}")
                    count_failed += 1
                    continue

            subject = ai_result.get("subject")
            body = ai_result.get("body")
            
            # 件名や本文が空の場合はエラー扱い
            if not subject or not body:
                print(f"DEBUG: AI generated empty subject or body for card {card.id}")
                count_failed += 1
                continue

            # 2. メール送信
            data = {
                "to": card.email,
                "subject": subject,
                "body": body
            }
            
            # 3. 送信処理（メールサービス呼び出し）
            send_id, message = send_email(u, data)
            
            # 4. 履歴保存
            history = History(
                user_id=u.id,
                customer_name=card.person_name,
                company_name=card.company_name,
                email=card.email,
                mail_subject=subject,
                mail_body=body
            )
            db.session.add(history)
            
            # 1件ごとにコミットすることで、途中失敗しても成功分は残す
            db.session.commit()
            count_success += 1
            
            # レート制限対策（連続送信時のAPI制限回避）
            time.sleep(1)

        except Exception as e:
            print(f"DEBUG: Error sending to card {card.id}: {str(e)}")
            count_failed += 1
            
    return jsonify({
        "success_count": count_success,
        "failed_count": count_failed,
        "message": f"{count_success}件のメールを送信しました（失敗: {count_failed}件）"
    })
