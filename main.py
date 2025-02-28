from app import app

if __name__ == "__main__":
    import uvicorn
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True) 