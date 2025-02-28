import stripe
from models.user import User
from datetime import datetime
import os
from services.user_service import UserService
from handlers.line_webhook import LineWebhookHandler
from linebot.models import TextSendMessage

class StripeWebhookHandler:
    def __init__(self, user_service: UserService, line_handler: LineWebhookHandler):
        self.stripe = stripe
        self.stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
        self.webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
        self.user_service = user_service
        self.line_handler = line_handler
        self.PRICE_ID_TO_TYPE = {
            os.getenv('STRIPE_PRICE_ID_month'): 'monthly',
            os.getenv('STRIPE_PRICE_ID_year'): 'yearly'
        }

    async def handle_webhook(self, payload, sig_header):
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, self.webhook_secret
            )

            # イベントタイプに応じて処理
            if event['type'] == 'checkout.session.completed':
                await self._handle_checkout_completed(event['data']['object'])
            elif event['type'] == 'customer.subscription.deleted':
                await self._handle_subscription_deleted(event['data']['object'])
            elif event['type'] == 'customer.subscription.updated':
                await self._handle_subscription_updated(event['data']['object'])

        except Exception as e:
            print(f'Error handling webhook: {str(e)}')
            raise

    async def _handle_checkout_completed(self, session):
        try:
            # セッションからユーザーIDとサブスクリプション情報を取得
            user_id = session.get('client_reference_id')
            subscription_id = session.get('subscription')
            price_id = session.get('line_items', {}).get('data', [{}])[0].get('price', {}).get('id')

            if not user_id or not subscription_id:
                print('Missing user_id or subscription_id in session')
                return

            # サブスクリプションタイプを決定
            subscription_type = self.PRICE_ID_TO_TYPE.get(price_id, 'monthly')

            # ユーザーのサブスクリプション情報を更新
            await self.user_service.update_subscription(user_id, subscription_type)
            
            # LINEメッセージを送信
            await self.line_handler.send_subscription_success_message(user_id)

        except Exception as e:
            print(f'Error handling checkout completed: {str(e)}')
            raise

    async def _handle_subscription_deleted(self, subscription):
        try:
            # メタデータからユーザーIDを取得
            user_id = subscription.get('metadata', {}).get('user_id')
            if not user_id:
                print('Missing user_id in subscription metadata')
                return

            # サブスクリプションを無効化
            await self.user_service.deactivate_subscription(user_id)
            
            # LINEメッセージを送信
            await self.line_handler.send_subscription_cancelled_message(user_id)

        except Exception as e:
            print(f'Error handling subscription deleted: {str(e)}')
            raise

    async def _handle_subscription_updated(self, subscription):
        try:
            # メタデータからユーザーIDを取得
            user_id = subscription.get('metadata', {}).get('user_id')
            if not user_id:
                print('Missing user_id in subscription metadata')
                return

            # サブスクリプションの状態をチェック
            status = subscription.get('status')
            price_id = subscription.get('items', {}).get('data', [{}])[0].get('price', {}).get('id')
            subscription_type = self.PRICE_ID_TO_TYPE.get(price_id, 'monthly')

            if status == 'active':
                await self.user_service.update_subscription(user_id, subscription_type)
            elif status in ['canceled', 'unpaid']:
                await self.user_service.deactivate_subscription(user_id)

        except Exception as e:
            print(f'Error handling subscription updated: {str(e)}')
            raise 