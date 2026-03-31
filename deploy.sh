#!/bin/bash

# Скрипт развертывания TeaStore на сервере
# Использование: ./deploy.sh [путь_к_проекту]

set -e  # Остановка при ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Путь к проекту (по умолчанию текущая директория)
PROJECT_DIR="${1:-$(pwd)}"
PROJECT_NAME="teastore"
SERVICE_USER="${SERVICE_USER:-$USER}"  # Можно задать через переменную окружения

echo -e "${GREEN}=== Развертывание TeaStore ===${NC}"
echo "Директория проекта: $PROJECT_DIR"
echo "Пользователь сервиса: $SERVICE_USER"

# Проверка Python
echo -e "\n${YELLOW}Проверка Python...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python3 не найден!${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo "Найден: $PYTHON_VERSION"

# Проверка наличия проекта
if [ ! -f "$PROJECT_DIR/requirements.txt" ]; then
    echo -e "${RED}Файл requirements.txt не найден в $PROJECT_DIR${NC}"
    exit 1
fi

# Создание виртуального окружения
echo -e "\n${YELLOW}Создание виртуального окружения...${NC}"
cd "$PROJECT_DIR"
if [ -d "venv" ]; then
    echo "Виртуальное окружение уже существует, пропускаем создание"
else
    python3 -m venv venv
    echo -e "${GREEN}Виртуальное окружение создано${NC}"
fi

# Активация виртуального окружения и установка зависимостей
echo -e "\n${YELLOW}Установка зависимостей...${NC}"
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo -e "${GREEN}Зависимости установлены${NC}"

# Создание директорий для логов
echo -e "\n${YELLOW}Создание директорий для логов...${NC}"
mkdir -p logs
chmod 755 logs

# Генерация SECRET_KEY если его нет
if [ ! -f .env ]; then
    echo -e "\n${YELLOW}Создание файла .env...${NC}"
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    cat > .env << EOF
# Конфигурация TeaStore
SECRET_KEY=$SECRET_KEY
# HOST=0.0.0.0
# PORT=8000
# DEBUG=False
EOF
    echo -e "${GREEN}Файл .env создан с автоматически сгенерированным SECRET_KEY${NC}"
else
    echo "Файл .env уже существует"
fi

# Инициализация базы данных (если нужно)
echo -e "\n${YELLOW}Проверка базы данных...${NC}"
if [ ! -f db.sqlite3 ]; then
    echo "База данных не найдена, будет создана при первом запуске"
else
    echo "База данных найдена"
fi

# Установка systemd сервиса
echo -e "\n${YELLOW}Установка systemd сервиса...${NC}"
SERVICE_FILE="/etc/systemd/system/${PROJECT_NAME}.service"

# Проверка прав на запись в systemd
if [ ! -w "/etc/systemd/system" ]; then
    echo -e "${YELLOW}Требуются права sudo для создания systemd сервиса${NC}"
    echo "Создаю временный файл сервиса..."
    
    cat > /tmp/${PROJECT_NAME}.service << EOF
[Unit]
Description=TeaStore FastAPI Application
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$PROJECT_DIR/venv/bin"
ExecStart=$PROJECT_DIR/venv/bin/python $PROJECT_DIR/run.py
Restart=always
RestartSec=10
StandardOutput=append:$PROJECT_DIR/logs/teastore.log
StandardError=append:$PROJECT_DIR/logs/teastore_error.log

[Install]
WantedBy=multi-user.target
EOF
    
    echo -e "${GREEN}Файл сервиса создан: /tmp/${PROJECT_NAME}.service${NC}"
    echo -e "${YELLOW}Выполните следующую команду для установки:${NC}"
    echo "sudo cp /tmp/${PROJECT_NAME}.service $SERVICE_FILE"
    echo "sudo systemctl daemon-reload"
    echo "sudo systemctl enable ${PROJECT_NAME}"
    echo "sudo systemctl start ${PROJECT_NAME}"
else
    # Если есть права, создаем напрямую
    sudo tee $SERVICE_FILE > /dev/null << EOF
[Unit]
Description=TeaStore FastAPI Application
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$PROJECT_DIR/venv/bin"
ExecStart=$PROJECT_DIR/venv/bin/python $PROJECT_DIR/run.py
Restart=always
RestartSec=10
StandardOutput=append:$PROJECT_DIR/logs/teastore.log
StandardError=append:$PROJECT_DIR/logs/teastore_error.log

[Install]
WantedBy=multi-user.target
EOF
    
    sudo systemctl daemon-reload
    sudo systemctl enable ${PROJECT_NAME}
    echo -e "${GREEN}Systemd сервис установлен и включен${NC}"
fi

# Обновление run.py для продакшена (убираем reload)
echo -e "\n${YELLOW}Проверка run.py для продакшена...${NC}"
if grep -q "reload=True" run.py; then
    echo "Обновляю run.py для продакшена (отключаю reload)..."
    sed -i 's/reload=True/reload=False/' run.py
    echo -e "${GREEN}run.py обновлен${NC}"
fi

echo -e "\n${GREEN}=== Развертывание завершено! ===${NC}"
echo ""
echo "Следующие шаги:"
echo "1. Если сервис не был установлен автоматически, выполните:"
echo "   sudo cp /tmp/${PROJECT_NAME}.service $SERVICE_FILE"
echo "   sudo systemctl daemon-reload"
echo "   sudo systemctl enable ${PROJECT_NAME}"
echo ""
echo "2. Запустите сервис:"
echo "   sudo systemctl start ${PROJECT_NAME}"
echo ""
echo "3. Проверьте статус:"
echo "   sudo systemctl status ${PROJECT_NAME}"
echo ""
echo "4. Просмотр логов:"
echo "   tail -f $PROJECT_DIR/logs/teastore.log"
echo "   tail -f $PROJECT_DIR/logs/teastore_error.log"
echo ""
echo "5. Управление сервисом:"
echo "   sudo systemctl stop ${PROJECT_NAME}    # Остановка"
echo "   sudo systemctl restart ${PROJECT_NAME} # Перезапуск"
echo "   sudo systemctl status ${PROJECT_NAME}  # Статус"






