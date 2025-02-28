import json
import os
from typing import Dict, List, Optional
from pathlib import Path

class PromptService:
    def __init__(self):
        self.prompts: Dict = {}
        self.load_prompts()

    def load_prompts(self) -> None:
        """プロンプトファイルを読み込む"""
        try:
            prompt_file = Path(__file__).parent.parent / 'prompts' / 'characters.json'
            with open(prompt_file, 'r', encoding='utf-8') as f:
                self.prompts = json.load(f)
        except Exception as e:
            print(f"Error loading prompts: {e}")
            self.prompts = {}

    def get_character_prompt(self, character: str = "ojou") -> Dict:
        """指定されたキャラクターのプロンプトを取得"""
        return self.prompts.get(character, self.prompts.get("ojou", {}))

    def get_system_message(self, character: str = "ojou") -> Dict:
        """システムメッセージを取得"""
        prompt = self.get_character_prompt(character)
        return {"role": "system", "content": prompt.get("system", "")}

    def get_instruction_message(self, character: str = "ojou") -> Dict:
        """指示メッセージを取得"""
        prompt = self.get_character_prompt(character)
        return {"role": "user", "content": prompt.get("user_instruction", "")}

    def get_example_conversation(self, character: str = "ojou") -> List[Dict]:
        """会話例を取得"""
        prompt = self.get_character_prompt(character)
        return prompt.get("example_conversation", []) 