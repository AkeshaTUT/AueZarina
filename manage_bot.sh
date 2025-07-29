#!/bin/bash

# 🔧 ZarinAI - Мониторинг и управление на Google Cloud VM

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_NAME="zarinai"
LOG_FILE="/var/log/zarinai.log"

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════╗"
    echo "║           🤖 ZarinAI Manager         ║"
    echo "║      Google Cloud VM Control        ║"
    echo "╚══════════════════════════════════════╝"
    echo -e "${NC}"
}

check_status() {
    echo -e "${BLUE}📊 Статус сервиса:${NC}"
    systemctl is-active --quiet $SERVICE_NAME
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ ZarinAI запущен${NC}"
        echo -e "${BLUE}🕐 Uptime:${NC} $(systemctl show $SERVICE_NAME --property=ActiveEnterTimestamp --value | cut -d' ' -f2-)"
    else
        echo -e "${RED}❌ ZarinAI остановлен${NC}"
    fi
    
    echo -e "\n${BLUE}💾 Использование памяти:${NC}"
    ps aux | grep python | grep -v grep | awk '{print $4"% RAM, PID: "$2}'
    
    echo -e "\n${BLUE}💿 Использование диска:${NC}"
    df -h / | tail -1 | awk '{print "Использовано: "$3" из "$2" ("$5")"}'
}

show_logs() {
    echo -e "${BLUE}📋 Последние 20 строк логов:${NC}"
    if [ -f "$LOG_FILE" ]; then
        tail -20 "$LOG_FILE"
    else
        journalctl -u zarinai -n 20 --no-pager
    fi
}

follow_logs() {
    echo -e "${BLUE}📋 Логи в реальном времени (Ctrl+C для выхода):${NC}"
    if [ -f "$LOG_FILE" ]; then
        tail -f "$LOG_FILE"
    else
        journalctl -u zarinai -f
    fi
}

start_bot() {
    echo -e "${YELLOW}🚀 Запуск ZarinAI...${NC}"
    sudo systemctl start $SERVICE_NAME
    sleep 2
    check_status
}

stop_bot() {
    echo -e "${YELLOW}🛑 Остановка ZarinAI...${NC}"
    sudo systemctl stop $SERVICE_NAME
    sleep 2
    check_status
}

restart_bot() {
    echo -e "${YELLOW}🔄 Перезапуск ZarinAI...${NC}"
    sudo systemctl restart $SERVICE_NAME
    sleep 3
    check_status
}

update_bot() {
    echo -e "${YELLOW}📥 Обновление ZarinAI...${NC}"
    
    cd /home/zarinai/AueZarina
    
    echo "1. Остановка бота..."
    sudo systemctl stop $SERVICE_NAME
    
    echo "2. Обновление кода..."
    sudo -u zarinai git pull origin main
    
    echo "3. Обновление зависимостей..."
    sudo -u zarinai ./venv/bin/pip install -r requirements.txt --upgrade
    
    echo "4. Запуск бота..."
    sudo systemctl start $SERVICE_NAME
    
    sleep 3
    check_status
    echo -e "${GREEN}✅ Обновление завершено!${NC}"
}

backup_database() {
    echo -e "${YELLOW}💾 Создание резервной копии базы данных...${NC}"
    
    BACKUP_DIR="/home/zarinai/backups"
    sudo -u zarinai mkdir -p $BACKUP_DIR
    
    BACKUP_FILE="$BACKUP_DIR/steam_bot_$(date +%Y%m%d_%H%M%S).db"
    sudo -u zarinai cp /home/zarinai/AueZarina/steam_bot.db $BACKUP_FILE
    
    echo -e "${GREEN}✅ Резервная копия создана: $BACKUP_FILE${NC}"
    
    # Показать размеры резервных копий
    echo -e "\n${BLUE}📊 Резервные копии:${NC}"
    sudo -u zarinai ls -lh $BACKUP_DIR/*.db 2>/dev/null || echo "Резервных копий не найдено"
}

system_info() {
    echo -e "${BLUE}🖥️ Информация о системе:${NC}"
    echo "OS: $(lsb_release -d | cut -f2)"
    echo "Kernel: $(uname -r)"
    echo "CPU: $(nproc) cores"
    echo "RAM: $(free -h | awk '/^Mem:/ {print $2}')"
    echo "Disk: $(df -h / | tail -1 | awk '{print $2}')"
    echo ""
    echo -e "${BLUE}🌐 Сетевая информация:${NC}"
    echo "Internal IP: $(hostname -I | awk '{print $1}')"
    echo "External IP: $(curl -s ifconfig.me 2>/dev/null || echo 'Не удалось получить')"
}

install_dependencies() {
    echo -e "${YELLOW}📦 Установка дополнительных зависимостей...${NC}"
    
    # Обновление системы
    sudo apt update
    
    # Установка полезных утилит
    sudo apt install -y htop iotop nethogs ncdu tree
    
    echo -e "${GREEN}✅ Зависимости установлены!${NC}"
}

show_menu() {
    print_header
    echo "Выберите действие:"
    echo ""
    echo "1) 📊 Проверить статус"
    echo "2) 🚀 Запустить бота"
    echo "3) 🛑 Остановить бота"
    echo "4) 🔄 Перезапустить бота"
    echo "5) 📋 Показать логи"
    echo "6) 📋 Следить за логами"
    echo "7) 📥 Обновить бота"
    echo "8) 💾 Создать резервную копию БД"
    echo "9) 🖥️ Информация о системе"
    echo "10) 📦 Установить дополнительные утилиты"
    echo "0) 🚪 Выход"
    echo ""
    read -p "Введите номер (0-10): " choice
}

# Основной цикл
while true; do
    show_menu
    
    case $choice in
        1) check_status ;;
        2) start_bot ;;
        3) stop_bot ;;
        4) restart_bot ;;
        5) show_logs ;;
        6) follow_logs ;;
        7) update_bot ;;
        8) backup_database ;;
        9) system_info ;;
        10) install_dependencies ;;
        0) 
            echo -e "${GREEN}👋 До свидания!${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}❌ Неверный выбор. Попробуйте еще раз.${NC}"
            ;;
    esac
    
    echo ""
    read -p "Нажмите Enter для продолжения..."
    clear
done
