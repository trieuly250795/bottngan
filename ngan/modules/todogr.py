import time
from zlapi.models import Message, ThreadType
from config import ADMIN

des = {
    'version': "1.0.2",
    'credits': "Nguyễn Đức Tài",
    'description': "Gửi spam công việc vào nhóm và riêng tư cho những người được tag"
}

def handle_spamtodo_command(message, message_object, thread_id, thread_type, author_id, client):
    if author_id not in ADMIN:
        client.replyMessage(
            Message(text="Mày có quyền lồn gì mà đòi xài"),
            message_object, thread_id, thread_type
        )
        return

    if not message_object.mentions:
        response_message = "Vui lòng tag người dùng để giao công việc."
        client.replyMessage(Message(text=response_message), message_object, thread_id, thread_type)
        return

    # Lấy danh sách UID người được tag
    tagged_users = [mention['uid'] for mention in message_object.mentions]

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

    # Gửi todo trong nhóm
    for _ in range(num_repeats):
        client.sendToDo(
            message_object=message_object,
            content=content,
            assignees=tagged_users,  # Chỉ định những người được tag
            thread_id=thread_id,
            thread_type=thread_type,
            due_date=-1,
            description="BOT MITAIZL-PROJECT"
        )
        time.sleep(0.001)

def get_mitaizl():
    return {
        'todogr': handle_spamtodo_command
    }