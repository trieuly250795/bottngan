import json
import threading
import time
import os
import requests
from io import BytesIO
from zlapi.models import Message, ThreadType, Mention

des = {
    'tác giả': "Rosy",
    'mô tả': "Gửi ảnh đến tất cả nhóm",
    'tính năng': [
        "📷 Tải ảnh từ URL và gửi đến tất cả nhóm, trừ các nhóm bị loại trừ.",
        "🔍 Kiểm tra định dạng URL và xử lý các lỗi liên quan.",
        "🔗 Gửi ảnh kèm chú thích đến các nhóm đã nhập.",
        "🔒 Kiểm tra quyền admin trước khi thực hiện lệnh.",
        "🗑️ Tự động xóa file ảnh tạm sau khi gửi."
    ],
    'hướng dẫn sử dụng': [
        "📩 Gửi lệnh sendanh <link ảnh> <chú thích> để gửi ảnh đến tất cả nhóm.",
        "📌 Ví dụ: sendanh https://example.com/image.jpg Đây là chú thích để gửi ảnh cùng chú thích đến tất cả nhóm.",
        "✅ Nhận thông báo trạng thái và kết quả gửi ảnh ngay lập tức."
    ]
}

# Đảm bảo sử dụng đúng ID của admin
ADMIN_IDS = {"2670654904430771575", "5835232686339531421"}  # Dùng set cho tốc độ tra cứu nhanh
EXCLUDED_GROUPS = {"9034032228046851908", "643794532760252296", "5117775802243172962", "1161697978337789816"}  # Danh sách nhóm không gửi

def download_and_send_image(client, image_url, caption, thread_id, thread_type, author_id):
    try:
        # Tải ảnh từ URL
        response = requests.get(image_url)
        if response.status_code == 200:
            # Lưu ảnh vào bộ nhớ
            image_data = BytesIO(response.content)
            # Lưu tạm ảnh vào file để gửi bằng sendLocalImage
            temp_image_path = "temp_image.jpg"
            with open(temp_image_path, 'wb') as f:
                f.write(image_data.read())
            
            # Tạo mention và chú thích
            mention = Mention(author_id, length=len("@Member"), offset=0)
            message = Message(text="@Member\n" + caption, mention=mention)
            
            # Gửi ảnh đã tải xuống bằng sendLocalImage
            client.sendLocalImage(
                temp_image_path,
                message=message,
                thread_id=thread_id,
                thread_type=thread_type,
                width=800,
                height=333,
                ttl=180000
            )
            print("Ảnh đã được gửi thành công!")
            # Xóa ảnh tạm sau khi gửi
            os.remove(temp_image_path)
        else:
            print(f"Không thể tải ảnh từ URL: {image_url}")
    except Exception as e:
        # In ra lỗi nếu có
        print(f"Đã xảy ra lỗi khi gửi ảnh: {e}")

def start_sendall_image(client, image_url, caption, author_id):
    try:
        # Lấy tất cả các nhóm mà bot có quyền truy cập
        all_groups = client.fetchAllGroups()
        allowed_thread_ids = [gid for gid in all_groups.gridVerMap.keys() if gid not in EXCLUDED_GROUPS]
        
        for thread_id in allowed_thread_ids:
            try:
                # Gửi ảnh từ URL đến nhóm
                download_and_send_image(client, image_url, caption, thread_id, ThreadType.GROUP, author_id)
                time.sleep(1)  # Thêm một khoảng thời gian chờ nhỏ giữa các lần gửi
            except Exception as e:
                print(f"Lỗi khi gửi ảnh đến nhóm {thread_id}: {e}")
    except Exception as e:
        print(f"Lỗi trong quá trình gửi ảnh: {e}")

def handle_sendanh_command(message, message_object, thread_id, thread_type, author_id, client):
    # Gửi phản ứng ngay khi người dùng soạn đúng lệnh
    action = "✅"
    client.sendReaction(message_object, action, thread_id, thread_type, reactionType=75)

    try:
        # Kiểm tra xem người gửi có phải là admin không
        if author_id not in ADMIN_IDS:
            response_message = Message(text="Bạn không có quyền thực hiện lệnh này.")
            client.replyMessage(response_message, message_object, thread_id, thread_type, ttl=30000)
            return
        
        # Kiểm tra lệnh có bắt đầu bằng "sendanh" hoặc ",sendanh"
        if message.lower().startswith("sendanh") or message.lower().startswith(",sendanh"):
            # Trích xuất link ảnh và chú thích từ tin nhắn
            parts = message[7:].strip().split(" ", 1)
            if len(parts) < 2:
                response_message = Message(text="Vui lòng nhập đầy đủ link ảnh và chú thích!")
                client.replyMessage(response_message, message_object, thread_id, thread_type, ttl=30000)
                return
            
            image_url, caption = parts
            if not image_url:
                response_message = Message(text="Vui lòng cung cấp link ảnh!")
                client.replyMessage(response_message, message_object, thread_id, thread_type, ttl=30000)
                return

            # Khởi chạy việc gửi ảnh trong một luồng mới
            threading.Thread(target=start_sendall_image, args=(client, image_url, caption, author_id), daemon=True).start()
            
            # Phản hồi cho người dùng biết lệnh đang được thực hiện
            response_message = Message(text="Đang gửi ảnh và chú thích: " + caption)
            client.replyMessage(response_message, message_object, thread_id, thread_type, ttl=30000)
        else:
            print("Không phải lệnh sendanh, bỏ qua.")
    except Exception as e:
        print(f"Lỗi khi xử lý lệnh sendanh: {e}")

def get_mitaizl():
    return { 'sendanh': handle_sendanh_command }
