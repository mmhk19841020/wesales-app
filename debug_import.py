import sys
import google
print(f"google path: {google.__path__}")
try:
    from google import genai
    print(f"genai path: {genai.__path__}")
except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    print(f"Error: {e}")
