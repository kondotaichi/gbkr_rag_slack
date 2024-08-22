import os
import logging
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv
from chatbot_engine import chat, create_index
from langchain.memory import ChatMessageHistory

# 環境変数の読み込み
load_dotenv()

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 環境を特定するための環境変数
app_env = os.getenv('APP_ENV', 'development')
logger.info(f"Running in {app_env} environment.")

index = create_index()

# ボットトークンとソケットモードハンドラーを使ってアプリを初期化します
app = App(token=os.environ.get("SLACK_BOT_TOKEN"))

# 全体の会話履歴を保持する
channel_histories = {}

def fetch_history(channel:str) -> ChatMessageHistory:
    if channel in channel_histories:
        return channel_histories[channel]
    
    bot_user_id = app.client.auth_test()["user_id"]
    conversation_history = app.client.conversations_history(
        channel=channel,
        limit=10  # 必要に応じて過去メッセージの数を調整
    )
    history = ChatMessageHistory()
    # メッセージを逆順に取得した方が、最新のメッセージが最初に来るため精度はよい
    for message in reversed(conversation_history["messages"]):
        text = message["text"]
        if message["user"] == bot_user_id:
            history.add_ai_message(text)
        else:
            history.add_user_message(text)
    
    # 履歴を保存
    channel_histories[channel] = history
    return history

@app.event("app_mention")
def handle_mention(event, say):
    channel = event["channel"]
    history = fetch_history(channel)
    message = event["text"]

    bot_message = chat(message, history, index)
    say(bot_message)
    # 会話の履歴を更新
    channel_histories[channel] = history

# アプリを起動します
if __name__ == "__main__":
    if app_env == "production":
        logger.info("Starting app in production mode.")
        app.start(port=int(os.environ.get("PORT", 3000)))
    else:
        logger.info("Starting app in development mode using SocketMode.")
        SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()
