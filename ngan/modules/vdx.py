import random
from zlapi.models import Message
import requests

des = {
    'version': "1.0.2",
    'credits': "ROSY ",
    'description': "Gửi video gái từ tệp vdsex.txt"
}

def read_video_links(file_path):
    """ Đọc các link video từ tệp txt. """
    with open(file_path, 'r') as file:
        return file.readlines()

def handle_vdsex_command(message, message_object, thread_id, thread_type, author_id, client):
    # Gửi phản ứng ngay khi người dùng soạn đúng lệnh
    action = "✅"
    client.sendReaction(message_object, action, thread_id, thread_type, reactionType=75)
    uptime_message = "Video sex+ của bạn đây, chúc ngon miệng"
    message_to_send = Message(text=uptime_message)
    
    # Đọc các link video từ tệp txt
    video_links = read_video_links('vdsex.txt')  # Đường dẫn tệp txt của bạn

    if not video_links:
        error_message = Message(text="Không tìm thấy link video nào trong tệp.")
        client.sendMessage(error_message, thread_id, thread_type)
        return

    # Chọn ngẫu nhiên một video từ danh sách
    video_url = random.choice(video_links).strip()  # Loại bỏ ký tự thừa (newline, space...)
    thumbnail_url = '2.jpeg'
    duration = '100'

    try:
        # Gửi video
        client.sendRemoteVideo(
            video_url, 
            thumbnail_url,
            duration=duration,
            message=message_to_send,
            thread_id=thread_id,
            thread_type=thread_type,
            width=1080,
            height=1920,
            ttl=300000
        )
        
    except Exception as e:
        error_message = Message(text=f"Đã xảy ra lỗi khi gửi video: {str(e)}")
        client.sendMessage(error_message, thread_id, thread_type)

def get_mitaizl():
    return {
        'vdx': handle_vdsex_command  # Đã thay đổi tên từ 'vdsexv3' thành 'vdsex'
    }
