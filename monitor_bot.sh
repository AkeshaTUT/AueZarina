#!/bin/bash

# ZarinAI Bot Health Monitor
# Скрипт для мониторинга здоровья бота и автоматического восстановления

SERVICE_NAME="zarinai-bot"
LOG_FILE="/var/log/zarinai-monitor.log"
TELEGRAM_BOT_TOKEN="8255737143:AAHMEy6kmHIee4H9__bSp0LEbaBQBlWt_Q0"
ADMIN_CHAT_ID="5784871405"  # Замените на ваш Telegram ID

# Функция логирования
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Отправка уведомления в Telegram
send_telegram_notification() {
    local message="$1"
    local full_message="🤖 ZarinAI Monitor: $message"
    
    curl -s -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage" \
        -d chat_id="$ADMIN_CHAT_ID" \
        -d text="$full_message" > /dev/null 2>&1
}

# Проверка работы бота
check_bot_health() {
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        return 0  # Бот работает
    else
        return 1  # Бот не работает
    fi
}

# Проверка использования ресурсов
check_resources() {
    # Проверка памяти (если использует больше 80% доступной)
    local memory_usage=$(ps -eo pid,ppid,cmd,%mem,%cpu --sort=-%mem | grep "main.py" | head -1 | awk '{print $4}')
    if [[ -n "$memory_usage" ]] && (( $(echo "$memory_usage > 80" | bc -l) )); then
        log_message "WARNING: High memory usage: ${memory_usage}%"
        return 1
    fi
    
    # Проверка CPU (если использует больше 90% в течение длительного времени)
    local cpu_usage=$(ps -eo pid,ppid,cmd,%mem,%cpu --sort=-%cpu | grep "main.py" | head -1 | awk '{print $5}')
    if [[ -n "$cpu_usage" ]] && (( $(echo "$cpu_usage > 90" | bc -l) )); then
        log_message "WARNING: High CPU usage: ${cpu_usage}%"
        return 1
    fi
    
    return 0
}

# Проверка логов на ошибки
check_logs_for_errors() {
    local recent_errors=$(journalctl -u "$SERVICE_NAME" --since "5 minutes ago" -p err --no-pager | wc -l)
    if [[ $recent_errors -gt 5 ]]; then
        log_message "WARNING: $recent_errors errors in the last 5 minutes"
        return 1
    fi
    return 0
}

# Основная функция мониторинга
monitor_bot() {
    log_message "Starting health check..."
    
    local issues=0
    
    # Проверка работы сервиса
    if ! check_bot_health; then
        log_message "ERROR: Bot service is not running"
        send_telegram_notification "❌ Бот не работает! Попытка перезапуска..."
        
        # Попытка перезапуска
        systemctl start "$SERVICE_NAME"
        sleep 10
        
        if check_bot_health; then
            log_message "SUCCESS: Bot service restarted successfully"
            send_telegram_notification "✅ Бот успешно перезапущен"
        else
            log_message "ERROR: Failed to restart bot service"
            send_telegram_notification "🚨 КРИТИЧЕСКАЯ ОШИБКА: Не удалось перезапустить бота!"
            issues=$((issues + 1))
        fi
    else
        log_message "OK: Bot service is running"
    fi
    
    # Проверка ресурсов
    if ! check_resources; then
        log_message "WARNING: Resource usage is high"
        issues=$((issues + 1))
    fi
    
    # Проверка логов
    if ! check_logs_for_errors; then
        log_message "WARNING: Recent errors detected in logs"
        issues=$((issues + 1))
    fi
    
    # Проверка доступности диска
    local disk_usage=$(df /home | tail -1 | awk '{print $5}' | sed 's/%//')
    if [[ $disk_usage -gt 90 ]]; then
        log_message "WARNING: Disk usage is high: ${disk_usage}%"
        send_telegram_notification "⚠️ Мало места на диске: ${disk_usage}%"
        issues=$((issues + 1))
    fi
    
    # Итоговый статус
    if [[ $issues -eq 0 ]]; then
        log_message "HEALTH CHECK PASSED: All systems operational"
    else
        log_message "HEALTH CHECK ISSUES: $issues issues detected"
    fi
    
    return $issues
}

# Установка cron задачи для мониторинга
install_monitoring() {
    # Создание лог файла
    touch "$LOG_FILE"
    chmod 644 "$LOG_FILE"
    
    # Добавление в crontab (проверка каждые 5 минут)
    (crontab -l 2>/dev/null; echo "*/5 * * * * /home/akezhanseytqasym/AueZarina/monitor_bot.sh > /dev/null 2>&1") | crontab -
    
    echo "✅ Мониторинг установлен (проверка каждые 5 минут)"
    echo "📄 Логи: $LOG_FILE"
}

# Удаление мониторинга
uninstall_monitoring() {
    crontab -l 2>/dev/null | grep -v "monitor_bot.sh" | crontab -
    echo "✅ Мониторинг удален"
}

# Показать последние логи
show_logs() {
    if [[ -f "$LOG_FILE" ]]; then
        tail -n 50 "$LOG_FILE"
    else
        echo "Лог файл не найден: $LOG_FILE"
    fi
}

# Главная функция
case "$1" in
    monitor)
        monitor_bot
        ;;
    install)
        if [[ $EUID -ne 0 ]]; then
            echo "Требуются права администратора. Запустите с sudo."
            exit 1
        fi
        install_monitoring
        ;;
    uninstall)
        if [[ $EUID -ne 0 ]]; then
            echo "Требуются права администратора. Запустите с sudo."
            exit 1
        fi
        uninstall_monitoring
        ;;
    logs)
        show_logs
        ;;
    test)
        send_telegram_notification "🧪 Тест уведомлений работает!"
        echo "Тестовое уведомление отправлено"
        ;;
    *)
        cat << EOF
🔍 ZarinAI Bot Health Monitor

ИСПОЛЬЗОВАНИЕ:
    $0 <команда>

КОМАНДЫ:
    monitor     Выполнить проверку здоровья бота
    install     Установить автоматический мониторинг (каждые 5 минут)
    uninstall   Удалить автоматический мониторинг
    logs        Показать логи мониторинга
    test        Отправить тестовое уведомление

ФУНКЦИИ МОНИТОРИНГА:
    ✅ Проверка работы сервиса
    ✅ Автоматический перезапуск при сбое
    ✅ Мониторинг использования ресурсов
    ✅ Отслеживание ошибок в логах
    ✅ Проверка свободного места на диске
    ✅ Уведомления в Telegram при проблемах

ФАЙЛЫ:
    Логи: $LOG_FILE
    Сервис: $SERVICE_NAME
EOF
        ;;
esac
