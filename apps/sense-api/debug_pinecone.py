import traceback
try:
    from services.retrieval import generate_rag_response
    print("Success")
except Exception as e:
    with open("err_debug.txt", "w", encoding="utf-8") as f:
        f.write(traceback.format_exc())
