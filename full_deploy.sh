#!/bin/bash

# 🚀 Полный автоматический деплой Steam Bot на Digital Ocean

set -e  # Останавливаем скрипт при ошибке

echo "🚀 Начинаем полный деплой Steam Bot на Digital Ocean..."

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Проверяем, что мы root
if [[ $EUID -ne 0 ]]; then
   log_error "Этот скрипт должен запускаться под root пользователем"
   echo "Выполните: sudo ./full_deploy.sh"
   exit 1
fi

log_info "Обновляем систему..."
apt update && apt upgrade -y

log_info "Устанавливаем необходимые пакеты..."
apt install -y curl wget git htop nano ufw

log_info "Устанавливаем Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    log_success "Docker установлен"
else
    log_warning "Docker уже установлен"
fi

log_info "Устанавливаем Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    log_success "Docker Compose установлен"
else
    log_warning "Docker Compose уже установлен"
fi

log_info "Создаем пользователя steambot..."
if ! id "steambot" &>/dev/null; then
    useradd -m -s /bin/bash steambot
    usermod -aG docker steambot
    log_success "Пользователь steambot создан"
else
    log_warning "Пользователь steambot уже существует"
fi

log_info "Настраиваем firewall..."
ufw --force enable
ufw allow ssh
ufw allow 80
ufw allow 443
ufw allow 8000  # Для healthcheck
log_success "Firewall настроен"

log_info "Переключаемся на пользователя steambot..."

# Создаем скрипт для выполнения от имени steambot
cat > /tmp/steambot_setup.sh << 'EOF'
#!/bin/bash

cd /home/steambot

log_info() {
    echo -e "\033[0;34m[INFO]\033[0m $1"
}

log_success() {
    echo -e "\033[0;32m[SUCCESS]\033[0m $1"
}

log_warning() {
    echo -e "\033[1;33m[WARNING]\033[0m $1"
}

log_info "Создаем директорию для бота..."
mkdir -p steam-bot
cd steam-bot

# Здесь нужно загрузить файлы бота
# Если есть git репозиторий - используйте git clone
# Если нет - файлы нужно загрузить вручную

if [ ! -f "requirements.txt" ]; then
    log_warning "Файлы бота не найдены!"
    log_warning "Загрузите файлы бота в директорию /home/steambot/steam-bot/"
    log_warning "Затем запустите: ./deploy.sh"
    exit 1
fi

log_info "Проверяем файл .env..."
if [ ! -f ".env" ]; then
    if [ -f "env.example" ]; then
        cp env.example .env
        log_warning "Создан файл .env из примера"
        log_warning "Отредактируйте файл .env и укажите ваши токены:"
        log_warning "nano .env"
    else
        log_error "Файл .env не найден и нет примера!"
        exit 1
    fi
else
    log_success "Файл .env найден"
fi

log_info "Создаем необходимые директории..."
mkdir -p data logs

log_info "Делаем скрипты исполняемыми..."
chmod +x *.sh

log_success "Настройка завершена!"
echo ""
echo "📝 Следующие шаги:"
echo "1. Отредактируйте файл .env: nano .env"
echo "2. Запустите деплой: ./deploy.sh"
echo "3. Настройте мониторинг: ./setup_monitoring.sh"

EOF

chmod +x /tmp/steambot_setup.sh
chown steambot:steambot /tmp/steambot_setup.sh

# Выполняем скрипт от имени steambot
su - steambot -c "/tmp/steambot_setup.sh"

# Удаляем временный скрипт
rm /tmp/steambot_setup.sh

log_success "Базовая настройка сервера завершена!"
echo ""
echo "🎯 Что дальше:"
echo "1. Загрузите файлы бота в /home/steambot/steam-bot/"
echo "2. Перейдите к пользователю steambot: su - steambot"
echo "3. Перейдите в директорию бота: cd steam-bot"
echo "4. Настройте .env файл: nano .env"
echo "5. Запустите деплой: ./deploy.sh"
echo ""
echo "📊 Полезные команды после деплоя:"
echo "docker-compose logs -f     # Просмотр логов"
echo "docker-compose ps          # Статус контейнеров"
echo "curl localhost:8000/health # Проверка здоровья"
echo ""
echo "🚀 Удачного деплоя!"
