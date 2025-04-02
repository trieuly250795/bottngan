from zlapi.models import Message
from config import ADMIN
import time
import random

des = {
    'tác giả': "Rosy",
    'mô tả': "Gửi sticker đến nhóm",
    'tính năng': [
        "📨 Gửi sticker đến nhóm hoặc người dùng.",
        "🔒 Kiểm tra quyền admin trước khi thực hiện lệnh.",
        "🔍 Xử lý lỗi và thông báo kết quả gửi sticker."
    ],
    'hướng dẫn sử dụng': [
        "📩 Gửi lệnh stkmoi để gửi sticker đến nhóm hoặc người dùng.",
        "📌 Ví dụ: stkmoi để gửi sticker với loại, ID và danh mục đã định sẵn.",
        "✅ Nhận thông báo trạng thái và kết quả gửi sticker ngay lập tức."
    ]
}

# Danh sách các sticker với loại, ID và danh mục
stickers = [
    {"sticker_type": 3, "sticker_id": "23339", "category_id": "10425"},
    # Thêm sticker ID 23311
]

def handle_stklag_command(message, message_object, thread_id, thread_type, author_id, client):
    print("Bắt đầu xử lý lệnh gửi sticker...")

    if author_id not in ADMIN:
        print("𓂄𓆩 Rosy 🫧 Arena Shop 🫒 𓆪𓂁 mới sài đc thoii cu 😜🖕")
        client.replyMessage(
            Message(text=" 𓂄𓆩 Rosy 🫧 Arena Shop 🫒 𓆪𓂁 mà sài cái con đỉ mẹ m 🥺😝."),
            message_object, thread_id, thread_type
        )
        return

    # Cố định số lượng sticker cần gửi là 10
    num_stickers_to_send = 10
    print(f"Số lượng sticker cố định: {num_stickers_to_send}")

    for i in range(num_stickers_to_send):
        sticker = random.choice(stickers)  # Chọn sticker ngẫu nhiên
        sticker_type = sticker['sticker_type']
        sticker_id = sticker['sticker_id']
        category_id = sticker['category_id']

        try:
            print(f"Gửi sticker: {sticker_id}...")
            response = client.sendSticker(sticker_type, sticker_id, category_id, thread_id, thread_type, ttl=60000)

            if response:
                client.sendMessage(Message(text=f"Đã gửi sticker 👊 thành công."), thread_id, thread_type, ttl=60000)
            else:
                client.sendMessage(Message(text=f"Không thể gửi sticker {sticker_id}."), thread_id, thread_type)

            # Thêm thời gian chờ giữa các sticker nếu cần
            time.sleep(1)  # Chờ 1 giây trước khi gửi sticker tiếp theo

        except Exception as e:
            print(f"Error khi gửi sticker: {e}")
            client.sendMessage(Message(text="Đã xảy ra lỗi khi gửi sticker."), thread_id, thread_type)

def get_mitaizl():
    return {
        'stkmoi': handle_stklag_command
    }
