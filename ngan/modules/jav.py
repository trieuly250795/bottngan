from zlapi.models import Message
import os
import random

des = {
    'tác giả': "Rosy",
    'mô tả': "Gửi ảnh idol jav ngẫu nhiên từ thư mục jav",
    'tính năng': [
        "📷 Gửi ảnh vú ngẫu nhiên từ thư mục 'anhvu'",
        "⏳ Hạn chế spam bằng cooldown 60 giây (trừ admin)",
        "🛠️ Admin có thể sử dụng lệnh không bị giới hạn thời gian",
        "🖼️ Hỗ trợ nhiều định dạng ảnh như JPG, PNG, GIF, BMP",
        "⚡ Tích hợp phản ứng khi sử dụng lệnh",
        "🗑️ Ảnh tự động xóa sau 60 giây để tránh chiếm bộ nhớ"
    ],
    'hướng dẫn sử dụng': "Dùng lệnh 'jav' để nhận một ảnh idol jav ngẫu nhiên từ thư mục 'jav'."
}
def handle_anhgai_command(message, message_object, thread_id, thread_type, author_id, client):
    # Gửi phản ứng ngay khi người dùng soạn đúng lệnh
    action = "✅"
    client.sendReaction(message_object, action, thread_id, thread_type, reactionType=75)

    try:
        # Gửi phản hồi vào tin nhắn người đã soạn
        reply_message = f""
        client.sendMessage(Message(text=reply_message), thread_id, thread_type, ttl=20000)

        # Đường dẫn đến thư mục ảnh mới (jav)
        folder_path = 'jav'

        # Kiểm tra xem thư mục có tồn tại không
        if not os.path.exists(folder_path):
            error_message = Message(text="Thư mục 'jav' không tồn tại!")
            client.sendMessage(error_message, thread_id, thread_type)
            return

        # Lấy danh sách các tệp ảnh trong thư mục
        image_files = [f for f in os.listdir(folder_path) if f.lower().endswith(('jpg', 'jpeg', 'png', 'gif', 'bmp'))]

        # Kiểm tra xem thư mục có ảnh không
        if not image_files:
            error_message = Message(text="Không tìm thấy ảnh trong thư mục 'jav'.")
            client.sendMessage(error_message, thread_id, thread_type)
            return

        # Chọn một ảnh ngẫu nhiên từ thư mục
        selected_image = random.choice(image_files)
        image_path = os.path.join(folder_path, selected_image)

        # Gửi ảnh với TTL 60 giây (tự xóa ảnh sau 60 giây)
        client.sendLocalImage(
            image_path, 
            message=Message(text="Idol dành cho bạn"),
            thread_id=thread_id,
            thread_type=thread_type,
            width=1200,
            height=1600,
            ttl=60000  # 60 giây (60,000 ms) tự xóa ảnh sau thời gian này
        )

    except Exception as e:
        error_message = Message(text=f"Đã xảy ra lỗi: {str(e)}")
        client.sendMessage(error_message, thread_id, thread_type)

def get_mitaizl():
    return {
        'jav': handle_anhgai_command
    }
