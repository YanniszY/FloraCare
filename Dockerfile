FROM python:3.11-slim

WORKDIR /app

# Системные зависимости для torch и pillow
RUN apt-get update && apt-get install -y \
    gcc \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

# Сначала копируем requirements чтобы кэш слоёв работал
COPY requirements.txt .

# Устанавливаем torch CPU отдельно (нет на обычном PyPI индексе)
RUN pip install --no-cache-dir \
    torch==2.10.0+cpu \
    torchvision==0.25.0+cpu \
    --index-url https://download.pytorch.org/whl/cpu

# Остальные зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# Папки которые нужны в рантайме
RUN mkdir -p temp uploads
