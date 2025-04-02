import os
import math
import pytz
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
from zlapi.models import Message, Mention

# ---------------------------
# Các hàm hỗ trợ cho gradient
# ---------------------------
def get_gradient_color(colors, ratio):
    """
    Nội suy màu dựa trên danh sách màu colors và giá trị ratio trong [0, 1].
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
# Hàm tạo viền đa sắc cho khung ảnh
# ---------------------------
def add_multicolor_rectangle_border(image, colors, border_thickness):
    """
    Thêm viền đa sắc liền mạch quanh khung ảnh.
    - image: ảnh gốc (RGBA)
    - colors: danh sách màu dùng để tạo gradient cho viền
    - border_thickness: độ dày của viền
    """
    new_w = image.width + 2 * border_thickness
    new_h = image.height + 2 * border_thickness
    border_img = Image.new("RGBA", (new_w, new_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(border_img)
    # Vẽ top border
    for x in range(new_w):
        color = get_gradient_color(colors, x / new_w)
        draw.line([(x, 0), (x, border_thickness - 1)], fill=color)
    # Vẽ bottom border
    for x in range(new_w):
        color = get_gradient_color(colors, x / new_w)
        draw.line([(x, new_h - border_thickness), (x, new_h - 1)], fill=color)
    # Vẽ left border
    for y in range(new_h):
        color = get_gradient_color(colors, y / new_h)
        draw.line([(0, y), (border_thickness - 1, y)], fill=color)
    # Vẽ right border
    for y in range(new_h):
        color = get_gradient_color(colors, y / new_h)
        draw.line([(new_w - border_thickness, y), (new_w - 1, y)], fill=color)
    border_img.paste(image, (border_thickness, border_thickness), image)
    return border_img

# ---------------------------
# Hàm tạo viền đa sắc cho mặt đồng hồ
# ---------------------------
def add_multicolor_clock_border(clock_face, center, radius, border_width, colors):
    """
    Thêm viền đa sắc cho mặt đồng hồ.
    - clock_face: ảnh mặt đồng hồ (RGBA)
    - center: tọa độ tâm của mặt đồng hồ (tuple)
    - radius: bán kính của mặt đồng hồ
    - border_width: độ dày của viền (số bước)
    - colors: danh sách màu dùng để tạo gradient
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
# Hàm tạo nền radial gradient
# ---------------------------
def create_radial_gradient_background(width, height, start_color, end_color):
    """
    Tạo ảnh nền với gradient hướng tâm (radial gradient).
    start_color và end_color là tuple (R, G, B).
    """
    bg = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    center_x, center_y = width // 2, height // 2
    max_dist = math.sqrt(center_x ** 2 + center_y ** 2)
    px = bg.load()
    for y in range(height):
        for x in range(width):
            dx = x - center_x
            dy = y - center_y
            dist = math.sqrt(dx * dx + dy * dy)
            ratio = min(dist / max_dist, 1)
            r = int(start_color[0] + (end_color[0] - start_color[0]) * ratio)
            g = int(start_color[1] + (end_color[1] - start_color[1]) * ratio)
            b = int(start_color[2] + (end_color[2] - start_color[2]) * ratio)
            px[x, y] = (r, g, b, 255)
    return bg.convert("RGB")

# ---------------------------
# Hàm xử lý hình ảnh đồng hồ
# ---------------------------
def create_enhanced_clock_face(width, height, center, radius, base_color=(240, 240, 240)):
    """
    Tạo mặt đồng hồ với hiệu ứng gradient nội bộ và viền đa sắc mềm mại.
    """
    clock_face = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(clock_face)
    # Vẽ gradient nội bộ: ánh sáng hơn ở trung tâm, tối dần ra rìa
    for r in range(radius, 0, -1):
        ratio = r / radius
        r_color = int(base_color[0] * (0.8 + 0.2 * ratio))
        g_color = int(base_color[1] * (0.8 + 0.2 * ratio))
        b_color = int(base_color[2] * (0.8 + 0.2 * ratio))
        draw.ellipse([
            center[0] - r, center[1] - r,
            center[0] + r, center[1] + r
        ], fill=(r_color, g_color, b_color, 255))
    # Thêm viền đa sắc cho mặt đồng hồ (sử dụng border_width = 6)
    multicolor_border = [(255, 0, 0), (255, 165, 0), (255, 255, 0),
                         (0, 255, 0), (0, 0, 255), (75, 0, 130), (148, 0, 211)]
    clock_face = add_multicolor_clock_border(clock_face, center, radius, border_width=6, colors=multicolor_border)
    return clock_face

# ---------------------------
# Hàm vẽ văn bản gradient
# ---------------------------
def draw_gradient_text(draw, text, position, font, gradient_colors, shadow_offset=(2, 2), outline_thickness=1):
    gradient = interpolate_colors(gradient_colors, text_length=len(text), change_every=4)
    x, y = position
    shadow_color = (0, 0, 0)
    for i in range(len(text)):
        char = text[i]
        char_color = tuple(gradient[i])
        draw.text((x + shadow_offset[0], y + shadow_offset[1]), char, font=font, fill=shadow_color)
        draw.text((x, y), char, font=font, fill=char_color)
        char_width = draw.textbbox((0, 0), char, font=font)[2]
        x += char_width

def draw_centered_text(draw, text, position, font, gradient_colors, background):
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    x_position = (background.width - text_width) // 2
    if x_position < 450:
        x_position = 450
    draw_gradient_text(draw, text, (x_position, position[1]), font, gradient_colors)

# ---------------------------
# Hàm tạo ảnh đồng hồ (time command)
# ---------------------------
def create_clock_image():
    """
    Tạo ảnh đồng hồ hiển thị thời gian hiện tại theo múi giờ Hồ Chí Minh.
    """
    # Kích thước ảnh
    image_width = image_height = 800
    # Tạo nền radial gradient
    start_color = (180, 210, 255)
    end_color = (100, 120, 255)
    background = create_radial_gradient_background(image_width, image_height, start_color, end_color)
    draw = ImageDraw.Draw(background)
    # Xác định tâm và bán kính mặt đồng hồ
    center = (image_width // 2, image_height // 2)
    radius = 300

    # Tạo layer bóng cho mặt đồng hồ
    shadow_layer = Image.new("RGBA", (image_width, image_height), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow_layer)
    shadow_offset = 10
    shadow_bbox = [
        center[0] - radius + shadow_offset,
        center[1] - radius + shadow_offset,
        center[0] + radius + shadow_offset,
        center[1] + radius + shadow_offset
    ]
    shadow_draw.ellipse(shadow_bbox, fill=(0, 0, 0, 200))
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(20))
    background.paste(shadow_layer, (0, 0), shadow_layer)

    # Vẽ mặt đồng hồ với gradient nội bộ và viền đa sắc
    clock_face = create_enhanced_clock_face(image_width, image_height, center, radius)
    background.paste(clock_face, (0, 0), clock_face)

    # Vẽ vạch giờ và số (hiệu ứng gradient cho số)
    font_path = os.path.abspath("modules/Font/NotoSans-Bold.ttf")
    label_font = ImageFont.truetype(font_path, 30)
    tick_length = 25
    gradient_colors = [(255, 0, 0), (255, 165, 0), (255, 255, 0),
                       (0, 255, 0), (0, 0, 255), (75, 0, 130), (148, 0, 211)]
    for i in range(12):
        angle = math.radians(i * 30 - 90)
        start_pt = (
            center[0] + (radius - tick_length) * math.cos(angle),
            center[1] + (radius - tick_length) * math.sin(angle)
        )
        end_pt = (
            center[0] + radius * math.cos(angle),
            center[1] + radius * math.sin(angle)
        )
        draw.line([start_pt, end_pt], fill=(0, 0, 0), width=4)
        hour_label = i if i > 0 else 12
        label = str(hour_label)
        label_radius = radius - 60
        label_x = center[0] + label_radius * math.cos(angle)
        label_y = center[1] + label_radius * math.sin(angle)
        text_bbox = draw.textbbox((0, 0), label, font=label_font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        draw_gradient_text(draw, label, (label_x - text_width/2, label_y - text_height/2), label_font, gradient_colors)

    # Vẽ vạch phụ cho phút
    minor_tick_length = 10
    for i in range(60):
        if i % 5 != 0:
            angle = math.radians(i * 6 - 90)
            start_pt = (
                center[0] + (radius - minor_tick_length) * math.cos(angle),
                center[1] + (radius - minor_tick_length) * math.sin(angle)
            )
            end_pt = (
                center[0] + radius * math.cos(angle),
                center[1] + radius * math.sin(angle)
            )
            draw.line([start_pt, end_pt], fill=(0, 0, 0), width=2)

    # Lấy thời gian hiện tại theo múi giờ Hồ Chí Minh
    hcm_tz = pytz.timezone('Asia/Ho_Chi_Minh')
    current_time = datetime.now(hcm_tz)
    hour = current_time.hour
    minute = current_time.minute
    second = current_time.second

    # Tính góc cho các kim đồng hồ
    hour_angle = math.radians((hour % 12 + minute / 60.0) * 30 - 90)
    minute_angle = math.radians((minute + second / 60.0) * 6 - 90)
    second_angle = math.radians(second * 6 - 90)
    hour_hand_length = radius * 0.5
    minute_hand_length = radius * 0.7
    second_hand_length = radius * 0.85

    # Vẽ kim giờ (polygon)
    hour_end = (
        center[0] + hour_hand_length * math.cos(hour_angle),
        center[1] + hour_hand_length * math.sin(hour_angle)
    )
    hour_polygon = [
        (center[0] - 5, center[1]),
        (center[0] + 5, center[1]),
        (hour_end[0] + 3, hour_end[1]),
        (hour_end[0] - 3, hour_end[1])
    ]
    draw.polygon(hour_polygon, fill=(0, 0, 0))

    # Vẽ kim phút (polygon)
    minute_end = (
        center[0] + minute_hand_length * math.cos(minute_angle),
        center[1] + minute_hand_length * math.sin(minute_angle)
    )
    minute_polygon = [
        (center[0] - 4, center[1]),
        (center[0] + 4, center[1]),
        (minute_end[0] + 2, minute_end[1]),
        (minute_end[0] - 2, minute_end[1])
    ]
    draw.polygon(minute_polygon, fill=(50, 50, 50))

    # Vẽ kim giây (line)
    second_end = (
        center[0] + second_hand_length * math.cos(second_angle),
        center[1] + second_hand_length * math.sin(second_angle)
    )
    draw.line([center, second_end], fill=(255, 0, 0), width=2)

    # Vẽ chấm trung tâm
    center_radius = 10
    draw.ellipse([
        center[0] - center_radius, center[1] - center_radius,
        center[0] + center_radius, center[1] + center_radius
    ], fill=(0, 0, 0))

    # Vẽ thời gian dạng số bên dưới đồng hồ với hiệu ứng gradient
    time_str = current_time.strftime('%H:%M:%S')
    date_str = current_time.strftime('%d-%m-%Y')
    digital_text = f"{time_str} - {date_str}"
    text_font = ImageFont.truetype(font_path, 40)
    text_bbox = draw.textbbox((0, 0), digital_text, font=text_font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    text_x = center[0] - text_width // 2
    text_y = center[1] + radius + 20
    draw_gradient_text(draw, digital_text, (text_x, text_y), text_font, gradient_colors)

    # Tạo ảnh cuối cùng với viền đa sắc quanh khung ảnh
    multicolor_frame = [(255, 0, 0), (255, 165, 0), (255, 255, 0),
                        (0, 255, 0), (0, 0, 255), (75, 0, 130), (148, 0, 211)]
    final_image = add_multicolor_rectangle_border(background.convert("RGBA"), multicolor_frame, border_thickness=10)
    return final_image

# ---------------------------
# Hàm xử lý lệnh "time" (gửi ảnh đồng hồ)
# ---------------------------
def handle_create_timenow_image_command(message, message_object, thread_id, thread_type, author_id, client):
    try:
        final_image = create_clock_image()
        output_path = "modules/cache/temp_analog_clock.jpg"
        final_image = final_image.convert("RGB")
        final_image.save(output_path)
        if os.path.exists(output_path):
            client.sendLocalImage(
                output_path,
                message=Message(text="@Member", mention=Mention(author_id, length=len("@Member"), offset=0)),
                thread_id=thread_id,
                thread_type=thread_type,
                width=800,
                height=800,
                ttl=30000
            )
            os.remove(output_path)
        else:
            raise Exception("Không thể lưu ảnh.")
    except Exception as e:
        client.sendMessage(Message(text=f"Đã xảy ra lỗi: {str(e)}"), thread_id, thread_type)

def get_mitaizl():
    return {
        'time': handle_create_timenow_image_command
    }
