import urllib.request
import json
from dotenv import load_dotenv
import os

env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=env_path)

api_key = os.getenv("GEMINI_API_KEY")

url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"

try:
    with urllib.request.urlopen(url) as response:
        data = json.loads(response.read().decode("utf-8"))
        chat_models = []
        embed_models = []
        for m in data.get('models', []):
            methods = m.get('supportedGenerationMethods', [])
            if 'generateContent' in methods:
                chat_models.append(m['name'])
            if 'embedContent' in methods:
                embed_models.append(m['name'])
        print(f"Contains 1.5-flash chat? {any('1.5-flash' in m for m in chat_models)}")
        print(f"Contains text-embedding-004 embed? {any('text-embedding-004' in m for m in embed_models)}")
        if not any('text-embedding-004' in m for m in embed_models):
            print(f"Embed models available: {embed_models}")
except Exception as e:
    print(f"Error checking models: {e}")
