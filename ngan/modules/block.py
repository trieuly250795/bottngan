from zlapi.models import Message
from config import ADMIN

des = {
    'tác giả': "Rosy",
    'mô tả': "Module hỗ trợ admin chặn hoặc mở chặn người dùng trong bot.",
    'tính năng': [
        "🚫 Chặn người dùng bằng UID",
        "✅ Mở chặn người dùng bằng UID",
        "🔒 Chỉ admin mới có quyền sử dụng lệnh",
        "⚠️ Kiểm tra tính hợp lệ của UID trước khi thực hiện",
        "📌 Phản hồi ngay lập tức khi thao tác thành công hoặc thất bại",
        "🔧 Xử lý lỗi khi chặn/mở chặn không thành công"
    ],
    'hướng dẫn sử dụng': "Dùng lệnh 'block' hoặc 'unblock' kèm theo UID của người dùng. Ví dụ: 'block 123456789' hoặc 'unblock 123456789'."
}

# Handle blocking a user by UID
def handle_block_user_by_uid(message, message_object, thread_id, thread_type, author_id, client):
    # Gửi phản ứng ngay khi người dùng soạn đúng lệnh
    action = "✅"
    client.sendReaction(message_object, action, thread_id, thread_type, reactionType=75)
    
    # Verify admin privileges
    if author_id not in ADMIN:
        client.replyMessage(Message(text="Bạn không có quyền sử dụng lệnh này."), message_object, thread_id, thread_type)
        return
    
    # Parse command input
    parts = message.split(' ', 2)
    if len(parts) < 2:
        client.replyMessage(Message(text="Vui lòng cung cấp UID người dùng để chặn.\nVí dụ: block UID"), message_object, thread_id, thread_type)
        return
    
    user_id = parts[1]
    if not user_id.isdigit():
        client.replyMessage(Message(text="UID không hợp lệ. Vui lòng nhập UID hợp lệ."), message_object, thread_id, thread_type)
        return
    
    try:
        # Block the user
        client.blockUser(user_id)
        client.replyMessage(Message(text=f"Đã chặn người dùng với UID {user_id}."), message_object, thread_id, thread_type)
    except Exception as e:
        client.replyMessage(Message(text=f"Không thể chặn người dùng với UID {user_id}. Lỗi: {str(e)}"), message_object, thread_id, thread_type)

# Handle unblocking a user by UID
def handle_unblock_user_by_uid(message, message_object, thread_id, thread_type, author_id, client):
    # Gửi phản ứng ngay khi người dùng soạn đúng lệnh
    action = "✅"
    client.sendReaction(message_object, action, thread_id, thread_type, reactionType=75)
    
    # Verify admin privileges
    if author_id not in ADMIN:
        client.replyMessage(Message(text="Bạn không có quyền sử dụng lệnh này."), message_object, thread_id, thread_type)
        return
    
    # Parse command input
    parts = message.split(' ', 2)
    if len(parts) < 2:
        client.replyMessage(Message(text="Vui lòng cung cấp UID người dùng để mở chặn.\nVí dụ: unblock UID"), message_object, thread_id, thread_type)
        return
    
    user_id = parts[1]
    if not user_id.isdigit():
        client.replyMessage(Message(text="UID không hợp lệ. Vui lòng nhập UID hợp lệ."), message_object, thread_id, thread_type)
        return
    
    try:
        # Unblock the user
        client.unblockUser(user_id)
        client.replyMessage(Message(text=f"Đã mở chặn người dùng với UID {user_id}."), message_object, thread_id, thread_type)
    except Exception as e:
        client.replyMessage(Message(text=f"Không thể mở chặn người dùng với UID {user_id}. Lỗi: {str(e)}"), message_object, thread_id, thread_type)

# Register commands with the bot
def get_mitaizl():
    return {
        'block': handle_block_user_by_uid,
        'unblock': handle_unblock_user_by_uid
    }
