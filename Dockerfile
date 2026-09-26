FROM python:3.10-slim

WORKDIR /app

# Khai báo biến môi trường chuẩn của Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Hugging Face yêu cầu chạy với user ID 1000
RUN useradd -m -u 1000 user
USER user

# Mở cổng 7860 cho Hugging Face nhận diện
EXPOSE 7860

# Chạy bot
CMD ["python", "bot.py"]