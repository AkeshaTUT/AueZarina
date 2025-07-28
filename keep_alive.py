# Keep the bot alive
import threading
import time
from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Steam Discount Bot is running!"

@app.route('/health')
def health():
    return {
        "status": "healthy",
        "bot": "Steam Discount Bot",
        "timestamp": time.time()
    }

def run():
    app.run(host='0.0.0.0', port=8000)

def keep_alive():
    """Запускает веб-сервер в отдельном потоке для поддержания активности бота"""
    t = threading.Thread(target=run)
    t.daemon = True
    t.start()
    print("✅ Keep-alive сервер запущен на порту 8000")
