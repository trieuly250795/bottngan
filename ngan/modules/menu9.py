import os
import importlib
from zlapi.models import Message
from datetime import datetime

des = {
    'tác giả': "Rosy",
    'mô tả': "Hiển thị toàn bộ các lệnh hiện có của bot.",
    'tính năng': [
        "📜 Liệt kê tất cả các lệnh hiện có",
        "🔍 Tự động quét thư mục 'modules' để lấy danh sách lệnh",
        "🖼️ Gửi kèm hình ảnh minh họa menu",
        "⚡ Phản hồi ngay khi người dùng nhập lệnh"
    ],
    'hướng dẫn sử dụng': [
        "📩 Dùng lệnh 'menu9' để hiển thị toàn bộ các lệnh hiện có của bot.",
        "📌 Ví dụ: nhập menu9 để hiển thị danh sách lệnh.",
        "✅ Nhận thông báo trạng thái và kết quả ngay lập tức."
    ]
}

def get_all_mitaizl():
    """
    Lấy toàn bộ các lệnh từ thư mục modules.
    """
    mitaizl = {}
    for module_name in os.listdir('modules'):
        if module_name.endswith('.py') and module_name != '__init__.py':
            module_path = f'modules.{module_name[:-3]}'
            module = importlib.import_module(module_path)
            if hasattr(module, 'get_mitaizl'):
                get_mitaizl = module.get_mitaizl()
                mitaizl.update(get_mitaizl)
    command_names = list(mitaizl.keys())
    return command_names

def handle_menu_command(message, message_object, thread_id, thread_type, author_id, client):
    """
    Xử lý lệnh menu để liệt kê toàn bộ các lệnh hiện có.
    """
    # Lấy tất cả các lệnh
    command_names = get_all_mitaizl()
    # Tính tổng số lệnh và tạo danh sách các lệnh
    total_mitaizl = len(command_names)
    numbered_mitaizl = [f"{i+1}. {name}" for i, name in enumerate(command_names)]
    # Tạo nội dung menu
    menu_message = (
        f"────────────────────⭔𝑹𝑶𝑺𝒀 𝑨𝑹𝑬𝑵𝑨 𝑺𝑯𝑶𝑷 👾𝐀𝐝𝐦𝐢𝐧 ¦ 𝑹𝑶𝑺𝒀 𝑨𝑹𝑬𝑵𝑨 𝑺𝑯𝑶𝑷\n"
        f"-----------------\n"
        f"𝙈𝙚𝙣𝙪 𝘽𝙤𝙩 : {total_mitaizl} 𝘾𝙝𝙪̛́𝙘 𝙣𝙖̆𝙣𝙜🌸\n"
        f"0. vdtt\n" + "\n".join(numbered_mitaizl)
    )
    # Gửi ảnh và nội dung menu
    client.sendLocalImage(
        "2.jpg", 
        thread_id=thread_id, 
        thread_type=thread_type, 
        message=Message(text=menu_message), 
        ttl=120000
    )

def get_mitaizl():
    """
    Hàm trả về danh sách lệnh và hàm xử lý tương ứng.
    """
    return {
        'menu9': handle_menu_command
    }
