from zlapi.models import Message
import requests

des = {
    'version': "1.0.2",
    'credits': "𝑋𝑆𝐻𝐼𝑁",
    'description': "Gửi video 19"
}

def handle_vd18_command(message, message_object, thread_id, thread_type, author_id, client):
    uptime_message = "Video Anime của bạn đây."
    message_to_send = Message(text=uptime_message)
    
    api_url = 'https://raw.githubusercontent.com/ankunzt12/vdmat.jison/refs/heads/main/vdmat.js'
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
        }

        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        video_url = data.get('url', '')
        thumbnail_url = 'https://files.catbox.moe/mdwflc.jpg'
        duration = '1000'

        # Lấy tên người dùng hoặc dùng author_id
        caller_name = getattr(message_object, 'sender_name', None) or author_id
        
        client.sendRemoteVideo(
            video_url, 
            thumbnail_url,
            duration=duration,
            message=Message(text=f"𝐷𝐴 𝐺𝑈𝐼 𝑉𝐼𝐷𝐸𝑂 18 [𝑆𝑈𝐶𝐶𝐸𝑆𝑆✅]"),
            thread_id=thread_id,
            thread_type=thread_type,
            ttl=1200000,
            width=1280,
            height=720
        )
        
    except requests.exceptions.RequestException as e:
        error_message = Message(text=f"Đã xảy ra lỗi khi gọi API: {str(e)}")
        client.sendMessage(error_message, thread_id, thread_type, ttl=1000)
    except Exception as e:
        error_message = Message(text=f"Đã xảy ra lỗi: {str(e)}")
        client.sendMessage(error_message, thread_id, thread_type, ttl=1000)

def get_mitaizl():
    return {
        'vd19': handle_vd18_command
    }
