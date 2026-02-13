import json
from azure.ai.vision.imageanalysis import ImageAnalysisClient
from azure.ai.vision.imageanalysis.models import VisualFeatures
from azure.core.credentials import AzureKeyCredential
from openai import AzureOpenAI
from google import genai

from config import Config

def get_vision_client():
    if not Config.VISION_KEY or not Config.VISION_ENDPOINT:
        return None
    return ImageAnalysisClient(
        endpoint=Config.VISION_ENDPOINT, 
        credential=AzureKeyCredential(Config.VISION_KEY)
    )

def get_openai_client():
    if not Config.OPENAI_KEY or not Config.OPENAI_ENDPOINT:
        return None
    
    # AzureOpenAI expects only the base endpoint (e.g., https://name.cognitiveservices.azure.com/)
    # If the user provides a full URL, we extract the base part and the deployment name if present.
    endpoint = Config.OPENAI_ENDPOINT
    deployment = Config.OPENAI_DEPLOYMENT
    
    if "/openai/" in endpoint:
        # Extract deployment name from URL if it exists: .../deployments/{deployment_name}/...
        if "/deployments/" in endpoint:
            parts = endpoint.split("/deployments/")
            if len(parts) > 1:
                potential_deployment = parts[1].split("/")[0]
                if potential_deployment:
                    deployment = potential_deployment
        
        endpoint = endpoint.split("/openai/")[0]
        
    return AzureOpenAI(
        api_key=Config.OPENAI_KEY, 
        api_version="2025-01-01-preview", 
        azure_endpoint=endpoint
    ), deployment



def get_gemini_client():
    if Config.GEMINI_API_KEY:
        return genai.Client(api_key=Config.GEMINI_API_KEY)
    return None

def list_gemini_models():
    """利用可能なGeminiモデルをデバッグ出力する"""
    try:
        client = get_gemini_client()
        if not client:
            print("Gemini API Key not configured.")
            return

        print("--- Available Gemini Models ---")
        # Note: list_models in new SDK might differ, using simple iteration if iterable or verifying documentation.
        # Assuming client.models.list() exists and returns models.
        for m in client.models.list():
            print(f"Name: {m.name}, DisplayName: {m.display_name}")
        print("-------------------------------")
    except Exception as e:
        print(f"Error listing Gemini models: {str(e)}")

def get_ai_completion(prompt, system_prompt="You are a professional business assistant.", response_format=None):
    """Azure OpenAI または Gemini を使用してテキスト生成を行う"""
    if Config.AI_ENGINE_TYPE == "gemini":
        client = get_gemini_client()
        if not client:
             raise Exception("Gemini API Key is not configured.")

        # 429 (Rate Limit) への対策としてリトライ処理を追加
        import time
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # 利用可能な最新の安定版 'gemini-2.0-flash' を使用
                config = {}
                if response_format == "json_object":
                    config["response_mime_type"] = "application/json"
                
                if system_prompt:
                    config["system_instruction"] = system_prompt

                response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=prompt,
                    config=config
                )
                return response.text
            except Exception as e:
                # SDK might raise custom errors, but checking string for 429 is a safe fallback
                if "429" in str(e) and attempt < max_retries - 1:
                    time.sleep(2 ** attempt) # 指数バックオフ
                    continue
                if "404" in str(e) or "not found" in str(e).lower():
                    list_gemini_models()
                raise e

    else:
        # Azure OpenAI
        result = get_openai_client()
        if not result:
            raise Exception("Azure OpenAI client is not configured.")
        client, deployment = result
            
        args = {
            "model": deployment,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        }
        if response_format == "json_object":
            args["response_format"] = {"type": "json_object"}
        
        response = client.chat.completions.create(**args)
        return response.choices[0].message.content


def analyze_card_image(image_data, filename):
    """名刺画像を解析して構造化データを返す"""
    if Config.AI_ENGINE_TYPE == "gemini":
        client = get_gemini_client()
        if not client:
             raise Exception("Gemini API Key is not configured.")

        import time
        max_retries = 3
        for attempt in range(max_retries):
            try:
                prompt = """
                あなたはプロのビジネス・アシスタントです。
                提供された名刺画像から情報を抽出し、以下のJSON形式でのみ回答してください。
                不明な項目は空文字にしてください。
                JSONのキーは必ず以下を使用してください: 
                name, company, department, title, url, email, phone
                """
                
                # New SDK handles generic Part objects or directly accepts compatible types
                from google.genai import types
                
                # Create image part
                # Assuming image_data is bytes
                # We can construct the content part
                image_part = types.Part.from_bytes(data=image_data, mime_type="image/jpeg") # Default to jpeg, adjust as needed or rely on SDK detection if possible
                
                # Adjust mime type based on filename if needed
                if filename.lower().endswith(".png"):
                    image_part = types.Part.from_bytes(data=image_data, mime_type="image/png")
                elif filename.lower().endswith(".webp"):
                    image_part = types.Part.from_bytes(data=image_data, mime_type="image/webp")

                response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=[prompt, image_part],
                    config={"response_mime_type": "application/json"}
                )
                return json.loads(response.text)
            except Exception as e:
                if "429" in str(e) and attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                if "404" in str(e) or "not found" in str(e).lower():
                    list_gemini_models()
                raise e

    else:
        # Azure Vision + Azure OpenAI
        vision_client = get_vision_client()
        if not vision_client:
            raise Exception("Azure Vision client is not configured.")
            
        result = vision_client.analyze(
            image_data=image_data, visual_features=[VisualFeatures.READ]
        )
        raw_text = " ".join(
            [line.text for block in result.read.blocks for line in block.lines]
        )

        struct_prompt = f"以下のテキストからJSON(name, company, department, title, url, email, phone)を抽出して。テキスト: {raw_text}"
        result = get_openai_client()
        if not result:
            raise Exception("Azure OpenAI client is not configured.")
        openai_client, deployment = result
            
        struct_res = openai_client.chat.completions.create(
            model=deployment,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that outputs only JSON.",
                },
                {"role": "user", "content": struct_prompt},
            ],
            response_format={"type": "json_object"},
        )
        return json.loads(struct_res.choices[0].message.content)

