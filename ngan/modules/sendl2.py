import re
import threading
import time
import json
from zlapi.models import Message, ThreadType, MessageStyle, MultiMsgStyle

des = {
    'tác giả': "Rosy",
    'mô tả': "Gửi tin nhắn và liên kết đến tất cả nhóm",
    'tính năng': [
        "📨 Gửi tin nhắn và liên kết đến tất cả nhóm, trừ các nhóm bị loại trừ.",
        "🔒 Kiểm tra quyền admin trước khi thực hiện lệnh.",
        "🔗 Gửi liên kết kèm hình ảnh minh họa, tiêu đề và mô tả.",
        "⏳ Gửi tin nhắn với khoảng cách thời gian cố định giữa các lần gửi.",
        "🔍 Kiểm tra định dạng URL và xử lý các lỗi liên quan."
    ],
    'hướng dẫn sử dụng': [
        "📩 Gửi lệnh sendl2 <link>|<link ảnh nền>|<title>|<domain>|<des> để gửi tin nhắn và liên kết đến tất cả nhóm.",
        "📌 Ví dụ: sendl2 https://example.com|https://example.com/image.jpg|Tiêu đề|https://example.com|Mô tả để gửi liên kết với hình ảnh và mô tả.",
        "✅ Nhận thông báo trạng thái và kết quả gửi tin nhắn ngay lập tức."
    ]
}

# Danh sách admin (định nghĩa cứng)
ADMIN_IDS = {
    "2670654904430771575", "1632905559702714318"
}

# Regex kiểm tra URL
url_pattern = re.compile(
    r'http[s]?://(?:[a-zA-Z0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
)

def get_excluded_group_ids(filename="danhsachnhom.json"):
    """
    Đọc tệp JSON và trả về tập hợp các group_id cần loại trừ.
    Giả sử file chứa danh sách các đối tượng với khóa "group_id".
    Nếu file không tồn tại hoặc lỗi định dạng, trả về tập rỗng.
    """
    try:
        with open(filename, "r", encoding="utf-8") as f:
            groups = json.load(f)
            return {grp.get("group_id") for grp in groups if "group_id" in grp}
    except Exception as e:
        print(f"Lỗi khi đọc file {filename}: {e}")
        return set()

def send_link_to_group(client, link_url, thumbnail_url, title, domain_url, desc, thread_id):
    """Gửi một liên kết có hình ảnh đến một nhóm cụ thể."""
    try:
        client.sendLink(
            linkUrl=link_url,
            title=title,
            thread_id=thread_id,
            thread_type=ThreadType.GROUP,
            domainUrl=domain_url,
            desc=desc,
            thumbnailUrl=thumbnail_url,
            ttl=600000
        )
        print(f"Đã gửi link đến nhóm {thread_id}")
    except Exception as e:
        print(f"Lỗi khi gửi link đến nhóm {thread_id}: {e}")

def sendl2_command(message, message_object, thread_id, thread_type, author_id, client):
    """Xử lý lệnh sendl2 để gửi link đến tất cả nhóm."""
    print(f"[START] Xử lý command sendl2 từ author_id: {author_id} trong thread: {thread_id}")
    
    if author_id not in ADMIN_IDS:
        client.sendMessage(Message(text="🚫 Bạn không có quyền sử dụng lệnh này!"), thread_id, thread_type)
        print("Quyền hạn không đủ. Dừng command.")
        return

    # Thêm phản ứng ngay khi nhận lệnh (giả sử client có hàm react)
    try:
        client.react(message_object, "⚡")
        print("Đã thêm phản ứng ngay khi nhận lệnh.")
    except Exception as e:
        print(f"Lỗi khi thêm phản ứng: {e}")

    parts = message[7:].strip().split('|')
    if len(parts) < 5:
        client.sendMessage(
            Message(text="🚫 Cú pháp không chính xác! Vui lòng nhập: sendl2 <link>|<link ảnh nền>|<title>|<domain>|<des>"),
            thread_id, thread_type
        )
        print("Cú pháp không chính xác. Dừng command.")
        return

    possible_urls = re.findall(url_pattern, parts[0])
    if not possible_urls:
        client.sendMessage(
            Message(text="🚫 **Không tìm thấy URL hợp lệ!** Vui lòng cung cấp một URL hợp lệ."),
            thread_id, thread_type
        )
        print("Không tìm thấy URL hợp lệ. Dừng command.")
        return

    link_url = possible_urls[0].strip()
    thumbnail_url = parts[1].strip()
    title = parts[2].strip()
    domain_url = parts[3].strip()
    desc = parts[4].strip()

    print(f"Command hợp lệ: link_url = {link_url}, title = {title}")

    # Thông báo khi bắt đầu xử lý lệnh gửi link
    client.sendMessage(Message(text="⏳ Đang bắt đầu gửi link đến các nhóm..."), thread_id, thread_type)
    
    try:
        all_groups = client.fetchAllGroups()
        excluded_ids = get_excluded_group_ids()
        allowed_thread_ids = [gid for gid in all_groups.gridVerMap.keys() if gid not in excluded_ids]
        print(f"Đang gửi link đến {len(allowed_thread_ids)} nhóm (đã loại trừ các nhóm không cho phép).")
        for group_id in allowed_thread_ids:
            threading.Thread(
                target=send_link_to_group,
                args=(client, link_url, thumbnail_url, title, domain_url, desc, group_id),
                daemon=True
            ).start()
            print(f"Đã khởi tạo thread gửi link đến nhóm {group_id}, chờ 3 giây...")
            time.sleep(3)  # Độ trễ 3 giây giữa các lần gửi
        # Thông báo hoàn thành sau khi khởi chạy các thread gửi link
        client.sendMessage(Message(text="✅ Hoàn thành gửi link đến tất cả nhóm!"), thread_id, thread_type)
        print("Đã khởi chạy các thread gửi link với độ trễ 3 giây giữa các lần gửi.")
    except Exception as e:
        client.sendMessage(Message(text=f"🚫 Lỗi khi gửi link: {e}"), thread_id, thread_type)
        print(f"Lỗi khi gửi link: {e}")

def get_mitaizl():
    return {
        'sendl2': sendl2_command
    }
