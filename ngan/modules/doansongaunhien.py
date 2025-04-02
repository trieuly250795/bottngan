import random
from zlapi.models import Message

des = {
    'tác giả': "Rosy",
    'mô tả': "Trò chơi đoán số",
    'tính năng': [
        "🎲 Bắt đầu trò chơi mới bằng cách chọn một số ngẫu nhiên giữa min và max.",
        "🔍 Xử lý dự đoán của người chơi trong trò chơi hiện tại.",
        "📝 Lưu trạng thái trò chơi cho từng thread.",
        "🔔 Thông báo lỗi cụ thể nếu cú pháp lệnh không chính xác hoặc giá trị không hợp lệ."
    ],
    'hướng dẫn sử dụng': [
        "📩 Gửi lệnh ngaunhien <min> <max> để bắt đầu trò chơi mới.",
        "📩 Gửi lệnh doan <số đoán của bạn> để đoán số trong trò chơi hiện tại.",
        "📌 Ví dụ: ngaunhien 1 100 để bắt đầu trò chơi mới với số ngẫu nhiên từ 1 đến 100, doan 50 để đoán số 50 trong trò chơi hiện tại.",
        "✅ Nhận thông báo trạng thái và kết quả ngay lập tức."
    ]
}

# Dictionary lưu trạng thái trò chơi theo từng thread
active_games = {}

def handle_random_command(message, message_object, thread_id, thread_type, author_id, client):
    """
    Bắt đầu trò chơi mới: Bot chọn một số ngẫu nhiên giữa min và max.
    Cú pháp: random <min> <max>
    """
    args = message.split()
    if len(args) != 3:
        error_message = Message(text="Cú pháp không hợp lệ. Vui lòng nhập: random <min> <max>")
        client.replyMessage(error_message, message_object, thread_id, thread_type)
        return

    try:
        min_value = int(args[1])
        max_value = int(args[2])
        if min_value >= max_value:
            error_message = Message(text="Giá trị min phải nhỏ hơn max.")
            client.replyMessage(error_message, message_object, thread_id, thread_type)
            return

        secret_number = random.randint(min_value, max_value)
        # Lưu trạng thái trò chơi cho thread hiện tại
        active_games[thread_id] = {
            'secret': secret_number,
            'min': min_value,
            'max': max_value
        }

        response_message = (
            f"Tôi đã chọn một số ngẫu nhiên giữa {min_value} và {max_value}.\n"
            "Hãy đoán số đó bằng cách nhập: guess <số đoán của bạn>"
        )
        message_to_send = Message(text=response_message)
        client.replyMessage(message_to_send, message_object, thread_id, thread_type)
    except ValueError:
        error_message = Message(text="Giá trị không hợp lệ. Vui lòng nhập số nguyên.")
        client.replyMessage(error_message, message_object, thread_id, thread_type)

def handle_guess_command(message, message_object, thread_id, thread_type, author_id, client):
    """
    Xử lý dự đoán của người chơi trong trò chơi hiện tại.
    Cú pháp: guess <số đoán của bạn>
    """
    args = message.split()
    if len(args) != 2:
        error_message = Message(text="Cú pháp không hợp lệ. Vui lòng nhập: guess <số đoán của bạn>")
        client.replyMessage(error_message, message_object, thread_id, thread_type)
        return

    # Kiểm tra xem có trò chơi nào đang diễn ra trong thread này không
    if thread_id not in active_games:
        error_message = Message(
            text="Không có trò chơi nào đang diễn ra. Hãy bắt đầu một trò chơi mới bằng cách nhập: random <min> <max>"
        )
        client.replyMessage(error_message, message_object, thread_id, thread_type)
        return

    try:
        guess = int(args[1])
    except ValueError:
        error_message = Message(text="Giá trị không hợp lệ. Vui lòng nhập số nguyên.")
        client.replyMessage(error_message, message_object, thread_id, thread_type)
        return

    game = active_games[thread_id]
    secret = game['secret']

    if guess < secret:
        response_text = "Số bạn đoán nhỏ hơn số bí mật. Thử lại!"
    elif guess > secret:
        response_text = "Số bạn đoán lớn hơn số bí mật. Thử lại!"
    else:
        response_text = f"Chúc mừng! Bạn đã đoán đúng số {secret}."
        # Kết thúc trò chơi khi đoán đúng
        del active_games[thread_id]

    message_to_send = Message(text=response_text)
    client.replyMessage(message_to_send, message_object, thread_id, thread_type)

def get_mitaizl():
    return {
        'ngaunhien': handle_random_command,
        'doan': handle_guess_command
    }
