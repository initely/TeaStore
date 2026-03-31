#!/bin/bash

# Скрипт для создания архива проекта для развертывания
# Использование: ./create_deploy_archive.sh [--with-db]
#   --with-db  - включить базу данных db.sqlite3 в архив

set -e

INCLUDE_DB=false
for arg in "$@"; do
    case $arg in
        --with-db)
            INCLUDE_DB=true
            ;;
    esac
done

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
ARCHIVE_NAME="teastore_deploy_$(date +%Y%m%d_%H%M%S).tar.gz"
TEMP_DIR=$(mktemp -d)

echo "Создание архива для развертывания..."
if [ "$INCLUDE_DB" = true ]; then
    echo "База данных будет включена в архив"
else
    echo "База данных НЕ будет включена (используйте --with-db для включения)"
fi

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

# Копируем проект во временную директорию, исключая ненужные файлы
rsync -av "${EXCLUDE_ARGS[@]}" "$PROJECT_DIR/" "$TEMP_DIR/teastore/"

# Создаем архив
cd "$TEMP_DIR"
tar -czf "$PROJECT_DIR/$ARCHIVE_NAME" teastore/

# Удаляем временную директорию
rm -rf "$TEMP_DIR"

echo "Архив создан: $ARCHIVE_NAME"
echo ""
echo "Для загрузки на сервер:"
echo "  scp $ARCHIVE_NAME user@server:/tmp/"
echo ""
echo "На сервере:"
echo "  cd /var/www"
echo "  tar -xzf /tmp/$ARCHIVE_NAME"
echo "  cd teastore"
echo "  chmod +x deploy.sh"
echo "  ./deploy.sh"

