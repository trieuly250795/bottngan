import requests
import urllib.parse
from zlapi import ZaloAPI
from zlapi.models import Message

des = {
    'tác giả': "Rosy",
    'mô tả': "Dịch vụ cung cấp bài thơ tình yêu",
    'tính năng': [
        "📨 Lấy và trả về nội dung bài thơ tình yêu từ API.",
        "🔍 Kiểm tra phản hồi API và báo lỗi nếu không thành công.",
        "🔄 Gửi tin nhắn phản hồi với nội dung bài thơ.",
        "🔔 Thông báo lỗi cụ thể nếu có vấn đề xảy ra khi xử lý yêu cầu."
    ],
    'hướng dẫn sử dụng': [
        "📩 Gửi lệnh thinh để nhận bài thơ tình yêu.",
        "📌 Ví dụ: thinh để nhận nội dung bài thơ tình yêu từ API.",
        "✅ Nhận thông báo trạng thái và kết quả ngay lập tức."
    ]
}

def handle_joker_command(message, message_object, thread_id, thread_type, author_id, client):
    try:
        # Gọi API để lấy nội dung (ví dụ: một bài thơ yêu)
        joker_url = f'https://api.ntmdz.online/poem/love'
        text_response = requests.get(joker_url)
        if text_response.status_code == 200:
            text_data = text_response.json()
            content = text_data.get("data", "Nội dung không có sẵn")
            message_to_send = Message(text=f"> : {content}")
            client.replyMessage(message_to_send, message_object, thread_id, thread_type, ttl=120000)
    except requests.exceptions.RequestException as e:
        error_message = Message(text=f"Đã xảy ra lỗi khi gọi API: {str(e)}")
        client.sendMessage(error_message, thread_id, thread_type)
    except KeyError as e:
        error_message = Message(text=f"Dữ liệu từ API không đúng cấu trúc: {str(e)}")
        client.sendMessage(error_message, thread_id, thread_type)
    except Exception as e:
        error_message = Message(text=f"Đã xảy ra lỗi không xác định: {str(e)}")
        client.sendMessage(error_message, thread_id, thread_type)

def get_mitaizl():
    return {
        'thinh': handle_joker_command
    }
