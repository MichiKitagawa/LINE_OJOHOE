from datetime import datetime
from typing import List, Dict, Any

class Message:
    def __init__(self, sender: str = None, text: str = None, timestamp: datetime = None, role: str = "user", content: str = None):
        self.sender = sender
        self.text = text
        self.timestamp = timestamp or datetime.now()
        self.role = role
        self.content = content or text  # textが指定されている場合はcontentとして使用

    def to_dict(self) -> Dict[str, Any]:
        return {
            'sender': self.sender,
            'text': self.text,
            'content': self.content,
            'role': self.role,
            'timestamp': self.timestamp
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Message':
        return Message(
            sender=data.get('sender'),
            text=data.get('text'),
            content=data.get('content'),
            role=data.get('role', 'user'),
            timestamp=data.get('timestamp')
        )

class Summary:
    def __init__(self, text: str, timestamp: datetime = None):
        self.text = text
        self.timestamp = timestamp or datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        return {
            'text': self.text,
            'timestamp': self.timestamp
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Summary':
        return Summary(
            text=data['text'],
            timestamp=data['timestamp']
        )

class Conversation:
    def __init__(self, conversation_id: str):
        self.conversation_id = conversation_id
        self.messages: List[Message] = []
        self.summaries: List[Summary] = []
        self.last_updated = datetime.now()

    def add_message(self, message: Message) -> None:
        self.messages.append(message)
        self.last_updated = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        return {
            'conversation_id': self.conversation_id,
            'messages': [msg.to_dict() for msg in self.messages],
            'summaries': [summary.to_dict() for summary in self.summaries],
            'last_updated': self.last_updated
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Conversation':
        conversation = Conversation(data['conversation_id'])
        conversation.messages = [Message.from_dict(msg) for msg in data.get('messages', [])]
        conversation.summaries = [Summary.from_dict(summary) for summary in data.get('summaries', [])]
        conversation.last_updated = data.get('last_updated', datetime.now())
        return conversation 