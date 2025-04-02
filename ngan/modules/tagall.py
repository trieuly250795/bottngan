from zlapi.models import Message, Mention
from config import ADMIN

des = {
    'tác giả': "Rosy",
    'mô tả': "Thông báo cho toàn bộ nhóm",
    'tính năng': [
        "📨 Gửi thông báo cho toàn bộ nhóm với nội dung được chỉ định.",
        "🔒 Kiểm tra quyền admin trước khi thực hiện lệnh.",
        "🔍 Xử lý cú pháp lệnh và kiểm tra giá trị hợp lệ.",
        "🔔 Thông báo lỗi cụ thể nếu cú pháp lệnh không chính xác hoặc giá trị không hợp lệ."
    ],
    'hướng dẫn sử dụng': [
        "📩 Gửi lệnh tagall <nội dung> để gửi thông báo cho toàn bộ nhóm.",
        "📌 Ví dụ: tagall Chào các bạn! để gửi thông báo 'Chào các bạn!' cho toàn bộ nhóm.",
        "✅ Nhận thông báo trạng thái và kết quả gửi thông báo ngay lập tức."
    ]
}

def handle_tagall_command(message, message_object, thread_id, thread_type, author_id, client):
    # Check if author is an admin
    if author_id not in ADMIN:
        client.replyMessage(
            Message(text="🚫 **Bạn không có quyền để thực hiện điều này!**"),
            message_object,
            thread_id,
            thread_type
        )
        return

    # Check if content is provided
    noidung = message.split()
    if len(noidung) < 2:
        error_message = Message(text="Vui lòng nhập nội dung cần thông báo.")
        client.sendMessage(error_message, thread_id, thread_type)
        return

    # Prepare the content to send
    noidung1 = " ".join(noidung[1:])
    
    # Mention all members (consider updating this with specific logic for mentioning all)
    mention = Mention("-1", length=len(noidung1), offset=0)  # Check if "-1" is valid for mentioning all
    content = f"{noidung1}"

    # Send the message with mention
    client.replyMessage(
        Message(text=content, mention=mention),
        message_object,
        thread_id,
        thread_type
    )

def get_mitaizl():
    return {
        'tagall': handle_tagall_command
    }
