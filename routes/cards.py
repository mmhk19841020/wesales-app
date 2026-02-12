import os
import uuid
import json
from flask import Blueprint, render_template, redirect, url_for, request, jsonify, abort, current_app
from flask_login import current_user, login_required
from extensions import db
from models import Card, User
from services.ai_service import analyze_card_image, get_ai_completion
from services.web_service import get_company_info
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
        save_dir = Config.UPLOAD_FOLDER
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
            url=info.get("url", "")
        )
        db.session.add(new_card)
        db.session.commit()

        return jsonify({"message": "登録完了", "card_id": new_card.id})
    except Exception as e:
        return jsonify({"message": f"エラー: {str(e)}"}), 500

@cards_bp.route("/cards/<int:card_id>")
@login_required
def card_detail(card_id):
    card = Card.query.get_or_404(card_id)
    if not current_user.is_admin and card.user_id != current_user.id:
        abort(403)
    return render_template("card_detail.html", card=card)

@cards_bp.route("/cards/<int:card_id>/edit", methods=["GET", "POST"])
@login_required
def card_edit(card_id):
    card = Card.query.get_or_404(card_id)
    if not current_user.is_admin and card.user_id != current_user.id:
        abort(403)
        
    if request.method == "POST":
        card.company_name = request.form.get("company_name")
        card.department_name = request.form.get("department_name")
        card.job_title = request.form.get("job_title")
        card.person_name = request.form.get("person_name")
        card.email = request.form.get("email")
        card.phone_number = request.form.get("phone_number")
        card.url = request.form.get("url")
        
        db.session.commit()
        return redirect(url_for("cards.card_detail", card_id=card.id))
        
    return render_template("card_edit.html", card=card)

@cards_bp.route("/cards/<int:card_id>/delete", methods=["POST"])
@login_required
def card_delete(card_id):
    card = Card.query.get_or_404(card_id)
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
    card = Card.query.get_or_404(card_id)
    if card.user_id != current_user.id:
        return redirect(url_for('main.index'))
    return render_template("create_email.html", card=card)

@cards_bp.route("/api/generate_initial_email/<int:card_id>")
@login_required
def generate_initial_email(card_id):
    card = Card.query.get_or_404(card_id)
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
        return jsonify(json.loads(result_text))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@cards_bp.route("/rewrite", methods=["POST"])
@login_required
def rewrite():
    try:
        data = request.json
        instruction = data.get("instruction", "")
        customer_info = data.get("customer_info", {})
        current_body = data.get("current_body", "")

        u = current_user
        
        # 指示に「英語」「English」が含まれるかチェック
        is_english = any(kw in instruction.lower() for kw in ["英語", "english"])
        
        lang_instruction = ""
        if is_english:
            lang_instruction = "IMPORTANT: Write the entire email in English. Please also translate/transliterate names and company names into English (Latin alphabet)."

        rewrite_prompt = f"""
        あなたはプロの営業担当です。
        以下の【現在のメール案】を、【追加指示】に基づいて書き直してください。
        {lang_instruction}

        【差出人情報（あなた）】
        会社名: {u.company_name or '（会社名未設定）'}
        役職: {u.job_title or ''}
        氏名: {u.real_name or '（氏名未設定）'}
        電話: {u.phone_number or ''}
        Email: {u.email_address or ''}

        【相手の情報】
        会社名: {customer_info.get('company', '貴社')}
        役職: {customer_info.get('title', '')}
        氏名: {customer_info.get('name', '担当者')} 様

        【現在のメール案】
        {current_body}

        【作成依頼の追加指示】
        {instruction}

        【出力ルール】
        - 以下のJSON形式のみを出力してください。
        {{
            "subject": "件名（AIが指示に合わせて最適化）",
            "body": "メール本文（会社名と名前から開始し、署名まで含む）"
        }}
        - 本文の冒頭は会社名と氏名（および様）から開始し、適切に改行を入れること。
        """

        result_text = get_ai_completion(
            rewrite_prompt,
            system_prompt="You are a professional business assistant. Output only raw JSON.",
            response_format="json_object"
        )
        res_data = json.loads(result_text)
        return jsonify(res_data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

