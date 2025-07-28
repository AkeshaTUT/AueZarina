# Keep the bot alive
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class KeepAliveHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write("<h1>🤖 Steam Discount Bot is running!</h1>".encode('utf-8'))
        elif self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            health_data = {
                "status": "healthy",
                "bot": "Steam Discount Bot",
                "timestamp": time.time()
            }
            self.wfile.write(json.dumps(health_data).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        # Отключаем логирование HTTP запросов
        pass

def run_server():
    server = HTTPServer(('0.0.0.0', 8000), KeepAliveHandler)
    server.serve_forever()

def keep_alive():
    """Запускает веб-сервер в отдельном потоке для поддержания активности бота"""
    t = threading.Thread(target=run_server)
    t.daemon = True
    t.start()
    print("✅ Keep-alive сервер запущен на порту 8000")
