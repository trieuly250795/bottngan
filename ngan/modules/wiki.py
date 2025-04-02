import re
import time
import wikipedia
import requests
import tempfile
import os
import difflib

from zlapi.models import Message, MultiMsgStyle, MessageStyle
from config import PREFIX

des = {
    'tác giả': "Rosy",
    'mô tả': "Tìm kiếm thông tin từ Wikipedia",
    'tính năng': [
        "🔍 Tìm kiếm trang Wikipedia dựa trên từ khóa người dùng cung cấp.",
        "🌐 Lấy tóm tắt nội dung và các mục chính từ trang Wikipedia.",
        "📸 Lấy ảnh bìa của trang Wikipedia (nếu có) hoặc chọn ảnh đại diện từ danh sách ảnh của trang.",
        "📄 Chia nội dung thành nhiều phần nếu quá dài, mỗi phần không vượt quá giới hạn độ dài tin nhắn.",
        "🔔 Thông báo lỗi cụ thể nếu không tìm thấy trang hoặc xảy ra vấn đề khi kết nối."
    ],
    'hướng dẫn sử dụng': [
        "📩 Gửi lệnh wiki <từ khoá> để tìm kiếm thông tin từ Wikipedia.",
        "📌 Ví dụ: wiki Elon Musk để tìm kiếm thông tin về Elon Musk trên Wikipedia.",
        "✅ Nhận thông báo trạng thái và kết quả ngay lập tức."
    ]
}

# Cấu hình Wikipedia với ngôn ngữ Tiếng Việt
wikipedia.set_lang("vi")

MAX_MESSAGE_LENGTH = 1024  # Giới hạn độ dài của mỗi tin nhắn, có thể điều chỉnh

def translate_summary(summary):
    # Tạm thời không dịch; có thể tích hợp API dịch nếu cần
    return summary

def extract_main_sections(content):
    """
    Trích xuất các tiêu đề chính (mục) từ nội dung của trang Wikipedia.
    Sử dụng regex để tìm các dòng tiêu đề có định dạng "== ... =="
    """
    headings = re.findall(r'(?:\n|^)==\s*([^=].*?)\s*==', content)
    return headings

def get_cover_image(title):
    """
    Sử dụng Wikipedia API (prop=pageimages) để lấy ảnh bìa của trang.
    Nếu thành công, trả về URL của thumbnail với kích thước pithumbsize.
    """
    endpoint = "https://vi.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "titles": title,
        "prop": "pageimages",
        "pithumbsize": 1200
    }
    try:
        response = requests.get(endpoint, params=params)
        data = response.json()
        pages = data.get("query", {}).get("pages", {})
        for page_id, page_data in pages.items():
            if "thumbnail" in page_data:
                return page_data["thumbnail"]["source"]
    except Exception:
        return None
    return None

def get_representative_image_from_list(images):
    """
    Nếu không lấy được ảnh bìa qua API, duyệt qua danh sách ảnh của trang.
    Chọn ảnh có đuôi .jpg, .jpeg hoặc .png, loại trừ các ảnh chứa "logo" hoặc "icon".
    """
    for img in images:
        if img.lower().endswith(('.jpg', '.jpeg', '.png')):
            if "logo" not in img.lower() and "icon" not in img.lower():
                return img
    return None

def split_message_text(text, max_length):
    """
    Tách nội dung tin nhắn thành nhiều phần, mỗi phần có độ dài không vượt quá max_length.
    Ưu tiên tách theo dòng nếu có thể.
    """
    if len(text) <= max_length:
        return [text]
    
    lines = text.split("\n")
    chunks = []
    current_chunk = ""
    for line in lines:
        candidate = f"{current_chunk}\n{line}" if current_chunk else line
        if len(candidate) > max_length:
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = line
            else:
                # Nếu một dòng đơn lẻ quá dài, chia nhỏ dòng đó
                while len(line) > max_length:
                    chunks.append(line[:max_length])
                    line = line[max_length:]
                current_chunk = line
        else:
            current_chunk = candidate
    if current_chunk:
        chunks.append(current_chunk)
    return chunks

def create_style(text):
    return MultiMsgStyle([
        MessageStyle(
            offset=0,
            length=len(text),
            style="color",
            color="#15a85f",
            auto_format=False,
        ),
        MessageStyle(
            offset=0,
            length=len(text),
            style="font",
            size="16",
            auto_format=False,
        ),
    ])

def handle_wikipedia_search_command(message, message_object, thread_id, thread_type, author_id, client):
    # Gửi phản ứng xác nhận khi nhận lệnh hợp lệ
    action = "✅"
    client.sendReaction(message_object, action, thread_id, thread_type, reactionType=75)
    
    text = message.split()
    if len(text) < 2:
        error_message = "Hãy nhập từ khóa để tìm kiếm thông tin trên Wikipedia.\nCú pháp: wiki <từ khoá>"
        style_error = create_style(error_message)
        client.sendMessage(Message(text=error_message, style=style_error), thread_id, thread_type, ttl=60000)
        return

    query = " ".join(text[1:])
    try:
        page = wikipedia.page(query)
        # Lấy tóm tắt 3 câu đầu của trang
        summary_sentences = page.summary.split(". ")
        summary = ". ".join(summary_sentences[:3])
        if not summary.endswith("."):
            summary += "."
        main_sections = extract_main_sections(page.content)
        page_url = page.url
        # Ưu tiên lấy ảnh bìa qua API
        cover_image = get_cover_image(page.title)
        if cover_image:
            representative_image = cover_image
        else:
            representative_image = get_representative_image_from_list(page.images)
    except wikipedia.exceptions.DisambiguationError:
        summary = f"Đã có nhiều kết quả liên quan đến '{query}'. Hãy thử rõ ràng hơn."
        main_sections = []
        representative_image = None
        page_url = f"https://vi.wikipedia.org/wiki/{query}"
    except wikipedia.exceptions.HTTPTimeoutError:
        summary = "Không thể kết nối với Wikipedia, vui lòng thử lại sau."
        main_sections = []
        representative_image = None
        page_url = f"https://vi.wikipedia.org/wiki/{query}"
    except wikipedia.exceptions.PageError:
        summary = "Không tìm thấy trang Wikipedia cho từ khóa này."
        main_sections = []
        representative_image = None
        page_url = f"https://vi.wikipedia.org/wiki/{query}"

    # Xây dựng nội dung tin nhắn
    message_lines = [f"Thông tin về {query}:"]
    message_lines.append(translate_summary(summary))
    if main_sections:
        message_lines.append("\nCác mục chính:")
        for section in main_sections:
            message_lines.append(f"- {section}")
    message_lines.append(f"\nXem thêm tại: {page_url}")
    full_message = "\n".join(message_lines)

    # Chia nội dung thành các tin nhắn nếu quá dài
    message_chunks = split_message_text(full_message, MAX_MESSAGE_LENGTH)
    
    if representative_image:
        try:
            response = requests.get(representative_image, stream=True)
            if response.status_code == 200:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
                    for chunk in response.iter_content(1024):
                        tmp_file.write(chunk)
                    tmp_file_path = tmp_file.name
                # Gửi chunk đầu tiên kèm ảnh bìa qua phương thức sendLocalImage
                client.sendLocalImage(
                    tmp_file_path,
                    message=Message(text=message_chunks[0], style=create_style(message_chunks[0])),
                    thread_id=thread_id,
                    thread_type=thread_type,
                    width=1200,
                    height=1600,
                    ttl=60000  # 60 giây tự xóa ảnh sau thời gian này
                )
                os.remove(tmp_file_path)
                # Gửi các chunk còn lại với delay 5 giây mỗi tin nhắn
                for chunk in message_chunks[1:]:
                    time.sleep(5)
                    client.sendMessage(Message(text=chunk, style=create_style(chunk)), thread_id, thread_type)
            else:
                for chunk in message_chunks:
                    time.sleep(5)
                    client.sendMessage(Message(text=chunk, style=create_style(chunk)), thread_id, thread_type)
        except Exception:
            for chunk in message_chunks:
                time.sleep(5)
                client.sendMessage(Message(text=chunk, style=create_style(chunk)), thread_id, thread_type)
    else:
        # Nếu không có ảnh bìa, gửi toàn bộ nội dung dưới dạng tin nhắn văn bản
        for chunk in message_chunks:
            time.sleep(5)
            client.sendMessage(Message(text=chunk, style=create_style(chunk)), thread_id, thread_type)
    
    client.sendReaction(message_object, action, thread_id, thread_type, reactionType=75)

def get_mitaizl():
    return {
        'wiki': handle_wikipedia_search_command  # Lệnh tìm kiếm Wikipedia
    }
