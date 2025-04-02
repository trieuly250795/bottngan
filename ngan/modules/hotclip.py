from zlapi.models import Message
import requests

des = {
    'tác giả': "ROSY",
    'mô tả': "Gửi thông tin admin và video ngẫu nhiên từ API.",
    'tính năng': [
        "✅ Gửi phản ứng xác nhận khi lệnh được nhập đúng.",
        "🚀 Lấy thông tin từ API và gửi phản hồi.",
        "🔗 Tải video từ URL và gửi lại trong nhóm.",
        "📊 Gửi phản hồi khi lấy thông tin thành công hoặc thất bại.",
        "⚡ Gửi video với thông báo thông tin admin."
    ],
    'hướng dẫn sử dụng': [
        "📌 Gửi lệnh `hotclip` để nhận thông tin admin và video ngẫu nhiên.",
        "📎 Bot sẽ tự động tìm kiếm thông tin từ API và gửi video.",
        "📢 Hệ thống sẽ gửi phản hồi khi hoàn thành."
    ]
}

def handle_ad_command(message, message_object, thread_id, thread_type, author_id, client):
        # Thêm hành động phản hồi
    action = "✅ "
    client.sendReaction(message_object, action, thread_id, thread_type, reactionType=75)
    uptime_message = "𝙍𝙊𝙎𝙔 𝘼𝙍𝙀𝙉𝘼 𝙎𝙃𝙊𝙋"
    message_to_send = Message(text=uptime_message)

    
    api_url = 'https://duongkum999.tech/gai/'
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
        }

        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        video_url = data.get('data', '')
        thumbnail_url = 'https://i.imgur.com/ucvLa5G.jpeg'
        duration = '100'

        client.sendRemoteVideo(
            video_url, 
            thumbnail_url,
            duration=duration,
            message=message_to_send,
            thread_id=thread_id,
            thread_type=thread_type,
            width=1080,
            height=1920
        )
        
    except requests.exceptions.RequestException as e:
        error_message = Message(text=f"Đã xảy ra lỗi khi gọi API: {str(e)}")
        client.sendMessage(error_message, thread_id, thread_type)
    except Exception as e:
        error_message = Message(text=f"Đã xảy ra lỗi: {str(e)}")
        client.sendMessage(error_message, thread_id, thread_type)
    

def get_mitaizl():
    return {
        'hotclip': handle_ad_command
    }