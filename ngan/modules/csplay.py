from zlapi.models import Message
import os
import random

des = {
    'version': "1.0.2",
    'credits': "時崎狂三 ",
    'description': "Gửi ảnh anime từ thư mục cosplay18"
}

def handle_anhgai_command(message, message_object, thread_id, thread_type, author_id, client):
    # Gửi phản ứng ngay khi người dùng soạn đúng lệnh
    action = "✅"
    client.sendReaction(message_object, action, thread_id, thread_type, reactionType=75)

    try:
        # Gửi phản hồi vào tin nhắn người đã soạn
        reply_message = f""
        client.sendMessage(Message(text=reply_message), thread_id, thread_type, ttl=20000)

        # Đường dẫn đến thư mục ảnh mới (cosplay18)
        folder_path = 'cosplay18'

        # Kiểm tra xem thư mục có tồn tại không
        if not os.path.exists(folder_path):
            error_message = Message(text="Thư mục 'cosplay18' không tồn tại!")
            client.sendMessage(error_message, thread_id, thread_type)
            return

        # Lấy danh sách các tệp ảnh trong thư mục
        image_files = [f for f in os.listdir(folder_path) if f.lower().endswith(('jpg', 'jpeg', 'png', 'gif', 'bmp'))]

        # Kiểm tra xem thư mục có ảnh không
        if not image_files:
            error_message = Message(text="Không tìm thấy ảnh trong thư mục 'cosplay18'.")
            client.sendMessage(error_message, thread_id, thread_type)
            return

        # Chọn một ảnh ngẫu nhiên từ thư mục
        selected_image = random.choice(image_files)
        image_path = os.path.join(folder_path, selected_image)

        # Gửi ảnh với TTL 60 giây (tự xóa ảnh sau 60 giây)
        client.sendLocalImage(
            image_path, 
            message=Message(text=""),
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
        'csplay': handle_anhgai_command
    }
