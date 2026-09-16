import os
import sys
from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(env_path)

print("--- Testing API Connectivity ---")

# Test Gemini via langchain_google_genai
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("[FAIL] GEMINI_API_KEY not found in environment.")
    else:
        llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=api_key)
        res = llm.invoke("Hello")
        if res.content:
            print("[OK] Gemini API connected successfully.")
        else:
            print("[FAIL] Gemini API returned empty response.")
except Exception as e:
    print(f"[FAIL] Gemini API connectivity error: {str(e)[:150]}")

# Test Pinecone
try:
    from pinecone import Pinecone
    pc_api_key = os.getenv("PINECONE_API_KEY")
    if not pc_api_key:
        print("[FAIL] PINECONE_API_KEY not found in environment.")
    else:
        pc = Pinecone(api_key=pc_api_key)
        idx = pc.list_indexes()
        names = [i.name for i in idx.indexes]
        print(f"[OK] Pinecone API connected successfully. Available indexes: {names}")
except Exception as e:
    print(f"[FAIL] Pinecone API connectivity error: {str(e)[:150]}")
