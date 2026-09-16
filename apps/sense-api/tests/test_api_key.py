import os
from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(dotenv_path=env_path)

api_key = os.getenv("GEMINI_API_KEY")

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

try:
    chat = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=api_key)
    result = chat.invoke("Hi")
    print(f"SUCCESS Chat: {result.content}")
except Exception as e:
    print(f"FAILED Chat: {e}")

try:
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-2-preview", google_api_key=api_key)
    result = embeddings.embed_query("Troubleshoot Tetra Pak pasteurizer")
    print(f"SUCCESS gemini-embedding-2-preview, embedding size: {len(result)}")
except Exception as e:
    print(f"FAILED gemini-embedding-2-preview: {e}")
