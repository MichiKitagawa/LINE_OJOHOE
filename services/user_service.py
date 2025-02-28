from datetime import datetime, date, timedelta, timezone
from typing import Optional, Tuple
from models.user import User
from models.conversation import Message
from services.conversation_service import ConversationService
from services.stripe_service import StripeService
import os
from google.cloud.firestore import Client
from firebase_admin.exceptions import FirebaseError

class UserService:
    def __init__(self, db: Client, conversation_service: ConversationService):
        try:
            self.db = db
            self.conversation_service = conversation_service
            self.users_ref = db.collection('users')
            self.MONTHLY_SUBSCRIPTION_DAYS = 30
            self.YEARLY_SUBSCRIPTION_DAYS = 365
            self.stripe_service = StripeService()
            print("Database connection initialized successfully")
            self.initialize_collections()
        except Exception as e:
            print(f"Error initializing database connection: {e}")
            raise

    def get_now_utc(self) -> datetime:
        """UTCのタイムゾーン情報付きの現在時刻を取得"""
        return datetime.now(timezone.utc)

    def get_today_utc(self) -> datetime:
        """UTCのタイムゾーン情報付きの今日の日付（00:00）を取得"""
        now = self.get_now_utc()
        return datetime(now.year, now.month, now.day, tzinfo=timezone.utc)

    def get_subscription_end_message(self) -> str:
        try:
            checkout_url = self.stripe_service.create_checkout_session(None, 'month')
            return f"""🤖「サブスクの有効期限が切れました。引き続き無制限で相談するには、再登録をお願いします！✨
👉【再登録はこちら】{checkout_url}」"""
        except Exception as e:
            print(f"Error creating checkout URL: {e}")
            return """🤖「サブスクの有効期限が切れました。
引き続き無制限で相談するには、「サブスク」と送信して再登録をお願いします！✨」"""

    def get_limit_exceeded_message(self, user_id: str) -> str:
        return """🤖「本日の無料相談回数を超えました！
次の相談は **明日 0:00 以降** に送信できます。⏳

また明日お話ししましょう！」"""

    async def check_subscription_status(self, user: User) -> Tuple[bool, Optional[str]]:
        """サブスクリプションの状態をチェックし、必要に応じてメッセージを返す"""
        if not user.is_paid:
            return False, None

        now_utc = self.get_now_utc()
        if user.subscription_end and now_utc > user.subscription_end:
            await self.deactivate_subscription(user.user_id)
            return False, self.get_subscription_end_message()

        return True, None

    def get_user(self, user_id: str) -> Optional[User]:
        try:
            print(f"Getting user data for: {user_id}")
            doc = self.users_ref.document(user_id).get()
            if doc.exists:
                print(f"User data found: {doc.to_dict()}")
                return User.from_dict(doc.to_dict())
            print("User not found")
            return None
        except FirebaseError as e:
            print(f"Firebase error in get_user: {e}")
            raise
        except Exception as e:
            print(f"Unexpected error in get_user: {e}")
            raise

    async def can_consult(self, user_id: str) -> Tuple[bool, str]:
        try:
            user = self.get_user(user_id)
            
            if not user:
                print(f"Creating new user: {user_id}")
                user = User(user_id)
                try:
                    self.users_ref.document(user_id).set(user.to_dict())
                    print(f"New user created successfully: {user_id}")
                except Exception as e:
                    print(f"Error creating new user: {e}")
                    raise
                return True, "新規ユーザー"

            print(f"Checking consultation status for user: {user_id}")
            
            # サブスクリプションのチェック
            is_active, message = await self.check_subscription_status(user)
            if message:
                return False, message
            
            if is_active:
                return True, "メンバー"

            today_utc = self.get_today_utc()
            if not user.last_consultation_date:
                return True, "無料相談可能"
                
            # タイムゾーン情報がない場合は付与
            last_date = user.last_consultation_date
            if last_date.tzinfo is None:
                last_date = last_date.replace(tzinfo=timezone.utc)
                
            # 日付部分だけを比較
            if last_date.date() != today_utc.date():
                return True, "無料相談可能"
                
            return False, self.get_limit_exceeded_message(user_id)
            
        except Exception as e:
            print(f"Error in can_consult: {e}")
            raise

    async def handle_message(self, user_id: str, message_text: str, conversation_id: str) -> Optional[str]:
        """メッセージを処理し、必要に応じて制限メッセージを返す"""
        try:
            can_send, status = await self.can_consult(user_id)
            if not can_send:
                return status

            # メッセージを保存
            message = Message("USER", message_text)
            await self.conversation_service.add_message(user_id, conversation_id, message)
            
            # 無料ユーザーの場合、相談回数を更新
            user = self.get_user(user_id)
            if not user.is_paid:
                await self.update_consultation(user_id)

            return None

        except Exception as e:
            print(f"Error handling message: {e}")
            raise

    @staticmethod
    def _update_user_data(transaction, user_ref, user_data):
        transaction.update(user_ref, user_data)

    async def update_consultation(self, user_id: str) -> None:
        try:
            user_ref = self.users_ref.document(user_id)
            user = self.get_user(user_id)
            
            if user:
                today_utc = self.get_today_utc()
                update_data = {
                    'consultation_count': user.consultation_count + 1,
                    'last_consultation_date': today_utc,
                    'updated_at': self.get_now_utc()
                }
                user_ref.update(update_data)
                print(f"Updated consultation count for user: {user_id}")
        except Exception as e:
            print(f"Error updating consultation: {e}")
            raise

    async def update_membership_status(self, user_id: str, is_paid: bool) -> None:
        user = self.get_user(user_id)
        if user:
            user.is_paid = is_paid
            user.updated_at = self.get_now_utc()
            self.users_ref.document(user_id).update(user.to_dict())

    async def update_subscription_status(self, user_id: str, is_active: bool, subscription_id: str = None):
        try:
            user_ref = self.users_ref.document(user_id)
            update_data = {
                'is_paid': is_active,
                'subscription_id': subscription_id,
                'updated_at': self.get_now_utc()
            }
            user_ref.update(update_data)
            print(f"Updated subscription status for user {user_id}: {is_active}")
        except Exception as e:
            print(f"Error updating subscription status: {e}")
            raise

    async def update_subscription(self, user_id: str, subscription_type: str) -> None:
        """サブスクリプションを更新または開始"""
        try:
            user = self.get_user(user_id)
            if not user:
                # ユーザーが存在しない場合は新規作成
                user = User(user_id=user_id)
                self.users_ref.document(user_id).set(user.to_dict())

            days = self.YEARLY_SUBSCRIPTION_DAYS if subscription_type == "yearly" else self.MONTHLY_SUBSCRIPTION_DAYS
            now_utc = self.get_now_utc()
            subscription_end = now_utc + timedelta(days=days)

            update_data = {
                'user_id': user_id,
                'line_user_id': user_id,
                'is_paid': True,
                'subscription_type': subscription_type,
                'subscription_end': subscription_end,
                'updated_at': now_utc
            }
            
            self.users_ref.document(user_id).update(update_data)
            print(f"Updated subscription for user {user_id}: {subscription_type}")
        except Exception as e:
            print(f"Error updating subscription: {e}")
            raise

    async def deactivate_subscription(self, user_id: str) -> None:
        """サブスクリプションを無効化"""
        try:
            update_data = {
                'is_paid': False,
                'subscription_type': None,
                'subscription_end': None,
                'updated_at': self.get_now_utc()
            }
            self.users_ref.document(user_id).update(update_data)
            print(f"Deactivated subscription for user: {user_id}")
        except Exception as e:
            print(f"Error deactivating subscription: {e}")
            raise

    def initialize_collections(self):
        print("Initializing Firestore collections...")
        try:
            # usersコレクションが存在することを確認
            users_ref = self.db.collection('users')
            
            # テストドキュメントの作成（開発環境のみ）
            if os.getenv('ENVIRONMENT') == 'development':
                test_user = User('test_user_id')
                users_ref.document('test_user_id').set(test_user.to_dict())
                print("Test user created successfully")
                
            print("Collections initialized successfully")
        except Exception as e:
            print(f"Error initializing collections: {e}")
            raise 