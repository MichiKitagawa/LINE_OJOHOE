import os
import json
import httpx
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from models.conversation import Message
import re
from services.conversation_service import ConversationService
from services.prompt_service import PromptService

# 型チェック時のみインポートする（実行時には評価されない）
if TYPE_CHECKING:
    from services.conversation_service import ConversationService

class AIService:
    def __init__(self, conversation_service: ConversationService):
        self.conversation_service = conversation_service
        self.prompt_service = PromptService()
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://localhost:8000",  # あなたのドメインに変更してください
            "Content-Type": "application/json"
        }
        self.user_names = {}  # ユーザーの名前を保存する辞書

    def _extract_name(self, message: str) -> Optional[str]:
        """メッセージから名前を抽出する試み"""
        patterns = [
            r"私の名前は(.+?)(?:です|だよ|だ|よ|。|$)",
            r"(.+?)(?:です|だよ|だ|って言います|と言います|と申します|よ|。|$)",
            r"(.+?)(?:って|と)(?:呼んで|言って)",
            r"名前は(.+?)(?:です|だよ|だ|よ|。|$)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message)
            if match:
                name = match.group(1).strip()
                # 名前として不適切な長さや内容を除外
                if 1 <= len(name) <= 10 and not re.match(r"^[0-9]+$", name):
                    return name
        return None

    async def generate_response(self, message_text: str, user_id: str, conversation_id: str, character: str = "ojou") -> str:
        """応答を生成"""
        try:
            # 名前の抽出と保存
            extracted_name = self._extract_name(message_text)
            if extracted_name:
                self.user_names[user_id] = extracted_name
                
            # プロンプトを準備
            messages = []
            
            # システムメッセージを追加
            messages.append(self.prompt_service.get_system_message(character))
            
            # 指示メッセージを追加
            messages.append(self.prompt_service.get_instruction_message(character))
            
            # 会話例を追加
            messages.extend(self.prompt_service.get_example_conversation(character))
            
            # 過去の会話履歴を取得
            history = await self.conversation_service.get_messages(user_id, conversation_id)
            for msg in history:
                messages.append({
                    "role": msg.role,
                    "content": msg.content or msg.text
                })
            
            # ユーザー名情報を追加（存在する場合）
            if user_id in self.user_names:
                messages.append({
                    "role": "system",
                    "content": f"相談者の名前は「{self.user_names[user_id]}」です。親しみを込めて呼びかけてください。"
                })
            
            # 新しいメッセージを追加
            messages.append({
                "role": "user",
                "content": message_text
            })

            # OpenRouter APIを呼び出し
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_url,
                    headers=self.headers,
                    json={
                        "model": "anthropic/claude-3-haiku",
                        "messages": messages,
                        "temperature": 0.7,
                        "max_tokens": 1000
                    }
                )
                response.raise_for_status()
                result = response.json()
                return result["choices"][0]["message"]["content"]

        except Exception as e:
            print(f"Error generating response: {e}")
            return "申し訳ありません。エラーが発生しました。"

    async def generate_summary(self, messages: List[Message]) -> str:
        """会話の要約を生成"""
        try:
            conversation_text = "\n".join([f"{msg.role}: {msg.content}" for msg in messages])
            prompt = f"""以下の会話を要約してください。重要なポイントを簡潔にまとめ、
            後で文脈を理解できるようにしてください：

            {conversation_text}"""

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_url,
                    headers=self.headers,
                    json={
                        "model": "anthropic/claude-3-haiku",
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.3,
                        "max_tokens": 500
                    }
                )
                response.raise_for_status()
                result = response.json()
                return result["choices"][0]["message"]["content"]

        except Exception as e:
            print(f"Error generating summary: {e}")
            raise

    async def combine_summaries(self, summaries: List[str]) -> str:
        """複数の要約を1つに統合"""
        try:
            summaries_text = "\n\n".join([f"要約{i+1}:\n{summary}" for i, summary in enumerate(summaries)])
            prompt = f"""以下の複数の要約を1つの簡潔な要約に統合してください。
            重要なポイントを保持しながら、冗長な情報は省いてください：

            {summaries_text}"""

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_url,
                    headers=self.headers,
                    json={
                        "model": "anthropic/claude-3-haiku",
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.3,
                        "max_tokens": 500
                    }
                )
                response.raise_for_status()
                result = response.json()
                return result["choices"][0]["message"]["content"]

        except Exception as e:
            print(f"Error combining summaries: {e}")
            raise 