import requests
from bs4 import BeautifulSoup

def get_company_info(url):
    """URLから会社のWebサイト情報を取得する"""
    if not url or "." not in url:
        return "ウェブサイト情報なし"
    if not url.startswith("http"):
        url = "https://" + url
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, timeout=10, headers=headers)
        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text, "html.parser")
        for s in soup(["script", "style", "header", "footer", "nav"]):
            s.decompose()
        
        text_content = soup.get_text()
        if not text_content:
            return "Webサイトに内容がありません"
            
        full_text = " ".join(text_content.split())
        return str(full_text)[:1200]
    except Exception:
        return "Webサイトにアクセス不可"
