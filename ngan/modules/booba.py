
from zlapi import ZaloAPI
from zlapi.models import *
import time
import random
import os
import requests  # Để tải ảnh từ URL
from io import BytesIO

des = {
    'tác giả': "ROSY",
    'mô tả': "Gửi ảnh nude từ danh sách link trong tệp nude.txt, đảm bảo người dùng nhận được ảnh ngẫu nhiên mỗi khi yêu cầu.",
    'tính năng': [
        "✅ Gửi phản ứng xác nhận khi lệnh được nhập đúng.",
        "🚀 Tìm kiếm và lấy ảnh từ tệp nude.txt",
        "🔗 Chọn ngẫu nhiên một ảnh từ danh sách link để gửi.",
        "📊 Gửi phản hồi khi tìm kiếm thành công hoặc thất bại.",
        "⚡ Gửi ảnh với TTL 60 giây (tự xóa ảnh sau 60 giây)."
    ],
    'hướng dẫn sử dụng': [
        "📌 Gửi lệnh `nude` để tìm kiếm và gửi ảnh.",
        "📎 Bot sẽ tự động lấy ảnh từ danh sách link trong tệp nude.txt",
        "📢 Hệ thống sẽ gửi phản hồi khi hoàn thành."
    ]
}

# Sử dụng set cho danh sách admin để tối ưu kiểm tra membership
ADMIN_IDS = {"2670654904430771575", "987654321"}

# Thời gian chờ (cooldown) cho người dùng không phải admin (tính bằng giây)
COOLDOWN = 180
cooldown_dict = {}

# Global cache cho file ảnh
IMAGE_FILE = 'boo.txt'
image_links_cache = None
image_file_mtime = None

# Sử dụng session để tối ưu kết nối HTTP
session = requests.Session()

def get_image_links():
    """
    Đọc file chứa các link ảnh và lưu vào cache.
    Nếu file chưa thay đổi, trả về danh sách đã được cache.
    """
    global image_links_cache, image_file_mtime
    try:
        current_mtime = os.path.getmtime(IMAGE_FILE)
    except OSError:
        print(f"File {IMAGE_FILE} không tồn tại!")
        return None

    if image_links_cache is not None and image_file_mtime == current_mtime:
        return image_links_cache

    try:
        with open(IMAGE_FILE, 'r') as f:
            # Loại bỏ các dòng rỗng và loại bỏ khoảng trắng thừa
            lines = [line.strip() for line in f if line.strip()]
        if not lines:
            print(f"File {IMAGE_FILE} không chứa bất kỳ link ảnh nào!")
            return None
        image_links_cache = lines
        image_file_mtime = current_mtime
        return image_links_cache
    except Exception as e:
        print(f"Lỗi khi đọc file {IMAGE_FILE}: {e}")
        return None

def boo(message, message_object, thread_id, thread_type, author_id, self):
    # Kiểm tra cooldown nếu người dùng không phải admin
    if author_id not in ADMIN_IDS:
        current_time = time.time()
        last_used = cooldown_dict.get(author_id, 0)
        if current_time - last_used < COOLDOWN:
            remaining = int(COOLDOWN - (current_time - last_used))
            cooldown_msg = f"Bạn phải chờ thêm {remaining} giây trước khi dùng lệnh này."
            self.sendMessage(Message(cooldown_msg), thread_id, thread_type)
            return
        cooldown_dict[author_id] = current_time

    # Phản ứng ngay khi nhận lệnh
    action = "✅"
    self.sendReaction(message_object, action, thread_id, thread_type, reactionType=75)

    # Lấy danh sách link ảnh từ file (sử dụng cache nếu có)
    image_links = get_image_links()
    if image_links is None:
        return

    # Chọn ngẫu nhiên một link ảnh
    random_image_url = random.choice(image_links)
    print(f"Đang gửi ảnh từ URL: {random_image_url}")

    try:
        # Tải ảnh từ URL với timeout để tránh treo nếu đường truyền chậm
        response = session.get(random_image_url, timeout=10)
        if response.status_code == 200:
            # Lưu nội dung ảnh vào file tạm
            temp_image_path = "temp_image.jpg"
            with open(temp_image_path, 'wb') as f:
                f.write(response.content)
            
            self.sendLocalImage(
                imagePath=temp_image_path,
                thread_id=thread_id,
                thread_type=thread_type,
                message=Message(""),
                ttl=60000
            )
            print("Ảnh đã được gửi thành công!")
            os.remove(temp_image_path)
        else:
            print(f"Không thể tải ảnh từ URL: {random_image_url} (HTTP {response.status_code})")
    except Exception as e:
        print(f"Đã xảy ra lỗi khi gửi ảnh: {e}")

def get_mitaizl():
    return {
        'boo': boo  # Đảm bảo tên hàm chính xác
    }
