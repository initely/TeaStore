#!/usr/bin/env python3
"""
Скрипт для запуска FastAPI приложения
"""
import os
import uvicorn

# Чтение настроек из переменных окружения
HOST = os.getenv("HOST", "localhost")
PORT = int(os.getenv("PORT", 8000))
RELOAD = os.getenv("RELOAD", "False").lower() == "true"
WORKERS = int(os.getenv("WORKERS", 1))

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=HOST,
        port=PORT,
        reload=RELOAD,
        workers=WORKERS if not RELOAD else 1,
    )

