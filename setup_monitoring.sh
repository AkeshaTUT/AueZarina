#!/bin/bash

# Скрипт для настройки автоматического мониторинга

echo "🔧 Настраиваем автоматический мониторинг Steam Bot..."

# Делаем скрипт мониторинга исполняемым
chmod +x monitor.sh

# Создаем cron задачу для мониторинга каждые 5 минут
SCRIPT_PATH="$(pwd)/monitor.sh"
CRON_JOB="*/5 * * * * $SCRIPT_PATH"

# Проверяем, есть ли уже такая задача
if crontab -l 2>/dev/null | grep -q "$SCRIPT_PATH"; then
    echo "⚠️ Cron задача уже существует"
else
    # Добавляем новую cron задачу
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    echo "✅ Cron задача добавлена: мониторинг каждые 5 минут"
fi

# Показываем текущие cron задачи
echo ""
echo "📋 Текущие cron задачи:"
crontab -l

echo ""
echo "✅ Настройка мониторинга завершена!"
echo ""
echo "📊 Полезные команды:"
echo "tail -f monitor.log           # Просмотр логов мониторинга"
echo "crontab -l                    # Просмотр cron задач"
echo "crontab -e                    # Редактирование cron задач"
echo "./monitor.sh                  # Ручной запуск проверки"
