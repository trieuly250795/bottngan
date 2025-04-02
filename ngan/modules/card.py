from zlapi.models import Message, ThreadType

des = {
    'tác giả': "Rosy",
    'mô tả': "Lấy danh thiếp người dùng hoặc danh thiếp người được tag.",
    'tính năng': [
        "✅ Gửi phản ứng xác nhận khi lệnh được nhập đúng.",
        "📇 Lấy thông tin danh thiếp từ người dùng được tag hoặc chính người dùng nếu không có tag.",
        "🔗 Sử dụng thông tin người dùng để tạo danh thiếp và hiển thị ảnh đại diện.",
        "❗ Hiển thị thông báo lỗi nếu không lấy được thông tin hoặc người dùng không có ảnh đại diện."
    ],
    'hướng dẫn sử dụng': ["Dùng lệnh 'card' để lấy danh thiếp của bạn hoặc tag người khác vào tin nhắn."]
}

def handle_cardinfo_command(message, message_object, thread_id, thread_type, author_id, client):
    # Gửi phản ứng ngay khi người dùng soạn đúng lệnh
    action = "✅"
    client.sendReaction(message_object, action, thread_id, thread_type, reactionType=75)

    userId = message_object.mentions[0]['uid'] if message_object.mentions else author_id
    
    if not userId:
        client.send(
            Message(text="Không tìm thấy người dùng."),
            thread_id=thread_id,
            thread_type=thread_type
        )
        return
    
    
    user_info = client.fetchUserInfo(userId).changed_profiles.get(userId)
    
    if not user_info:
        client.send(
            Message(text="Không thể lấy thông tin người dùng."),
            thread_id=thread_id,
            thread_type=thread_type
        )
        return
    
    avatarUrl = user_info.avatar
    
    if not avatarUrl:
        client.send(
            Message(text="Người dùng này không có ảnh đại diện."),
            thread_id=thread_id,
            thread_type=thread_type, ttl=60000
        )
        return
    
    client.sendBusinessCard(userId=userId, qrCodeUrl=avatarUrl, thread_id=thread_id, thread_type=thread_type, ttl=60000)

def get_mitaizl():
    return {
        'card': handle_cardinfo_command
    }
