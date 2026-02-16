import io
import pandas as pd
from extensions import db
from models import Card

def process_csv_import(file_content, user_id):
    """CSVを解析してDBに登録/更新する。フォーマットを自動判別する"""
    df = None
    # 3. 文字コードは UTF-8 を優先しつつ、エラー時は cp932 (Shift_JIS) でリトライ
    for enc in ["utf-8-sig", "cp932"]:
        try:
            df = pd.read_csv(io.BytesIO(file_content), encoding=enc)
            print(f"DEBUG: Successfully read CSV with encoding {enc}")
            break
        except Exception as e:
            print(f"DEBUG: Failed to read CSV with encoding {enc}: {str(e)}")
    
    if df is None:
        raise Exception("CSVファイルの読み込みに失敗しました（対応していない文字コードです）")

    columns = list(df.columns)
    # 1. 自動判別: 「企業名」と「代表者名」が含まれていれば企業リスト形式とみなす
    if "企業名" in columns and "代表者名" in columns:
        print("DEBUG: Detected Corporate List format")
        return _process_corporate_list(df, user_id)
    else:
        print("DEBUG: Detected Eight format (or default)")
        return _process_eight_csv(df, user_id)

def _process_corporate_list(df, user_id):
    """企業リスト形式のCSV処理"""
    count_success = 0
    count_updated = 0
    
    for i, row in df.iterrows():
        # メールアドレスをキーにする
        email = str(row.get("メールアドレス", "")).strip()
        if not email or email == "nan":
            continue
            
        company = _get_val(row, "企業名")
        person = _get_val(row, "代表者名")
        
        # 電話番号の先頭の ' を削除
        phone = _get_val(row, "電話番号")
        if phone.startswith("'"):
            phone = phone[1:]
            
        url = _get_val(row, "企業ホームページURL")
        # 業種（分類１） -> department_name (便宜上)
        department = _get_val(row, "業種（分類１）")
        
        existing_card = Card.query.filter_by(user_id=user_id, email=email).first()
        
        if existing_card:
            existing_card.company_name = company
            existing_card.person_name = person
            existing_card.phone_number = phone
            existing_card.url = url
            existing_card.department_name = department
            existing_card.job_title = "代表者" # 固定
            count_updated += 1
        else:
            new_card = Card(
                user_id=user_id,
                image_path="no-image.png",
                company_name=company,
                department_name=department,
                job_title="代表者",
                person_name=person,
                phone_number=phone,
                email=email,
                url=url
            )
            db.session.add(new_card)
            count_success += 1
            
    db.session.commit()
    return count_success, count_updated

def _process_eight_csv(df, user_id):
    """Eight形式のCSV処理（既存ロジック）"""

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

    db.session.commit()
    return count_success, count_updated

def _get_val(row, key):
    """Helper for corporate list"""
    val = row.get(key)
    return str(val).strip() if pd.notnull(val) else ""

def _get_row_val(row, key, default):
    val = row.get(key)
    return str(val) if pd.notnull(val) else default
