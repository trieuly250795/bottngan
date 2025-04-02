from zlapi.models import Message
import json
import urllib.parse
import requests
import pytesseract
from PIL import Image
from io import BytesIO

des = {
    'tác giả': "Rosy",
    'mô tả': "Scan text từ ảnh sử dụng Tesseract OCR",
    'tính năng': [
        "📷 Quét văn bản từ ảnh sử dụng Tesseract OCR.",
        "🔍 Kiểm tra và xử lý ảnh được gửi kèm tin nhắn hoặc được quote lại.",
        "📨 Gửi phản hồi với nội dung đã quét từ ảnh.",
        "🔔 Thông báo lỗi cụ thể nếu có vấn đề xảy ra khi quét văn bản từ ảnh."
    ],
    'hướng dẫn sử dụng': [
        "📩 Gửi lệnh scantext kèm ảnh chứa văn bản để quét văn bản.",
        "📌 Ví dụ: scantext và gửi kèm ảnh chứa văn bản hoặc reply lại ảnh chứa văn bản.",
        "✅ Nhận thông báo trạng thái và kết quả quét văn bản từ ảnh ngay lập tức."
    ]
}

last_sent_image_url = None

def handle_scantext_command(message, message_object, thread_id, thread_type, author_id, client):
    # Gửi phản ứng ngay khi người dùng soạn đúng lệnh
    action = "✅"
    client.sendReaction(message_object, action, thread_id, thread_type, reactionType=75)
    global last_sent_image_url
    msg_obj = message_object
    if msg_obj.msgType == "chat.photo":
        img_url = urllib.parse.unquote(msg_obj.content.href.replace("\\/", "/"))
        last_sent_image_url = img_url
        handle_text_scan(img_url, thread_id, thread_type, client, message_object)
    elif msg_obj.quote:
        attach = msg_obj.quote.attach
        if attach:
            try:
                attach_data = json.loads(attach)
                image_url = attach_data.get('hdUrl') or attach_data.get('href')
                if image_url:
                    handle_text_scan(image_url, thread_id, thread_type, client, message_object)
                else:
                    send_error_message(thread_id, thread_type, client)
            except json.JSONDecodeError as e:
                print(f"Lỗi JSON: {str(e)}")
                send_error_message(thread_id, thread_type, client)
        else:
            send_error_message(thread_id, thread_type, client)
    else:
        send_error_message(thread_id, thread_type, client)

def handle_text_scan(image_url, thread_id, thread_type, client, message_object):
    if image_url:
        client.replyMessage(Message(text="Đang quét nội dung từ ảnh... vui lòng đợi"), message_object, thread_id=thread_id, thread_type=thread_type)
        try:
            response = requests.get(image_url)
            response.raise_for_status()
            image = Image.open(BytesIO(response.content))
            extracted_text = pytesseract.image_to_string(image, lang='vie+eng')  # Hỗ trợ tiếng Việt và Anh
            extracted_text = extracted_text.strip()
            if extracted_text:
                client.replyMessage(Message(text=f"Nội dung trích xuất từ ảnh:\n{extracted_text}"), message_object, thread_id=thread_id, thread_type=thread_type)
            else:
                client.replyMessage(Message(text="Không tìm thấy nội dung."), message_object, thread_id=thread_id, thread_type=thread_type)
        except requests.RequestException as e:
            print(f"Lỗi tải ảnh: {str(e)}")
            client.send(Message(text="Lỗi khi tải ảnh"), thread_id=thread_id, thread_type=thread_type)
        except Exception as e:
            print(f"Lỗi OCR: {str(e)}")
            client.send(Message(text="Lỗi quét ảnh"), thread_id=thread_id, thread_type=thread_type)

def send_error_message(thread_id, thread_type, client, error_message="Vui lòng reply ảnh chứa văn bản cần quét"):
    client.send(Message(text=error_message), thread_id=thread_id, thread_type=thread_type)

def get_mitaizl():
    return {
        'scantext': handle_scantext_command
    }
