from zlapi.models import Message, Mention, MultiMsgStyle, MessageStyle
from config import ADMIN
import time

ADMIN_ID = ADMIN

des = {
    'tác giả': "Rosy",
    'mô tả': "Tag tên thành viên trong nhóm",
    'tính năng': [
        "📨 Tag tên tất cả các thành viên trong nhóm.",
        "🔒 Kiểm tra quyền admin trước khi thực hiện lệnh.",
        "🔍 Lấy thông tin nhóm và thành viên.",
        "🔔 Thông báo lỗi cụ thể nếu cú pháp lệnh không chính xác hoặc giá trị không hợp lệ."
    ],
    'hướng dẫn sử dụng': [
        "📩 Gửi lệnh tagmem để tag tên tất cả thành viên trong nhóm.",
        "📌 Ví dụ: tagmem để tag tên tất cả thành viên trong nhóm.",
        "✅ Nhận thông báo trạng thái và kết quả gửi thông báo ngay lập tức."
    ]
}

def is_admin(author_id):
    return author_id == ADMIN_ID

def handle_checkid_command(message, message_object, thread_id, thread_type, author_id, client):
    try:
        group_info = client.fetchGroupInfo(thread_id).gridInfoMap[thread_id]
        creator_id = group_info.get('creatorId')
        admin_ids = group_info.get('adminIds', [])
        
        # If admin_ids is None, default to an admin ID
        if admin_ids is None:
            admin_ids = [841772837717522604]  # Replace with a valid admin ID
        
        # Convert to a set for easier management
        all_admin_ids = set(admin_ids)
        all_admin_ids.add(creator_id)
        all_admin_ids.update(ADMIN)  # Ensure ADMIN is always a set
        
        # Check if the author is an admin
        if author_id not in all_admin_ids:
            msg = "• Bạn Không Có Quyền! Chỉ có admin mới có thể sử dụng được lệnh này."
            styles = MultiMsgStyle([
                MessageStyle(offset=0, length=2, style="color", color="#f38ba8", auto_format=False),
                MessageStyle(offset=2, length=len(msg)-2, style="color", color="#cdd6f4", auto_format=False),
                MessageStyle(offset=0, length=len(msg), style="font", size="11", auto_format=False)
            ])
            client.replyMessage(Message(text=msg, style=styles), message_object, thread_id, thread_type, ttl=20000)
            return

        # Fetch group members
        data = client.fetchGroupInfo(groupId=thread_id)
        members = data['gridInfoMap'][str(thread_id)]['memVerList']
        
        messages = []
        for mem in members:
            try:
                user_id, user_name = mem.split('_')  # Assuming mem is in "user_id_user_name" format
                mention = Mention(uid=user_id, offset=0, length=len(user_name))
                messages.append(Message(text=f" {user_name}", mention=mention))
            except ValueError:
                # Handle case where splitting fails (perhaps log or skip invalid entries)
                print(f"Invalid member format: {mem}")
                continue
        
        # Send tagged messages to all members
        for msg in messages:
            client.send(msg, thread_id=thread_id, thread_type=thread_type)
            time.sleep(1)  # Add a small delay to avoid spammy behavior

    except Exception as e:
        error_message = f"Đã xảy ra lỗi: {str(e)}"
        client.send(Message(text=error_message), thread_id=thread_id, thread_type=thread_type)

def get_mitaizl():
    """ Trả về một dictionary ánh xạ lệnh 'tagmem' tới hàm xử lý tương ứng. """
    return {
        'tagmem': handle_checkid_command
    }
