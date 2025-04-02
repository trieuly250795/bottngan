from zlapi.models import Message, MultiMsgStyle, MessageStyle
import requests
import urllib.parse

des = {
    'tác giả': "Rosy",
    'mô tả': "Trò chuyện với chatbot ",
    'tính năng': [
        "📨 Gửi tin nhắn với định dạng màu sắc và cỡ chữ.",
        "🔍 Gọi API chatbot để lấy câu trả lời cho nội dung trò chuyện.",
        "🔄 Xử lý lệnh trò chuyện và gửi phản hồi từ chatbot.",
        "🔔 Thông báo lỗi cụ thể nếu có vấn đề xảy ra khi xử lý yêu cầu."
    ],
    'hướng dẫn sử dụng': [
        "📩 Gửi lệnh alo <nội dung trò chuyện> để trò chuyện với chatbot.",
        "📌 Ví dụ: alo Xin chào để trò chuyện với chatbot và nhận phản hồi từ chatbot.",
        "✅ Nhận thông báo trạng thái và kết quả ngay lập tức."
    ]
}

def send_message_with_style(client, text, thread_id, thread_type, color="#db342e"):
    """Gửi tin nhắn với định dạng màu sắc."""
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
    client.send(
        Message(text=text, style=style),
        thread_id=thread_id,
        thread_type=thread_type,
        ttl=60000
    )

def handle_sim_command(message, message_object, thread_id, thread_type, author_id, client):
    if "alo" in message.lower():
        action = "CC"  # Biểu tượng phản ứng
        try:
            client.sendReaction(message_object, action, thread_id, thread_type, reactionType=75)
        except Exception as e:
            print(f"Error sending reaction: {e}")
    
    text = message.split()
    if len(text) < 2:
        # Tin nhắn sẽ tự xóa sau 60 giây
        error_message = Message(
            text="⭕ Chat bot zalo tự động xin chào\n⭕ Soạn lệnh menu để mở menu chức năng"
        )
        client.sendMessage(error_message, thread_id, thread_type, ttl=60000)
        return
    
    content = " ".join(text[1:])
    encoded_text = urllib.parse.quote(content, safe='')
    try:
        sim_url = f'https://subhatde.id.vn/sim?type=ask&ask={encoded_text}'
        response = requests.get(sim_url)
        response.raise_for_status()
        data = response.json()
        simi = data.get('answer', 'Không có phản hồi từ Simi.')
        message_to_send = Message(text=f"> Sim: {simi}")
        # Gửi tin nhắn với TTL 60000ms (60 giây)
        client.replyMessage(
            message_to_send,
            message_object,
            thread_id,
            thread_type,
            ttl=60000
        )
    except requests.exceptions.RequestException as e:
        error_message = Message(text=f"Đã xảy ra lỗi khi gọi API: {str(e)}")
        client.sendMessage(error_message, thread_id, thread_type)
    except KeyError as e:
        error_message = Message(text=f"Dữ liệu từ API không đúng cấu trúc: {str(e)}")
        client.sendMessage(error_message, thread_id, thread_type)
    except Exception as e:
        error_message = Message(text=f"Đã xảy ra lỗi không xác định: {str(e)}")
        client.sendMessage(error_message, thread_id, thread_type)

# Đăng ký các lệnh
def get_mitaizl():
    return {
        'alo': handle_sim_command
    }
