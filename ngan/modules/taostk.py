from zlapi.models import Message
import json
import urllib.parse
import os
import requests

des = {
    'version': "1.0.0",
    'credits': "Tai sex",
    'description': "Tạo sticker khi reply vào một ảnh"
}

def handle_stk_command(message, message_object, thread_id, thread_type, author_id, client):
    if message_object.quote:
        attach = message_object.quote.attach
        if attach:
            try:
                attach_data = json.loads(attach)
                print(f"[DEBUG] Attach data: {attach_data}")  # Debug log
            except json.JSONDecodeError as e:
                client.sendMessage(
                    Message(text="Dữ liệu ảnh không hợp lệ."),
                    thread_id=thread_id,
                    thread_type=thread_type
                )
                print(f"[ERROR] JSON decode error: {e}")  # Error log
                return

            # Lấy URL ảnh
            image_url = attach_data.get('hdUrl') or attach_data.get('href') or attach_data.get('url')
            if not image_url:
                client.sendMessage(
                    Message(text="Không tìm thấy URL ảnh."),
                    thread_id=thread_id,
                    thread_type=thread_type
                )
                return

            image_url = urllib.parse.unquote(image_url)
            print(f"[DEBUG] Image URL: {image_url}")  # Debug log

            # Kiểm tra và xử lý ảnh
            if is_valid_image_url(image_url) and is_url_accessible(image_url):
                # Gửi ảnh qua URL trực tiếp
                try:
                    client.sendMessage(
                        Message(
                            text="Sticker đã được tạo!",
                            attachment={"type": "image", "url": image_url}
                        ),
                        thread_id=thread_id,
                        thread_type=thread_type
                    )
                except Exception as e:
                    print(f"[ERROR] Error sending image: {e}")
                    client.sendMessage(
                        Message(text="Không thể gửi ảnh."),
                        thread_id=thread_id,
                        thread_type=thread_type
                    )
            else:
                client.sendMessage(
                    Message(text="URL không phải là ảnh hợp lệ hoặc không thể truy cập."),
                    thread_id=thread_id,
                    thread_type=thread_type
                )
        else:
            client.sendMessage(
                Message(text="Không có ảnh nào được reply."),
                thread_id=thread_id,
                thread_type=thread_type
            )
    else:
        client.sendMessage(
            Message(text="Hãy reply vào ảnh cần tạo sticker."),
            thread_id=thread_id,
            thread_type=thread_type
        )

def is_valid_image_url(url):
    valid_extensions = ['.jpg', '.jpeg', '.png', '.gif']
    return any(url.lower().endswith(ext) for ext in valid_extensions)

def is_url_accessible(url):
    try:
        response = requests.head(url, timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False

def get_mitaizl():
    return {
        'stkk2': handle_stk_command
    }
