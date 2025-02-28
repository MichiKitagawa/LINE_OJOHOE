from linebot import LineBotApi
from linebot.models import TextSendMessage
from services.user_service import UserService
from services.ai_service import AIService
from linebot.exceptions import LineBotApiError
from services.stripe_service import StripeService

class LineWebhookHandler:
    def __init__(self, line_bot_api: LineBotApi, user_service: UserService, ai_service: AIService):
        self.line_bot_api = line_bot_api
        self.user_service = user_service
        self.ai_service = ai_service
        self.stripe_service = StripeService()

    async def handle_message(self, event):
        """メッセージイベントを処理"""
        if event.message.type != "text":
            return

        try:
            user_id = event.source.user_id
            message_text = event.message.text
            print(f"Processing message: {message_text} from user: {user_id}")

            # 通常のメッセージ処理
            limit_message = await self.user_service.handle_message(user_id, message_text, "default")
            if limit_message:
                self.line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=limit_message)
                )
                return

            # AIレスポンスを生成（ユーザーIDを渡す）
            response = await self.ai_service.generate_response(message_text, user_id, "default")
            self.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=response)
            )

        except Exception as e:
            print(f"Error handling message: {e}")
            self.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="申し訳ありません。エラーが発生しました。")
            )

    async def send_subscription_success_message(self, user_id: str) -> None:
        """サブスクリプション開始時のメッセージを送信"""
        try:
            message = """🎉 決済が完了しました！

これより無制限で相談可能です。
ご利用ありがとうございます。✨

💡 サブスクリプションの有効期限が近づいた際は、
自動的にお知らせいたします。"""

            self.line_bot_api.push_message(
                user_id,
                TextSendMessage(text=message)
            )
        except Exception as e:
            print(f"Error sending subscription success message: {e}")

    async def send_subscription_cancelled_message(self, user_id: str) -> None:
        """サブスクリプション終了時のメッセージを送信"""
        try:
            message = """📢 サブスクリプションが終了しました。

これより無料プランとなり、
1日1回までの相談制限が適用されます。"""

            self.line_bot_api.push_message(
                user_id,
                TextSendMessage(text=message)
            )
        except Exception as e:
            print(f"Error sending subscription cancelled message: {e}")

    async def handle_membership_event(self, user_id: str, is_active: bool) -> None:
        """メンバーシップの状態変更を処理"""
        try:
            if is_active:
                await self.send_subscription_success_message(user_id)
            else:
                await self.send_subscription_cancelled_message(user_id)
        except Exception as e:
            print(f"Error handling membership event: {e}")
            raise 