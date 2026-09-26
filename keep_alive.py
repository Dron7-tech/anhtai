from flask import Flask
from threading import Thread
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot đang hoạt động 24/7 cực kỳ ổn định trên Render!"

def run():
    # Tự động bắt đúng Port mà hệ thống mây cấp phát, tránh hoàn toàn lỗi 502
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()