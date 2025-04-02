from zlapi.models import Message, Mention, MessageStyle, MultiMsgStyle
from config import ADMIN
import time

ADMIN_ID = ADMIN

des = {
    'tác giả': "Rosy",
    'mô tả': "Gửi lời mời kết bạn đến tất cả thành viên trong nhóm.",
    'tính năng': [
        "🤖 Tự động gửi lời mời kết bạn cho tất cả thành viên trong nhóm.",
        "📩 Hiển thị số lượng lời mời đã gửi thành công.",
        "🎨 Tin nhắn phản hồi có màu sắc và định dạng in đậm.",
        "⏳ Thêm độ trễ giữa các yêu cầu để tránh bị giới hạn."
    ],
    'hướng dẫn sử dụng': [
        "💬 Nhập lệnh để bot tự động gửi lời mời kết bạn.",
        "📊 Xem số lượng thành viên và số lời mời đã gửi thành công.",
        "⚠️ Chỉ quản trị viên mới có thể sử dụng lệnh này."
    ]
}

def send_reply_with_style(client, text, message_object, thread_id, thread_type, ttl=None, color="#db342e"):
    """
    Gửi tin nhắn phản hồi với định dạng màu sắc và in đậm thông qua client.replyMessage.
    """
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

def send_message_with_style(client, text, thread_id, thread_type, ttl=None, color="#db342e"):
    """
    Gửi tin nhắn với định dạng màu sắc và in đậm thông qua client.send.
    """
    base_length = len(text)
    adjusted_length = base_length + 355
    style = MultiMsgStyle([
        MessageStyle(offset=0, length=adjusted_length, style="color", color=color, auto_format=False),
        MessageStyle(offset=0, length=adjusted_length, style="bold", size="8", auto_format=False)
    ])
    msg = Message(text=text, style=style)
    if ttl is not None:
        client.send(msg, thread_id, thread_type, ttl=ttl)
    else:
        client.send(msg, thread_id, thread_type)

def is_admin(author_id):
    return author_id == ADMIN_ID

def handle_add_group_command(message, message_object, thread_id, thread_type, author_id, client):
    action = "✅ "
    client.sendReaction(message_object, action, thread_id, thread_type, reactionType=75)

    if not is_admin(author_id):
        action = "🚫 ĐÉO QUYỀN"
        client.sendReaction(message_object, action, thread_id, thread_type, reactionType=75)
        return

    try:
        group_info = client.fetchGroupInfo(thread_id).gridInfoMap[thread_id]
        members = group_info.get('memVerList', [])
        total_members = len(members)
        successful_requests = 0

        print(f"Bắt đầu gửi lời mời kết bạn đến {total_members} thành viên...")

        start_message = "🔄 Đang gửi lời mời kết bạn cho tất cả thành viên trong nhóm. Vui lòng chờ..."
        send_reply_with_style(client, start_message, message_object, thread_id, thread_type)

        for mem in members:
            user_id = mem.split('_')[0]
            user_name = mem.split('_')[1]
            friend_request_message = f"Xin chào {user_name} ĐỒNG Ý KB IK"
            try:
                client.sendFriendRequest(userId=user_id, msg=friend_request_message)
                successful_requests += 1
                print(f"✔️ Đã gửi lời mời kết bạn đến: {user_name} ({user_id})")
            except Exception as e:
                print(f"❌ Lỗi khi gửi yêu cầu kết bạn cho {user_name}: {str(e)}")
            time.sleep(1)  # Không delay

        print(f"Hoàn thành! Đã gửi {successful_requests}/{total_members} lời mời kết bạn.")

        success_message = (
            f"✅ Đã gửi lời mời kết bạn đến tất cả thành viên trong nhóm.\n"
            f"📌 Tổng số thành viên trong nhóm: {total_members}\n"
            f"✔️ Số lời mời đã gửi thành công: {successful_requests}/{total_members}"
        )
        send_reply_with_style(client, success_message, message_object, thread_id, thread_type)

        action = "🎉"
        client.sendReaction(message_object, action, thread_id, thread_type, reactionType=75)

    except Exception as e:
        error_message = f"❌ Lỗi: {str(e)}"
        send_message_with_style(client, error_message, thread_id, thread_type)
        print(f"⚠️ Lỗi trong quá trình gửi lời mời kết bạn: {str(e)}")

        action = "⚠️"
        client.sendReaction(message_object, action, thread_id, thread_type, reactionType=75)

def get_mitaizl():
    return {
        'kb': handle_add_group_command
    }
