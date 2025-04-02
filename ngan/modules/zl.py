from zlapi import ZaloAPIException
from zlapi.models import Message, MessageStyle, MultiMsgStyle
from datetime import datetime
from config import PREFIX

des = {
    'tác giả': "Rosy",
    'mô tả': "Lấy thông tin tài khoản Zalo",
    'tính năng': [
        "📨 Lấy thông tin tài khoản Zalo của người dùng qua UID hoặc mention.",
        "🔍 Kiểm tra thông tin người dùng từ unchanged_profiles hoặc changed_profiles.",
        "📅 Hiển thị ngày tham gia Zalo của người dùng.",
        "🔔 Thông báo lỗi cụ thể nếu không thể lấy thông tin hoặc cú pháp lệnh không hợp lệ."
    ],
    'hướng dẫn sử dụng': [
        "📩 Gửi lệnh zl để lấy thông tin tài khoản Zalo của người dùng.",
        "📌 Ví dụ: zl hoặc zl <UID> hoặc mention người dùng để lấy thông tin tài khoản Zalo.",
        "✅ Nhận thông báo trạng thái và kết quả ngay lập tức."
    ]
}

def send_message_with_style(client, text, thread_id, thread_type, ttl=60000, color="#db342e"):
    """Gửi tin nhắn với định dạng màu sắc và in đậm."""
    base_length = len(text)
    adjusted_length = base_length + 355  # Tăng độ dài để đảm bảo style được áp dụng đầy đủ
    style = MultiMsgStyle([
        MessageStyle(offset=0, length=adjusted_length, style="color", color=color, auto_format=False),
        MessageStyle(offset=0, length=adjusted_length, style="bold", size="8", auto_format=False)
    ])
    msg = Message(text=text, style=style)
    client.send(msg, thread_id=thread_id, thread_type=thread_type, ttl=ttl)

def handle_infouser_command(message, message_object, thread_id, thread_type, author_id, client):
    action = "✅"
    client.sendReaction(message_object, action, thread_id, thread_type, reactionType=75)
    msg_error = "🔴 Không thể lấy thông tin tài khoản Zalo!"
    try:
        # Nếu có mention thì lấy UID từ mention
        if message_object.mentions:
            author_id = message_object.mentions[0]['uid']
        # Nếu tin nhắn có chứa UID (định dạng số) sau ký tự thứ 3
        elif message[3:].strip().isnumeric():
            author_id = message[3:].strip()
        # Nếu tin nhắn chỉ chứa lệnh (vd: {PREFIX}zl) thì sử dụng UID của người gửi
        elif message.strip() == f"{PREFIX}zl":
            author_id = author_id
        else:
            send_message_with_style(client, msg_error, thread_id, thread_type)
            return

        try:
            info = client.fetchUserInfo(author_id)
            # Lấy thông tin từ unchanged_profiles hoặc changed_profiles
            info = info.unchanged_profiles or info.changed_profiles
            info = info[str(author_id)]
            userName = info.zaloName if info.zaloName else "Người dùng"
            createTime = info.createdTs
            if isinstance(createTime, int):
                createTime = datetime.fromtimestamp(createTime).strftime("%d/%m/%Y")
            else:
                createTime = "Không xác định"
            msg = f'📅 Người dùng "{userName}" đã tham gia Zalo từ {createTime}'
            send_message_with_style(client, msg, thread_id, thread_type)
        except ZaloAPIException:
            send_message_with_style(client, msg_error, thread_id, thread_type)
        except Exception:
            send_message_with_style(client, "Đã xảy ra lỗi", thread_id, thread_type)
    except Exception:
        send_message_with_style(client, "Đã xảy ra lỗi", thread_id, thread_type)

def get_mitaizl():
    return {
        'zl': handle_infouser_command
    }
