import os
import requests
from config import ADMIN
from zlapi.models import Message, ThreadType

ADMIN_ID = "2670654904430771575"

des = {
    'tác giả': "Rosy",
    'mô tả': "Áp dụng code all link raw",
    'tính năng': [
        "📨 Gửi nội dung của một lệnh dưới dạng file qua Mocky.io",
        "🔍 Đọc nội dung của lệnh từ module chỉ định.",
        "🔗 Tạo link runmocky với nội dung của lệnh.",
        "🔒 Kiểm tra quyền admin trước khi thực hiện lệnh.",
        "🔔 Thông báo lỗi cụ thể nếu có vấn đề xảy ra khi xử lý lệnh."
    ],
    'hướng dẫn sử dụng': [
        "📩 Gửi lệnh sharecode <tên lệnh> để tạo link runmocky và gửi file của lệnh.",
        "📌 Ví dụ: sharecode my_command để tạo link runmocky và gửi file của lệnh 'my_command'.",
        "✅ Nhận thông báo trạng thái và kết quả gửi file ngay lập tức."
    ]
}

def is_admin(author_id):
    return author_id == ADMIN_ID

def read_command_content(command_name):
    try:
        file_path = f"modules/{command_name}.py"
        
        if not os.path.exists(file_path):
            return None
        
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        return str(e)

def handle_adc_command(message, message_object, thread_id, thread_type, author_id, client):
    lenhcanlay = message.split()

    if len(lenhcanlay) < 2:
        error_message = Message(text="Vui lòng nhập tên lệnh cần lấy.")
        client.replyMessage(error_message, message_object, thread_id, thread_type)
        return

    command_name = lenhcanlay[1].strip()

    if not is_admin(author_id):
        response_message = "Bạn không đủ quyền hạn để sử dụng lệnh này."
        message_to_send = Message(text=response_message)
        client.replyMessage(message_to_send, message_object, thread_id, thread_type)
        return

    command_content = read_command_content(command_name)
    
    if command_content is None:
        response_message = f"Lệnh '{command_name}' không được tìm thấy trong các module."
        message_to_send = Message(text=response_message)
        client.replyMessage(message_to_send, message_object, thread_id, thread_type)
        return

    try:
        data = {
            "status": 200,
            "content": command_content,
            "content_type": "application/json",
            "charset": "UTF-8",
            "secret": "Kaito Kid",
            "expiration": "never"
        }

        response = requests.post("https://api.mocky.io/api/mock", json=data)
        response_data = response.json()

        mock_url = response_data.get("link")

        if mock_url:
            response_message = f"Thành công ✅\nDưới đây là link runmocky với file của lệnh {command_name}\nLink: {mock_url}"
            client.replyMessage(Message(text=response_message), message_object, thread_id, thread_type)
            
            # Gửi file qua Mocky
            client.sendRemoteFile(
                fileUrl=mock_url,
                fileName=f"{command_name}.py",
                thread_id=thread_id,  # Gửi về chính nhóm/người đã gửi lệnh
                thread_type=thread_type,
                fileSize=None,
                extension="PY"
            )
        else:
            response_message = "Không thể tạo link run.mocky."
            client.replyMessage(Message(text=response_message), message_object, thread_id, thread_type, ttl=30000)

    except Exception as e:
        response_message = f"Có lỗi xảy ra: {str(e)}"
        client.replyMessage(Message(text=response_message), message_object, thread_id, thread_type)

def get_mitaizl():
    return {
        'sharecode': handle_adc_command
    }