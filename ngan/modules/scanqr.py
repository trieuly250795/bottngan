from zlapi.models import Message
import json
import urllib.parse
import requests

des = {
    'tác giả': "Rosy",
    'mô tả': "Scan QRCODE",
    'tính năng': [
        "📷 Quét mã QR từ ảnh do người dùng cung cấp.",
        "🔍 Kiểm tra và xử lý ảnh được gửi kèm tin nhắn hoặc được quote lại.",
        "📨 Gửi phản hồi với nội dung đã quét từ mã QR.",
        "🔔 Thông báo lỗi cụ thể nếu có vấn đề xảy ra khi quét mã QR."
    ],
    'hướng dẫn sử dụng': [
        "📩 Gửi lệnh scanqr kèm ảnh QR code để quét mã QR.",
        "📌 Ví dụ: scanqr và gửi kèm ảnh QR code hoặc reply lại ảnh QR code.",
        "✅ Nhận thông báo trạng thái và kết quả quét mã QR ngay lập tức."
    ]
}

last_sent_image_url = None

def handle_scanqr_command(message, message_object, thread_id, thread_type, author_id, client):
    # Gửi phản ứng ngay khi người dùng soạn đúng lệnh
    action = "✅"
    client.sendReaction(message_object, action, thread_id, thread_type, reactionType=75)
    global last_sent_image_url
    msg_obj = message_object
    if msg_obj.msgType == "chat.photo":
        img_url = urllib.parse.unquote(msg_obj.content.href.replace("\\/", "/"))
        last_sent_image_url = img_url
        handle_scan_command(img_url, thread_id, thread_type, client, message_object)
    elif msg_obj.quote:
        attach = msg_obj.quote.attach
        if attach:
            try:
                attach_data = json.loads(attach)
                image_url = attach_data.get('hdUrl') or attach_data.get('href')
                if image_url:
                    handle_scan_command(image_url, thread_id, thread_type, client, message_object)
                else:
                    send_error_message(thread_id, thread_type, client)
            except json.JSONDecodeError as e:
                print(f"loi json: {str(e)}")
                send_error_message(thread_id, thread_type, client)
        else:
            send_error_message(thread_id, thread_type, client)
    else:
        send_error_message(thread_id, thread_type, client)

def handle_scan_command(image_url, thread_id, thread_type, client, message_object):
    if image_url:
        api_url = f"http://api.qrserver.com/v1/read-qr-code/?fileurl={image_url}"
        client.replyMessage(Message(text="Đang tiến hành scan qrcode... vui lòng đợi"), message_object, thread_id=thread_id, thread_type=thread_type)
        try:
            response = requests.get(api_url)
            response.raise_for_status()
            data = response.json()
            if data and 'symbol' in data[0]:
                datascan = data[0]['symbol'][0].get('data', 'Không thấy dữ liệu.')
            else:
                datascan = 'Không thấy dữ liệu.'
            client.replyMessage(Message(text=f"Nội dung đã scan QRCODE:\n {datascan}"), message_object, thread_id=thread_id, thread_type=thread_type, ttl=30000)
        except requests.RequestException as e:
            print(f"Lỗi gọi API: {str(e)}")
            client.send(Message(text="Lỗi"), thread_id=thread_id, thread_type=thread_type)

def send_error_message(thread_id, thread_type, client, error_message="Vui lòng reply ảnh QRCODE cần scan"):
    client.send(Message(text=error_message), thread_id=thread_id, thread_type=thread_type, ttl=30000)

def get_mitaizl():
    return {
        'scanqr': handle_scanqr_command
    }
