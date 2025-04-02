from zlapi.models import Message, MessageStyle, MultiMsgStyle

des = {
    'tác giả': "Rosy",
    'mô tả': "Lệnh tính toán",
    'tính năng': [
        "📨 Nhận và xử lý lệnh tính toán từ người dùng.",
        "🔍 Kiểm tra và đánh giá biểu thức toán học.",
        "🔄 Gửi kết quả tính toán với định dạng màu sắc và in đậm.",
        "🔔 Thông báo lỗi cụ thể nếu có vấn đề xảy ra khi xử lý yêu cầu."
    ],
    'hướng dẫn sử dụng': [
        "📩 Gửi lệnh calc <phép toán> để tính toán và nhận kết quả.",
        "📌 Ví dụ: calc 2 + 2 để tính toán kết quả của phép toán 2 + 2.",
        "✅ Nhận thông báo trạng thái và kết quả ngay lập tức."
    ]
}

def send_message_with_style(client, text, thread_id, thread_type, ttl=None, color="#db342e"):
    """
    Gửi tin nhắn với định dạng màu sắc và in đậm.
    """
    base_length = len(text)
    adjusted_length = base_length + 355
    style = MultiMsgStyle([
        MessageStyle(
            offset=0,
            length=adjusted_length,
            style="color",
            color=color,
            auto_format=False,
        ),
        MessageStyle(
            offset=0,
            length=adjusted_length,
            style="bold",
            size="8",
            auto_format=False
        )
    ])
    msg = Message(text=text, style=style)
    if ttl is not None:
        client.sendMessage(msg, thread_id, thread_type, ttl=ttl)
    else:
        client.sendMessage(msg, thread_id, thread_type)

def handle_calculator_command(message, message_object, thread_id, thread_type, author_id, client):
    action = "✅"
    client.sendReaction(message_object, action, thread_id, thread_type, reactionType=75)

    text = message.split()
    if len(text) < 2:
        error_message = "🚨 Hãy nhập phép toán cần tính.\nCú pháp: calc <phép toán>"
        send_message_with_style(client, error_message, thread_id, thread_type)
        return

    expression = " ".join(text[1:])
    try:
        # Try to evaluate the expression
        result = eval(expression)
        # Send the result back
        send_message_with_style(
            client, 
            f"━━━━━━━━━━━━━━━━\n💡 KẾT QUẢ:\n🎯 = {result}\n━━━━━━━━━━━━━━━━", 
            thread_id, 
            thread_type
        )
    except Exception as e:
        # Handle any errors in the expression
        send_message_with_style(
            client, 
            f"❌ Lỗi khi tính toán: {e}", 
            thread_id, 
            thread_type
        )

    client.sendReaction(message_object, action, thread_id, thread_type, reactionType=75)

def get_mitaizl():
    return {
        'calc': handle_calculator_command  # Lệnh tính toán
    }
