import requests
import os
from zlapi.models import Message

des = {
    'tác giả': "Rosy",
    'mô tả': "Tìm kiếm và gửi ảnh từ API, đồng thời phản hồi tin nhắn của người dùng.",
    'tính năng': [
        "✅ Gửi phản ứng xác nhận khi lệnh được nhập đúng.",
        "🚀 Tìm kiếm và lấy dữ liệu từ API.",
        "🔗 Tải ảnh từ URL và gửi lại trong nhóm.",
        "📊 Gửi phản hồi khi tìm kiếm thành công hoặc thất bại.",
        "⚡ Xóa tệp ảnh tạm thời sau khi gửi."
    ],
    'hướng dẫn sử dụng': [
        "📌 Gửi lệnh `xxxhub` để tìm kiếm và gửi ảnh.",
        "📎 Bot sẽ tự động tìm kiếm và gửi ảnh từ API.",
        "📢 Hệ thống sẽ gửi phản hồi khi hoàn thành."
    ]
}

def handle_anhgai_command(message, message_object, thread_id, thread_type, author_id, client):
    # Gửi phản hồi ngay khi người dùng chỉnh sửa đúng lệnh
    action = "✅"
    client.sendReaction(message_object, action, thread_id, thread_type, reactionType=75)
    
    try:
        # Gửi phản hồi vào tin nhắn người viết
        reply_message = f"Đang tìm kiếm [{message}]..."
        client.sendMessage(Message(text=reply_message), thread_id, thread_type, ttl=30000)
        
        # Lấy dữ liệu từ API thính
        url = "https://subhatde.id.vn/text/thinh"
        reply = requests.get(url)
        reply.raise_for_status()
        data = reply.json()
        thinh = data.get('data')
        sendmess = f"{thinh}"
        message_to_send = Message(text=sendmess)
        
        # Lấy dữ liệu từ API ảnh
        api_url = 'https://api.sumiproject.net/images/nude'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, như Gecko) Chrome/58.0.3029.110 Safari/537.36'
        }
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        data = response.json()
        image_url = data['url']
        
        # Tải ảnh về
        image_response = requests.get(image_url, headers=headers)
        image_response.raise_for_status()
        
        image_path = 'temp_image.jpeg'
        with open(image_path, 'wb') as f:
            f.write(image_response.content)
        
        # Gửi ảnh lên nhóm/chat
        client.sendLocalImage(
            image_path, message=message_to_send, thread_id=thread_id, thread_type=thread_type, width=1200, height=1600, ttl=60000
        )
        
        # Xóa ảnh sau khi gửi
        os.remove(image_path)
        
    except requests.exceptions.RequestException as e:
        error_message = Message(text=f"Đã xảy ra lỗi khi gọi API: {str(e)}")
        client.sendMessage(error_message, thread_id, thread_type)
    except Exception as e:
        error_message = Message(text=f"Đã xảy ra lỗi: {str(e)}")
        client.sendMessage(error_message, thread_id, thread_type)

def get_mitaizl():
    return {
        'xxxhub': handle_anhgai_command
    }