from datetime import datetime
import time
from zlapi.models import Message, MessageStyle, MultiMsgStyle

des = {
    'tác giả': "Rosy",
    'mô tả': "Mời toàn bộ bạn bè của bot vào nhóm",
    'tính năng': [
        "👥 Duyệt qua toàn bộ danh sách bạn bè của bot.",
        "🚀 Tự động mời bạn bè vào nhóm thông qua addUsersToGroup.",
        "🔔 Thông báo kết quả sau khi thực hiện mời.",
        "⏱️ Có độ trễ 0.5 giây giữa các lời mời để tránh bị hạn chế từ server.",
        "🔔 Thông báo khi bắt đầu và hoàn tất mời bạn bè."
    ],
    'hướng dẫn sử dụng': [
        "📩 Gửi lệnh inviteall để mời tất cả bạn bè của bot vào nhóm.",
        "✅ Nhận thông báo trạng thái mời thành công và thất bại."
    ]
}

def send_message_with_style(client, text, thread_id, thread_type, ttl=30000, color="#db342e"):
    """Gửi tin nhắn với định dạng màu sắc và in đậm, TTL mặc định là 30000."""
    base_length = len(text)
    adjusted_length = base_length + 355  # Tăng độ dài để đảm bảo style được áp dụng đầy đủ
    style = MultiMsgStyle([
        MessageStyle(offset=0, length=adjusted_length, style="color", color=color, auto_format=False),
        MessageStyle(offset=0, length=adjusted_length, style="bold", size="8", auto_format=False)
    ])
    msg = Message(text=text, style=style)
    client.sendMessage(msg, thread_id, thread_type, ttl=ttl)

def handle_invite_all(message, message_object, thread_id, thread_type, author_id, client):
    """Duyệt qua toàn bộ danh sách bạn bè của bot và mời họ vào nhóm."""
    # Gửi phản ứng khi nhận lệnh
    client.sendReaction(message_object, "✅", thread_id, thread_type, reactionType=75)
    
    # Thông báo bắt đầu mời
    start_msg = "⏳ Đang bắt đầu mời tất cả bạn bè vào nhóm. Vui lòng chờ..."
    send_message_with_style(client, start_msg, thread_id, thread_type, color="#FFA500")
    
    try:
        friends = client.fetchAllFriends()
    except Exception as e:
        error_msg = f"Đã xảy ra lỗi khi lấy danh sách bạn bè: {e}"
        send_message_with_style(client, error_msg, thread_id, thread_type)
        return

    total_friends = len(friends)
    success_count = 0
    failed_count = 0
    failed_ids = []

    for friend in friends:
        friend_id = friend.userId
        try:
            client.addUsersToGroup(friend_id, thread_id)
            success_count += 1
            time.sleep(0.5)  # Độ trễ 0.5 giây giữa các lời mời
        except Exception as e:
            failed_count += 1
            failed_ids.append(friend_id)
    
    result_msg = (
        f"👥 Tổng số bạn bè: {total_friends}\n"
        f"✅ Mời thành công: {success_count}\n"
        f"❌ Mời thất bại: {failed_count}"
    )
    if failed_ids:
        result_msg += f"\nDanh sách ID mời thất bại: {', '.join(map(str, failed_ids))}"
    
    finish_msg = f"✅✅ Mời bạn bè vào nhóm hoàn tất:\n{result_msg}"
    send_message_with_style(client, finish_msg, thread_id, thread_type, color="#000000")

def get_mitaizl():
    """Trả về mapping các lệnh của bot."""
    return {
        'inviteall': handle_invite_all
    }
