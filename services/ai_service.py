import json
from azure.ai.vision.imageanalysis import ImageAnalysisClient
from azure.ai.vision.imageanalysis.models import VisualFeatures
from azure.core.credentials import AzureKeyCredential
from openai import AzureOpenAI
import google.generativeai as genai

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



def configure_gemini():
    if Config.GEMINI_API_KEY:
        genai.configure(api_key=Config.GEMINI_API_KEY)

def list_gemini_models():
    """利用可能なGeminiモデルをデバッグ出力する"""
    try:
        configure_gemini()
        print("--- Available Gemini Models ---")
        for m in genai.list_models():
            print(f"Name: {m.name}, DisplayName: {m.display_name}, Methods: {m.supported_generation_methods}")
        print("-------------------------------")
    except Exception as e:
        print(f"Error listing Gemini models: {str(e)}")

def get_ai_completion(prompt, system_prompt="You are a professional business assistant.", response_format=None):
    """Azure OpenAI または Gemini を使用してテキスト生成を行う"""
    if Config.AI_ENGINE_TYPE == "gemini":
        configure_gemini()
        # 429 (Rate Limit) への対策としてリトライ処理を追加
        import time
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # 利用可能な最新の安定版 'gemini-2.0-flash' を使用
                model = genai.GenerativeModel(
                    model_name="gemini-2.0-flash",
                    system_instruction=system_prompt
                )
                generation_config = {}
                if response_format == "json_object":
                    generation_config["response_mime_type"] = "application/json"
                
                response = model.generate_content(prompt, generation_config=generation_config)
                return response.text
            except Exception as e:
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
        configure_gemini()
        import time
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # 最新の 2.0-flash モデルを使用
                model = genai.GenerativeModel("gemini-2.0-flash")
                prompt = """
                あなたはプロのビジネス・アシスタントです。
                提供された名刺画像から情報を抽出し、以下のJSON形式でのみ回答してください。
                不明な項目は空文字にしてください。
                JSONのキーは必ず以下を使用してください: 
                name, company, department, title, url, email, phone
                """
                
                mime_type = "image/jpeg"
                if filename.lower().endswith(".png"):
                    mime_type = "image/png"
                elif filename.lower().endswith(".webp"):
                    mime_type = "image/webp"

                response = model.generate_content([
                    prompt,
                    {"mime_type": mime_type, "data": image_data}
                ], generation_config={"response_mime_type": "application/json"})
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

