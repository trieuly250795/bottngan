import os
import pytz
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from zlapi.models import Message, Mention
from forex_python.converter import CurrencyRates

des = {
    'tác giả': "Rosy",
    'mô tả': "Hiển thị tỷ giá ngoại tệ",
    'tính năng': [
        "💹 Lấy tỷ giá hối đoái so với VND cho các đồng tiền phổ biến.",
        "🎨 Vẽ văn bản với hiệu ứng gradient và bóng đổ.",
        "🖼️ Tạo ảnh hiển thị tỷ giá với viền đa sắc và góc bo tròn.",
        "🕒 Hiển thị thời gian cập nhật tỷ giá.",
        "🔍 Thông báo lỗi cụ thể nếu có vấn đề xảy ra khi xử lý yêu cầu."
    ],
    'hướng dẫn sử dụng': [
        "📩 Gửi lệnh tygia để hiển thị tỷ giá ngoại tệ hiện tại.",
        "📌 Ví dụ: tygia để lấy và hiển thị tỷ giá của các đồng tiền phổ biến so với VND.",
        "✅ Nhận thông báo trạng thái và kết quả ngay lập tức."
    ]
}

# ---------------------------
# Các hàm hỗ trợ cho hiệu ứng gradient
# ---------------------------
def get_gradient_color(colors, ratio):
    """Nội suy màu dựa trên danh sách màu 'colors' và giá trị 'ratio' trong khoảng [0, 1]."""
    if ratio <= 0:
        return colors[0]
    if ratio >= 1:
        return colors[-1]
    total_segments = len(colors) - 1
    segment = int(ratio * total_segments)
    segment_ratio = (ratio * total_segments) - segment
    c1 = colors[segment]
    c2 = colors[segment + 1]
    r = int(c1[0] * (1 - segment_ratio) + c2[0] * segment_ratio)
    g = int(c1[1] * (1 - segment_ratio) + c2[1] * segment_ratio)
    b = int(c1[2] * (1 - segment_ratio) + c2[2] * segment_ratio)
    return (r, g, b)

def draw_gradient_text(draw, text, position, font, gradient_colors, shadow_offset=(2, 2)):
    """Vẽ văn bản với hiệu ứng gradient và bóng đổ."""
    gradient = []
    text_length = len(text)
    for i in range(text_length):
        ratio = i / max(text_length - 1, 1)
        gradient.append(get_gradient_color(gradient_colors, ratio))
    x, y = position
    shadow_color = (0, 0, 0)
    for i, char in enumerate(text):
        # Vẽ bóng đổ cho từng ký tự
        draw.text((x + shadow_offset[0], y + shadow_offset[1]), char, font=font, fill=shadow_color)
        # Vẽ ký tự với màu sắc gradient
        draw.text((x, y), char, font=font, fill=gradient[i])
        char_width = draw.textbbox((0, 0), char, font=font)[2]
        x += char_width

def add_multicolor_rectangle_border(image, colors, border_thickness):
    """Thêm viền đa sắc cho ảnh với độ dày 'border_thickness'."""
    new_w = image.width + 2 * border_thickness
    new_h = image.height + 2 * border_thickness
    border_img = Image.new("RGBA", (new_w, new_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(border_img)
    # Vẽ cạnh trên và dưới
    for x in range(new_w):
        color = get_gradient_color(colors, x / new_w)
        draw.line([(x, 0), (x, border_thickness - 1)], fill=color)
        draw.line([(x, new_h - border_thickness), (x, new_h - 1)], fill=color)
    # Vẽ cạnh trái và phải
    for y in range(new_h):
        color = get_gradient_color(colors, y / new_h)
        draw.line([(0, y), (border_thickness - 1, y)], fill=color)
        draw.line([(new_w - border_thickness, y), (new_w - 1, y)], fill=color)
    # Dán ảnh gốc lên ảnh viền
    image_rgba = image.convert("RGBA")
    border_img.paste(image_rgba, (border_thickness, border_thickness), image_rgba)
    return border_img

def round_corners(image, radius):
    """Bo tròn 4 góc của ảnh với bán kính 'radius'."""
    mask = Image.new('L', image.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([(0, 0), image.size], radius=radius, fill=255)
    image.putalpha(mask)
    return image

# ---------------------------
# Tỷ giá ngoại tệ
# ---------------------------
# Danh sách 10 đồng tiền phổ biến
CURRENCIES = ["USD", "EUR", "GBP", "JPY", "CNY", "AUD", "CAD", "SGD", "KRW", "THB"]

def get_exchange_rates():
    """Lấy tỷ giá hối đoái so với VND bằng forex-python."""
    c = CurrencyRates()
    rates = {}
    for currency in CURRENCIES:
        try:
            rates[currency] = c.convert(currency, "VND", 1)
        except Exception:
            rates[currency] = "N/A"
    return rates

def create_exchange_rate_image():
    """Tạo ảnh hiển thị tỷ giá hối đoái với hiệu ứng gradient, viền đa sắc và góc bo tròn."""
    rates = get_exchange_rates()
    # Lấy thời gian hiện tại theo múi giờ Việt Nam
    hcm_tz = pytz.timezone('Asia/Ho_Chi_Minh')
    current_time = datetime.now(hcm_tz).strftime("%H:%M %d/%m/%Y")
    
    # Kích thước ảnh
    width, height = 600, 600
    output_path = "modules/cache/temp_exchange_rates.jpg"
    
    # Tạo ảnh nền đơn sắc
    background = Image.new("RGB", (width, height), (230, 230, 250))
    draw = ImageDraw.Draw(background)
    
    # Đường dẫn font chữ
    font_path = os.path.abspath("modules/Font/NotoSans-Bold.ttf")
    title_font = ImageFont.truetype(font_path, 40)
    text_font = ImageFont.truetype(font_path, 30)
    
    # Định nghĩa danh sách màu gradient
    gradient_colors = [
        (255, 0, 0), (255, 165, 0), (255, 255, 0),
        (0, 255, 0), (0, 0, 255), (75, 0, 130), (148, 0, 211)
    ]
    
    # Vẽ tiêu đề (căn giữa theo chiều ngang)
    title_text = "Tỷ giá ngoại tệ (VND)"
    title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
    title_width = title_bbox[2] - title_bbox[0]
    title_x = (width - title_width) // 2
    draw_gradient_text(draw, title_text, (title_x, 20), title_font, gradient_colors)
    
    # Hiển thị danh sách tỷ giá
    y_offset = 100
    for currency, rate in rates.items():
        rate_str = f"{rate:,.2f}" if rate != "N/A" else rate
        line_text = f"{currency}: {rate_str} VND"
        draw_gradient_text(draw, line_text, (40, y_offset), text_font, gradient_colors)
        y_offset += 40
    
    # Hiển thị thời gian cập nhật, căn giữa
    time_text = f"Cập nhật: {current_time}"
    time_bbox = draw.textbbox((0, 0), time_text, font=text_font)
    time_width = time_bbox[2] - time_bbox[0]
    time_x = (width - time_width) // 2
    draw_gradient_text(draw, time_text, (time_x, y_offset + 20), text_font, gradient_colors)
    
    # Thêm viền đa sắc quanh khung ảnh
    border_thickness = 10
    bordered_img = add_multicolor_rectangle_border(background, gradient_colors, border_thickness)
    
    # Bo tròn 4 góc của ảnh (bao gồm cả viền)
    final_img = round_corners(bordered_img, radius=20)
    
    # Chuyển về RGB nếu cần lưu dưới định dạng JPEG (không hỗ trợ alpha)
    final_img = final_img.convert("RGB")
    final_img.save(output_path)
    return output_path

def handle_exchange_rate_command(message, message_object, thread_id, thread_type, author_id, client):
    # Gửi phản ứng ngay khi người dùng soạn đúng lệnh
    action = "✅"
    client.sendReaction(message_object, action, thread_id, thread_type, reactionType=75)
    
    # Gửi thông báo ban đầu
    reply_message = "Đang tiến hành lấy tỷ giá hối đoái hôm nay ..."
    client.sendMessage(Message(text=reply_message), thread_id, thread_type, ttl=30000)
    
    try:
        image_path = create_exchange_rate_image()
        if os.path.exists(image_path):
            # Gửi ảnh tỷ giá kèm tin nhắn, sử dụng mention để tag người dùng nếu cần
            client.sendLocalImage(
                image_path,
                message=Message(text="@Member", mention=Mention(author_id, length=len("@Member"), offset=0)),
                thread_id=thread_id,
                thread_type=thread_type,
                width=600,
                height=600,
                ttl=30000
            )
            os.remove(image_path)
        else:
            raise Exception("Không thể lưu ảnh.")
    except Exception as e:
        client.sendMessage(Message(text=f"Đã xảy ra lỗi: {str(e)}"), thread_id, thread_type)

def get_mitaizl():
    """Trả về danh sách các lệnh hỗ trợ trong bot."""
    return {
        'tygia': handle_exchange_rate_command
    }
