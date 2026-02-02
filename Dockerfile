# ============================================
# Dockerfile для Flask приложения
# ============================================

FROM python:3.9-slim

# МЕТАДАННЫЕ
LABEL maintainer="student@university.edu"
LABEL version="1.0"
LABEL description="Flask приложение для лабораторной работы по Docker"

# ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

ENV PORT=8000

ENV APP_NAME="Flask Docker App"

ENV DEBUG="False"

ENV IN_DOCKER="True"

# УСТАНОВКА ЗАВИСИМОСТЕЙ СИСТЕМЫ
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    vim \
    tree \
    && rm -rf /var/lib/apt/lists/*

# НАСТРОЙКА РАБОЧЕЙ ДИРЕКТОРИИ
RUN useradd -m -u 1000 appuser

WORKDIR /app

RUN chown -R appuser:appuser /app

USER appuser

# УСТАНОВКА PYTHON ЗАВИСИМОСТЕЙ
COPY --chown=appuser:appuser requirements.txt .

RUN pip install --no-cache-dir --user -r requirements.txt

ENV PATH="/home/appuser/.local/bin:${PATH}"

# КОПИРОВАНИЕ ИСХОДНОГО КОДА
COPY --chown=appuser:appuser . .

# СОЗДАНИЕ ДИРЕКТОРИЙ
RUN mkdir -p storage

# VOLUME ДЛЯ СОХРАНЕНИЯ ДАННЫХ
VOLUME ["/app/storage"]

# ОТКРЫТИЕ ПОРТА
EXPOSE ${PORT}

# КОМАНДА ЗАПУСКА

# Запускаем приложение
CMD ["python", "app.py"]

# ДОПОЛНИТЕЛЬНЫЕ КОМАНДЫ ДЛЯ ТЕСТИРОВАНИЯ
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:${PORT}/health || exit 1
