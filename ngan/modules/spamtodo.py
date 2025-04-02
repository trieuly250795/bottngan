import time
from zlapi.models import Message, ThreadType
from config import ADMIN

des = {
    'tác giả': "Rosy",
    'mô tả': "Spam công việc đến người dùng",
    'tính năng': [
        "📨 Gửi nhiệm vụ (To-Do) đến người dùng được tag với số lần lặp cụ thể.",
        "🔒 Kiểm tra quyền admin trước khi thực hiện lệnh.",
        "🔍 Xử lý cú pháp lệnh và kiểm tra giá trị hợp lệ.",
        "🔔 Thông báo lỗi cụ thể nếu cú pháp lệnh không chính xác hoặc giá trị không hợp lệ."
    ],
    'hướng dẫn sử dụng': [
        "📩 Gửi lệnh spamtodo @nguoitag <nội dung> <số lần> để gửi nhiệm vụ đến người dùng được tag.",
        "📌 Ví dụ: spamtodo @nguoitag Hoàn thành báo cáo 5 để gửi nhiệm vụ 'Hoàn thành báo cáo' đến người dùng được tag 5 lần.",
        "✅ Nhận thông báo trạng thái và kết quả gửi nhiệm vụ ngay lập tức."
    ]
}

def handle_spamtodo_command(message, message_object, thread_id, thread_type, author_id, client):
    if author_id not in ADMIN:
        client.replyMessage(
            Message(text="Quyền lồn biên giới"),
            message_object, thread_id, thread_type
        )
        return

    if not message_object.mentions:
        response_message = "Vui lòng tag người dùng để giao công việc."
        client.replyMessage(Message(text=response_message), message_object, thread_id, thread_type)
        return

    tagged_user = message_object.mentions[0]['uid']
    parts = message.split(' ', 2)
    
    if len(parts) < 3:
        response_message = "Vui lòng cung cấp nội dung và số lần spam công việc. Ví dụ: spamtodo @nguoitag Nội dung công việc 5"
        client.replyMessage(Message(text=response_message), message_object, thread_id, thread_type)
        return

    try:
        content_and_count = message.split(' ', 2)[2]
        content, num_repeats_str = content_and_count.rsplit(' ', 1)
        num_repeats = int(num_repeats_str)
    except ValueError:
        response_message = "Số lần phải là một số nguyên."
        client.replyMessage(Message(text=response_message), message_object, thread_id, thread_type)
        return

    for _ in range(num_repeats):
        client.sendToDo(
            message_object=message_object,
            content=content,
            assignees=[tagged_user],
            thread_id=tagged_user,
            thread_type=ThreadType.USER,
            due_date=-1,
            description="Bot Dzi"
        )
        time.sleep(0.2)

def get_mitaizl():
    return {
        'spamtodo': handle_spamtodo_command
    }
