from zlapi import ZaloAPI, ZaloAPIException
from zlapi.models import *
from zlapi.models import Message, Mention
from threading import Thread
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
import requests
from io import BytesIO
import os
import random
import logging
import math
from datetime import datetime, timezone, timedelta

des = {
    'version': "1.0.1",
    'credits': "ROSY FIX",
    'description': "WELCOM"
}

logging.basicConfig(
    level=logging.ERROR,
    filename="bot_error.log",
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ------------------ HẰNG SỐ CHUNG & ẢNH NỀN ------------------
MULTICOLOR_GRADIENT = [
    (255, 0, 0), (255, 165, 0), (255, 255, 0),
    (0, 255, 0), (0, 0, 255), (75, 0, 130), (148, 0, 211)
]
# Định nghĩa nhiều dải màu gradient
GRADIENT_SETS = [
    # Dải màu Neon sặc sỡ
    [(255, 0, 255), (0, 255, 255), (255, 255, 0), (0, 255, 0)],

    # Dải màu cầu vồng rực rỡ
    [(255, 0, 0), (255, 165, 0), (255, 255, 0), (0, 128, 0), (0, 0, 255), (75, 0, 130), (148, 0, 211)],

    # Dải màu pastel nhẹ nhàng
    [(255, 182, 193), (173, 216, 230), (152, 251, 152), (240, 230, 140)],

    # Dải màu hoàng hôn
    [(255, 94, 77), (255, 160, 122), (255, 99, 71), (255, 215, 0)],

    # Dải màu vàng - cam - đỏ rực cháy
    [(255, 165, 0), (255, 69, 0), (220, 20, 60), (255, 0, 0)],

    # Dải màu hồng ngọt ngào
    [(255, 182, 193), (255, 105, 180), (255, 20, 147), (255, 0, 255)],

    # Dải màu xanh lá - xanh dương đại dương
    [(0, 255, 127), (0, 255, 255), (30, 144, 255), (0, 0, 255)],

    # Dải màu ánh sáng phương Bắc
    [(0, 255, 127), (0, 191, 255), (123, 104, 238), (75, 0, 130)],

    # Dải màu xanh lá - tím - xanh dương
    [(0, 255, 0), (138, 43, 226), (0, 0, 255), (0, 255, 255)],

    # Dải màu bầu trời bình minh
    [(255, 127, 80), (255, 165, 0), (255, 69, 0), (255, 99, 71)],

    # Dải màu pastel đa sắc
    [(255, 223, 186), (255, 182, 193), (255, 160, 122), (255, 99, 71)],

    # Dải màu ánh sáng thiên đường
    [(176, 196, 222), (135, 206, 250), (70, 130, 180), (25, 25, 112)],

    # Dải màu hồng - xanh dương huyền ảo
    [(255, 105, 180), (0, 191, 255), (30, 144, 255), (75, 0, 130)],

    # Dải màu vàng - cam - đỏ sáng rực
    [(255, 140, 0), (255, 99, 71), (255, 69, 0), (220, 20, 60)],

    # Dải màu gradient đỏ - xanh lá - xanh dương
    [(255, 0, 0), (0, 255, 0), (0, 0, 255), (0, 255, 255)],

    # Dải màu xanh biển mát mẻ
    [(0, 255, 255), (70, 130, 180), (0, 0, 255), (25, 25, 112)],

    # Dải màu ngọc bích huyền bí
    [(0, 255, 127), (60, 179, 113), (34, 139, 34), (0, 128, 0)],

    # Dải màu xanh dương sáng rực
    [(0, 0, 255), (0, 255, 255), (30, 144, 255), (135, 206, 235)],

    # Dải màu xanh lá tươi sáng
    [(0, 255, 0), (50, 205, 50), (34, 139, 34), (154, 205, 50)],

    # Dải màu cam - vàng nắng ấm
    [(255, 165, 0), (255, 223, 0), (255, 140, 0), (255, 69, 0)],

    # Dải màu hồng - tím rực rỡ
    [(255, 105, 180), (148, 0, 211), (138, 43, 226), (255, 20, 147)]
]



# Mỗi lần sử dụng, chọn ngẫu nhiên 1 dải màu
def get_random_gradient():
    return random.choice(GRADIENT_SETS)
    
BACKGROUND_FOLDER = 'gai'
if os.path.isdir(BACKGROUND_FOLDER):
    BACKGROUND_IMAGES = [
        os.path.join(BACKGROUND_FOLDER, f) 
        for f in os.listdir(BACKGROUND_FOLDER) 
        if f.lower().endswith(('.jpg', '.jpeg', '.png'))
    ]
else:
    BACKGROUND_IMAGES = []

def create_background_from_folder(width, height):
    """Chọn ảnh nền ngẫu nhiên từ thư mục, resize về (width, height)."""
    if BACKGROUND_IMAGES:
        bg_path = random.choice(BACKGROUND_IMAGES)
        bg = Image.open(bg_path).convert("RGB")
        return bg.resize((width, height), Image.LANCZOS)
    else:
        # Nếu không có ảnh, tạo nền màu xanh
        return Image.new("RGB", (width, height), (130, 190, 255))

# ------------------ CÁC HÀM PHỤ TRỢ ------------------
_FONT_CACHE = {}
def get_font(font_path, size):
    """Load font (cache lại) để không load nhiều lần."""
    key = (font_path, size)
    if key not in _FONT_CACHE:
        _FONT_CACHE[key] = ImageFont.truetype(font_path, size)
    return _FONT_CACHE[key]

def make_round_avatar(avatar):
    """Tăng sáng nhẹ, cắt avatar thành hình tròn."""
    avatar = ImageEnhance.Brightness(avatar).enhance(1.2)
    w, h = avatar.size
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, w, h), fill=255)
    round_img = Image.new("RGBA", (w, h), (255, 255, 255, 0))
    round_img.paste(avatar, (0, 0), mask)
    return round_img

def get_gradient_color(colors, ratio):
    """Nội suy màu theo tỉ lệ 0..1 dựa trên danh sách colors."""
    if ratio <= 0:
        return colors[0]
    if ratio >= 1:
        return colors[-1]
    total_segments = len(colors) - 1
    seg = int(ratio * total_segments)
    seg_ratio = (ratio * total_segments) - seg
    c1, c2 = colors[seg], colors[seg + 1]
    return (
        int(c1[0]*(1 - seg_ratio) + c2[0]*seg_ratio),
        int(c1[1]*(1 - seg_ratio) + c2[1]*seg_ratio),
        int(c1[2]*(1 - seg_ratio) + c2[2]*seg_ratio)
    )

def add_multicolor_circle_border(image, colors, border_thickness=5):
    """Thêm viền tròn đa sắc xung quanh ảnh tròn."""
    w, h = image.size
    new_size = (w + 2 * border_thickness, h + 2 * border_thickness)
    border_img = Image.new("RGBA", new_size, (0, 0, 0, 0))
    draw_border = ImageDraw.Draw(border_img)
    cx, cy = new_size[0] / 2, new_size[1] / 2
    r = w / 2
    outer_r = r + border_thickness

    for angle in range(360):
        rad = math.radians(angle)
        inner_point = (cx + r * math.cos(rad), cy + r * math.sin(rad))
        outer_point = (cx + outer_r * math.cos(rad), cy + outer_r * math.sin(rad))
        color = get_gradient_color(colors, angle / 360.0)
        draw_border.line([inner_point, outer_point], fill=color, width=border_thickness)

    border_img.paste(image, (border_thickness, border_thickness), image)
    return border_img

def add_multicolor_rectangle_border(image, colors, border_thickness=10):
    """Thêm viền đa sắc quanh khung ảnh."""
    new_w = image.width + 2 * border_thickness
    new_h = image.height + 2 * border_thickness
    border_img = Image.new("RGBA", (new_w, new_h), (0, 0, 0, 0))
    draw_b = ImageDraw.Draw(border_img)
    for x in range(new_w):
        color = get_gradient_color(colors, x / new_w)
        draw_b.line([(x, 0), (x, border_thickness - 1)], fill=color)
        draw_b.line([(x, new_h - border_thickness), (x, new_h - 1)], fill=color)
    for y in range(new_h):
        color = get_gradient_color(colors, y / new_h)
        draw_b.line([(0, y), (border_thickness - 1, y)], fill=color)
        draw_b.line([(new_w - border_thickness, y), (new_w - 1, y)], fill=color)

    border_img.paste(image, (border_thickness, border_thickness), image)
    return border_img

def draw_circle_with_text(base_img, x, y, radius, text, font, fill=(255,255,255),
                          bg_color=(255,0,0), alpha=255):
    """
    Vẽ 1 vòng tròn màu bg_color (alpha) tại (x, y) với bán kính radius,
    và vẽ text căn giữa bên trong vòng tròn. Sau đó dán vào ảnh gốc (base_img).
    """
    circle_img = Image.new("RGBA", (radius * 2, radius * 2), (0, 0, 0, 0))
    draw_c = ImageDraw.Draw(circle_img)
    draw_c.ellipse((0, 0, radius * 2, radius * 2),
                   fill=(bg_color[0], bg_color[1], bg_color[2], alpha))
    text_bbox = draw_c.textbbox((0, 0), text, font=font)
    text_w, text_h = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]
    tx = (radius * 2 - text_w) // 2
    ty = (radius * 2 - text_h) // 2
    draw_c.text((tx, ty), text, font=font, fill=fill)
    base_img.alpha_composite(circle_img, (x, y))

def draw_gradient_text(draw, text, position, font, gradient_colors, shadow_offset=(2, 2)):
    """
    Vẽ text với hiệu ứng gradient màu kết hợp bóng (shadow).
    """
    if not text:
        return
    text_len = len(text)
    change_every = 4
    color_list = []
    num_segments = len(gradient_colors) - 1
    steps_per_segment = (text_len // change_every) + 1
    for i in range(num_segments):
        for j in range(steps_per_segment):
            if len(color_list) < text_len:
                ratio = j / steps_per_segment
                c1, c2 = gradient_colors[i], gradient_colors[i+1]
                interpolated = (
                    int(c1[0] * (1 - ratio) + c2[0] * ratio),
                    int(c1[1] * (1 - ratio) + c2[1] * ratio),
                    int(c1[2] * (1 - ratio) + c2[2] * ratio)
                )
                color_list.append(interpolated)
    while len(color_list) < text_len:
        color_list.append(gradient_colors[-1])

    x, y = position
    shadow_color = (0, 0, 0)
    for i, ch in enumerate(text):
        ch_color = color_list[i]
        # Vẽ bóng
        draw.text((x + shadow_offset[0], y + shadow_offset[1]), ch, font=font, fill=shadow_color)
        # Vẽ ký tự chính
        draw.text((x, y), ch, font=font, fill=ch_color)
        cw = draw.textbbox((0, 0), ch, font=font)[2]
        x += cw

# ------------------ HÀM TẠO ẢNH CHÀO MỪNG / TẠM BIỆT ------------------
def create_welcome_or_farewell_image(member_name, left_avatar_url, right_avatar_url,
                                     right_number, group_name, event_text,
                                     time_line, executed_by, cover_url=None):
    """
    Tạo ảnh chào mừng/tạm biệt với layout:
      - Nền: nếu có ảnh bìa (cover_url) của người dùng thì sử dụng làm nền, 
             nếu không có thì lấy ảnh ngẫu nhiên từ folder hoặc tạo nền màu xanh.
      - Overlay: khung bo góc hồng mờ.
      - Avatar trái: avatar của thành viên.
      - Avatar phải: avatar của nhóm, có vòng tròn hiển thị số thành viên.
      - Các dòng text: được căn giữa theo overlay.
    Trả về đường dẫn file ảnh ("welcome_or_farewell.jpg").
    """
    # Cập nhật kích thước ảnh: tăng chiều cao từ 600 lên 800
    WIDTH, HEIGHT = 1472, 800

    # 1) Tạo nền ảnh: Ưu tiên sử dụng ảnh bìa của người dùng nếu có.
    if cover_url and cover_url != "https://cover-talk.zadn.vn/default":
        try:
            resp = requests.get(cover_url, timeout=5)
            resp.raise_for_status()
            background = Image.open(BytesIO(resp.content)).convert("RGB")
            background = background.resize((WIDTH, HEIGHT), Image.LANCZOS)
        except Exception as e:
            logging.error(f"Lỗi khi tải ảnh bìa: {e}")
            background = create_background_from_folder(WIDTH, HEIGHT)
    else:
        background = create_background_from_folder(WIDTH, HEIGHT)

    base_img = background.convert("RGBA")

    # 2) Vẽ overlay bo góc hồng mờ.
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw_overlay = ImageDraw.Draw(overlay)
    # Giả sử overlay vẫn có độ cao cố định (ví dụ 460) và được căn giữa theo HEIGHT mới.
    overlay_height = 460
    rect_y0 = (HEIGHT - overlay_height) // 2
    rect_y1 = rect_y0 + overlay_height
    rect_x0, rect_x1 = 30, WIDTH - 30
    draw_overlay.rounded_rectangle(
        (rect_x0, rect_y0, rect_x1, rect_y1),
        radius=50,
        fill=(128, 128, 128, 150)
    )
    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=2))
    base_img.alpha_composite(overlay)

    # 3) Tải avatar, resize, cắt tròn và thêm viền đa sắc.
    def load_avatar(url):
        if not url:
            return Image.new("RGBA", (150, 150), (200, 200, 200, 255))
        try:
            resp = requests.get(url, timeout=5)
            resp.raise_for_status()
            av = Image.open(BytesIO(resp.content)).convert("RGBA")
            return av
        except Exception as e:
            logging.error(f"Lỗi tải avatar: {e}")
            return Image.new("RGBA", (150, 150), (200, 200, 200, 255))

    left_avatar = load_avatar(left_avatar_url)
    right_avatar = load_avatar(right_avatar_url)

    AVATAR_SIZE = 250
    left_avatar = left_avatar.resize((AVATAR_SIZE, AVATAR_SIZE), Image.LANCZOS)
    right_avatar = right_avatar.resize((AVATAR_SIZE, AVATAR_SIZE), Image.LANCZOS)

    left_avatar = make_round_avatar(left_avatar)
    left_avatar = add_multicolor_circle_border(left_avatar, MULTICOLOR_GRADIENT, 4)
    right_avatar = make_round_avatar(right_avatar)
    right_avatar = add_multicolor_circle_border(right_avatar, MULTICOLOR_GRADIENT, 4)

    # 4) Paste avatar vào ảnh (các vị trí được căn giữa theo HEIGHT mới).
    lx = rect_x0 + 70
    ly = (HEIGHT - left_avatar.height) // 2
    base_img.alpha_composite(left_avatar, (lx, ly))

    rx = rect_x1 - right_avatar.width - 70
    ry = (HEIGHT - right_avatar.height) // 2
    base_img.alpha_composite(right_avatar, (rx, ry))

    # 5) Vẽ vòng tròn hiển thị số thành viên trên avatar phải.
    circle_r = 50
    circle_font = get_font("font/Kanit-Medium.ttf", 40)
    draw_circle_with_text(
        base_img,
        x=rx + (AVATAR_SIZE - 2 * circle_r),
        y=ry - circle_r - 10,
        radius=circle_r,
        text=str(right_number),
        font=circle_font,
        fill=(255, 255, 255),
        bg_color=(85, 0, 255),
        alpha=200
    )

    # 6) Vẽ các dòng text căn giữa theo overlay.
    if "tham gia" in event_text.lower():
        line1 = f"{member_name}"
    elif "rời" in event_text.lower():
        line1 = f"{member_name}"
    else:
        line1 = f"{member_name}"
    line2 = event_text
    line3 = group_name
    line4 = f"bởi : {executed_by}"
    line5 = time_line

    font_title = get_font("font/FrancoisOne-Regular.ttf", 150)
    font_sub = get_font("font/Kanit-Medium.ttf", 60)
    font_small = get_font("font/Kanit-Medium.ttf", 50)
    circle_font = get_font("font/Kanit-Medium.ttf", 50)

    base_draw = ImageDraw.Draw(base_img)

    def draw_centered_text(txt, y, font, grad_colors):
        bbox = base_draw.textbbox((0, 0), txt, font=font)
        t_w = bbox[2] - bbox[0]
        region_w = rect_x1 - rect_x0
        x = rect_x0 + (region_w - t_w) // 2
        draw_gradient_text(base_draw, txt, (x, y), font, grad_colors, shadow_offset=(2, 2))
    
    draw_centered_text(line1, rect_y0 - 30, font_title, MULTICOLOR_GRADIENT)
    random_gradients = random.sample(GRADIENT_SETS, 4)
    draw_centered_text(line2, rect_y0 + 170, font_sub, random_gradients[0])
    draw_centered_text(line3, rect_y0 + 250, font_sub, random_gradients[1])
    draw_centered_text(line4, rect_y1 - 130, font_small, random_gradients[2])
    draw_centered_text(line5, rect_y1 - 70, font_small, random_gradients[3])
    
        # ---- THÊM DÒNG CHỮ NHỎ Ở GÓC DƯỚI PHẢI: "design by Rosy" ----
    # Giả sử bạn đã có đoạn vẽ ô chữ nhật màu đỏ:
    red_rect_x0 = 50
    red_rect_y0 = 700
    red_rect_x1 = 1422
    red_rect_y1 = 780

    # Vẽ ô chữ nhật màu đỏ (bán trong suốt):
    draw_overlay.rounded_rectangle(
        (red_rect_x0, red_rect_y0, red_rect_x1, red_rect_y1),
        radius=10,
        fill=(255, 0, 0, 100)  # R,G,B,Alpha
    )

    # Sau đó, bạn vẽ chữ "design by Rosy" bên trong ô chữ nhật này.
    designer_text = "design by Rosy"
    designer_font = get_font("font/Kanit-Medium.ttf", 30)  # Font cỡ nhỏ

    # Tính kích thước của text
    text_bbox = base_draw.textbbox((0, 0), designer_text, font=designer_font)
    text_w = text_bbox[2] - text_bbox[0]
    text_h = text_bbox[3] - text_bbox[1]

    # Canh lề 10px từ góc phải & góc dưới của ô chữ nhật
    margin = 10
    designer_x = red_rect_x1 - text_w - margin
    designer_y = red_rect_y1 - text_h - margin

    # Vẽ chữ với gradient và bóng đổ nhẹ
    draw_gradient_text(
        base_draw,
        text=designer_text,
        position=(designer_x, designer_y),
        font=designer_font,
        gradient_colors=MULTICOLOR_GRADIENT,  # Bạn có thể dùng dải màu khác
        shadow_offset=(1, 1)                 # Bóng đổ nhẹ
    )

    # 7) Thêm viền đa sắc quanh ảnh.
    final_image = add_multicolor_rectangle_border(base_img, MULTICOLOR_GRADIENT, 10)
    final_image = final_image.convert("RGB")
    image_path = "welcome_or_farewell.jpg"
    final_image.save(image_path, quality=90)
    return image_path

def delete_file(file_path):
    """Xóa file nếu tồn tại."""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Đã xóa file: {file_path}")
        else:
            print(f"Không tìm thấy file: {file_path}")
    except Exception as e:
        logging.error(f"Lỗi khi xóa file {file_path}: {e}")

# ------------------ HÀM XỬ LÝ SỰ KIỆN NHÓM ------------------
def welcome(self, event_data, event_type, ttl=3600000):
    """
    Hàm xử lý sự kiện nhóm (JOIN, LEAVE, v.v.).
    Lấy thông tin nhóm, thành viên và gọi hàm tạo ảnh chào mừng/tạm biệt.
    Sau đó gửi ảnh kèm tin nhắn đến nhóm.
    """
    if event_type == GroupEventType.UNKNOWN:
        return

    thread_id = event_data['groupId']
    group_info = self.fetchGroupInfo(thread_id)
    if not group_info or 'gridInfoMap' not in group_info or thread_id not in group_info.gridInfoMap:
        print(f"Không thể lấy thông tin nhóm cho thread_id: {thread_id}")
        return

    group_data = group_info.gridInfoMap[thread_id]
    group_name = group_data['name']
    group_logo_url = group_data.get('avt', '')
    group_total_member = group_data['totalMember']

    def get_name(user_id):
        try:
            user_info = self.fetchUserInfo(user_id)
            return user_info.changed_profiles[user_id].zaloName
        except KeyError:
            return "Không tìm thấy tên"

    group_leader = get_name(group_data['creatorId'])
    actor_name = get_name(event_data['sourceId'])  # Người kích hoạt sự kiện

    # Cấu hình các sự kiện với thông số cho tin nhắn và ảnh
    event_config = {
        GroupEventType.JOIN: {
            "img_type": "JOIN",
            "msg_func": lambda member: (                
                f"❤ https://accvip.vn \n"
                f"💛 Shop acc giá rẻ - uy tín chất lượng\n"
                f"💛 Group shop acc Best Kai\n"
                f"💛 https://zalo.me/g/pngpmo754"
            ),
            "ttl": 3600000
        },
        GroupEventType.LEAVE: {
            "img_type": "LEAVE",
            "msg_func": lambda member: (               
                f"❤ https://accvip.vn \n"
                f"💛 Shop acc giá rẻ - uy tín chất lượng\n"
                f"💛 Group shop acc Best Kai\n"
                f"💛 https://zalo.me/g/pngpmo754"
            ),
            "ttl": 500000
        },
        GroupEventType.REMOVE_MEMBER: {
            "img_type": "REMOVE_MEMBER",
            "msg_func": lambda member: (
                f"❤ https://accvip.vn \n"
                f"💛 Shop acc giá rẻ - uy tín chất lượng\n"
                f"💛 Group shop acc Best Kai\n"
                f"💛 https://zalo.me/g/pngpmo754"
            ),
            "ttl": 500000
        },
        GroupEventType.ADD_ADMIN: {
            "img_type": "ADD_ADMIN",
            "msg_func": lambda member: (
                f"❤ https://accvip.vn \n"
                f"💛 Shop acc giá rẻ - uy tín chất lượng\n"
                f"💛 Group shop acc Best Kai\n"
                f"💛 https://zalo.me/g/pngpmo754"
            ),
            "ttl": 500000
        },
        GroupEventType.REMOVE_ADMIN: {
            "img_type": "REMOVE_ADMIN",
            "msg_func": lambda member: (
                f"❤ https://accvip.vn \n"
                f"💛 Shop acc giá rẻ - uy tín chất lượng\n"
                f"💛 Group shop acc Best Kai\n"
                f"💛 https://zalo.me/g/pngpmo754"
            ),
            "ttl": 500000
        },
        GroupEventType.UPDATE: {
            "img_type": "UPDATE",
            "msg_func": lambda member: (
                f"❤ https://accvip.vn \n"
                f"💛 Shop acc giá rẻ - uy tín chất lượng\n"
                f"💛 Group shop acc Best Kai\n"
                f"💛 https://zalo.me/g/pngpmo754"
            ),
            "ttl": 500000
        }
    }

    if event_type not in event_config:
        return

    config = event_config[event_type]
    # Mapping nội dung event cho ảnh
    event_text_mapping = {
        "JOIN": "Được duyệt vào nhóm",
        "LEAVE": "Đã rời khỏi nhóm",
        "REMOVE_MEMBER": "Đã bị kick khỏi nhóm",
        "ADD_ADMIN": "Đã trở thành phó nhóm",
        "REMOVE_ADMIN": "Đã bị cắt chức phó nhóm",
        "UPDATE": "Đã cập nhật nội quy nhóm"
    }
    # Lấy thời gian hiện tại
    time_line = datetime.now(timezone(timedelta(hours=7))).strftime("%H:%M:%S %Y-%m-%d")

    def process_member(member):
        member_name = member['dName']
        avatar_url = member.get('avatar', '')
        # Thêm: Lấy ảnh bìa của người dùng (cover) nếu có
        cover_url = None
        try:
            user_info = self.fetchUserInfo(member['id'])
            cover_url = user_info.changed_profiles[member['id']].cover
            print(f"Link ảnh bìa của {member_name}: {cover_url}")  # In link ảnh bìa ra terminal
        except Exception as e:
            logging.error(f"Lỗi khi lấy ảnh bìa của người dùng (id {member['id']}): {e}")

        image_path = create_welcome_or_farewell_image(
            member_name=member_name,
            left_avatar_url=avatar_url,
            right_avatar_url=group_logo_url,
            right_number=group_total_member,
            group_name=group_name,
            event_text=event_text_mapping.get(config["img_type"], ""),
            time_line=time_line,
            executed_by=actor_name,
            cover_url=cover_url  # Truyền cover_url vào hàm
        )
        message_text = config["msg_func"](member_name)
        message = Message(text=message_text)
        self.sendLocalImage(
            image_path,
            thread_id,
            ThreadType.GROUP,
            message=message,
            width=1472,
            height=800,
            ttl=config["ttl"]
        )
        delete_file(image_path)

    if len(event_data.updateMembers) > 1:
        with ThreadPoolExecutor(max_workers=4) as executor:
            executor.map(process_member, event_data.updateMembers)
    else:
        for member in event_data.updateMembers:
            process_member(member)

def get_mitaizl():
    return {
        'welcome': None
    }
