from zlapi.models import Message, Mention, ZaloAPIException, ThreadType
from config import ADMIN
import time

des = {
    'tác giả': "Rosy",
    'mô tả': "Tự động tham gia nhóm Zalo từ liên kết và gửi tin nhắn nhiều lần để spam.",
    'tính năng': [
        "🔍 Kiểm tra quyền hạn của người dùng trước khi thực hiện lệnh",
        "🔗 Xác minh và kiểm tra tính hợp lệ của liên kết nhóm Zalo",
        "🚀 Tự động tham gia nhóm từ liên kết do người dùng cung cấp",
        "📊 Lấy thông tin nhóm sau khi tham gia thành công",
        "💬 Gửi tin nhắn spam với nội dung và số lần tùy chỉnh"
    ],
    'hướng dẫn sử dụng': [
        "📩 Gửi lệnh attack [liên kết nhóm] [tin nhắn] [số lần spam] để thực hiện lệnh.",
        "📌 Ví dụ: attack https://zalo.me/g/example Admin duyệt mình vào nhóm với ạ 5 để tham gia nhóm và gửi tin nhắn spam 5 lần.",
        "✅ Nhận thông báo trạng thái và kết quả ngay lập tức."
    ]
}

def handle_spnhom_command(message, message_object, thread_id, thread_type, author_id, client):
    if author_id not in ADMIN:
        client.replyMessage(
            Message(text="🚫 Bạn không có quyền sử dụng lệnh này!"), 
            message_object, thread_id, thread_type
        )
        return
    
    try:
        parts = message.split(" ", 2)
        if len(parts) < 2:
            client.replyMessage(
                Message(text="⚠️ Vui lòng cung cấp link nhóm!"), 
                message_object, thread_id, thread_type, ttl=10000
            )
            return
            
        url = parts[1].strip()
        if not url.startswith("https://zalo.me/"):
            client.replyMessage(
                Message(text="⛔ Link không hợp lệ! Link phải bắt đầu bằng https://zalo.me/"), 
                message_object, thread_id, thread_type
            )
            return
        
        spam_message = "Admin duyệt mình vào nhóm với ạ "  # Mặc định nội dung spam
        spam_count = 2  # Mặc định spam 2 lần
        
        if len(parts) >= 3:
            extra_parts = parts[2].rsplit(" ", 1)
            if len(extra_parts) == 2 and extra_parts[1].isdigit():
                spam_message = extra_parts[0]
                spam_count = int(extra_parts[1])
            else:
                spam_message = parts[2]
        
        client.replyMessage(
            Message(text="🔄 Đã nhận lệnh tấn công cộng đồng..."),
            message_object, thread_id, thread_type, ttl=5000
        )
        time.sleep(2)
        join_result = client.joinGroup(url)
        if not join_result:
            raise ZaloAPIException("Không thể tham gia nhóm")
        
        client.replyMessage(
            Message(text="✅ Đã tham gia nhóm! Đang lấy thông tin nhóm..."),
            message_object, thread_id, thread_type, ttl=10000
        )
        time.sleep(2)
        group_info = client.getiGroup(url)
        if not isinstance(group_info, dict) or 'groupId' not in group_info:
            raise ZaloAPIException("Không lấy được thông tin nhóm")
        
        group_id = group_info['groupId']
        client.replyMessage(
            Message(text=f"📢 Bắt đầu spam {spam_count} lần..."),
            message_object, thread_id, thread_type, ttl=60000
        )
        time.sleep(2)
        
        for i in range(1, spam_count + 1):
            mention = Mention("-1", length=len(spam_message), offset=0) 
            client.send(
                Message(text=f"{spam_message}", mention=mention),
                group_id, ThreadType.GROUP, ttl=10
            )
            time.sleep(1.5)
        
        client.replyMessage(
            Message(text=f"✅ Đã hoàn thành spam {spam_count} lần\n📌 ID nhóm: {group_id}"),
            message_object, thread_id, thread_type, ttl=180000
        )
        
    except ZaloAPIException as e:
        client.replyMessage(
            Message(text=f"❌ Lỗi API: {str(e)}"),
            message_object, thread_id, thread_type
        )
    except Exception as e:
        client.replyMessage(
            Message(text=f"❌ Lỗi: {str(e)}"),
            message_object, thread_id, thread_type
        )

def get_mitaizl():
    return {
        'attack': handle_spnhom_command
    }
