from zlapi.models import Message
from config import ADMIN
import time
import random

des = {
    'tác giả': "Rosy",
    'mô tả': "Chửi chết cụ 1 con chó",
    'tính năng': [
        "📨 Spam sticker đến nhóm hoặc người dùng.",
        "🔒 Kiểm tra quyền admin trước khi thực hiện lệnh.",
        "🛑 Tạm dừng spam sticker nếu cần.",
        "🔔 Thông báo trạng thái hiện tại và kết quả sau khi thay đổi cài đặt spam sticker."
    ],
    'hướng dẫn sử dụng': [
        "📩 Gửi lệnh stklag để bắt đầu spam sticker.",
        "📩 Gửi lệnh stop để dừng spam sticker.",
        "✅ Nhận thông báo trạng thái và kết quả thay đổi ngay lập tức."
    ]
}

# Danh sách các sticker với loại, ID và danh mục
stickers = [
    {"sticker_type": 3, "sticker_id": "23339", "category_id": "10425"},
    {"sticker_type": 3, "sticker_id": "23340", "category_id": "10425"},
    {"sticker_type": 3, "sticker_id": "23341", "category_id": "10425"},
    {"sticker_type": 3, "sticker_id": "23342", "category_id": "10425"},
    {"sticker_type": 3, "sticker_id": "23343", "category_id": "10425"},
    {"sticker_type": 3, "sticker_id": "23344", "category_id": "10425"},
    {"sticker_type": 3, "sticker_id": "23345", "category_id": "10425"},
    {"sticker_type": 3, "sticker_id": "23346", "category_id": "10425"},
    {"sticker_type": 3, "sticker_id": "23347", "category_id": "10425"},
    {"sticker_type": 3, "sticker_id": "23348", "category_id": "10425"},
    {"sticker_type": 3, "sticker_id": "23349", "category_id": "10425"},
    {"sticker_type": 3, "sticker_id": "23350", "category_id": "10425"},
    {"sticker_type": 3, "sticker_id": "23311", "category_id": "10425"},
    # Thêm sticker ID 23311
]

# Biến toàn cục để theo dõi trạng thái gửi sticker
sending_stickers = False

def handle_stklag_command(message, message_object, thread_id, thread_type, author_id, client):
    global sending_stickers  # Sử dụng biến toàn cục
    print("Bắt đầu xử lý lệnh gửi sticker...")

    if author_id not in ADMIN:
        print("Người dùng không có quyền thực hiện hành động này.")
        client.replyMessage(
            Message(text="Xin lỗi, bạn không có quyền thực hiện hành động này."),
            message_object, thread_id, thread_type
        )
        return

    if sending_stickers:
        print("Đang gửi sticker. Không thể thực hiện lệnh dừng.")
        client.replyMessage(
            Message(text="Đang gửi sticker, không thể thực hiện lệnh dừng ngay lúc này."),
            message_object, thread_id, thread_type
        )
        return

    # Cố định số lượng sticker cần gửi là 10
    num_stickers_to_send = 30
    print(f"Số lượng sticker cố định: {num_stickers_to_send}")

    # Đánh dấu trạng thái bắt đầu gửi sticker
    sending_stickers = True

    try:
        for i in range(num_stickers_to_send):
            if not sending_stickers:  # Kiểm tra trạng thái dừng
                print("Lệnh gửi sticker đã bị dừng.")
                client.sendMessage(
                    Message(text="Quá trình gửi sticker đã bị dừng."),
                    thread_id, thread_type
                )
                break

            sticker = random.choice(stickers)  # Chọn sticker ngẫu nhiên
            sticker_type = sticker['sticker_type']
            sticker_id = sticker['sticker_id']
            category_id = sticker['category_id']

            try:
                print(f"Gửi sticker: {sticker_id}...")
                response = client.sendSticker(sticker_type, sticker_id, category_id, thread_id, thread_type, ttl=60000)

                if response:
                    client.sendMessage(Message(text=f"Đã gửi sticker {sticker_id} thành công."), thread_id, thread_type, ttl=60000)
                else:
                    client.sendMessage(Message(text=f"Không thể gửi sticker {sticker_id}."), thread_id, thread_type)

                # Thêm thời gian chờ giữa các sticker nếu cần
                time.sleep(7)  # Chờ 1 giây trước khi gửi sticker tiếp theo

            except Exception as e:
                print(f"Error khi gửi sticker: {e}")
                client.sendMessage(Message(text="Đã xảy ra lỗi khi gửi sticker."), thread_id, thread_type)

    finally:
        # Đánh dấu trạng thái kết thúc gửi sticker
        sending_stickers = False

def handle_stop_command(message, message_object, thread_id, thread_type, author_id, client):
    global sending_stickers  # Sử dụng biến toàn cục

    if author_id not in ADMIN:
        print("Người dùng không có quyền dừng lệnh.")
        client.replyMessage(
            Message(text="Xin lỗi, bạn không có quyền dừng lệnh này."),
            message_object, thread_id, thread_type
        )
        return

    # Đổi trạng thái để dừng việc gửi sticker
    sending_stickers = False
    client.sendMessage(
        Message(text="Đã dừng lệnh gửi sticker."),
        thread_id, thread_type
    )

def get_mitaizl():
    return {
        'stklag': handle_stklag_command,
        'stop': handle_stop_command
    }
