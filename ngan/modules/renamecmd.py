import os
import requests
from config import ADMIN
from zlapi.models import Message, MessageStyle, MultiMsgStyle
import time

ADMIN_ID = ADMIN

des = {
    'tác giả': "Rosy",
    'mô tả': "Quản lý commands",
    'tính năng': [
        "🛠️ Xóa hoặc đổi tên các lệnh hiện có.",
        "📨 Gửi phản hồi với kết quả xóa hoặc đổi tên lệnh.",
        "🔒 Chỉ quản trị viên mới có quyền sử dụng lệnh này."
    ],
    'hướng dẫn sử dụng': [
        "📩 Gửi lệnh để quản lý các commands trong hệ thống.",
        "📌 Sử dụng cú pháp: renamecmd del <command_name> để xóa lệnh.",
        "📌 Sử dụng cú pháp: renamecmd rename <old_command_name> <new_command_name> để đổi tên lệnh.",
        "✅ Nhận thông báo trạng thái xóa hoặc đổi tên lệnh ngay lập tức."
    ]
}

def send_reply_with_style(client, text, message_object, thread_id, thread_type, ttl=None, color="#db342e"):
    """ Gửi tin nhắn phản hồi với định dạng màu sắc và in đậm. """
    base_length = len(text)
    adjusted_length = base_length + 355
    style = MultiMsgStyle([
        MessageStyle(offset=0, length=adjusted_length, style="color", color=color, auto_format=False),
        MessageStyle(offset=0, length=adjusted_length, style="bold", size="8", auto_format=False)
    ])
    msg = Message(text=text, style=style)
    if ttl is not None:
        client.replyMessage(msg, message_object, thread_id, thread_type, ttl=ttl)
    else:
        client.replyMessage(msg, message_object, thread_id, thread_type)

def is_admin(author_id):
    return author_id == ADMIN_ID

def handle_cmdl_command(message, message_object, thread_id, thread_type, author_id, client):
    lenhcanlay = message.split()
    if len(lenhcanlay) < 3:
        send_reply_with_style(
            client, "Cú pháp không hợp lệ. Vui lòng nhập lệnh đúng theo mẫu:\n"
                    " - Xóa lệnh: renamecmd del <command_name>\n"
                    " - Đổi tên lệnh: renamecmd rename <old_command_name> <new_command_name>",
            message_object, thread_id, thread_type
        )
        return

    command_action = lenhcanlay[1].strip()
    command_name = lenhcanlay[2].strip()

    if command_action == "del":
        if not is_admin(author_id):
            send_reply_with_style(
                client, "Bạn không đủ quyền hạn để sử dụng lệnh này.", message_object, thread_id, thread_type
            )
            return
        file_path = f"modules/{command_name}.py"
        if os.path.exists(file_path):
            os.remove(file_path)
            response_message = (
                f"Lệnh '{command_name}' đã được xóa.\n"
                "Cách sử dụng: renamecmd del <command_name>"
            )
        else:
            response_message = (
                f"Lệnh '{command_name}' không tồn tại. Kiểm tra lại tên lệnh.\n"
                "Cách sử dụng: renamecmd del <command_name>"
            )
    elif command_action == "rename":
        if len(lenhcanlay) < 4:
            send_reply_with_style(
                client, "Vui lòng cung cấp tên mới cho lệnh.\nCách sử dụng: renamecmd rename <old_command_name> <new_command_name>",
                message_object, thread_id, thread_type
            )
            return

        new_command_name = lenhcanlay[3].strip()
        if not is_admin(author_id):
            send_reply_with_style(
                client, "Bạn không đủ quyền hạn để sử dụng lệnh này.", message_object, thread_id, thread_type
            )
            return

        old_file_path = f"modules/{command_name}.py"
        new_file_path = f"modules/{new_command_name}.py"
        if os.path.exists(old_file_path):
            os.rename(old_file_path, new_file_path)
            response_message = (
                f"Lệnh '{command_name}' đã được đổi tên thành '{new_command_name}'.\n"
                "Cách sử dụng: renamecmd rename <old_command_name> <new_command_name>"
            )
        else:
            response_message = (
                f"Lệnh '{command_name}' không tồn tại. Kiểm tra lại tên lệnh.\n"
                "Cách sử dụng: renamecmd rename <old_command_name> <new_command_name>"
            )
    else:
        response_message = (
            "Cú pháp không hợp lệ. Vui lòng sử dụng 'del' hoặc 'rename'.\n"
            "Cách sử dụng:\n"
            " - Xóa lệnh: renamecmd del <command_name>\n"
            " - Đổi tên lệnh: renamecmd rename <old_command_name> <new_command_name>"
        )

    send_reply_with_style(client, response_message, message_object, thread_id, thread_type)

def get_mitaizl():
    return {
        'renamecmd': handle_cmdl_command
    }
