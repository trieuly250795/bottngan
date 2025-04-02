import os
import math
import random
import pytz
import lunarcalendar
import textwrap
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
from zlapi.models import Message, Mention

# ---------------------------
# HÀM HỖ TRỢ CHO GRADIENT
# ---------------------------
def get_gradient_color(colors, ratio):
    """
    Nội suy màu dựa trên danh sách màu 'colors' và giá trị ratio trong [0, 1].
    """
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

def interpolate_colors(colors, text_length, change_every):
    """
    Tạo danh sách các màu gradient theo số lượng ký tự 'text_length'.
    """
    gradient = []
    num_segments = len(colors) - 1
    steps_per_segment = (text_length // change_every) + 1
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
    while len(gradient) < text_length:
        gradient.append(colors[-1])
    return gradient[:text_length]

# ---------------------------
# HÀM TẠO VIỀN ĐA SẮC
# ---------------------------
def add_multicolor_rectangle_border(image, colors, border_thickness):
    """
    Thêm viền đa sắc cho ảnh theo dạng hình chữ nhật.
    """
    new_w = image.width + 2 * border_thickness
    new_h = image.height + 2 * border_thickness
    border_img = Image.new("RGBA", (new_w, new_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(border_img)
    # Vẽ top và bottom border
    for x in range(new_w):
        color = get_gradient_color(colors, x / new_w)
        draw.line([(x, 0), (x, border_thickness - 1)], fill=color)
        draw.line([(x, new_h - border_thickness), (x, new_h - 1)], fill=color)
    # Vẽ left và right border
    for y in range(new_h):
        color = get_gradient_color(colors, y / new_h)
        draw.line([(0, y), (border_thickness - 1, y)], fill=color)
        draw.line([(new_w - border_thickness, y), (new_w - 1, y)], fill=color)
    border_img.paste(image, (border_thickness, border_thickness), image)
    return border_img

def add_multicolor_clock_border(clock_face, center, radius, border_width, colors):
    """
    Vẽ viền gradient cho mặt đồng hồ với các vòng tròn dần dần.
    """
    draw = ImageDraw.Draw(clock_face)
    for offset in range(border_width):
        ratio = offset / (border_width - 1) if border_width > 1 else 0
        color = get_gradient_color(colors, ratio)
        draw.ellipse([
            center[0] - radius - offset,
            center[1] - radius - offset,
            center[0] + radius + offset,
            center[1] + radius + offset
        ], outline=color)
    return clock_face

# ---------------------------
# HÀM VẼ VĂN BẢN THEO GRADIENT
# ---------------------------
def draw_gradient_text(draw, text, position, font, gradient_colors, shadow_offset=(2,2)):
    """
    Vẽ từng ký tự của văn bản với hiệu ứng gradient và bóng mờ.
    """
    gradient = interpolate_colors(gradient_colors, text_length=len(text), change_every=4)
    x, y = position
    shadow_color = (0, 0, 0)
    for i, char in enumerate(text):
        char_color = gradient[i]
        # Vẽ bóng mờ
        draw.text((x + shadow_offset[0], y + shadow_offset[1]), char, font=font, fill=shadow_color)
        # Vẽ chữ chính
        draw.text((x, y), char, font=font, fill=char_color)
        char_width = draw.textbbox((0, 0), char, font=font)[2]
        x += char_width

def draw_centered_text(draw, text, position, font, gradient_colors, background):
    """
    Căn giữa văn bản theo chiều ngang trên nền cho trước.
    """
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    x_position = (background.width - text_width) // 2
    draw_gradient_text(draw, text, (x_position, position[1]), font, gradient_colors)

def draw_wrapped_gradient_text(draw, text, position, font, gradient_colors, max_width):
    """
    Vẽ văn bản được bọc dòng theo gradient, căn giữa theo chiều ngang.
    """
    words = text.split()
    lines = []
    current_line = ""
    for word in words:
        test_line = current_line + " " + word if current_line else word
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    y_offset = 0
    for line in lines:
        line_bbox = draw.textbbox((0, 0), line, font=font)
        line_height = line_bbox[3] - line_bbox[1]
        line_width = line_bbox[2] - line_bbox[0]
        x_position = position[0] + (max_width - line_width) // 2
        draw_gradient_text(draw, line, (x_position, position[1] + y_offset), font, gradient_colors)
        y_offset += line_height + 5

# ---------------------------
# HÀM TẠO ẢNH LỊCH ÂM VỚI HIỆU ỨNG VĂN BẢN GRADIENT
# ---------------------------
def create_lunar_calendar_image():
    """
    Tạo ảnh lịch âm với nền ngẫu nhiên, chữ gradient và overlay mờ bao bọc vùng chữ.
    Trả về đường dẫn đến ảnh được lưu.
    """
    # Lấy thời gian hiện tại theo múi giờ TP.HCM và chuyển sang âm lịch
    hcm_tz = pytz.timezone('Asia/Ho_Chi_Minh')
    current_time = datetime.now(hcm_tz)
    lunar_date = lunarcalendar.Converter.Solar2Lunar(current_time)
    
    # Lấy thông tin ngày dương và âm
    day_solar, month_solar, year_solar = current_time.day, current_time.month, current_time.year
    day_lunar, month_lunar, year_lunar = lunar_date.day, lunar_date.month, lunar_date.year
    weekdays = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]
    weekday_solar = weekdays[current_time.weekday()]
    
    # Các thông tin bổ sung
    zodiac_hours = get_zodiac_hours()
    good_bad_day = get_good_bad_day()
    historical_event = get_historical_event()
    seasonal_event = get_seasonal_event(month_solar, day_solar)
    
    # Thiết lập kích thước ảnh và đường dẫn lưu
    width, height = 600, 900
    output_path = "modules/cache/temp_lunar_calendar.jpg"
    
    # Lấy ảnh nền ngẫu nhiên từ thư mục (nếu có)
    background_dir = "modules/hinhnenamlich"
    image_files = [os.path.join(background_dir, file) for file in os.listdir(background_dir) 
                   if file.lower().endswith(('.png', '.jpg', '.jpeg'))]
    if image_files:
        background_path = random.choice(image_files)
        background = Image.open(background_path).convert("RGB").resize((width, height))
    else:
        background = Image.new("RGB", (width, height), (255, 250, 240))
    
    # Chuyển nền sang RGBA để hỗ trợ alpha
    background = background.convert("RGBA")
    
    # Thiết lập font chữ (sử dụng font NotoSans-Bold)
    font_path = os.path.abspath("modules/Font/NotoSans-Bold.ttf")
    title_font = ImageFont.truetype(font_path, 70)
    date_font = ImageFont.truetype(font_path, 120)
    small_font = ImageFont.truetype(font_path, 24)
    
    # Danh sách màu gradient cho văn bản (hiệu ứng cầu vồng)
    text_gradient = [(255,0,0), (255,165,0), (255,255,0), (0,255,0), (0,0,255), (75,0,130), (148,0,211)]
    
    # Tạo danh sách các khối văn bản với định dạng (văn bản, font, wrapped)
    blocks = []
    blocks.append(("Lịch Âm", title_font, False))
    blocks.append((str(day_lunar), date_font, False))
    blocks.append((f"Tháng {month_lunar} - {year_lunar}", small_font, False))
    solar_text = f"{weekday_solar}, {day_solar:02d}/{month_solar:02d}/{year_solar}"
    blocks.append((solar_text, small_font, False))
    blocks.append((zodiac_hours, small_font, True))
    blocks.append((good_bad_day, small_font, True))
    blocks.append((historical_event, small_font, True))
    if seasonal_event:
        blocks.append((f"Tiết khí: {seasonal_event}", small_font, True))
    
    # Tạo đối tượng Draw tạm thời để đo kích thước văn bản
    temp_draw = ImageDraw.Draw(background)
    text_heights = []
    for text, font, wrapped in blocks:
        if not wrapped:
            bbox = temp_draw.textbbox((0, 0), text, font=font)
            block_height = bbox[3] - bbox[1]
        else:
            lines = textwrap.wrap(text, width=40)
            # Dùng font truyền vào thay vì cứng small_font
            bbox = temp_draw.textbbox((0, 0), "A", font=font)
            line_height = bbox[3] - bbox[1]
            block_height = len(lines) * line_height + (len(lines) - 1) * 5
        text_heights.append(block_height)
    
    total_text_height = sum(text_heights)
    n = len(blocks)
    gap = (height - total_text_height) // (n + 1)
    
    starting_offset = 20
    starting_y = max(gap - starting_offset, 0)
    
    # Tính vị trí cuối cùng của văn bản để xác định vùng chứa
    current_y = starting_y
    for block_height in text_heights:
        current_y += block_height + gap
    final_y = current_y - gap
    
    # Xác định vùng chữ nhật bao bọc với margin
    margin_x, margin_y = 50, 30
    rect_box = (margin_x,
                max(starting_y - margin_y, 0),
                width - margin_x,
                min(final_y + margin_y, height))
    
    # Tạo overlay với hình chữ nhật bán trong suốt, bo góc và hiệu ứng mờ
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.rounded_rectangle(rect_box, radius=50, fill=(255, 255, 255, 100))
    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=5))
    
    # Hợp layer overlay vào nền
    combined = Image.alpha_composite(background, overlay)
    draw = ImageDraw.Draw(combined)
    
    # Vẽ các khối văn bản với khoảng cách đều
    current_y = starting_y
    for i, ((text, font, wrapped), block_height) in enumerate(zip(blocks, text_heights)):
        # Nếu đây là khối ngày âm (index 1) thì nâng thêm 40 pixel
        draw_y = current_y - 40 if i == 1 else current_y
        if not wrapped:
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            x_position = (width - text_width) // 2
            draw_gradient_text(draw, text, (x_position, draw_y), font, text_gradient)
        else:
            draw_wrapped_gradient_text(draw, text, (30, draw_y), font, text_gradient, max_width=width - 60)
        current_y += block_height + gap

    combined = combined.convert("RGB")
    combined.save(output_path)
    return output_path

# ---------------------------
# HÀM TRỢ GIÚP (Nội dung cố định)
# ---------------------------
def get_zodiac_hours():
    return ("Giờ hoàng đạo: Tý, Sửu, Mão, Ngọ, Thân, Dậu\n"
            "Giờ hắc đạo: Dần, Thìn, Tỵ, Mùi, Tuất, Hợi")

def get_good_bad_day():
    return "Ngày tốt để xuất hành, cưới hỏi. Không tốt cho xây dựng."

def get_historical_event():
    return "Sự kiện: Ngày này năm 1945, Việt Nam giành độc lập."

def get_seasonal_event(month, day):
    seasonal_events = {
        (3, 21): "Xuân phân",
        (6, 21): "Hạ chí",
        (9, 23): "Thu phân",
        (12, 22): "Đông chí"
    }
    return seasonal_events.get((month, day), "")

# ---------------------------
# XỬ LÝ LỆNH "amlich" (Gửi ảnh Lịch Âm)
# ---------------------------
def handle_create_lunar_calendar_command(message, message_object, thread_id, thread_type, author_id, client):
    try:
        image_path = create_lunar_calendar_image()
        if os.path.exists(image_path):
            client.sendLocalImage(
                image_path,
                message=Message(
                    text="@Member", 
                    mention=Mention(author_id, length=len("@Member"), offset=0)
                ),
                thread_id=thread_id,
                thread_type=thread_type,
                width=600,
                height=900,
                ttl=30000
            )
            os.remove(image_path)
        else:
            raise Exception("Không thể lưu ảnh.")
    except Exception as e:
        client.sendMessage(Message(text=f"Đã xảy ra lỗi: {str(e)}"), thread_id, thread_type)

def get_mitaizl():
    return {
        'amlich': handle_create_lunar_calendar_command
    }
