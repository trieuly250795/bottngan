from zlapi.models import *
import os
import time
import threading
from zlapi.models import MessageStyle, MultiMsgStyle  # Cần import MultiMsgStyle để định dạng style
from config import ADMIN

des = {
    'tác giả': "Rosy",
    'mô tả': "Tự động đổi tên nhóm Zalo liên tục bằng nội dung từ file 'noidung.txt'.",
    'tính năng': [
        "🔍 Kiểm tra quyền hạn của người dùng trước khi thực hiện lệnh",
        "🔄 Hỗ trợ bật/tắt tính năng đổi tên nhóm theo lệnh",
        "📄 Đọc nội dung từ file 'noidung.txt' để sử dụng làm tên nhóm",
        "⏳ Tự động đổi tên nhóm liên tục với khoảng cách thời gian ngắn",
        "🛑 Hỗ trợ dừng quá trình đổi tên khi có lệnh từ quản trị viên"
    ],
    'hướng dẫn sử dụng': [
        "📩 Gửi lệnh atknamegr [on/stop] để bật hoặc tắt tính năng đổi tên nhóm.",
        "📌 Ví dụ: atknamegr on để bắt đầu đổi tên nhóm, atknamegr stop để dừng quá trình đổi tên.",
        "✅ Nhận thông báo trạng thái và kết quả ngay lập tức."
    ]
}

is_reo_running = False

def send_message_with_style(client, text, thread_id, thread_type, color="#db342e"):
    """
    Gửi tin nhắn với định dạng màu sắc và in đậm.
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
    client.send(Message(text=text, style=style), thread_id=thread_id, thread_type=thread_type)

def stop_reo(client, message_object, thread_id, thread_type):
    global is_reo_running
    is_reo_running = False
    send_message_with_style(client, "Tạm tha lũ gay", thread_id, thread_type)

def handle_reonamegr_command(message, message_object, thread_id, thread_type, author_id, client):
    global is_reo_running
    if author_id not in ADMIN:
        send_message_with_style(
            client,
            "⭕ Lệnh dùng tấn công tên nhóm\n❌ Bạn không có quyền sử dụng ",
            thread_id,
            thread_type
        )
        return

    command_parts = message.split()
    if len(command_parts) < 2:
        send_message_with_style(
            client,
            "⭕ Vui lòng chỉ định lệnh hợp lệ (vd: atknamegr on hoặc atknamegr stop).",
            thread_id,
            thread_type
        )
        return

    action = command_parts[1].lower()
    if action == "stop":
        if not is_reo_running:
            send_message_with_style(client, "tạm tha lũ gay", thread_id, thread_type)
        else:
            stop_reo(client, message_object, thread_id, thread_type)
        return

    if action != "on":
        send_message_with_style(
            client,
            "Vui lòng chỉ định lệnh 'on' hoặc 'stop'.",
            thread_id,
            thread_type
        )
        return

    try:
        with open("noidung.txt", "r", encoding="utf-8") as file:
            Ngon = file.readlines()
    except FileNotFoundError:
        send_message_with_style(
            client,
            "Không tìm thấy file noidung.txt.",
            thread_id,
            thread_type
        )
        return

    if not Ngon:
        send_message_with_style(
            client,
            "File noidung.txt không có nội dung nào để gửi.",
            thread_id,
            thread_type
        )
        return

    is_reo_running = True

    def reo_loop():
        while is_reo_running:
            for noidung in Ngon:
                if not is_reo_running:
                    break
                client.changeGroupName(noidung, thread_id)
                time.sleep(0.5)

    reo_thread = threading.Thread(target=reo_loop)
    reo_thread.start()

def get_mitaizl():
    return {
        'atknamegr': handle_reonamegr_command
    }
