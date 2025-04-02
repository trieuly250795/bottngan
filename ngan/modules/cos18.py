import os
import random
from zlapi.models import Message

des = {
    'tác giả': "ROSY",
    'mô tả': "Gửi ảnh anime từ thư mục cosplay18, đảm bảo người dùng nhận được ảnh ngẫu nhiên mỗi khi yêu cầu.",
    'tính năng': [
        "✅ Gửi phản ứng xác nhận khi lệnh được nhập đúng.",
        "🚀 Tìm kiếm và lấy ảnh từ thư mục cosplay18.",
        "🔗 Chọn ngẫu nhiên một ảnh từ thư mục để gửi.",
        "📊 Gửi phản hồi khi tìm kiếm thành công hoặc thất bại.",
        "⚡ Gửi ảnh với TTL 60 giây (tự xóa ảnh sau 60 giây)."
    ],
    'hướng dẫn sử dụng': [
        "📌 Gửi lệnh `cos18` để tìm kiếm và gửi ảnh.",
        "📎 Bot sẽ tự động tìm kiếm và gửi ảnh từ thư mục cosplay18.",
        "📢 Hệ thống sẽ gửi phản hồi khi hoàn thành."
    ]
}

def handle_anhgai_command(message, message_object, thread_id, thread_type, author_id, client):
    # Gửi phản ứng ngay khi người dùng soạn đúng lệnh
    action = "✅"
    client.sendReaction(message_object, action, thread_id, thread_type, reactionType=75)

    try:

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
            ttl=60000 # 60 giây (60,000 ms) tự xóa ảnh sau thời gian này
        )
    except Exception as e:
        error_message = Message(text=f"Đã xảy ra lỗi: {str(e)}")
        client.sendMessage(error_message, thread_id, thread_type)

def get_mitaizl():
    return {
        'cos18': handle_anhgai_command
    }
