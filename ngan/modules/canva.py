import os
import random
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from zlapi.models import Message, Mention

des = {
    'tác giả': "Rosy",
    'mô tả': "Tạo ảnh với văn bản có viền đa sắc từ tin nhắn của người dùng.",
    'tính năng': [
        "📝 Tạo ảnh có chứa văn bản do người dùng nhập",
        "🎨 Viền đa sắc quanh ảnh giúp nổi bật nội dung",
        "🔠 Tự động điều chỉnh kích thước chữ để phù hợp với ảnh",
        "🌈 Hiệu ứng chuyển màu cho từng ký tự trong văn bản",
        "🖼️ Hỗ trợ nền ngẫu nhiên hoặc hình nền tùy chỉnh",
        "⚡ Gửi ảnh nhanh chóng với phản hồi tự động",
        "🗑️ Ảnh tự động xóa sau 60 giây để tránh chiếm bộ nhớ"
    ],
    'hướng dẫn sử dụng': [
        "📩 Dùng lệnh 'canva [nội dung]' để tạo ảnh với chữ theo ý muốn.",
        "📌 Ví dụ: canva Chúc mừng năm mới để tạo ảnh với chữ 'Chúc mừng năm mới'.",
        "✅ Nhận thông báo trạng thái và kết quả ngay lập tức."
    ]
}

def get_gradient_color(colors, ratio):
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

def create_rgb_colors(num_colors):
    return [
        (
            random.randint(0, 255),
            random.randint(0, 255),
            random.randint(0, 255)
        )
        for _ in range(num_colors)
    ]

def interpolate_colors(colors, text_length):
    if text_length == 0:
        return []
    
    gradient = []
    num_segments = len(colors) - 1
    steps_per_segment = max(1, (text_length // len(colors)) + 1)

    for i in range(num_segments):
        for j in range(steps_per_segment):
            if len(gradient) < text_length:
                ratio = j / steps_per_segment
                interpolated_color = (
                    int(colors[i][0] * (1 - ratio) + colors[i + 1][0] * ratio),
                    int(colors[i][1] * (1 - ratio) + colors[i + 1][1] * ratio),
                    int(colors[i][2] * (1 - ratio) + colors[i + 1][2] * ratio)
                )
                gradient.append(interpolated_color)
    
    return gradient[:text_length]

def add_multicolor_rectangle_border(image, colors, border_thickness):
    new_w = image.width + 2 * border_thickness
    new_h = image.height + 2 * border_thickness
    border_img = Image.new("RGBA", (new_w, new_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(border_img)
    # Vẽ viền trên
    for x in range(new_w):
        color = get_gradient_color(colors, x / new_w)
        draw.line([(x, 0), (x, border_thickness - 1)], fill=color)
    # Vẽ viền dưới
    for x in range(new_w):
        color = get_gradient_color(colors, x / new_w)
        draw.line([(x, new_h - border_thickness), (x, new_h - 1)], fill=color)
    # Vẽ viền trái
    for y in range(new_h):
        color = get_gradient_color(colors, y / new_h)
        draw.line([(0, y), (border_thickness - 1, y)], fill=color)
    # Vẽ viền phải
    for y in range(new_h):
        color = get_gradient_color(colors, y / new_h)
        draw.line([(new_w - border_thickness, y), (new_w - 1, y)], fill=color)
    border_img.paste(image, (border_thickness, border_thickness), image)
    return border_img

def split_text_to_lines(draw, text, font, max_width):
    """
    Tách text thành nhiều dòng (list) dựa trên:
    - Xuống dòng thủ công do người dùng nhập (khi gặp \n).
    - Xuống dòng tự động khi dòng vượt quá max_width.
    """
    if not text.strip():
        return []

    lines = []
    paragraphs = text.split('\n')

    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            lines.append("")
            continue

        words = paragraph.split(' ')
        current_line = ""

        for word in words:
            test_line = f"{current_line} {word}".strip()
            bbox = draw.textbbox((0, 0), test_line, font=font)
            text_width = bbox[2] - bbox[0]
            if text_width <= max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)

    return lines

def find_best_font_size(draw, text, font_path, max_width, max_height):
    font_size = 10
    max_font_size = 100
    best_size = font_size

    while font_size <= max_font_size:
        font = ImageFont.truetype(font_path, font_size)
        lines = split_text_to_lines(draw, text, font, max_width)
        total_text_height = sum(
            draw.textbbox((0, 0), line, font=font)[3] - draw.textbbox((0, 0), line, font=font)[1]
            for line in lines
        ) + (len(lines) - 1) * 10

        if total_text_height <= max_height:
            best_size = font_size
        else:
            break

        font_size += 2

    return best_size

def get_random_background(image_width, image_height):
    backgrounds_dir = "modules/Backgrounds"
    if os.path.exists(backgrounds_dir):
        bg_files = [f for f in os.listdir(backgrounds_dir) if f.endswith(('.jpg', '.png'))]
        if bg_files:
            bg_path = os.path.join(backgrounds_dir, random.choice(bg_files))
            return Image.open(bg_path).resize((image_width, image_height))
    return Image.new("RGB", (image_width, image_height), color=(0, 0, 0))

def get_background(image_width, image_height, background_link=None):
    """
    Cố gắng tải ảnh nền từ link nếu có.
    Nếu không có link hoặc bị lỗi => fallback về ảnh nền ngẫu nhiên.
    """
    if background_link:
        try:
            resp = requests.get(background_link, timeout=10)
            resp.raise_for_status()
            img = Image.open(BytesIO(resp.content))
            # Nếu ảnh quá nhỏ hoặc quá to => resize
            return img.resize((image_width, image_height))
        except:
            pass
    # Fallback: ảnh ngẫu nhiên
    return get_random_background(image_width, image_height)

# ============================
# HÀM DRAW_TEXT CÓ THÊM VIỀN + ĐỔ BÓNG
# ============================
def draw_text(draw, lines, position, gradient_fill, font, line_spacing, image_width):
    """
    - Vẽ mỗi ký tự 2 lần:
      1) Vẽ bóng (shadow) ở vị trí lệch (shadow_offset, shadow_offset).
      2) Vẽ chữ chính + outline (stroke) ngay vị trí gốc.
    """
    # Điều chỉnh shadow_offset, màu đổ bóng, và stroke_width, stroke_fill nếu muốn
    shadow_offset = 5
    shadow_color = (0, 0, 0)      # màu bóng đen
    stroke_width = 2
    stroke_fill = (0, 0, 0)       # viền chữ màu đen

    x, y = position
    for line in lines:
        line_gradient = gradient_fill[:len(line)] if gradient_fill else [(255, 255, 255)] * len(line)
        total_line_width = sum(
            draw.textbbox((0, 0), char, font=font)[2] - draw.textbbox((0, 0), char, font=font)[0]
            for char in line
        )
        line_start_x = (image_width - total_line_width) // 2

        for index, char in enumerate(line):
            # 1) Vẽ bóng ở vị trí lệch
            draw.text(
                (line_start_x + shadow_offset, y + shadow_offset),
                char,
                font=font,
                fill=shadow_color
            )
            # 2) Vẽ chữ chính + outline
            draw.text(
                (line_start_x, y),
                char,
                fill=line_gradient[index],
                font=font,
                stroke_width=stroke_width,
                stroke_fill=stroke_fill
            )
            # Tính độ rộng ký tự
            char_width = draw.textbbox((line_start_x, y), char, font=font)[2] - draw.textbbox((line_start_x, y), char, font=font)[0]
            line_start_x += char_width
        
        # Khoảng cách giữa các dòng
        bbox = draw.textbbox((0, 0), line, font=font)
        line_height = bbox[3] - bbox[1]
        y += line_height + line_spacing

def handle_create_image_command(message, message_object, thread_id, thread_type, author_id, client):
    try:
        splitted = message.strip().split(" ", 1)
        if len(splitted) < 2 or not splitted[1].strip():
            client.replyMessage(
                Message(
                    text="@Member, vui lòng cung cấp nội dung cần tạo ảnh!",
                    mention=Mention(author_id, length=len("@Member"), offset=0)
                ),
                message_object, thread_id, thread_type, ttl=20000
            )
            return
        
        remainder = splitted[1].strip()
        splitted2 = remainder.rsplit(" ", 1)

        if len(splitted2) == 2 and (
            splitted2[1].startswith("http://") or splitted2[1].startswith("https://")
        ):
            content = splitted2[0]
            background_link = splitted2[1]
        else:
            content = remainder
            background_link = None

        if not content.strip():
            content = "Nội dung trống"

        image_width, image_height = 800, 333
        output_path = "modules/cache/temp_image_with_text.jpg"
        
        # Lấy ảnh nền
        image = get_background(image_width, image_height, background_link)
        draw = ImageDraw.Draw(image)
        font_path = os.path.abspath("modules/Font/NotoSans-Bold.ttf")
        
        # Tìm kích thước phông chữ phù hợp
        best_font_size = find_best_font_size(draw, content, font_path,
                                             max_width=int(image_width * 0.9),
                                             max_height=int(image_height * 0.8))
        font = ImageFont.truetype(font_path, best_font_size)
        
        # Bảng màu cầu vồng
        gradient_colors = [(255,0,0), (255,165,0), (255,255,0), (0,255,0), (0,0,255), (75,0,130), (148,0,211)]
        gradient_fill = interpolate_colors(gradient_colors, len(content))
        
        max_width = int(image_width * 0.9)
        lines = split_text_to_lines(draw, content, font, max_width)
        total_text_height = sum(
            draw.textbbox((0, 0), line, font=font)[3] - draw.textbbox((0, 0), line, font=font)[1]
            for line in lines
        ) + (len(lines) - 1) * 10
        y_start = (image_height - total_text_height) // 2
        
        # Vẽ văn bản (có bóng + viền)
        draw_text(draw, lines, (0, y_start), gradient_fill, font, line_spacing=10, image_width=image_width)
        
        # Thêm viền đa sắc quanh khung
        border_thickness = 10
        image = image.convert("RGBA")
        image = add_multicolor_rectangle_border(image, gradient_colors, border_thickness)
        image = image.convert("RGB")
        
        # Lưu ảnh và gửi lại
        image.save(output_path)
        if os.path.exists(output_path):
            client.sendLocalImage(
                output_path,
                message=Message(text="@Member", mention=Mention(author_id, length=len("@Member"), offset=0)),
                thread_id=thread_id,
                thread_type=thread_type,
                width=1600,
                height=666,
                ttl=60000
            )
            os.remove(output_path)
        else:
            raise Exception("Không thể lưu ảnh.")

    except Exception as e:
        client.sendMessage(Message(text=f"Đã xảy ra lỗi: {str(e)}"), thread_id, thread_type)

def get_mitaizl():
    return {
        'canva': handle_create_image_command
    }
