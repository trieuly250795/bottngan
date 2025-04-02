import requests
import os
from zlapi.models import Message

des = {
    'version': "1.0.2",
    'credits': "時崎狂三",
    'description': "Hướng dẫn sử dụng ảnh hentai"
}

def handle_anhgai_command(message, message_object, thread_id, thread_type, author_id, client):
    # Gửi phản hồi ngay khi người dùng chỉnh sửa đúng lệnh
    action = "✅"
    client.sendReaction(message_object, action, thread_id, thread_type, reactionType=75)
    
    try:
        api_url = "https://api-dowig.onrender.com/images/hentai"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, như Gecko) Chrome/58.0.3029.110 Safari/537.36'
        }
        
        # Gửi yêu cầu API
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        # Lấy URL ảnh
        image_url = data.get('url')
        if not image_url:
            raise ValueError("Không tìm thấy URL ảnh trong phản hồi API.")
        
        # Gửi tin nhắn có đường dẫn ảnh
        message_to_send = Message(text=image_url.encode('utf-8').decode('utf-8'))  # Sử dụng UTF-8
        client.sendMessage(message_to_send, thread_id, thread_type)
        
        # Tải ảnh về
        image_response = requests.get(image_url, headers=headers)
        image_response.raise_for_status()
        
        image_path = 'temp_image.jpeg'
        with open(image_path, 'wb') as f:
            f.write(image_response.content)
        
        # Gửi ảnh lên nhóm/chat
        client.sendLocalImage(
            image_path, thread_id=thread_id, thread_type=thread_type, width=1200, height=1600
        )
        
        # Xóa ảnh sau khi gửi
        os.remove(image_path)
        
    except requests.exceptions.RequestException as e:
        error_message = Message(text=f"Đã xảy ra lỗi khi gọi API: {str(e)}".encode('utf-8').decode('utf-8'))  # Sử dụng UTF-8
        client.sendMessage(error_message, thread_id, thread_type)
    except Exception as e:
        error_message = Message(text=f"Đã xảy ra lỗi: {str(e)}".encode('utf-8').decode('utf-8'))  # Sử dụng UTF-8
        client.sendMessage(error_message, thread_id, thread_type)

def get_mitaizl():
    return {
        'hentai': handle_anhgai_command
    }
