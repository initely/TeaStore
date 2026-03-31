#!/bin/bash

# Скрипт для загрузки проекта на сервер
# Использование: ./upload_to_server.sh user@server:/path/to/destination [--with-db]
#   --with-db  - передать базу данных db.sqlite3 на сервер

set -e

# Цвета
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Проверка аргументов
INCLUDE_DB=false
DEST=""

for arg in "$@"; do
    case $arg in
        --with-db)
            INCLUDE_DB=true
            ;;
        *)
            if [ -z "$DEST" ]; then
                DEST="$arg"
            fi
            ;;
    esac
done

if [ -z "$DEST" ]; then
    echo "Использование: $0 user@server:/path/to/destination [--with-db]"
    echo "Пример: $0 root@192.168.1.100:/var/www/teastore"
    echo "Пример с БД: $0 root@192.168.1.100:/var/www/teastore --with-db"
    exit 1
fi

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo -e "${GREEN}=== Загрузка TeaStore на сервер ===${NC}"
echo "Источник: $PROJECT_DIR"
echo "Назначение: $DEST"
if [ "$INCLUDE_DB" = true ]; then
    echo -e "${BLUE}База данных будет передана на сервер${NC}"
else
    echo -e "${YELLOW}База данных НЕ будет передана (создастся на сервере)${NC}"
    echo "   Используйте --with-db для передачи локальной БД"
fi
echo ""

# Проверка наличия rsync
if command -v rsync &> /dev/null; then
    echo -e "${YELLOW}Используется rsync (рекомендуется)${NC}"
    
    # Базовые исключения
    EXCLUDE_ARGS=(
        --exclude='venv/'
        --exclude='__pycache__/'
        --exclude='*.pyc'
        --exclude='*.pyo'
        --exclude='.git/'
        --exclude='.vscode/'
        --exclude='.idea/'
        --exclude='*.swp'
        --exclude='*.swo'
        --exclude='.env'
        --exclude='*.log'
        --exclude='logs/'
        --exclude='.DS_Store'
    )
    
    # Исключаем БД только если не указан --with-db
    if [ "$INCLUDE_DB" = false ]; then
        EXCLUDE_ARGS+=(--exclude='db.sqlite3')
        EXCLUDE_ARGS+=(--exclude='db.sqlite3-shm')
        EXCLUDE_ARGS+=(--exclude='db.sqlite3-wal')
    fi
    
    rsync -avz --progress "${EXCLUDE_ARGS[@]}" "$PROJECT_DIR/" "$DEST/"
    echo -e "${GREEN}Загрузка завершена!${NC}"
else
    echo -e "${YELLOW}rsync не найден, используем scp${NC}"
    echo "Внимание: scp передаст все файлы, включая ненужные"
    echo "Рекомендуется установить rsync или использовать архив"
    read -p "Продолжить? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        scp -r "$PROJECT_DIR" "$DEST"
        echo -e "${GREEN}Загрузка завершена!${NC}"
    else
        echo "Отменено"
        exit 1
    fi
fi

echo ""
echo "Следующие шаги на сервере:"
echo "1. cd $(basename "$DEST")"
echo "2. chmod +x deploy.sh"
echo "3. ./deploy.sh"

