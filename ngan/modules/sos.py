from zlapi.models import Message, MultiMsgStyle, MessageStyle
from config import ADMIN  # Lấy ADMIN từ config.py

des = {
    'tác giả': "Rosy",
    'mô tả': "Cài đặt đóng/mở chat cho nhóm",
    'tính năng': [
        "🔄 Đóng hoặc mở chat của nhóm.",
        "🔍 Kiểm tra quyền admin trước khi thực hiện lệnh.",
        "🔔 Thông báo trạng thái hiện tại và kết quả sau khi thay đổi cài đặt nhóm.",
        "🔒 Lưu trữ trạng thái hiện tại của nhóm để có thể đảo ngược lại."
    ],
    'hướng dẫn sử dụng': [
        "📩 Gửi lệnh sos để đóng/mở chat cho nhóm.",
        "📌 Ví dụ: sos để đảo ngược trạng thái hiện tại của nhóm.",
        "✅ Nhận thông báo trạng thái và kết quả thay đổi ngay lập tức."
    ]
}

# Biến trạng thái để lưu trạng thái hiện tại của nhóm (mở hoặc đóng chat)
group_chat_status = {}  # Lưu trạng thái theo thread_id

def is_admin(author_id):
    """Kiểm tra xem người dùng có phải là admin không"""
    return author_id == ADMIN

def handle_bot_sos_command(message, message_object, thread_id, thread_type, author_id, client):
    try:
        # Kiểm tra quyền admin
        if not is_admin(author_id):
            error_msg = "• Bạn Không Có Quyền! Chỉ có admin mới có thể sử dụng lệnh này."
            style_error = MultiMsgStyle(
                [
                    MessageStyle(
                        offset=0,
                        length=len(error_msg),
                        style="color",
                        color="#db342e",
                        auto_format=False,
                    ),
                    MessageStyle(
                        offset=0,
                        length=len(error_msg),
                        style="bold",
                        size="16",
                        auto_format=False,
                    ),
                ]
            )
            client.replyMessage(Message(text=error_msg, style=style_error), message_object, thread_id, thread_type)
            return

        # Lấy trạng thái hiện tại của nhóm
        current_status = group_chat_status.get(thread_id, 0)  # Mặc định là mở chat (0)

        # Đảo trạng thái: 0 -> 1 (đóng), 1 -> 0 (mở)
        new_status = 1 if current_status == 0 else 0
        group_chat_status[thread_id] = new_status

        # Cập nhật cài đặt nhóm
        kwargs = {"lockSendMsg": new_status}
        client.changeGroupSetting(thread_id, **kwargs)

        # Phản hồi trạng thái mới
        action = "Đóng chat thành công!" if new_status == 1 else "Mở chat thành công!"
        style_action = MultiMsgStyle(
            [
                MessageStyle(
                    offset=0,
                    length=len(action),
                    style="color",
                    color="#db342e",
                    auto_format=False,
                ),
                MessageStyle(
                    offset=0,
                    length=len(action),
                    style="bold",
                    size="16",
                    auto_format=False,
                ),
            ]
        )
        client.replyMessage(Message(text=action, style=style_action), message_object, thread_id, thread_type)

    except Exception as e:
        # Xử lý lỗi nếu có
        error_message = f"Lỗi khi thay đổi cài đặt nhóm: {str(e)}"
        style_error = MultiMsgStyle(
            [
                MessageStyle(
                    offset=0,
                    length=len(error_message),
                    style="color",
                    color="#db342e",
                    auto_format=False,
                ),
                MessageStyle(
                    offset=0,
                    length=len(error_message),
                    style="bold",
                    size="16",
                    auto_format=False,
                ),
            ]
        )
        client.replyMessage(Message(text=error_message, style=style_error), message_object, thread_id, thread_type)

def get_mitaizl():
    return {
        'sos': handle_bot_sos_command
    }
