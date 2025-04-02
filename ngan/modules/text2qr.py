import json
import random
from zlapi.models import *

des = {
    'tác giả': "Rosy",
    'mô tả': "Tạo mã QR từ văn bản",
    'tính năng': [
        "📨 Tạo mã QR từ nội dung văn bản người dùng nhập.",
        "🔍 Mã hóa URL cho nội dung văn bản.",
        "🔗 Gọi API để tạo mã QR và tải xuống hình ảnh mã QR.",
        "🖼️ Gửi hình ảnh mã QR đã tạo đến người dùng.",
        "🔔 Thông báo lỗi cụ thể nếu có vấn đề xảy ra khi xử lý yêu cầu."
    ],
    'hướng dẫn sử dụng': [
        "📩 Gửi lệnh text2qr <nội dung> để tạo mã QR từ văn bản.",
        "📌 Ví dụ: text2qr Hello world! để tạo mã QR từ nội dung 'Hello world!'.",
        "✅ Nhận thông báo trạng thái và kết quả tạo mã QR ngay lập tức."
    ]
}

# Tạo các tham số màu cầu vồng cho đoạn văn bản
def create_rainbow_params(text, size=20):
    styles = []
    colors = generate_gradient_colors(len(text))  # Tạo màu cầu vồng

    # Tạo các style cho mỗi ký tự trong văn bản
    for i, color in enumerate(colors):
        styles.append({"start": i, "len": 1, "st": f"c_{color}"})  # Màu sắc cho từng ký tự
    
    # Trả về các tham số màu sắc dưới dạng JSON
    params = {"styles": styles, "ver": 0}
    return json.dumps(params)

# Chuyển màu hex thành RGB
def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

# Chuyển màu RGB thành hex
def rgb_to_hex(rgb_color):
    return '{:02x}{:02x}{:02x}'.format(*rgb_color)

# Tạo một màu ngẫu nhiên
def generate_random_color():
    return "#{:06x}".format(random.randint(0, 0xFFFFFF))

# Tạo màu đối lập (complementary color)
def generate_complementary_color(hex_color):
    rgb = hex_to_rgb(hex_color)
    complementary_rgb = (255 - rgb[0], 255 - rgb[1], 255 - rgb[2])
    return rgb_to_hex(complementary_rgb)

# Tạo gradient màu cho toàn bộ đoạn văn bản
def generate_gradient_colors(length):
    start_color = generate_random_color()  # Màu khởi tạo
    end_color = generate_random_color()    # Màu kết thúc
    start_rgb = hex_to_rgb(start_color)
    end_rgb = hex_to_rgb(end_color)

    colors = []
    for i in range(length):
        # Tính toán màu trung gian cho từng ký tự
        interpolated_color = (
            int(start_rgb[0] + (end_rgb[0] - start_rgb[0]) * i / (length - 1)),
            int(start_rgb[1] + (end_rgb[1] - start_rgb[1]) * i / (length - 1)),
            int(start_rgb[2] + (end_rgb[2] - start_rgb[2]) * i / (length - 1))
        )
        colors.append(rgb_to_hex(interpolated_color))  # Thêm màu vào danh sách
    
    return colors

# Hàm gửi tin nhắn có màu sắc cầu vồng
def sendMessageColor(message, message_object, thread_id, thread_type, author_id, client):
    custom_text = message.split(' ', 1)[1].strip() if len(message.split(' ', 1)) > 1 else ""

    # Kiểm tra độ dài văn bản, nếu <= 77 ký tự, áp dụng màu cầu vồng
    if len(custom_text) <= 77:
        style = create_rainbow_params(custom_text)  # Tạo tham số màu cầu vồng
        mes = Message(text=custom_text, style=style)
        client.send(mes, thread_id, thread_type)  # Gửi tin nhắn có màu
    else:
        client.send(Message(text=f"{custom_text}"), thread_id, thread_type)  # Gửi tin nhắn không có màu

# Hàm trả lời tin nhắn có màu sắc cầu vồng
def replyMessageColor(message, message_object, thread_id, thread_type, author_id, client):
    custom_text = message.split(' ', 1)[1].strip() if len(message.split(' ', 1)) > 1 else ""

    # Kiểm tra độ dài văn bản, nếu <= 77 ký tự, áp dụng màu cầu vồng
    if len(custom_text) <= 77:
        style = create_rainbow_params(custom_text)  # Tạo tham số màu cầu vồng
        mes = Message(text=custom_text, style=style)
        client.replyMessage(mes, message_object, thread_id, thread_type)  # Trả lời tin nhắn có màu
    else:
        client.replyMessage(Message(text=f"{custom_text}"), message_object, thread_id, thread_type)  # Trả lời tin nhắn không có màu

# Trả về hàm replyMessageColor
def get_mitaizl():
    return {
        'text': replyMessageColor
    }
