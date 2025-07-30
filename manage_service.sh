#!/bin/bash

# ZarinAI Bot Service Management Script
# Скрипт для управления ботом 24/7 на Google Cloud VM

set -e

# Конфигурация
SERVICE_NAME="zarinai-bot"
USER_NAME="akezhanseytqasym"
BOT_DIR="/home/$USER_NAME/AueZarina"
VENV_PATH="$BOT_DIR/venv"
PYTHON_PATH="$VENV_PATH/bin/python"
MAIN_FILE="$BOT_DIR/main.py"
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для вывода с цветом
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_blue() {
    echo -e "${BLUE}[ACTION]${NC} $1"
}

# Проверка прав администратора
check_sudo() {
    if [[ $EUID -ne 0 ]]; then
        print_error "Этот скрипт требует прав администратора. Запустите с sudo:"
        echo "sudo $0 $@"
        exit 1
    fi
}

# Создание systemd сервиса
create_service() {
    print_blue "Создание systemd сервиса..."
    
    cat > $SERVICE_FILE << EOF
[Unit]
Description=ZarinAI Steam Bot - Multilingual Steam Deals Bot
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=$USER_NAME
Group=$USER_NAME
WorkingDirectory=$BOT_DIR
Environment=PATH=$VENV_PATH/bin:/usr/bin:/usr/local/bin
Environment=PYTHONPATH=$BOT_DIR
ExecStart=$PYTHON_PATH $MAIN_FILE
ExecReload=/bin/kill -HUP \$MAINPID
KillMode=mixed
Restart=always
RestartSec=10
TimeoutStopSec=30

# Ограничения ресурсов
MemoryMax=512M
CPUQuota=50%

# Логирование
StandardOutput=journal
StandardError=journal
SyslogIdentifier=zarinai-bot

# Безопасность
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$BOT_DIR

[Install]
WantedBy=multi-user.target
EOF

    print_status "Сервис создан: $SERVICE_FILE"
}

# Установка и настройка сервиса
install_service() {
    print_blue "Установка ZarinAI бота как системный сервис..."
    
    # Проверка существования файлов
    if [[ ! -f "$MAIN_FILE" ]]; then
        print_error "Файл main.py не найден: $MAIN_FILE"
        exit 1
    fi
    
    # Создание виртуального окружения если не существует
    if [[ ! -f "$PYTHON_PATH" ]]; then
        print_warning "Виртуальное окружение не найдено. Создание..."
        
        # Проверка наличия python3
        if ! command -v python3 &> /dev/null; then
            print_error "Python3 не установлен. Установите: sudo apt update && sudo apt install python3 python3-venv python3-pip"
            exit 1
        fi
        
        # Создание виртуального окружения от имени пользователя
        sudo -u $USER_NAME python3 -m venv $VENV_PATH
        print_status "Виртуальное окружение создано"
        
        # Обновление pip
        sudo -u $USER_NAME $VENV_PATH/bin/pip install --upgrade pip
        print_status "pip обновлен"
        
        # Установка зависимостей
        if [[ -f "$BOT_DIR/requirements.txt" ]]; then
            print_blue "Установка зависимостей..."
            sudo -u $USER_NAME $VENV_PATH/bin/pip install -r $BOT_DIR/requirements.txt
            print_status "Зависимости установлены"
        fi
        
        # Создание .env файла если не существует
        if [[ ! -f "$BOT_DIR/.env" ]] && [[ -f "$BOT_DIR/env.example" ]]; then
            print_blue "Создание .env файла..."
            sudo -u $USER_NAME cp $BOT_DIR/env.example $BOT_DIR/.env
            print_warning "⚠️  ВАЖНО: Отредактируйте файл .env и добавьте BOT_TOKEN!"
            print_warning "Выполните: nano $BOT_DIR/.env"
        fi
    fi
    
    # Финальная проверка
    if [[ ! -f "$PYTHON_PATH" ]]; then
        print_error "Не удалось создать виртуальное окружение: $PYTHON_PATH"
        exit 1
    fi
    
    # Создание сервиса
    create_service
    
    # Перезагрузка systemd
    systemctl daemon-reload
    print_status "systemd перезагружен"
    
    # Включение автозапуска
    systemctl enable $SERVICE_NAME
    print_status "Автозапуск включен"
    
    # Запуск сервиса
    systemctl start $SERVICE_NAME
    print_status "Сервис запущен"
    
    # Проверка статуса
    sleep 2
    if systemctl is-active --quiet $SERVICE_NAME; then
        print_status "✅ ZarinAI бот успешно установлен и запущен!"
        print_status "🚀 Бот будет работать 24/7 и автоматически запускаться при перезагрузке"
    else
        print_error "❌ Ошибка при запуске сервиса"
        print_warning "Проверьте логи: sudo journalctl -u $SERVICE_NAME -f"
        exit 1
    fi
}

# Показать статус
show_status() {
    print_blue "Статус ZarinAI бота:"
    echo
    systemctl status $SERVICE_NAME --no-pager
    echo
    if systemctl is-active --quiet $SERVICE_NAME; then
        print_status "🟢 Бот работает"
    else
        print_error "🔴 Бот остановлен"
    fi
    
    if systemctl is-enabled --quiet $SERVICE_NAME; then
        print_status "🟢 Автозапуск включен"
    else
        print_warning "🟡 Автозапуск отключен"
    fi
}

# Управление сервисом
manage_service() {
    case $1 in
        start)
            print_blue "Запуск бота..."
            systemctl start $SERVICE_NAME
            print_status "✅ Бот запущен"
            ;;
        stop)
            print_blue "Остановка бота..."
            systemctl stop $SERVICE_NAME
            print_status "⏹️ Бот остановлен"
            ;;
        restart)
            print_blue "Перезапуск бота..."
            systemctl restart $SERVICE_NAME
            print_status "🔄 Бот перезапущен"
            ;;
        reload)
            print_blue "Перезагрузка конфигурации..."
            systemctl reload $SERVICE_NAME
            print_status "🔄 Конфигурация перезагружена"
            ;;
        enable)
            print_blue "Включение автозапуска..."
            systemctl enable $SERVICE_NAME
            print_status "✅ Автозапуск включен"
            ;;
        disable)
            print_blue "Отключение автозапуска..."
            systemctl disable $SERVICE_NAME
            print_status "❌ Автозапуск отключен"
            ;;
        *)
            print_error "Неизвестная команда: $1"
            show_usage
            exit 1
            ;;
    esac
}

# Показать логи
show_logs() {
    case $1 in
        tail|follow)
            print_blue "Показ логов в реальном времени (Ctrl+C для выхода)..."
            journalctl -u $SERVICE_NAME -f
            ;;
        last)
            lines=${2:-50}
            print_blue "Последние $lines строк логов:"
            journalctl -u $SERVICE_NAME -n $lines --no-pager
            ;;
        today)
            print_blue "Логи за сегодня:"
            journalctl -u $SERVICE_NAME --since today --no-pager
            ;;
        errors)
            print_blue "Только ошибки:"
            journalctl -u $SERVICE_NAME -p err --no-pager
            ;;
        *)
            print_blue "Все логи:"
            journalctl -u $SERVICE_NAME --no-pager
            ;;
    esac
}

# Обновление бота
update_bot() {
    print_blue "Обновление ZarinAI бота..."
    
    # Остановка сервиса
    systemctl stop $SERVICE_NAME
    print_status "Бот остановлен"
    
    # Переход в директорию бота
    cd $BOT_DIR
    
    # Обновление кода
    print_blue "Загрузка обновлений из GitHub..."
    sudo -u $USER_NAME git pull
    
    # Обновление зависимостей
    print_blue "Обновление зависимостей..."
    sudo -u $USER_NAME $VENV_PATH/bin/pip install -r requirements.txt --upgrade
    
    # Запуск сервиса
    systemctl start $SERVICE_NAME
    print_status "✅ Бот обновлен и запущен"
    
    # Проверка статуса
    sleep 3
    if systemctl is-active --quiet $SERVICE_NAME; then
        print_status "🚀 Обновление прошло успешно!"
    else
        print_error "❌ Ошибка после обновления"
        print_warning "Проверьте логи: sudo journalctl -u $SERVICE_NAME -f"
    fi
}

# Удаление сервиса
uninstall_service() {
    print_warning "Удаление сервиса ZarinAI бота..."
    read -p "Вы уверены? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        systemctl stop $SERVICE_NAME 2>/dev/null || true
        systemctl disable $SERVICE_NAME 2>/dev/null || true
        rm -f $SERVICE_FILE
        systemctl daemon-reload
        print_status "✅ Сервис удален"
    else
        print_status "Отменено"
    fi
}

# Настройка виртуального окружения
setup_venv() {
    print_blue "Настройка виртуального окружения..."
    
    # Проверка наличия python3
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 не установлен. Установите:"
        echo "sudo apt update && sudo apt install python3 python3-venv python3-pip"
        exit 1
    fi
    
    # Удаление старого окружения если существует
    if [[ -d "$VENV_PATH" ]]; then
        print_warning "Удаление старого виртуального окружения..."
        sudo -u $USER_NAME rm -rf $VENV_PATH
    fi
    
    # Создание нового виртуального окружения
    print_blue "Создание виртуального окружения..."
    sudo -u $USER_NAME python3 -m venv $VENV_PATH
    print_status "Виртуальное окружение создано"
    
    # Обновление pip
    print_blue "Обновление pip..."
    sudo -u $USER_NAME $VENV_PATH/bin/pip install --upgrade pip
    print_status "pip обновлен"
    
    # Установка зависимостей
    if [[ -f "$BOT_DIR/requirements.txt" ]]; then
        print_blue "Установка зависимостей..."
        sudo -u $USER_NAME $VENV_PATH/bin/pip install -r $BOT_DIR/requirements.txt
        print_status "Зависимости установлены"
    else
        print_warning "Файл requirements.txt не найден"
    fi
    
    # Создание .env файла
    if [[ ! -f "$BOT_DIR/.env" ]] && [[ -f "$BOT_DIR/env.example" ]]; then
        print_blue "Создание .env файла..."
        sudo -u $USER_NAME cp $BOT_DIR/env.example $BOT_DIR/.env
        print_status ".env файл создан"
    fi
    
    # Проверка установки
    if [[ -f "$PYTHON_PATH" ]]; then
        print_status "✅ Виртуальное окружение настроено успешно!"
        print_status "🐍 Python: $($PYTHON_PATH --version)"
        print_warning "⚠️  ВАЖНО: Отредактируйте файл .env и добавьте BOT_TOKEN!"
        echo "Выполните: nano $BOT_DIR/.env"
    else
        print_error "❌ Ошибка при создании виртуального окружения"
        exit 1
    fi
}

# Показать информацию о системе
show_system_info() {
    print_blue "Информация о системе:"
    echo
    echo "🖥️  Система: $(lsb_release -d | cut -f2)"
    echo "🐧 Ядро: $(uname -r)"
    echo "💾 ОЗУ: $(free -h | grep '^Mem' | awk '{print $3 "/" $2}')"
    echo "💿 Диск: $(df -h $BOT_DIR | tail -1 | awk '{print $3 "/" $2 " (" $5 " используется)"}')"
    echo "🐍 Python: $($PYTHON_PATH --version 2>/dev/null || echo 'Не найден')"
    echo "📁 Директория бота: $BOT_DIR"
    echo "🔧 Виртуальное окружение: $VENV_PATH"
    echo
}

# Показать справку
show_usage() {
    cat << EOF
🤖 ZarinAI Bot Service Manager - Управление ботом 24/7

ИСПОЛЬЗОВАНИЕ:
    sudo $0 <команда> [опции]

КОМАНДЫ УПРАВЛЕНИЯ:
    install         Установить бота как системный сервис
    setup-venv      Настроить виртуальное окружение
    uninstall       Удалить сервис
    
    start           Запустить бота
    stop            Остановить бота
    restart         Перезапустить бота
    reload          Перезагрузить конфигурацию
    
    enable          Включить автозапуск
    disable         Отключить автозапуск
    
    status          Показать статус бота
    update          Обновить бота из GitHub
    
КОМАНДЫ ЛОГОВ:
    logs            Показать все логи
    logs tail       Показать логи в реальном времени
    logs last [N]   Показать последние N строк (по умолчанию 50)
    logs today      Показать логи за сегодня
    logs errors     Показать только ошибки
    
ДОПОЛНИТЕЛЬНО:
    info            Показать информацию о системе
    help            Показать эту справку

ПРИМЕРЫ:
    sudo $0 install          # Установить бота как сервис
    sudo $0 setup-venv       # Настроить виртуальное окружение
    sudo $0 status           # Проверить статус
    sudo $0 logs tail        # Смотреть логи в реальном времени
    sudo $0 restart          # Перезапустить бота
    sudo $0 update           # Обновить бота

ФАЙЛЫ:
    Сервис: $SERVICE_FILE
    Главный файл: $MAIN_FILE
    Python: $PYTHON_PATH

🚀 После установки бот будет работать 24/7 и автоматически запускаться при перезагрузке!
EOF
}

# Основная логика
main() {
    case $1 in
        install)
            check_sudo
            install_service
            ;;
        setup-venv)
            check_sudo
            setup_venv
            ;;
        uninstall)
            check_sudo
            uninstall_service
            ;;
        start|stop|restart|reload|enable|disable)
            check_sudo
            manage_service $1
            ;;
        status)
            show_status
            ;;
        update)
            check_sudo
            update_bot
            ;;
        logs)
            show_logs $2 $3
            ;;
        info)
            show_system_info
            ;;
        help|--help|-h)
            show_usage
            ;;
        "")
            show_usage
            ;;
        *)
            print_error "Неизвестная команда: $1"
            show_usage
            exit 1
            ;;
    esac
}

# Запуск основной функции
main "$@"
