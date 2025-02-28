from typing import List, Dict, Optional, Any, TYPE_CHECKING
from models.conversation import Message, Summary
from google.cloud.firestore import Client
from datetime import datetime, timezone
import uuid

class ConversationService:
    def __init__(self, db: Client):
        self.db = db
        self.messages_ref = db.collection('messages')
        self.summaries_ref = db.collection('summaries')
        self.MAX_MESSAGES_PER_SUMMARY = 50

    async def add_message(self, user_id: str, conversation_id: str, message: Message) -> str:
        """メッセージを追加"""
        try:
            message_id = str(uuid.uuid4())
            message_data = {
                'user_id': user_id,
                'conversation_id': conversation_id,
                'role': message.role,
                'content': message.content or message.text,  # contentがない場合はtextを使用
                'text': message.text,
                'sender': message.sender,
                'created_at': datetime.now(timezone.utc),
                'message_id': message_id
            }
            
            self.messages_ref.document(message_id).set(message_data)
            return message_id
        except Exception as e:
            print(f"Error adding message: {e}")
            raise

    async def get_messages(self, user_id: str, conversation_id: str, limit: int = 20) -> List[Message]:
        """会話履歴を取得"""
        try:
            messages = []
            query = (self.messages_ref
                    .where('user_id', '==', user_id)
                    .where('conversation_id', '==', conversation_id)
                    .order_by('created_at', direction='DESCENDING')
                    .limit(limit))
            
            docs = query.stream()
            
            for doc in docs:
                data = doc.to_dict()
                message = Message(
                    sender=data.get('sender'),
                    text=data.get('text'),
                    content=data.get('content'),
                    role=data.get('role', 'user'),
                    timestamp=data.get('created_at')
                )
                messages.append(message)
            
            # 古い順に並べ替え
            messages.reverse()
            return messages
        except Exception as e:
            print(f"Error getting messages: {e}")
            return []

    async def add_summary(self, user_id: str, conversation_id: str, content: str) -> str:
        """要約を追加"""
        try:
            summary_id = str(uuid.uuid4())
            summary_data = {
                'user_id': user_id,
                'conversation_id': conversation_id,
                'content': content,
                'created_at': datetime.now(timezone.utc),
                'summary_id': summary_id
            }
            
            self.summaries_ref.document(summary_id).set(summary_data)
            return summary_id
        except Exception as e:
            print(f"Error adding summary: {e}")
            raise

    async def get_summaries(self, user_id: str, conversation_id: str, limit: int = 5) -> List[Summary]:
        """要約履歴を取得"""
        try:
            summaries = []
            query = (self.summaries_ref
                    .where('user_id', '==', user_id)
                    .where('conversation_id', '==', conversation_id)
                    .order_by('created_at', direction='DESCENDING')
                    .limit(limit))
            
            docs = query.stream()
            
            for doc in docs:
                data = doc.to_dict()
                summary = Summary(
                    content=data.get('content'),
                    created_at=data.get('created_at')
                )
                summaries.append(summary)
            
            return summaries
        except Exception as e:
            print(f"Error getting summaries: {e}")
            return []

    async def should_create_summary(self, user_id: str, conversation_id: str) -> bool:
        """要約を作成すべきかどうかを判断"""
        try:
            # 最新の要約を取得
            latest_summaries = await self.get_summaries(user_id, conversation_id, limit=1)
            
            if not latest_summaries:
                # 要約がまだない場合、メッセージ数が閾値を超えたら要約を作成
                message_count = await self._count_messages(user_id, conversation_id)
                return message_count >= self.MAX_MESSAGES_PER_SUMMARY
            
            # 最新の要約以降のメッセージ数を取得
            latest_summary = latest_summaries[0]
            message_count = await self._count_messages_since(user_id, conversation_id, latest_summary.created_at)
            
            return message_count >= self.MAX_MESSAGES_PER_SUMMARY
        except Exception as e:
            print(f"Error checking if summary should be created: {e}")
            return False

    async def _count_messages(self, user_id: str, conversation_id: str) -> int:
        """メッセージ数をカウント"""
        try:
            query = (self.messages_ref
                    .where('user_id', '==', user_id)
                    .where('conversation_id', '==', conversation_id))
            
            docs = query.stream()
            return len(list(docs))
        except Exception as e:
            print(f"Error counting messages: {e}")
            return 0

    async def _count_messages_since(self, user_id: str, conversation_id: str, since_time) -> int:
        """特定の時間以降のメッセージ数をカウント"""
        try:
            query = (self.messages_ref
                    .where('user_id', '==', user_id)
                    .where('conversation_id', '==', conversation_id)
                    .where('created_at', '>', since_time))
            
            docs = query.stream()
            return len(list(docs))
        except Exception as e:
            print(f"Error counting messages since time: {e}")
            return 0

    async def get_messages_since(self, user_id: str, conversation_id: str, since_time) -> List[Message]:
        """特定の時間以降のメッセージを取得"""
        try:
            messages = []
            query = (self.messages_ref
                    .where('user_id', '==', user_id)
                    .where('conversation_id', '==', conversation_id)
                    .where('created_at', '>', since_time)
                    .order_by('created_at'))
            
            docs = query.stream()
            
            for doc in docs:
                data = doc.to_dict()
                message = Message(
                    role=data.get('role'),
                    content=data.get('content')
                )
                messages.append(message)
            
            return messages
        except Exception as e:
            print(f"Error getting messages since time: {e}")
            return [] 