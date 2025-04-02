from zlapi.models import Message, MultiMsgStyle, MessageStyle

def handle_sim_command(message, message_object, thread_id, thread_type, author_id, client):
    # Gửi phản ứng ngay khi người dùng soạn đúng lệnh
    action = "✅"
    client.sendReaction(message_object, action, thread_id, thread_type, reactionType=99)
    text = message.split()

    if len(text) < 2:
        # Create the error message
        error_text = "⚠ Cảnh báo: Bạn đang làm phiền người khác, hãy lịch sự nếu không bạn sẽ bị sút"

        # Define the style
        style = MultiMsgStyle(
            [
                MessageStyle(
                    offset=0,
                    length=len(error_text),  # Use the actual length of the message
                    style="color",
                    color="#db342e",  # The red color you want
                    auto_format=False,
                ),
                MessageStyle(
                    offset=0,
                    length=len(error_text),
                    style="bold",
                    size="16",  # Font size 16
                    auto_format=False,
                ),
            ]
        )

        # Create the styled error message
        error_message = Message(text=error_text, style=style)
        
        # Send the styled error message
        client.sendMessage(error_message, thread_id, thread_type, ttl=20000)
        return

def get_mitaizl():
    return {
        '@all': handle_sim_command
    }