from zlapi.models import Message, MultiMsgStyle, MessageStyle
from config import ADMIN
import time

des = {
    'tác giả': "ROSY",
    'mô tả': "Duyệt tất cả thành viên đang chờ phê duyệt trong nhóm.",
    'tính năng': [
        "✅ Kiểm tra danh sách thành viên đang chờ duyệt.",
        "🚀 Duyệt tất cả thành viên chỉ với một lệnh.",
        "🔒 Chỉ quản trị viên hoặc chủ nhóm mới có quyền sử dụng.",
        "📊 Hiển thị số lượng thành viên đã duyệt và lỗi (nếu có).",
        "⚡ Tự động xử lý với độ trễ hợp lý để tránh lỗi hệ thống."
    ],
    'hướng dẫn sử dụng': [
        "📌 Sử dụng duyetmem list để xem danh sách thành viên đang chờ.",
        "📌 Sử dụng duyetmem all để duyệt tất cả thành viên cùng một lúc.",
        "⚠️ Lệnh chỉ có thể được thực hiện bởi quản trị viên hoặc chủ nhóm.",
        "📢 Hệ thống sẽ gửi thông báo khi hoàn thành."
    ]
}

def handle_duyetmem_command(message, message_object, thread_id, thread_type, author_id, client):
    # Gửi phản ứng ngay khi người dùng soạn đúng lệnh
    action = "✅"
    client.sendReaction(message_object, action, thread_id, thread_type, reactionType=75)
    try:
        # Lấy thông tin nhóm
        group_info = client.fetchGroupInfo(thread_id).gridInfoMap[thread_id]
        creator_id = group_info.get('creatorId')
        admin_ids = group_info.get('adminIds', [])
        
        if admin_ids is None:
            admin_ids = []

        # Xác định tất cả quản trị viên
        all_admin_ids = set(admin_ids)
        all_admin_ids.add(creator_id)
        all_admin_ids.update(ADMIN)

        # Kiểm tra quyền
        if author_id not in all_admin_ids and author_id not in ADMIN:
            error_message = "Bạn không có quyền sử dụng lệnh này."
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
            client.replyMessage(Message(text=error_message, style=style_error), message_object, thread_id, thread_type, ttl=30000)
            return

        # Lấy danh sách thành viên đang chờ duyệt
        pending_members = group_info.pendingApprove.get('uids', [])

        # Phân tích lệnh
        command_parts = message.strip().split()
        if len(command_parts) < 2:
            error_message = "Lệnh không hợp lệ. Vui lòng sử dụng `duyetmem list` để xem danh sách hoặc `duyetmem all` để duyệt tất cả."
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
            client.replyMessage(Message(text=error_message, style=style_error), message_object, thread_id, thread_type, ttl=30000)
            return

        action = command_parts[1]

        # Xử lý lệnh `list`
        if action == "list":
            if not pending_members:
                no_pending = "Hiện tại không có thành viên nào đang chờ duyệt."
                style_no_pending = MultiMsgStyle(
                    [
                        MessageStyle(
                            offset=0,
                            length=len(no_pending),
                            style="color",
                            color="#db342e",
                            auto_format=False,
                        ),
                        MessageStyle(
                            offset=0,
                            length=len(no_pending),
                            style="bold",
                            size="16",
                            auto_format=False,
                        ),
                    ]
                )
                client.replyMessage(Message(text=no_pending, style=style_no_pending), message_object, thread_id, thread_type, ttl=30000)
            else:
                pending_count = f"Số thành viên đang chờ duyệt: {len(pending_members)} thành viên."
                style_pending_count = MultiMsgStyle(
                    [
                        MessageStyle(
                            offset=0,
                            length=len(pending_count),
                            style="color",
                            color="#db342e",
                            auto_format=False,
                        ),
                        MessageStyle(
                            offset=0,
                            length=len(pending_count),
                            style="bold",
                            size="16",
                            auto_format=False,
                        ),
                    ]
                )
                client.replyMessage(Message(text=pending_count, style=style_pending_count), message_object, thread_id, thread_type, ttl=30000)
        # Xử lý lệnh `all`
        elif action == "all":
            if not pending_members:
                no_pending = "Hiện tại không có thành viên nào đang chờ duyệt."
                style_no_pending = MultiMsgStyle(
                    [
                        MessageStyle(
                            offset=0,
                            length=len(no_pending),
                            style="color",
                            color="#db342e",
                            auto_format=False,
                        ),
                        MessageStyle(
                            offset=0,
                            length=len(no_pending),
                            style="bold",
                            size="16",
                            auto_format=False,
                        ),
                    ]
                )
                client.replyMessage(Message(text=no_pending, style=style_no_pending), message_object, thread_id, thread_type, ttl=30000)
                return
            
            # Duyệt tất cả thành viên
            approved_count = 0
            error_count = 0

            for member_id in pending_members:
                try:
                    if hasattr(client, 'handleGroupPending'):
                        client.handleGroupPending(member_id, thread_id)
                        approved_count += 1
                    time.sleep(3)    
                except Exception as e:
                    print(f"Lỗi khi duyệt thành viên {member_id}: {e}")
                    error_count += 1

            # Gửi phản hồi
            approval_message = f"Đã duyệt thành công {approved_count} thành viên. Lỗi: {error_count} thành viên."
            style_approval = MultiMsgStyle(
                [
                    MessageStyle(
                        offset=0,
                        length=len(approval_message),
                        style="color",
                        color="#db342e",
                        auto_format=False,
                    ),
                    MessageStyle(
                        offset=0,
                        length=len(approval_message),
                        style="bold",
                        size="16",
                        auto_format=False,
                    ),
                ]
            )
            client.replyMessage(Message(text=approval_message, style=style_approval), message_object, thread_id, thread_type, ttl=30000)
        # Xử lý lệnh không hợp lệ
        else:
            invalid_command = "Lệnh không hợp lệ. Vui lòng sử dụng `duyetmem list` để xem danh sách hoặc `duyetmem all` để duyệt tất cả."
            style_invalid_command = MultiMsgStyle(
                [
                    MessageStyle(
                        offset=0,
                        length=len(invalid_command),
                        style="color",
                        color="#db342e",
                        auto_format=False,
                    ),
                    MessageStyle(
                        offset=0,
                        length=len(invalid_command),
                        style="bold",
                        size="16",
                        auto_format=False,
                    ),
                ]
            )
            client.replyMessage(Message(text=invalid_command, style=style_invalid_command), message_object, thread_id, thread_type)

    except Exception as e:
        error_message = f"Đã xảy ra lỗi khi duyệt.\n{e}"
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
        'duyetmem': handle_duyetmem_command
    }
