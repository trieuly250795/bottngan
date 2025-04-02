from zlapi.models import Message
import time
import os
import requests

des = {
    'tác giả': "Rosy",
    'mô tả': "Chụp ảnh màn hình trang web theo yêu cầu.",
    'tính năng': [
        "📸 Chụp ảnh màn hình của bất kỳ trang web nào",
        "🔗 Hỗ trợ nhập URL để lấy ảnh chụp nhanh chóng",
        "🖼️ Ảnh chụp có độ phân giải cao lên đến 1920px",
        "⚡ Gửi ảnh ngay khi xử lý xong",
        "🛠️ Kiểm tra URL hợp lệ trước khi chụp",
        "🗑️ Ảnh tự động xóa sau khi gửi để tiết kiệm bộ nhớ"
    ],
    'hướng dẫn sử dụng': "Dùng lệnh 'cap [URL]' để chụp ảnh màn hình trang web mong muốn."
}

def handle_cap_command(message, message_object, thread_id, thread_type, author_id, client):
    """
    Xử lý lệnh 'cap' để chụp ảnh màn hình trang web.
    """
    if "cap" in message.lower():
        action = "✅"
        client.sendReaction(message_object, action, thread_id, thread_type, reactionType=75)
        
        content = message.strip().split()
        if len(content) < 2:
            error_message = Message(text="Vui lòng nhập link cần chụp ảnh màn hình.")
            client.replyMessage(error_message, message_object, thread_id, thread_type, ttl=30000)
            return
        
        url_to_capture = content[1].strip()
        if not url_to_capture.startswith("https://") or not validate_url(url_to_capture):
            error_message = Message(text="Vui lòng nhập link hợp lệ!")
            client.replyMessage(error_message, message_object, thread_id, thread_type, ttl=30000)
            return
        
        try:
            capture_url = f"https://image.thum.io/get/width/1920/crop/400/fullpage/noanimate/{url_to_capture}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
            }
            image_response = requests.get(capture_url, headers=headers)
            image_response.raise_for_status()
            
            image_path = 'modules/cache/temp_image9.jpeg'
            with open(image_path, 'wb') as f:
                f.write(image_response.content)
            
            success_message = f"Ảnh chụp trang web: {url_to_capture}"
            message_to_send = Message(text=success_message)
            client.sendLocalImage(image_path, message=message_to_send, thread_id=thread_id, thread_type=thread_type, ttl=120000)
            os.remove(image_path)
        except requests.exceptions.RequestException as e:
            error_message = Message(text=f"Đã xảy ra lỗi khi gọi API: {str(e)}")
            client.sendMessage(error_message, thread_id, thread_type)
        except Exception as e:
            error_message = Message(text=f"Đã xảy ra lỗi: {str(e)}")
            client.sendMessage(error_message, thread_id, thread_type)

def validate_url(url):
    """
    Kiểm tra URL hợp lệ.
    """
    return requests.utils.urlparse(url).scheme in ('http', 'https')

def get_mitaizl():
    """
    Hàm trả về danh sách lệnh và hàm xử lý tương ứng.
    """
    return {
        'cap': handle_cap_command
    }
