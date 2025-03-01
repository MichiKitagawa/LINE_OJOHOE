import os
import firebase_admin
from firebase_admin import credentials, firestore
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import JSONResponse
from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage
import uvicorn
from dotenv import load_dotenv
import json
from services.conversation_service import ConversationService
from services.user_service import UserService
from services.ai_service import AIService
from handlers.line_webhook import LineWebhookHandler
from handlers.stripe_webhook_handler import StripeWebhookHandler

# 環境変数の読み込み
load_dotenv()

# Firebaseの初期化とFirestoreクライアントの作成
firebase_initialized = False
db = None

try:
    # 環境変数から認証情報を読み込む
    firebase_credentials = os.getenv("FIREBASE_CREDENTIALS")
    if firebase_credentials:
        try:
            cred_dict = json.loads(firebase_credentials)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            db = firestore.client()
            firebase_initialized = True
            print("Firebase initialized with credentials from environment variable")
        except Exception as e:
            print(f"Firebase initialization error with credentials from environment: {e}")
except Exception as e:
    print(f"Firebase initialization error: {e}")

if not firebase_initialized:
    print("WARNING: Firebase not initialized. Some features may not work properly.")
    from unittest.mock import MagicMock
    db = MagicMock()

# LINEの設定
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
parser = WebhookParser(os.getenv("LINE_CHANNEL_SECRET"))

# サービスの初期化
conversation_service = ConversationService(db)
ai_service = AIService(conversation_service)
user_service = UserService(db, conversation_service)

# ハンドラーの初期化（依存関係の循環を解決）
line_webhook_handler = LineWebhookHandler(line_bot_api, user_service, ai_service)
stripe_webhook_handler = StripeWebhookHandler(user_service, line_webhook_handler)

app = FastAPI()

@app.get("/")
async def root():
    return {
        "message": "恋愛相談AIサービスが稼働中です", 
        "firebase_initialized": firebase_initialized,
        "environment": os.getenv("ENVIRONMENT", "not set")
    }

@app.post("/webhook")
async def line_webhook(request: Request):
    signature = request.headers.get("X-Line-Signature", "")
    body = await request.body()
    body_decode = body.decode("utf-8")
    
    try:
        events = parser.parse(body_decode, signature)
        for event in events:
            if isinstance(event, MessageEvent) and isinstance(event.message, TextMessage):
                await line_webhook_handler.handle_message(event)
        return JSONResponse(content={"message": "OK"}, status_code=200)
    except InvalidSignatureError:
        print("❌ 署名が一致しません")
        raise HTTPException(status_code=400, detail="Invalid signature")
    except Exception as e:
        print(f"Error in line_webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    body = await request.body()
    signature = request.headers.get("Stripe-Signature", "")
    
    try:
        await stripe_webhook_handler.handle_webhook(body, signature)
        return JSONResponse(content={"message": "OK"})
    except Exception as e:
        print(f"Error in stripe_webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True) 