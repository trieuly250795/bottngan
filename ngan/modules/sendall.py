import re
import threading
import time
from zlapi.models import Message, ThreadType, MessageStyle, MultiMsgStyle

des = {
    'tác giả': "Rosy",
    'mô tả': "Gửi tin nhắn đến tất cả nhóm",
    'tính năng': [
        "📨 Gửi tin nhắn đến tất cả nhóm, trừ các nhóm bị loại trừ.",
        "🔒 Kiểm tra quyền admin trước khi thực hiện lệnh.",
        "🔍 Kiểm tra định dạng URL và xử lý các lỗi liên quan.",
        "🔗 Gửi tin nhắn với màu sắc và in đậm cho các phần không phải đường link.",
        "⏳ Gửi tin nhắn với khoảng cách thời gian cố định giữa các lần gửi."
    ],
    'hướng dẫn sử dụng': [
        "📩 Gửi lệnh sendall <nội dung> để gửi tin nhắn đến tất cả nhóm.",
        "📌 Ví dụ: sendall Chào các bạn! để gửi tin nhắn 'Chào các bạn!' đến tất cả nhóm.",
        "✅ Nhận thông báo trạng thái và kết quả gửi tin nhắn ngay lập tức."
    ]
}

# Danh sách admin và nhóm bị loại trừ
ADMIN_IDS = { "2670654904430771575" }
EXCLUDED_GROUPS = {"643794532760252296",  # (𝟭) 𝗕𝗮́ 𝗰𝗵𝘂̉ 𝗟𝗶𝗲̂𝗻 𝗾𝘂𝗮̂𝗻
                    "3874796700298410913",  # ZxZVN - Mods Paid
                    "8723832487296917622",  # ZxZVN - Free Mods
                    "2325851487330397984", 
                    "5851561702644739411"}

# Gửi tin nhắn với định dạng màu sắc và in đậm cho các phần không phải là đường link
def send_message_with_style(client, text, thread_id, thread_type, ttl=None, color="#db342e"):
    url_pattern = r'(https?://\S+)'
    parts = re.split(url_pattern, text)
    styles = []
    current_offset = 0

    # Áp dụng style cho phần không phải là đường link
    for part in parts:
        part_length = len(part)
        if re.match(url_pattern, part):  # Nếu đây là đường link, không áp dụng style
            pass
        else:
            if part_length > 0:
                styles.append(MessageStyle(offset=current_offset, length=part_length, style="color", color=color, auto_format=False))
                styles.append(MessageStyle(offset=current_offset, length=part_length, style="bold", size="8", auto_format=False))
        current_offset += part_length

    # Gửi tin nhắn với style đã áp dụng
    if styles:
        msg = Message(text=text, style=MultiMsgStyle(styles))
    else:
        msg = Message(text=text)
    
    if ttl is not None:
        client.sendMessage(msg, thread_id, thread_type, ttl=ttl)
    else:
        client.sendMessage(msg, thread_id, thread_type)

# Gửi phản hồi tin nhắn với định dạng màu sắc và in đậm
def send_reply_with_style(client, text, message_object, thread_id, thread_type, ttl=None, color="#db342e"):
    base_length = len(text)
    style = MultiMsgStyle([
        MessageStyle(offset=0, length=base_length, style="color", color=color, auto_format=False),
        MessageStyle(offset=0, length=base_length, style="bold", size="8", auto_format=False)
    ])
    msg = Message(text=text, style=style)

    if ttl is not None:
        client.replyMessage(msg, message_object, thread_id, thread_type, ttl=ttl)
    else:
        client.replyMessage(msg, message_object, thread_id, thread_type)

# Gửi phản hồi tin nhắn với phần prefix và content có định dạng khác nhau
def send_reply_with_custom_style(client, prefix, content, message_object, thread_id, thread_type, ttl=None, prefix_color="#db342e"):
    full_text = prefix + content
    prefix_length = len(prefix)
    style = MultiMsgStyle([
        MessageStyle(offset=0, length=prefix_length, style="color", color=prefix_color, auto_format=False),
        MessageStyle(offset=0, length=prefix_length, style="bold", size="8", auto_format=False)
    ])
    msg = Message(text=full_text, style=style)

    if ttl is not None:
        client.replyMessage(msg, message_object, thread_id, thread_type, ttl=ttl)
    else:
        client.replyMessage(msg, message_object, thread_id, thread_type)

# Hàm gửi tin nhắn tới tất cả các nhóm (trừ nhóm bị loại trừ)
def start_sendall(client, content):
    try:
        all_groups = client.fetchAllGroups()  # Lấy tất cả các nhóm mà bot có quyền truy cập
        allowed_thread_ids = [gid for gid in all_groups.gridVerMap.keys() if gid not in EXCLUDED_GROUPS]

        for thread_id in allowed_thread_ids:
            try:
                # Gửi tin nhắn đến các nhóm
                send_message_with_style(client, content, thread_id, ThreadType.GROUP, ttl=300000)
                print(f"Đã gửi tin nhắn đến nhóm {thread_id}")
                time.sleep(0.55)  # Thêm khoảng thời gian chờ giữa các lần gửi
            except Exception as e:
                print(f"Lỗi khi gửi tin nhắn đến nhóm {thread_id}: {e}")
    except Exception as e:
        print(f"Lỗi trong quá trình gửi tin nhắn: {e}")

# Hàm xử lý lệnh gửi tin nhắn đến tất cả nhóm
def handle_sendall_command(message, message_object, thread_id, thread_type, author_id, client):
    action = "✅"  # Gửi phản ứng ngay khi người dùng soạn đúng lệnh
    client.sendReaction(message_object, action, thread_id, thread_type, reactionType=75)

    try:
        # Kiểm tra quyền admin
        if author_id not in ADMIN_IDS:
            send_reply_with_style(client, "Bạn không có quyền thực hiện lệnh này.", message_object, thread_id, thread_type, ttl=30000)
            return

        # Kiểm tra xem lệnh có bắt đầu bằng "sendall" hoặc ",sendall" không
        if message.lower().startswith("sendall") or message.lower().startswith("sendtoall"):
            # Trích xuất nội dung sau lệnh
            if message.lower().startswith("sendall"):
                content = message[8:].strip()
            else:
                content = message[9:].strip()

            if not content:
                send_reply_with_style(client, "Vui lòng nhập nội dung để gửi!", message_object, thread_id, thread_type, ttl=30000)
                return

            # Khởi chạy gửi tin nhắn trong một luồng mới
            threading.Thread(target=start_sendall, args=(client, content), daemon=True).start()

            # Phản hồi cho người dùng biết lệnh đang được thực hiện
            prefix = "Đang gửi nội dung đến toàn bộ nhóm :\n "
            send_reply_with_custom_style(client, prefix, content, message_object, thread_id, thread_type, ttl=180000)
        else:
            print("Không phải lệnh sendall, bỏ qua.")
    except Exception as e:
        print(f"Lỗi khi xử lý lệnh sendall: {e}")

# Hàm trả về các lệnh mà bot có thể xử lý
def get_mitaizl():
    return {
        'sendtoall': handle_sendall_command
    }
