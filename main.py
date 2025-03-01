from app import app
from fastapi import FastAPI, Request, Response
from linebot import WebhookParser
from linebot.exceptions import InvalidSignatureError
import sys
import os
import json

app = FastAPI()

@app.post("/webhook")
async def webhook(request: Request):
    print("🔍 Webhook received!", file=sys.stderr)
    
    # ヘッダーの出力
    print("Headers:", dict(request.headers), file=sys.stderr)
    
    # リクエストボディの取得と出力
    body = await request.body()
    body_text = body.decode("utf-8")
    print("Body:", body_text, file=sys.stderr)
    
    # 署名の検証
    signature = request.headers.get("X-Line-Signature", "")
    if not signature:
        print("❌ X-Line-Signature がありません", file=sys.stderr)
        return Response(status_code=400)
        
    parser = WebhookParser(os.getenv("LINE_CHANNEL_SECRET"))
    try:
        events = parser.parse(body_text, signature)
        # イベントの内容をログに出力
        for event in events:
            print(f"🔍 Received event: {event}", file=sys.stderr)
    except InvalidSignatureError:
        print("❌ 署名が一致しません", file=sys.stderr)
        return Response(status_code=400)
    except Exception as e:
        print(f"❌ エラーが発生しました: {str(e)}", file=sys.stderr)
        return Response(status_code=400)
        
    print("✅ Webhook 正常受信", file=sys.stderr)
    return "OK"

if __name__ == "__main__":
    import uvicorn
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True) 