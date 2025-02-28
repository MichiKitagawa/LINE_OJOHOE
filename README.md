# LINE_OJOHOE - LINEお嬢様恋愛相談Bot

## 概要
LINE_OJOHOEは、恋愛相談に特化したLINE Botです。28歳の恋愛経験豊富な「お嬢」というキャラクターが、ユーザーの恋愛相談に親身に答えてくれます。

## 特徴
- 🎭 個性的なキャラクター設定
- 💕 恋愛相談に特化した応答
- 💬 自然な会話フロー
- 🔄 柔軟な対話管理
- 💳 サブスクリプション管理機能

## 技術スタック
- FastAPI
- LINE Messaging API
- Firebase (Firestore)
- OpenRouter API (Claude 3 Haiku)
- Stripe API

## セットアップ
1. 必要なパッケージのインストール:
```bash
pip install -r requirements.txt
```

2. 環境変数の設定:
- `.env.example`を`.env`にコピーし、必要な情報を入力

3. Firebase設定:
- Firebaseプロジェクトの認証情報を設定

4. アプリケーションの起動:
```bash
python main.py
```

## 環境変数
必要な環境変数は`.env.example`を参照してください。以下の項目の設定が必要です：
- LINE Bot設定
- Firebase認証情報
- OpenRouter API設定
- Stripe設定

## 機能
- 恋愛相談対応
- 会話履歴管理
- サブスクリプション管理
- ユーザー管理

## ライセンス
MIT License

## 作者
Michi Kitagawa 