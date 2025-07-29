"""
Простой HTTP сервер для healthcheck бота
"""
import asyncio
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import threading
import time
from datetime import datetime

logger = logging.getLogger(__name__)

class HealthCheckHandler(BaseHTTPRequestHandler):
    """Обработчик healthcheck запросов"""
    
    def do_GET(self):
        """Обработка GET запросов"""
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            health_data = {
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'uptime': time.time() - getattr(self.server, 'start_time', time.time())
            }
            
            self.wfile.write(json.dumps(health_data).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        """Отключаем логирование HTTP запросов"""
        pass

class HealthCheckServer:
    """Сервер для healthcheck"""
    
    def __init__(self, port=8000):
        self.port = port
        self.server = None
        self.thread = None
        
    def start(self):
        """Запуск сервера"""
        try:
            self.server = HTTPServer(('0.0.0.0', self.port), HealthCheckHandler)
            self.server.start_time = time.time()
            
            self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.thread.start()
            
            logger.info(f"✅ HealthCheck сервер запущен на порту {self.port}")
        except Exception as e:
            logger.error(f"❌ Ошибка запуска HealthCheck сервера: {e}")
    
    def stop(self):
        """Остановка сервера"""
        if self.server:
            self.server.shutdown()
            logger.info("⏹️ HealthCheck сервер остановлен")
