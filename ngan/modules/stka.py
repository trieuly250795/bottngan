import os
import requests
import json
import urllib.parse
import subprocess
from zlapi.models import Message

des = {
    'version': "1.0.0",
    'credits': "Quốc Khánh",
    'description': "Tạo sticker khi reply vào một ảnh hoặc video GIF hoặc từ link .webp"
}

# Hàm xử lý lệnh sticker
def handle_stk_command(message, message_object, thread_id, thread_type, author_id, client):
    try:
        if message_object.quote and message_object.quote.attach:
            # Lấy thông tin media được reply
            handle_media_reply(message_object, thread_id, thread_type, client)
        else:
            # Lấy thông tin URL từ lệnh
            handle_media_url(message, thread_id, thread_type, client)
    except Exception as e:
        client.sendMessage(
            Message(text=f"Đã xảy ra lỗi: {e}"),
            thread_id=thread_id,
            thread_type=thread_type
        )

# Xử lý khi reply vào một media
def handle_media_reply(message_object, thread_id, thread_type, client):
    try:
        attach_data = json.loads(message_object.quote.attach)
        media_url = attach_data.get('hdUrl') or attach_data.get('href')
        if not media_url:
            raise ValueError("Không tìm thấy URL từ tệp được reply.")
        
        media_url = urllib.parse.unquote(media_url.replace("\\/", "/"))
        process_media(media_url, thread_id, thread_type, client)
    except (json.JSONDecodeError, ValueError) as e:
        client.sendMessage(
            Message(text=str(e)),
            thread_id=thread_id,
            thread_type=thread_type
        )

# Xử lý khi nhận URL từ lệnh
def handle_media_url(message, thread_id, thread_type, client):
    if not message.startswith(',stk '):
        client.sendMessage(
            Message(text="Vui lòng reply vào một ảnh hoặc sử dụng lệnh với URL hợp lệ."),
            thread_id=thread_id,
            thread_type=thread_type
        )
        return
    
    url = message[4:].strip()
    if url.endswith('.webp') and is_valid_media_url(url):
        send_sticker(client, url, url, thread_id, thread_type)
    else:
        client.sendMessage(
            Message(text="URL không hợp lệ hoặc không phải định dạng .webp."),
            thread_id=thread_id,
            thread_type=thread_type
        )

# Kiểm tra URL media hợp lệ
def is_valid_media_url(url):
    try:
        response = requests.head(url, timeout=5)
        return response.status_code == 200 and (
            'image/' in response.headers.get('Content-Type', '') or
            'video/' in response.headers.get('Content-Type', '')
        )
    except requests.RequestException as e:
        print(f"Lỗi kiểm tra URL: {e}")
    return False

# Chuyển đổi video sang webp
def convert_video_to_webp(video_url):
    try:
        response = requests.get(video_url, stream=True, timeout=10)
        if response.status_code != 200:
            raise ValueError("Không thể tải video.")
        
        # Tạo tệp tạm
        with open("temp.mp4", "wb") as temp_file:
            temp_file.write(response.content)

        # Chuyển đổi sang webp
        subprocess.run(
            ['ffmpeg', '-y', '-i', 'temp.mp4', '-t', '15', '-vcodec', 'libwebp', '-loop', '0', '-q:v', '120', 'output.webp'],
            check=True
        )

        # Upload webp lên Catbox
        with open("output.webp", "rb") as webp_file:
            return upload_to_catbox(webp_file)
    finally:
        clean_temp_files(["temp.mp4", "output.webp"])

# Upload tệp lên Catbox
def upload_to_catbox(buffered):
    response = requests.post(
        "https://catbox.moe/user/api.php",
        files={'fileToUpload': ('sticker.webp', buffered, 'image/webp')},
        data={'reqtype': 'fileupload'}
    )
    if response.status_code == 200 and response.text.startswith("http"):
        return response.text
    raise ValueError(f"Lỗi khi upload: {response.text}")

# Gửi sticker
def send_sticker(client, static_url, animation_url, thread_id, thread_type):
    try:
        client.sendCustomSticker(
            staticImgUrl=static_url,
            animationImgUrl=animation_url,
            thread_id=thread_id,
            ttl=500000,
            thread_type=thread_type
        )
        client.sendMessage(
            Message(text=f"Sticker đã tạo: {animation_url}"),
            thread_id=thread_id,
            thread_type=thread_type
        )
    except Exception as e:
        client.sendMessage(
            Message(text=f"Lỗi khi gửi sticker: {e}"),
            thread_id=thread_id,
            thread_type=thread_type
        )

# Dọn dẹp tệp tạm
def clean_temp_files(files):
    for file in files:
        if os.path.exists(file):
            os.remove(file)

def get_mitaizl():
    return {'stk': handle_stk_command}
