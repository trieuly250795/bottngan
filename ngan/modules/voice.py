from zlapi.models import Message
import json
import urllib.parse
import os
import requests
from gtts import gTTS
from langdetect import detect

des = {
    'tác giả': "Rosy",
    'mô tả': "Chuyển văn bản thành giọng nói",
    'tính năng': [
        "📨 Phát hiện ngôn ngữ của văn bản.",
        "🔍 Tạo giọng nói dựa trên ngôn ngữ đã phát hiện.",
        "🔗 Tải giọng nói lên máy chủ và trả về liên kết.",
        "🔔 Thông báo lỗi cụ thể nếu có vấn đề xảy ra khi xử lý yêu cầu."
    ],
    'hướng dẫn sử dụng': [
        "📩 Gửi lệnh voice <nội dung> để chuyển văn bản thành giọng nói.",
        "📌 Ví dụ: voice Xin chào thế giới để chuyển văn bản 'Xin chào thế giới' thành giọng nói.",
        "✅ Nhận thông báo trạng thái và kết quả ngay lập tức."
    ]
}

def convert_text_to_mp3(text):
    try:
        # Phát hiện ngôn ngữ của văn bản
        detected_lang = detect(text)
        print(f"Ngôn ngữ được phát hiện: {detected_lang}")
        # Tạo giọng nói dựa trên ngôn ngữ đã phát hiện
        tts = gTTS(text=text, lang=detected_lang)
        mp3_file = 'NGSONVOICE.mp3'
        tts.save(mp3_file)
        return mp3_file
    except Exception as e:
        print(f"Lỗi: {str(e)}")
        return None

def upload_to_host(file_name):
    try:
        with open(file_name, 'rb') as file:
            files = {'files[]': file}
            response = requests.post('https://uguu.se/upload', files=files).json()
            if response['success']:
                return response['files'][0]['url']
            return False
    except Exception as e:
        print(f"Error in upload_to_host: {e}")
        return False

def handle_voice_command(message, message_object, thread_id, thread_type, author_id, client):
    # Gửi phản ứng ngay khi người dùng soạn đúng lệnh
    action = "✅"
    client.sendReaction(message_object, action, thread_id, thread_type, reactionType=75)
    
    content = message_object.content.strip()
    command_parts = content.split(maxsplit=1)
    text = command_parts[1].strip() if len(command_parts) > 1 else ""
    
    if not text:
        send_error_message(thread_id, thread_type, client, "Vui lòng nhập nội dung.")
        return

    mp3_file = convert_text_to_mp3(text)
    if mp3_file:
        voice_url = upload_to_host(mp3_file)
        if voice_url:
            file_size = os.path.getsize(mp3_file)
            client.sendRemoteVoice(voice_url, thread_id, thread_type, fileSize=file_size)
        else:
            send_error_message(thread_id, thread_type, client, "Không thể tải âm thanh.")
    else:
        send_error_message(thread_id, thread_type, client, "Không thể tạo voice.")

def send_error_message(thread_id, thread_type, client, error_message="lỗi cmnr."):
    client.send(Message(text=error_message), thread_id=thread_id, thread_type=thread_type)

def process_message(message_object, thread_id, thread_type, author_id, client):
    content = message_object.content.strip()
    command_parts = content.split(maxsplit=1)
    command = command_parts[0].lower()
    commands = get_mitaizl()
    
    if command in commands:
        commands[command](message_object, thread_id, thread_type, author_id, client)
    else:
        send_error_message(thread_id, thread_type, client, "Lệnh không hợp lệ.")

def get_mitaizl():
    return {
        'voice': handle_voice_command
    }
