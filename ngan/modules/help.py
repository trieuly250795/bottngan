import os
import importlib
from zlapi.models import Message

des = {
    'tác giả': "ROSY",
    'mô tả': "Lệnh này cung cấp thông tin chi tiết về các lệnh khác.",
    'tính năng': [
        "🔍 Liệt kê tất cả các lệnh có sẵn cùng thông tin chi tiết",
        "📌 Hỗ trợ tìm kiếm thông tin về một lệnh cụ thể",
        "ℹ️ Hiển thị phiên bản, tác giả và mô tả của từng lệnh"
    ],
    'hướng dẫn sử dụng': [
        "📩 Gửi lệnh help [tên lệnh] để nhận thông tin chi tiết về lệnh.",
        "📌 Ví dụ: help cover để nhận thông tin chi tiết về lệnh cover.",
        "✅ Nhận thông báo trạng thái và kết quả ngay lập tức."
    ]
}

def get_all_mitaizl_with_info():
    mitaizl_info = {}
    for module_name in os.listdir('modules'):
        if module_name.endswith('.py') and module_name != '__init__.py':
            module_path = f'modules.{module_name[:-3]}'
            module = importlib.import_module(module_path)
            if hasattr(module, 'des'):
                des = getattr(module, 'des')
                author = des.get('tác giả', 'Chưa có thông tin')
                description = des.get('mô tả', 'Chưa có thông tin')
                features = "\n - ".join(des.get('tính năng', [])) or "Không có thông tin"
                usage = "\n - ".join(des.get('hướng dẫn sử dụng', [])) or "Không có hướng dẫn"
                mitaizl_info[module_name[:-3]] = (author, description, features, usage)
    return mitaizl_info

def handle_help1_command(message, message_object, thread_id, thread_type, author_id, client):
    command_parts = message.split()
    mitaizl_info = get_all_mitaizl_with_info()
    
    if len(command_parts) > 1:
        requested_command = command_parts[1].lower()
        if requested_command in mitaizl_info:
            author, description, features, usage = mitaizl_info[requested_command]
            single_command_help = (
                f"➤ Tên lệnh: {requested_command}\n"
                f"➤ Tác giả: {author}\n"
                f"➤ Mô tả: {description}\n"
                f"➤ Tính năng:\n - {features}\n"
                f"➤ Hướng dẫn sử dụng:\n - {usage}\n"
            )
            all_commands_help = None
        else:
            single_command_help = f"❌ Không tìm thấy lệnh '{requested_command}' trong hệ thống."
            all_commands_help = None
    else:
        total_mitaizl = len(mitaizl_info)
        help_message_lines = [f"📌 Tổng số lệnh bot hiện tại: {total_mitaizl} lệnh"]
        for i, (name, (author, description, features, usage)) in enumerate(mitaizl_info.items(), 1):
            help_message_lines.append(
                f"🔹 {i}.\n"
                f" ➤ Tên lệnh: {name}\n"
                f" ➤ Tác giả: {author}\n"
                f" ➤ Mô tả: {description}\n"
                f" ➤ Tính năng:\n - {features}\n"
                f" ➤ Hướng dẫn sử dụng:\n - {usage}\n"
            )
        all_commands_help = "\n".join(help_message_lines)
        single_command_help = None

    message_to_send = Message(text=single_command_help if single_command_help else all_commands_help)
    client.replyMessage(message_to_send, message_object, thread_id, thread_type)

def get_mitaizl():
    return {
        'help': handle_help1_command
    }
