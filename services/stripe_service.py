import stripe
from datetime import datetime
from models.user import User
import os
from dotenv import load_dotenv
from typing import Optional

# 明示的に.envを読み込む
load_dotenv()

class StripeService:
    def __init__(self):
        self.stripe = stripe
        self.stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
        self.PRICE_IDS = {
            'month': os.getenv('STRIPE_PRICE_ID_month'),
            'year': os.getenv('STRIPE_PRICE_ID_year')
        }
        self.SUCCESS_URL = os.getenv('SUCCESS_URL', 'http://localhost:8000/success')
        self.CANCEL_URL = os.getenv('CANCEL_URL', 'http://localhost:8000/cancel')
        print(f"Stripe API Key loaded: {stripe.api_key[:10]}...")  # デバッグ用（最初の10文字のみ表示）

    def create_checkout_session(self, user_id: Optional[str], plan_type: str = 'month') -> Optional[str]:
        """Stripeのチェックアウトセッションを作成"""
        try:
            price_id = self.PRICE_IDS.get(plan_type)
            if not price_id:
                print(f"Invalid plan type: {plan_type}")
                return None

            session = self.stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=self.SUCCESS_URL,
                cancel_url=self.CANCEL_URL,
                client_reference_id=user_id,
                metadata={
                    'user_id': user_id,
                    'plan_type': plan_type
                } if user_id else None
            )
            
            return session.url

        except Exception as e:
            print(f"Error creating checkout session: {e}")
            return None 