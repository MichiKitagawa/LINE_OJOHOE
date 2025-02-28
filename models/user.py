from datetime import datetime, timezone
from typing import Optional, Dict, Any

class User:
    def __init__(
        self,
        user_id: str,
        is_paid: bool = False,
        consultation_count: int = 0,
        last_consultation_date: Optional[datetime] = None,
        subscription_type: Optional[str] = None,
        subscription_end: Optional[datetime] = None,
        subscription_id: Optional[str] = None,
        stripe_customer_id: Optional[str] = None,
        message_count: int = 0,
        last_message_date: Optional[datetime] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        self.user_id = user_id
        self.line_user_id = user_id  # 後方互換性のため
        self.is_paid = is_paid
        self.consultation_count = consultation_count
        
        # タイムゾーン情報の処理
        self.last_consultation_date = self._ensure_timezone(last_consultation_date)
        self.subscription_end = self._ensure_timezone(subscription_end)
        self.last_message_date = self._ensure_timezone(last_message_date)
        self.created_at = self._ensure_timezone(created_at) or datetime.now(timezone.utc)
        self.updated_at = self._ensure_timezone(updated_at) or datetime.now(timezone.utc)
        
        self.subscription_type = subscription_type
        self.subscription_id = subscription_id
        self.stripe_customer_id = stripe_customer_id
        self.message_count = message_count

    def _ensure_timezone(self, dt: Optional[datetime]) -> Optional[datetime]:
        """日時にタイムゾーン情報がない場合はUTCを付与"""
        if dt is None:
            return None
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt

    def to_dict(self) -> Dict[str, Any]:
        return {
            'user_id': self.user_id,
            'line_user_id': self.line_user_id,
            'is_paid': self.is_paid,
            'consultation_count': self.consultation_count,
            'last_consultation_date': self.last_consultation_date,
            'subscription_type': self.subscription_type,
            'subscription_end': self.subscription_end,
            'subscription_id': self.subscription_id,
            'stripe_customer_id': self.stripe_customer_id,
            'message_count': self.message_count,
            'last_message_date': self.last_message_date,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'User':
        return User(
            user_id=data.get('user_id') or data.get('line_user_id'),
            is_paid=data.get('is_paid', False),
            consultation_count=data.get('consultation_count', 0),
            last_consultation_date=data.get('last_consultation_date'),
            subscription_type=data.get('subscription_type'),
            subscription_end=data.get('subscription_end'),
            subscription_id=data.get('subscription_id'),
            stripe_customer_id=data.get('stripe_customer_id'),
            message_count=data.get('message_count', 0),
            last_message_date=data.get('last_message_date'),
            created_at=data.get('created_at', datetime.now(timezone.utc)),
            updated_at=data.get('updated_at', datetime.now(timezone.utc))
        ) 