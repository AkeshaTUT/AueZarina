#!/bin/bash

# Скрипт мониторинга Steam Bot
# Проверяет работоспособность бота и перезапускает при необходимости

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$SCRIPT_DIR/monitor.log"
HEALTH_URL="http://localhost:8000/health"
MAX_RETRIES=3
RETRY_INTERVAL=30

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

check_health() {
    local response=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_URL" --max-time 10)
    if [ "$response" = "200" ]; then
        return 0
    else
        return 1
    fi
}

restart_bot() {
    log "🔄 Перезапускаем бота..."
    
    if command -v docker-compose &> /dev/null; then
        cd "$SCRIPT_DIR"
        docker-compose restart
        sleep 30
    elif systemctl is-active --quiet steam-bot; then
        systemctl restart steam-bot
        sleep 30
    else
        log "❌ Не удается найти способ перезапуска бота"
        return 1
    fi
    
    log "✅ Бот перезапущен"
}

main() {
    log "🔍 Проверяем состояние бота..."
    
    local retries=0
    while [ $retries -lt $MAX_RETRIES ]; do
        if check_health; then
            log "✅ Бот работает нормально"
            exit 0
        else
            retries=$((retries + 1))
            log "⚠️ Бот не отвечает (попытка $retries/$MAX_RETRIES)"
            
            if [ $retries -lt $MAX_RETRIES ]; then
                log "⏳ Ждем $RETRY_INTERVAL секунд перед следующей попыткой..."
                sleep $RETRY_INTERVAL
            fi
        fi
    done
    
    log "❌ Бот не отвечает после $MAX_RETRIES попыток. Перезапускаем..."
    restart_bot
    
    # Проверяем, что перезапуск прошел успешно
    sleep 60
    if check_health; then
        log "✅ Бот успешно перезапущен и работает"
        
        # Отправляем уведомление (опционально)
        # Можно настроить отправку в Telegram или email
        
    else
        log "💥 Критическая ошибка: бот не запустился после перезапуска!"
        
        # Здесь можно добавить отправку критического уведомления
        # или другие действия при критической ошибке
        
        exit 1
    fi
}

# Создаем лог файл если его нет
touch "$LOG_FILE"

# Запускаем основную функцию
main
