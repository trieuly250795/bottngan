
from zlapi import ZaloAPI
from zlapi.models import *
import random
import os
import requests  # Để tải ảnh từ URL
from io import BytesIO

des = {
    'tác giả': "ROSY",
    'mô tả': "Gửi ảnh ngẫu nhiên từ file text chứa các link ảnh, đảm bảo người dùng nhận được ảnh mỗi khi yêu cầu.",
    'tính năng': [
        "✅ Gửi phản ứng xác nhận khi lệnh được nhập đúng.",
        "🚀 Đọc file text chứa các link ảnh.",
        "🔗 Chọn ngẫu nhiên một link ảnh từ file text.",
        "📊 Tải ảnh từ URL và gửi lại trong nhóm.",
        "⚡ Gửi phản hồi khi tìm kiếm thành công hoặc thất bại."
    ],
    'hướng dẫn sử dụng': [
        "📌 Gửi lệnh `gai1` để nhận một ảnh ngẫu nhiên.",
        "📎 Bot sẽ tự động tìm kiếm và gửi ảnh từ link trong file text.",
        "📢 Hệ thống sẽ gửi phản hồi khi hoàn thành."
    ]
}

def anhgai2(message, message_object, thread_id, thread_type, author_id, self):
    # Phản ứng ngay khi người dùng gửi lệnh
    action = "✅"
    self.sendReaction(message_object, action, thread_id, thread_type, reactionType=75)

    # Đọc file text chứa các link ảnh
    txt_file = 'girl2.txt'
    if not os.path.exists(txt_file):
        print(f"File {txt_file} không tồn tại!")
        return

    with open(txt_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Xử lý từng dòng, loại bỏ khoảng trắng và dòng trống
    image_links = [line.strip() for line in lines if line.strip()]

    if not image_links:
        print("Không có link ảnh nào trong file gai1.txt!")
        return

    # Chọn ngẫu nhiên một link ảnh
    random_image_url = random.choice(image_links)
    print(f"Đang gửi ảnh từ URL: {random_image_url}")

    text = ""

    try:
        # Sử dụng header giả lập trình duyệt để tải ảnh
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
        }
        response = requests.get(random_image_url, headers=headers)
        if response.status_code == 200:
            image_data = BytesIO(response.content)
            temp_image_path = "temp_image.jpg"
            with open(temp_image_path, 'wb') as f:
                f.write(image_data.read())

            # Gửi ảnh đã tải xuống
            self.sendLocalImage(imagePath=temp_image_path, thread_id=thread_id, thread_type=thread_type, message=Message(text), ttl=60000)
            print("Ảnh đã được gửi thành công!")

            # Xóa file ảnh tạm
            os.remove(temp_image_path)
        else:
            print(f"Không thể tải ảnh từ URL: {random_image_url} (Mã lỗi: {response.status_code})")
    except Exception as e:
        print(f"Đã xảy ra lỗi khi gửi ảnh: {e}")

def get_mitaizl():
    return {
        'gai2': anhgai2
    }
