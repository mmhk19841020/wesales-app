import io
import pandas as pd
from extensions import db
from models import Card

def process_eight_csv(file_content, user_id):
    """Eight CSVを解析してDBに登録/更新する"""
    df = None
    for enc in ["cp932", "utf-8-sig"]:
        try:
            df = pd.read_csv(io.BytesIO(file_content), encoding=enc)
            print(f"DEBUG: Successfully read CSV with encoding {enc}")
            break
        except Exception as e:
            print(f"DEBUG: Failed to read CSV with encoding {enc}: {str(e)}")
    
    if df is None:
        raise Exception("CSVファイルの読み込みに失敗しました（対応していない文字コードです）")

    # Column mapping
    column_map = {
        "e-mail": "email",
        "会社名": "company_name",
        "役職": "job_title",
        "携帯電話": "phone_number_mobile",
        "TEL会社": "phone_number_office",
        "部署名": "department_name",
        "会社URL": "url",
        "Webサイト": "url",
        "URL": "url"
    }
    df = df.rename(columns=column_map)

    count_success = 0
    count_updated = 0

    for i, row in df.iterrows():
        email = str(row.get("email", "")).strip()
        
        sei = str(row.get("姓", "")).strip() if pd.notnull(row.get("姓")) else ""
        mei = str(row.get("名", "")).strip() if pd.notnull(row.get("名")) else ""
        person_name = (sei + " " + mei).strip() or "氏名不明"
        
        phone = str(row.get("phone_number_mobile", "")).strip()
        if not phone or phone == "nan":
            phone = str(row.get("phone_number_office", "")).strip()
        
        if not email or email == "nan":
            print(f"DEBUG: Row {i} skipped: Email empty. (Name: {person_name})")
            continue
        
        existing_card = Card.query.filter_by(user_id=user_id, email=email).first()
        
        if existing_card:
            print(f"DEBUG: Updating existing card: {email}")
            existing_card.company_name = _get_row_val(row, "company_name", existing_card.company_name)
            existing_card.department_name = _get_row_val(row, "department_name", existing_card.department_name)
            existing_card.job_title = _get_row_val(row, "job_title", existing_card.job_title)
            existing_card.person_name = person_name if person_name != "氏名不明" else existing_card.person_name
            existing_card.phone_number = phone if phone != "nan" else existing_card.phone_number
            existing_card.url = _get_row_val(row, "url", existing_card.url)
            count_updated += 1
        else:
            print(f"DEBUG: Registering new card: {email}")
            new_card = Card(
                user_id=user_id,
                image_path="no-image.png",
                company_name=_get_row_val(row, "company_name", ""),
                department_name=_get_row_val(row, "department_name", ""),
                job_title=_get_row_val(row, "job_title", ""),
                person_name=person_name,
                phone_number=phone if phone != "nan" else "",
                email=email,
                url=_get_row_val(row, "url", "")
            )
            db.session.add(new_card)
            count_success += 1

    return count_success, count_updated

def _get_row_val(row, key, default):
    val = row.get(key)
    return str(val) if pd.notnull(val) else default
