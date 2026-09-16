import os
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(dotenv_path=env_path)

from langchain_google_genai import GoogleGenerativeAIEmbeddings

try:
    embeddings = GoogleGenerativeAIEmbeddings(model="text-embedding-004")
    result = embeddings.embed_query("Troubleshoot Tetra Pak pasteurizer")
    print(f"SUCCESS with text-embedding-004, embedding size: {len(result)}")
except Exception as e:
    print(f"FAILED text-embedding-004: {e}")

try:
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    result = embeddings.embed_query("Troubleshoot Tetra Pak pasteurizer")
    print(f"SUCCESS with models/embedding-001, embedding size: {len(result)}")
except Exception as e:
    print(f"FAILED models/embedding-001: {e}")
