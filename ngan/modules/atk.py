from zlapi.models import *
import os
import time
import threading
from zlapi.models import MultiMsgStyle, Mention, MessageStyle
from config import ADMIN

des = {
    'tác giả': "Rosy",
    'mô tả': "Tự động réo tên người bị tag và spam tin nhắn từ file '5c.txt'.",
    'tính năng': [
        "🔍 Kiểm tra quyền hạn của người dùng trước khi thực hiện lệnh",
        "🔗 Xác định người bị tag để thực hiện spam",
        "📝 Đọc nội dung từ file '5c.txt' để gửi tin nhắn",
        "📩 Tự động gửi tin nhắn réo tên liên tục với khoảng thời gian ngắn",
        "🛑 Hỗ trợ dừng quá trình réo tên khi có lệnh từ quản trị viên"
    ],
    'hướng dẫn sử dụng': [
        "📩 Gửi lệnh atk [on/stop] [tag người cần bem] để bắt đầu hoặc dừng quá trình réo tên.",
        "📌 Ví dụ: atk on @username để bắt đầu réo tên người được tag, atk stop để dừng quá trình réo tên.",
        "✅ Nhận thông báo trạng thái và kết quả ngay lập tức."
    ]
}

is_reo_running = False

def send_message_with_style(client, text, thread_id, thread_type, color="#db342e"):
    """
    Gửi tin nhắn với định dạng màu sắc.
    """
    base_length = len(text)
    adjusted_length = base_length + 355
    style = MultiMsgStyle([
        MessageStyle(
            offset=0,
            length=adjusted_length,
            style="color",
            color=color,
            auto_format=False,
        ),
        MessageStyle(
            offset=0,
            length=adjusted_length,
            style="bold",
            size="8",
            auto_format=False
        )
    ])
    client.send(Message(text=text, style=style), thread_id=thread_id, thread_type=thread_type, ttl=10000)

def stop_reo(client, message_object, thread_id, thread_type):
    global is_reo_running
    is_reo_running = False
    send_message_with_style(client, "Đã tha cho nó ", thread_id, thread_type, ttl=10000)

def handle_reo_command(message, message_object, thread_id, thread_type, author_id, client):
    global is_reo_running

    if author_id not in ADMIN:
        send_message_with_style(client, "⭕ Chửi chết cụ 1 con chó được tag \n❌ Mày không có quyền", thread_id, thread_type, ttl=10000)
        return

    command_parts = message.split()
    if len(command_parts) < 2:
        send_message_with_style(client, "Xin chị Rosy hãy tag con chó đó để em bem nó", thread_id, thread_type, ttl=60000)
        return

    action = command_parts[1].lower()

    if action == "stop":
        if not is_reo_running:
            send_message_with_style(client, "⚠️ Réo tên đã dừng lại", thread_id, thread_type, ttl=60000)
        else:
            stop_reo(client, message_object, thread_id, thread_type)
        return

    if action != "on":
        send_message_with_style(client, "Xin chị Rosy hãy tag con chó đó để em bem nó'.", thread_id, thread_type)
        return

    if message_object.mentions:
        tagged_users = message_object.mentions[0]['uid']
    else:
        send_message_with_style(client, "Xin chị Rosy hãy tag con chó đó để em bem nó", thread_id, thread_type)
        return

    try:
        with open("5c.txt", "r", encoding="utf-8") as file:
            Ngon = file.readlines()
    except FileNotFoundError:
        send_message_with_style(client, "Không tìm thấy file noidung.txt.", thread_id, thread_type, ttl=60000)
        return

    if not Ngon:
        send_message_with_style(client, "File noidung.txt không có nội dung nào để gửi.", thread_id, thread_type, ttl=60000)
        return

    is_reo_running = True

    def reo_loop():
        while is_reo_running:
            for noidung in Ngon:
                if not is_reo_running:
                    break
                mention = Mention(tagged_users, length=0, offset=0)
                # Gửi tin nhắn không dùng style (vì cần thêm mention)
                client.send(Message(text=f" {noidung}", mention=mention), thread_id, thread_type, ttl=5000)
                time.sleep(5)

    reo_thread = threading.Thread(target=reo_loop)
    reo_thread.start()

def get_mitaizl():
    return {
        'atk': handle_reo_command
    }
