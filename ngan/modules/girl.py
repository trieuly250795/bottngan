from zlapi import ZaloAPI
from zlapi.models import *
import time
from concurrent.futures import ThreadPoolExecutor
import threading
import random
import os

des = {
    'tác giả': "ROSY",
    'mô tả': "Gửi ảnh từ thư mục gai, đảm bảo người dùng nhận được ảnh ngẫu nhiên mỗi khi yêu cầu.",
    'tính năng': [
        "✅ Gửi phản ứng xác nhận khi lệnh được nhập đúng.",
        "🚀 Tìm kiếm và lấy ảnh từ thư mục anhgai2.",
        "🔗 Chọn ngẫu nhiên một ảnh từ thư mục để gửi.",
        "📊 Gửi phản hồi khi tìm kiếm thành công hoặc thất bại.",
        "⚡ Gửi ảnh với TTL 60 giây (tự xóa ảnh sau 60 giây)."
    ],
    'hướng dẫn sử dụng': [
        "📌 Gửi lệnh girl để tìm kiếm và gửi ảnh.",
        "📎 Bot sẽ tự động tìm kiếm và gửi ảnh từ thư mục gai.",
        "📢 Hệ thống sẽ gửi phản hồi khi hoàn thành."
    ]
}
def ping(message, message_object, thread_id, thread_type, author_id, self):
    # Phản ứng ngay khi người dùng gửi lệnh
    action = "✅"  # Chọn phản ứng bạn muốn
    self.sendReaction(message_object, action, thread_id, thread_type, reactionType=75)

    # Tính thời gian ping
    start_time = time.time()

    # Trả lời tin nhắn với độ trễ ping
    end_time = time.time()
    ping_time = end_time - start_time

    # Lấy ảnh ngẫu nhiên từ thư mục
    image_dir = "gai"
    image_files = [f for f in os.listdir(image_dir) if f.endswith(('.jpg', '.jpeg', '.png'))]
    random_image = random.choice(image_files)
    image_path = os.path.join(image_dir, random_image)

    # Gửi độ trễ ping
    text = f""
    self.sendLocalImage(
    imagePath=image_path,
    thread_id=thread_id,
    thread_type=thread_type,
    message=Message(text),
    ttl=60000
)


def get_mitaizl():
    return {
        'girl': ping
    }
