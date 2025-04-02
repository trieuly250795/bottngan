
import json
import random
import os
import time
import threading
import io
from PIL import Image, ImageDraw, ImageFont
import matplotlib.pyplot as plt
from zlapi.models import Message, Mention, MessageStyle, MultiMsgStyle

# -------------------------------
# Mô tả module
des = {
    'tác giả': "Rosy & ChatGPT",
    'mô tả': "Chơi Tài Xỉu theo vòng, với ảnh hướng dẫn khi mở vòng và ảnh kết quả khi kết thúc vòng cược",
    'tính năng': [
        "🎲 Chế độ chơi theo vòng: 'taixiu on' hoặc 'txiu on' mở vòng đặt cược 30 giây.",
        "📸 Gửi ảnh hướng dẫn khi người chơi soạn lệnh mở vòng cược.",
        "🕒 Cho phép người chơi đặt cược bằng lệnh txiu <tài/xỉu/chẵn/lẻ> <số tiền/all/%số tiền> hoặc kết hợp đặt cược (txiu <tài/xỉu> <số tiền/all/%số tiền> <chẵn/lẻ> <số tiền/all/%số tiền>) trong 30 giây.",
        "📸 Sau vòng, gửi ảnh kết quả với danh sách người thắng, số tiền đặt cược từng người, số dư cuối và thông tin Hũ (số tiền & tiến trình nổ hũ).",
        "💸 Cập nhật ví, lịch sử, jackpot và tích hợp các chức năng soi cầu, xem phiên trước, lịch sử chiến tích như phiên bản cũ."
    ],
    'hướng dẫn sử dụng': [
        "📩 Gửi lệnh taixiu on hoặc txiu on để mở vòng cược.",
        "📩 Trong vòng 30 giây, gửi lệnh txiu <tài/xỉu/chẵn/lẻ> <số tiền/all/%số tiền> hoặc txiu <tài/xỉu> <số tiền/all/%số tiền> <chẵn/lẻ> <số tiền/all/%số tiền> để đặt cược.",
        "📩 Sau vòng, hệ thống sẽ thông báo kết quả bằng tin nhắn và ảnh kết quả.",
        "📩 Các lệnh khác: soi, xemphientruoc, lichsu, dsnohu, dudoan."
    ]
}

# -------------------------------
# Các hằng số và file dữ liệu
MONEY_DATA_FILE   = 'modules/cache/money.json'
HISTORY_DATA_FILE = 'modules/cache/taixiu_history.json'
JACKPOT_DATA_FILE = 'modules/cache/jackpot.json'
CURRENT_SOICAU_FILE = 'modules/cache/soicau_current.json'
OLD_SOICAU_FILE   = 'modules/cache/soicau_old.json'

# -------------------------------
# Hàm hỗ trợ đọc/ghi file JSON
def load_json(filepath, default):
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default

def save_json(filepath, data):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=4)

# -------------------------------
# Các hàm xử lý dữ liệu ví tiền và lịch sử
def load_money_data():
    return load_json(MONEY_DATA_FILE, {})

def save_money_data(data):
    save_json(MONEY_DATA_FILE, data)

def format_money(amount):
    return f"{amount:,} VNĐ"

def load_history_data():
    return load_json(HISTORY_DATA_FILE, {})

def save_history_data(data):
    save_json(HISTORY_DATA_FILE, data)

def get_user_name(client, user_id):
    try:
        user_info = client.fetchUserInfo(user_id)
        profiles = user_info.unchanged_profiles or user_info.changed_profiles
        return profiles.get(user_id, {}).get('zaloName', 'Không xác định')
    except AttributeError:
        return 'Không xác định'

# -------------------------------
# Hàm ghép hình ảnh (merge)
def merge_images(image_paths, output_path):
    images = []
    for img_path in image_paths:
        if os.path.exists(img_path):
            try:
                images.append(Image.open(img_path))
            except Exception as e:
                print(f"Lỗi mở ảnh {img_path}: {e}")
    if not images:
        return None
    total_width = sum(img.width for img in images)
    max_height = max(img.height for img in images)
    new_image = Image.new('RGB', (total_width, max_height))
    x_offset = 0
    for img in images:
        new_image.paste(img, (x_offset, 0))
        x_offset += img.width
    new_image.save(output_path)
    return output_path

# -------------------------------
# Hàm xử lý dữ liệu jackpot
def load_jackpot_data():
    data = load_json(JACKPOT_DATA_FILE, {})
    if not isinstance(data, dict) or "counter" not in data:
        return {"pool": 0, "counter": 100, "participants": []}
    return data

def save_jackpot_data(data):
    save_json(JACKPOT_DATA_FILE, data)

# -------------------------------
# Hàm xử lý dữ liệu soi cầu (phiên hiện tại và phiên cũ)
def load_current_soicau_data():
    return load_json(CURRENT_SOICAU_FILE, [])

def save_current_soicau_data(data):
    save_json(CURRENT_SOICAU_FILE, data)

def load_old_soicau_data():
    return load_json(OLD_SOICAU_FILE, [])

def save_old_soicau_data(data):
    save_json(OLD_SOICAU_FILE, data)

# -------------------------------
# Nạp font (nếu có)
try:
    FONT_TITLE = ImageFont.truetype("modules/cache/fonts/FrancoisOne-Regular.ttf", 26)
    FONT_TEXT  = ImageFont.truetype("modules/cache/fonts/Kanit-Medium.ttf", 26)
    FONT_SMALL = ImageFont.truetype("modules/cache/fonts/Kanit-Medium.ttf", 27)
except Exception:
    FONT_TITLE = ImageFont.load_default()
    FONT_TEXT  = ImageFont.load_default()
    FONT_SMALL = ImageFont.load_default()

# -------------------------------
def draw_multiline_centered_in_rect(
    draw_obj,          # Đối tượng ImageDraw
    lines,             # Danh sách các dòng text (list[str])
    font,              # Font
    rect,              # Tọa độ (x1, y1, x2, y2)
    fill_color="red",
    shadow=False,
    line_spacing=5,
    shift_x=110  # Thêm tham số shift_x, mặc định = 0
):
    x1, y1, x2, y2 = rect
    rect_w = x2 - x1
    rect_h = y2 - y1
    
    total_text_height = 0
    line_heights = []
    for line in lines:
        w, h = font.getbbox(line)[2:]
        line_heights.append(h)
        total_text_height += (h + line_spacing)
    total_text_height -= line_spacing

    current_y = y1 + (rect_h - total_text_height) // 2

    for line in lines:
        text_w, text_h = font.getbbox(line)[2:]
        x_mid = x1 + (rect_w - text_w) // 2
        x_mid -= shift_x
        if shadow:
            draw_obj.text((x_mid+1, current_y+1), line, font=font, fill="black")
        draw_obj.text((x_mid, current_y), line, font=font, fill=fill_color)
        current_y += (text_h + line_spacing)
        
# Hàm tạo ảnh xúc xắc theo hình tam giác
def merge_dice_images_triangle(
    dice_image_paths, bet_amount, choice,
    output_path="modules/cache/datatx/merged_dice.png",
    mode="individual",
    total_tai=None, total_xiu=None,
    total_chan=None, total_le=None, dice_sum=None, tai_or_xiu=None, chan_or_le=None
):
    import math
    try:
        background = Image.open("modules/cache/datatx/table_bg3.png")
        width, height = background.size
    except FileNotFoundError:
        width, height = 1000, 600
        background = Image.new("RGB", (width, height), color=(0, 100, 100))
    
    draw = ImageDraw.Draw(background)
    dice_imgs = []
    for path in dice_image_paths:
        if os.path.exists(path):
            try:
                dice_imgs.append(Image.open(path))
            except Exception as e:
                print(f"Lỗi mở ảnh {path}: {e}")
        else:
            print(f"File ảnh không tồn tại: {path}")

    if len(dice_imgs) != 3:
        print("Không đủ ảnh xúc xắc để ghép hình.")
        return None

    dice_w, dice_h = 120, 120
    dice_imgs = [img.resize((dice_w, dice_h)) for img in dice_imgs]

    center_x, center_y = width // 2, (height // 2) - 30
    radius = 60
    angles_deg = [0, 120, 240]
    positions = []
    for angle_deg in angles_deg:
        angle_rad = math.radians(angle_deg)
        x_center = center_x + radius * math.cos(angle_rad)
        y_center = center_y + radius * math.sin(angle_rad)
        x = x_center - dice_w / 2
        y = y_center - dice_h / 2
        positions.append((x, y))

    for i, dice_img in enumerate(dice_imgs):
        new_w, new_h = dice_img.size
        x = positions[i][0] + dice_w / 2 - new_w / 2
        y = positions[i][1] + dice_h / 2 - new_h / 2
        background.paste(dice_img, (int(x), int(y)), dice_img.convert("RGBA"))

    def draw_centered_in_rect(draw_obj, text, font, rect, fill_color="white", shadow=False):
        x1, y1, x2, y2 = rect
        text_w, text_h = font.getbbox(text)[2:]
        rect_w = x2 - x1
        rect_h = y2 - y1
        x_mid = x1 + (rect_w - text_w) // 2
        y_mid = y1 + (rect_h - text_h) // 2
        if shadow:
            draw_obj.text((x_mid + 2, y_mid + 2), text, font=font, fill="black")
        draw_obj.text((x_mid, y_mid), text, font=font, fill=fill_color)

    tai_rect   = (  -70, 350,  300, 190)
    xiu_rect   = ( 680, 350,  950, 190)
    chan_rect  = (  -70, 400,  300, 290)
    le_rect    = ( 680, 400,  950, 290)
    
    result_rect = (460, 470, 740, 550)

    font = FONT_TEXT

    if mode == "individual":
        bet_text = f"{format_money(bet_amount)}"
        choice_lower = choice.lower()
        if choice_lower == "tài":
            draw_centered_in_rect(draw, bet_text, font, tai_rect, fill_color="lime", shadow=True)
        elif choice_lower == "xỉu":
            draw_centered_in_rect(draw, bet_text, font, xiu_rect, fill_color="lime", shadow=True)
        elif choice_lower == "chẵn":
            draw_centered_in_rect(draw, bet_text, font, chan_rect, fill_color="lime", shadow=True)
        elif choice_lower == "lẻ":
            draw_centered_in_rect(draw, bet_text, font, le_rect, fill_color="lime", shadow=True)
    elif mode == "round":
        total_tai_text  = f"{format_money(total_tai)}"  if total_tai  else "0 VNĐ"
        total_xiu_text  = f"{format_money(total_xiu)}"  if total_xiu  else "0 VNĐ"
        total_chan_text = f"{format_money(total_chan)}" if total_chan else "0 VNĐ"
        total_le_text   = f"{format_money(total_le)}"   if total_le   else "0 VNĐ"
        draw_centered_in_rect(draw, total_tai_text,  font, tai_rect,   fill_color="yellow", shadow=True)
        draw_centered_in_rect(draw, total_xiu_text,  font, xiu_rect,   fill_color="yellow", shadow=True)
        draw_centered_in_rect(draw, total_chan_text, font, chan_rect,  fill_color="red", shadow=True)
        draw_centered_in_rect(draw, total_le_text,   font, le_rect,    fill_color="red", shadow=True)
        
    FONT_TEXT_BIG = ImageFont.truetype("modules/cache/fonts/Kanit-Medium.ttf", 40)
    lines_to_draw = [
        f"Số điểm: {dice_sum}",
        tai_or_xiu,
        chan_or_le
    ]
    draw_multiline_centered_in_rect(
        draw,
        lines=lines_to_draw,
        font=FONT_TEXT_BIG,
        rect=result_rect,
        fill_color="red",
        shadow=True,
        line_spacing=5
    )    

    background.save(output_path)
    return output_path

# Hàm tạo đồ thị thống kê (đồ thị dạng sóng)
def create_bar_chart(history, line_color='red', text_color='yellow'):
    points = [item['sum'] for item in history]
    x = list(range(len(points)))
    fig, ax = plt.subplots(figsize=(6, 4), dpi=120)
    ax.plot(x, points, color=line_color, linewidth=2.5, linestyle='-', 
            marker='o', markersize=6, markerfacecolor='white', markeredgewidth=1.5)
    ax.set_title("Đồ thị xu hướng xúc xắc", fontsize=16, color=text_color, pad=15, fontweight='bold')
    ax.set_xlabel("Số lượt", fontsize=14, color=text_color, labelpad=10)
    ax.set_ylabel("< Xỉu______Tài >", fontsize=14, color=text_color, labelpad=10)
    ax.tick_params(axis='x', colors=text_color, labelsize=12)
    ax.tick_params(axis='y', colors=text_color, labelsize=12)
    ax.grid(True, linestyle='--', linewidth=0.8, alpha=0.6)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    buf = io.BytesIO()
    fig.savefig(buf, format='PNG', bbox_inches='tight', transparent=True)
    plt.close(fig)
    buf.seek(0)
    return Image.open(buf)

# -------------------------------
# Hàm tạo ảnh soi cầu, vẽ lưới và ghép đồ thị
def create_soicau_image(history):
    jackpot_data = load_jackpot_data()
    width, height = 1000, 500
    img = Image.new('RGB', (width, height), color=(75, 54, 33))
    draw = ImageDraw.Draw(img)
    for y in range(height):
        gradient = int(75 + (150 - 75) * (y / height))
        draw.line([(0, y), (width, y)], fill=(gradient, gradient-30, gradient-50))
    title_text = "LỊCH SỬ PHIÊN HIỆN TẠI - SOI CẦU"
    draw.text((12, 12), title_text, font=FONT_TITLE, fill=(0, 0, 0))
    draw.text((10, 10), title_text, font=FONT_TITLE, fill=(255, 215, 0))
    cell_size = 40
    start_x, start_y = 10, 60
    rows, cols = 10, 10
    for r in range(rows + 1):
        y_line = start_y + r * cell_size
        draw.line([(start_x, y_line), (start_x + cols * cell_size, y_line)], fill=(200, 170, 100), width=1)
    for c in range(cols + 1):
        x_line = start_x + c * cell_size
        draw.line([(x_line, start_y), (x_line, start_y + rows * cell_size)], fill=(200, 170, 100), width=1)
    recent_100 = history[-100:]
    for i, item in enumerate(recent_100):
        if i >= rows * cols:
            break
        row, col = divmod(i, cols)
        center_x = start_x + col * cell_size + cell_size // 2
        center_y = start_y + row * cell_size + cell_size // 2
        fill_color = (100, 0, 0) if item['result'] in ['Tài', 'Chẵn'] else (255, 255, 255)
        draw.ellipse([center_x - 10, center_y - 10, center_x + 10, center_y + 10],
                     fill=fill_color, outline=(255, 215, 0), width=2)
    info_x, info_y = 590, 20
    dot_diameter, dot_margin = 25, 10
    draw.ellipse([info_x, info_y, info_x + dot_diameter, info_y + dot_diameter], fill=(100, 0, 0))
    draw.text((info_x + dot_diameter + dot_margin, info_y),
              f"TÀI : {sum(1 for x in history if x['result'] == 'Tài')}", font=FONT_TEXT, fill=(255, 215, 0))
    draw.ellipse([info_x, info_y + 30, info_x + dot_diameter, info_y + 30 + dot_diameter], fill=(255, 255, 255))
    draw.text((info_x + dot_diameter + dot_margin, info_y + 30),
              f"XỈU : {sum(1 for x in history if x['result'] == 'Xỉu')}", font=FONT_TEXT, fill=(255, 215, 0))
    draw.text((info_x, info_y + 60),  f"Tổng lượt: {len(history)}", font=FONT_TEXT, fill=(255, 215, 0))
    draw.text((info_x, info_y + 90),
              f"Hũ: {jackpot_data.get('pool', 0):,} VNĐ", font=FONT_TEXT, fill=(255, 215, 0))
    draw.text((info_x, info_y + 120),
              f"Xác suất nổ hũ: {100 - jackpot_data.get('counter', 100)}%", font=FONT_TEXT, fill=(255, 215, 0))
    chart_img = create_bar_chart(history)
    chart_img = chart_img.resize((580, 280))
    img.paste(chart_img, (width - 590, height - 280), chart_img.convert("RGBA"))
    soicau_image_path = "modules/cache/soicau.png"
    img.save(soicau_image_path)
    return soicau_image_path

# -------------------------------
from PIL import Image, ImageDraw, ImageFont

def create_round_result_image(
    bets,
    dice_values,
    total_points,
    outcome_result,
    even_odd_result,
    money_data,
    jackpot_data,
    client
):
    from PIL import Image, ImageDraw, ImageFont

    # 1) Các biến cơ bản
    num_rows = len(bets)
    margin = 30  # lề ngoài

    # Khối hiển thị xúc xắc
    info_block_height = 120

    # Tạm ước tính chiều cao bảng (header + row_height * số dòng)
    # ta sẽ điều chỉnh sau khi tìm cỡ font
    header_height = 50
    row_height = 40
    table_height = header_height + num_rows * row_height + 10

    width = 1200  # chiều rộng cố định

    # -------------------------------------------------
    # Tạo sẵn 2 dòng jackpot
    # -------------------------------------------------
    jackpot_pool = jackpot_data.get("pool", 0)
    progress = 100 - jackpot_data.get("counter", 100)
    fill_count = int(progress / 10)
    progress_bar = "█" * fill_count + "░" * (10 - fill_count)

    jackpot_line1 = f"Hũ hiện tại: {format_money(jackpot_pool)}"
    jackpot_line2 = f"Tiến trình nổ hũ: [{progress_bar}] {progress}%"

    # -------------------------------------------------
    # 2) Tìm cỡ font cho bảng
    # -------------------------------------------------
    header_texts = ["STT", "Tên", "Cược", "Số tiền", "Kết quả", "Số dư cuối"]
    table_data = []
    for idx, bet in enumerate(bets, start=1):
        user_id = bet["author_id"]
        username = get_user_name(client, user_id)  # hàm lấy tên user
        bet_choice = bet["choice"].capitalize()
        bet_amount = bet["bet_amount"]

        # Xác định thắng/thua (chỗ này logic cũ)
        if bet_choice.lower() in ["tài", "xỉu"]:
            win = (bet_choice.lower() == outcome_result.lower())
        else:
            win = (bet_choice.lower() == even_odd_result.lower())
        result_text = "Thắng" if win else "Thua"
        final_balance = money_data.get(str(user_id), 0)

        row_data = [
            str(idx),
            username,
            bet_choice,
            format_money(bet_amount),
            result_text,
            format_money(final_balance)
        ]
        table_data.append(row_data)

    num_cols = len(header_texts)

    def measure_columns_with_font(font, data_rows, headers):
        col_widths = [0] * num_cols
        for i, htext in enumerate(headers):
            w = font.getlength(htext)
            col_widths[i] = max(col_widths[i], w)
        for row in data_rows:
            for i, cell in enumerate(row):
                w = font.getlength(cell)
                if w > col_widths[i]:
                    col_widths[i] = w
        return col_widths

    col_padding = 20
    table_x = margin
    table_w = width - 2 * margin

    font_size_max = 36
    font_size_min = 10
    best_font_size = font_size_min

    # Dò font lớn nhất có thể
    for fs in range(font_size_max, font_size_min - 1, -1):
        temp_font = ImageFont.truetype("modules/cache/fonts/Kanit-Medium.ttf", fs)
        col_widths = measure_columns_with_font(temp_font, table_data, header_texts)
        total_cols_width = sum(col_widths) + num_cols * col_padding
        if total_cols_width <= table_w:
            best_font_size = fs
            break

    # Font table chính thức
    table_font = ImageFont.truetype("modules/cache/fonts/Kanit-Medium.ttf", best_font_size)

    # Đo lại cột
    col_widths = measure_columns_with_font(table_font, table_data, header_texts)
    header_height = best_font_size + 14
    row_height = best_font_size + 8
    table_height = header_height + num_rows * row_height + 10

    # -------------------------------------------------
    # 3) Font tiêu đề, hàm vẽ text
    # -------------------------------------------------
    try:
        title_font = FONT_TITLE
    except:
        title_font = ImageFont.truetype("modules/cache/fonts/FrancoisOne-Regular.ttf", 32)

    def get_text_size(font, text):
        bbox = font.getbbox(text)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]

    def draw_centered_text(txt, font, y, fill_color="white", shadow=False):
        w, h = get_text_size(font, txt)
        x = (width - w) // 2
        if shadow:
            draw.text((x+2, y+2), txt, font=font, fill="black")
        draw.text((x, y), txt, font=font, fill=fill_color)
        return h

    # -------------------------------------------------
    # 4) Đo chiều cao 2 dòng jackpot
    # -------------------------------------------------
    j1_w, j1_h = get_text_size(table_font, jackpot_line1)
    j2_w, j2_h = get_text_size(table_font, jackpot_line2)
    # Tổng = chiều cao 2 dòng + 5px cách giữa chúng
    jackpot_text_height = j1_h + j2_h + 5

    # -------------------------------------------------
    # 5) Tính chiều cao ảnh cuối
    # -------------------------------------------------
    # = margin trên + info_block_height + table_height + jackpot_text_height + 20 px khoảng đệm dưới + margin dưới
    #  => +20 px (hoặc tuỳ bạn) để 2 dòng jackpot không sát bảng
    space_above_jackpot = 20
    margin_bottom = 100
    height = margin + info_block_height + table_height + space_above_jackpot + jackpot_text_height + margin_bottom

    # Tạo ảnh
    base = Image.new("RGB", (width, height), (0, 0, 0))
    draw = ImageDraw.Draw(base)

    # -------------------------------------------------
    # 6) Vẽ gradient nền
    # -------------------------------------------------
    top_color = (50, 80, 150)
    bottom_color = (150, 80, 50)
    for y in range(height):
        blend = y / height
        r = int(top_color[0] * (1 - blend) + bottom_color[0] * blend)
        g = int(top_color[1] * (1 - blend) + bottom_color[1] * blend)
        b = int(top_color[2] * (1 - blend) + bottom_color[2] * blend)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # -------------------------------------------------
    # 7) Bắt đầu vẽ
    # -------------------------------------------------
    y_cursor = margin

    # Tiêu đề
    th = draw_centered_text("KẾT QUẢ VÒNG CƯỢC", title_font, y_cursor, fill_color=(255,215,0), shadow=True)
    y_cursor += (th + 10)

    # Thông tin xúc xắc
    line1 = f"Xúc xắc: {dice_values[0]} - {dice_values[1]} - {dice_values[2]}"
    line2 = f"Tổng điểm: {total_points}"
    line3 = f"Kết quả: {outcome_result}  |  Chẵn/Lẻ: {even_odd_result}"

    lh1 = draw_centered_text(line1, table_font, y_cursor)
    y_cursor += lh1 + 5
    lh2 = draw_centered_text(line2, table_font, y_cursor)
    y_cursor += lh2 + 5
    lh3 = draw_centered_text(line3, table_font, y_cursor)
    y_cursor += lh3 + 5

    # Bảng
    table_y = y_cursor + 20
    table_bg = Image.new("RGBA", (table_w, table_height), (255, 255, 255, 50))
    base.paste(table_bg, (table_x, table_y), table_bg)

    draw.rectangle([(table_x, table_y), (table_x + table_w, table_y + table_height)], outline="white", width=2)

    header_y = table_y + 5
    col_x_positions = []
    x_cursor = table_x
    for cw in col_widths:
        col_x_positions.append(x_cursor + col_padding / 2)
        x_cursor += (cw + col_padding)

    # Header
    for i, text_header in enumerate(header_texts):
        draw.text((col_x_positions[i], header_y), text_header, font=table_font, fill=(255, 230, 100))

    sep_y = header_y + header_height - 4
    draw.line([(table_x, sep_y), (table_x + table_w, sep_y)], fill="white", width=2)

    row_y = sep_y + 5
    for row_data in table_data:
        for i, cell_text in enumerate(row_data):
            draw.text((col_x_positions[i], row_y), cell_text, font=table_font, fill="white")
        row_y += row_height

    # -------------------------------------------------
    # 8) Vẽ 2 dòng jackpot
    # -------------------------------------------------
    jackpot_y = table_y + table_height + 20  # 20px cách bảng
    lh_j1 = draw_centered_text(jackpot_line1, table_font, jackpot_y, fill_color="yellow")
    draw_centered_text(jackpot_line2, table_font, jackpot_y + lh_j1 + 5, fill_color="yellow")

    # Viền ngoài
    draw.rectangle([(5, 5), (width - 5, height - 5)], outline="white", width=3)

    # -------------------------------------------------
    # 9) Lưu ảnh
    # -------------------------------------------------
    result_image_path = "modules/cache/round_result_improved.png"
    base.save(result_image_path)
    return result_image_path

# -------------------------------
# Helper: chạy hàm bất đồng bộ trên luồng riêng
def run_async(func, *args, **kwargs):
    threading.Thread(target=func, args=args, kwargs=kwargs, daemon=True).start()

# -------------------------------
# Global cho chế độ chơi theo vòng
current_round = None  # Nếu không có vòng nào đang mở thì là None

# Cấu trúc của một vòng chơi:
# current_round = {
#   "bets": [ { "author_id": ..., "choice": "tài/xỉu/chẵn/lẻ", "bet_amount": ..., "timestamp": ..., "type": "tx"/"ce" }, ... ],
#   "start_time": ...,
#   "duration": 30,  # giây
#   "timer": threading.Timer
# }

# -------------------------------
# Hàm hỗ trợ chuyển đổi số tiền cược
def parse_bet_amount(input_str, current_balance):
    if input_str.lower() == "all":
        return current_balance
    elif input_str.endswith('%'):
        try:
            percent = float(input_str[:-1])
            if 1 <= percent <= 100:
                return int(current_balance * (percent / 100))
            else:
                return None
        except ValueError:
            return None
    else:
        try:
            return int(input_str)
        except ValueError:
            return None

# -------------------------------
# Hàm xử lý lệnh mở vòng chơi Tài Xỉu theo vòng
def handle_taixiu_on_command(message, message_object, thread_id, thread_type, author_id, client):
    global current_round
    if current_round is not None:
        client.replyMessage(Message(text="❌ Vòng chơi đã được mở. Hãy chờ vòng hiện tại kết thúc!"),
                            message_object, thread_id, thread_type, ttl=20000)
        return
    current_round = {
        "bets": [],
        "start_time": time.time(),
        "duration": 45,
        "timer": None
    }
    guide_image_path = "modules/cache/images/taixiuhelp.png"
    if os.path.exists(guide_image_path):
        client.sendLocalImage(
            imagePath=guide_image_path,
            message=Message(text="❗❗❗ Vòng chơi Tài Xỉu đã chính thức bắt đầu ❗❗❗ 🔥\n\n⏱ Các bạn có 45 giây để đặt cược.\n\n💡 Hãy nhập lệnh: txiu <tài/xỉu/chẵn/lẻ> <số tiền/all/%số tiền> hoặc kết hợp cược: txiu <tài/xỉu> <số tiền/all/%số tiền> <chẵn/lẻ> <số tiền/all/%số tiền>\n\n💛💛💛 Nhà cái chốt cược và tung xúc xắc sau 45 giây nữa💛💛💛"),
            thread_id=thread_id,
            thread_type=thread_type,
            width=800,
            height=600,
            ttl=30000
        )
    timer = threading.Timer(45, process_round_end, args=(thread_id, thread_type, client))
    current_round["timer"] = timer
    timer.start()

# -------------------------------
# Hàm xử lý đặt cược trong vòng (cho cả lệnh đơn và lệnh kết hợp)
def handle_taixiu_bet_command(message, message_object, thread_id, thread_type, author_id, client):
    global current_round
    if current_round is None:
        handle_taixiu_command(message, message_object, thread_id, thread_type, author_id, client)
        return

    text = message.split()
    if len(text) not in [3, 5]:
        client.replyMessage(
            Message(text="❌ Cú pháp không đúng. Sử dụng: txiu <tài/xỉu/chẵn/lẻ> <số tiền/all/%số tiền> hoặc txiu <tài/xỉu> <số tiền/all/%số tiền> <chẵn/lẻ> <số tiền/all/%số tiền>"),
            message_object, thread_id, thread_type, ttl=20000
        )
        return

    # Kiểm tra trùng lặp cược
    for bet in current_round["bets"]:
        if bet["author_id"] == author_id:
            author_name = get_user_name(client, author_id)
            client.replyMessage(Message(text=f"❌ {author_name} bạn đã đặt cược trong vòng này."), message_object, thread_id, thread_type, ttl=20000)
            return

    money_data = load_money_data()
    current_balance = money_data.get(str(author_id), 0)
    jackpot_data = load_jackpot_data()

    if len(text) == 5:
        # Xử lý lệnh kết hợp: txiu <tài/xỉu> <số tiền/all/%> <chẵn/lẻ> <số tiền/all/%>
        choice_tx = text[1].lower()
        bet_tx_input = text[2].lower()
        choice_ce = text[3].lower()
        bet_ce_input = text[4].lower()
        if choice_tx not in ["tài", "xỉu"] or choice_ce not in ["chẵn", "lẻ"]:
            client.replyMessage(Message(text="❌ Lệnh không hợp lệ! Phần cược phải là: txiu <tài/xỉu> <số tiền/all/%> <chẵn/lẻ> <số tiền/all/%>"),
                                message_object, thread_id, thread_type, ttl=20000)
            return

        bet_tx = parse_bet_amount(bet_tx_input, current_balance)
        bet_ce = parse_bet_amount(bet_ce_input, current_balance)
        if bet_tx is None or bet_ce is None:
            client.replyMessage(Message(text="❌ Số tiền cược không hợp lệ."),
                                message_object, thread_id, thread_type, ttl=20000)
            return
        total_bet = bet_tx + bet_ce
        if total_bet > current_balance:
            client.replyMessage(Message(text="❌ Số dư không đủ cho cả hai cược."),
                                message_object, thread_id, thread_type, ttl=20000)
            return

        money_data[str(author_id)] = current_balance - total_bet
        save_money_data(money_data)
        if author_id not in jackpot_data.get("participants", []):
            jackpot_data.setdefault("participants", []).append(author_id)
        save_jackpot_data(jackpot_data)
        current_round["bets"].append({
            "author_id": author_id,
            "choice": choice_tx,
            "bet_amount": bet_tx,
            "timestamp": time.time(),
            "type": "tx"
        })
        current_round["bets"].append({
            "author_id": author_id,
            "choice": choice_ce,
            "bet_amount": bet_ce,
            "timestamp": time.time(),
            "type": "ce"
        })
        # Tính thời gian còn lại trong vòng chơi
        remaining_time = int(current_round["start_time"] + current_round["duration"] - time.time())
        
        author_name = get_user_name(client, author_id)
        client.sendMessage(Message(text=f"✅ {author_name} đã đặt cược: {format_money(bet_tx)} vào {choice_tx.capitalize()} và {format_money(bet_ce)} vào {choice_ce.capitalize()}\n⏱ Còn {remaining_time} giây nữa nhà cái sẽ chốt cược 💛💛💛"),
                           thread_id=thread_id, thread_type=thread_type, ttl=60000)
        return
    else:
        # Xử lý lệnh đơn (cũ)
        if text[1].lower() not in ["tài", "xỉu", "chẵn", "lẻ"]:
            client.replyMessage(Message(text="❌ Lệnh không hợp lệ! Chỉ được chọn: tài, xỉu, chẵn, hoặc lẻ."),
                                message_object, thread_id, thread_type, ttl=20000)
            return
        choice = text[1].lower()
        if text[2].lower() == "all":
            bet_amount = current_balance
        elif text[2].endswith('%'):
            try:
                percent = float(text[2][:-1])
                if 1 <= percent <= 100:
                    bet_amount = int(current_balance * (percent / 100))
                else:
                    client.replyMessage(Message(text="❌ Phần trăm phải từ 1% đến 100%."),
                                        message_object, thread_id, thread_type, ttl=20000)
                    return
            except ValueError:
                client.replyMessage(Message(text="❌ Phần trăm cược không hợp lệ."),
                                    message_object, thread_id, thread_type, ttl=20000)
                return
        else:
            try:
                bet_amount = int(text[2])
            except ValueError:
                client.replyMessage(Message(text="❌ Số tiền cược không hợp lệ."),
                                    message_object, thread_id, thread_type, ttl=20000)
                return
        if bet_amount <= 0:
            client.replyMessage(Message(text="❌ Số tiền cược phải lớn hơn 0."),
                                message_object, thread_id, thread_type, ttl=20000)
            return
        if bet_amount > current_balance:
            client.replyMessage(Message(text="❌ Số dư không đủ. Nhập 'tx daily' để nhận tiền miễn phí."),
                                message_object, thread_id, thread_type, ttl=20000)
            return
        money_data[str(author_id)] = current_balance - bet_amount
        save_money_data(money_data)
        if author_id not in jackpot_data.get("participants", []):
            jackpot_data.setdefault("participants", []).append(author_id)
        save_jackpot_data(jackpot_data)
        current_round["bets"].append({
            "author_id": author_id,
            "choice": choice,
            "bet_amount": bet_amount,
            "timestamp": time.time(),
            "type": "single"
        })
        remaining_time = int(current_round["start_time"] + current_round["duration"] - time.time())
        # THÊM CHECK Ở ĐÂY:
        if remaining_time <= 0:
            client.replyMessage(Message(text="❌ Vòng cược đã kết thúc, không thể đặt cược nữa!"),
                                message_object, thread_id, thread_type, ttl=20000)
            return
        author_name = get_user_name(client, author_id)
        client.sendMessage(Message(text=f"✅ {author_name} đã đặt cược {format_money(bet_amount)} vào {choice.capitalize()}\n⏱ Còn {remaining_time} giây nữa nhà cái sẽ chốt cược 💛💛💛"),
                           thread_id=thread_id, thread_type=thread_type, ttl=60000)
        return

# -------------------------------
# Hàm xử lý kết thúc vòng cược (sử dụng luồng riêng cho các lệnh sleep)
def process_round_end(thread_id, thread_type, client):
    global current_round
    if current_round is None:
        return
    bets = current_round["bets"]
    if not bets:
        client.sendMessage(Message(text="❌❌❌ Vòng cược kết thúc, nhưng không có ai đặt cược ❌❌❌"),
                           thread_id=thread_id, thread_type=thread_type, ttl=20000)
        current_round = None
        return
        
    total_tai = sum(bet["bet_amount"] for bet in bets if bet["choice"].lower() == "tài")
    total_xiu = sum(bet["bet_amount"] for bet in bets if bet["choice"].lower() == "xỉu")
    total_chan = sum(bet["bet_amount"] for bet in bets if bet["choice"].lower() == "chẵn")
    total_le = sum(bet["bet_amount"] for bet in bets if bet["choice"].lower() == "lẻ")
    
    dice_values = [random.randint(1, 6) for _ in range(3)]
    total_points = sum(dice_values)
    
    dice_sum = total_points
    tai_or_xiu = "Tài" if dice_sum >= 11 else "Xỉu"
    chan_or_le = "Chẵn" if dice_sum % 2 == 0 else "Lẻ"
    
    client.sendMessage(Message(text="❗❗❗ Hết giờ .... ❗❗❗ Thả tay ra ...."),
                       thread_id=thread_id, thread_type=thread_type, ttl=8000)
    
    if 11 <= total_points <= 18:
        outcome_result = "Tài"
    else:
        outcome_result = "Xỉu"
    even_odd_result = "Chẵn" if total_points % 2 == 0 else "Lẻ"
        
    current_history = load_current_soicau_data()
    current_history.append({
        "dice": dice_values,
        "sum": total_points,
        "result": outcome_result
    })
    if len(current_history) >= 100:
        save_old_soicau_data(current_history)
        current_history = []
    save_current_soicau_data(current_history)
    
    jackpot_data = load_jackpot_data()
    money_data = load_money_data()
    results_lines = [f"🎲 Kết quả vòng cược:"]
    results_lines.append(f"Xúc xắc: {dice_values[0]} - {dice_values[1]} - {dice_values[2]}")
    results_lines.append(f"Tổng điểm: {total_points}")
    results_lines.append(f"Kết quả: {outcome_result} (Chẵn/Lẻ: {even_odd_result})")
    results_lines.append("━━━━━━━━━━━━━━━━━━━━━━")
    for bet in bets:
        user_id = bet["author_id"]
        choice = bet["choice"]
        bet_amount = bet["bet_amount"]
        username = get_user_name(client, user_id)
        if choice in ["tài", "xỉu"]:
            win = (choice == outcome_result.lower())
        else:
            win = (choice == even_odd_result.lower())
        if win:
            winnings = bet_amount * 5
            jackpot_contribution = int(winnings * 0.05)
            net_win = winnings - jackpot_contribution
            money_data[str(user_id)] += net_win
            jackpot_data["pool"] += jackpot_contribution
            result_text = f"✅ {username} thắng {format_money(net_win)} (đóng góp {format_money(jackpot_contribution)} vào Hũ)"
        else:
            net_win = -bet_amount
            result_text = f"⛔ {username} thua {format_money(bet_amount)}"
        history_data = load_history_data()
        user_history = history_data.get(username, [])
        record = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            "bet": bet_amount,
            "choice": choice,
            "dice": dice_values,
            "total_points": total_points,
            "result": outcome_result,
            "outcome": "Thắng" if win else "Thua",
            "net_change": net_win,
            "balance": money_data.get(str(user_id), 0)
        }
        user_history.append(record)
        history_data[username] = user_history
        save_history_data(history_data)
        results_lines.append(result_text)
    save_money_data(money_data)
    save_jackpot_data(jackpot_data)
    
    result_image_path = create_round_result_image(bets, dice_values, total_points, outcome_result, even_odd_result, money_data, jackpot_data, client)
    
    def delayed_round_display():
        time.sleep(3)
        gif_path = "modules/cache/gif/giftxvipp.gif"
        client.sendLocalGif(
            gifPath=gif_path,
            thumbnailUrl=None,
            thread_id=thread_id,
            thread_type=thread_type,
            width=1000,
            height=600,
            ttl=6000
        )
        time.sleep(8)
        image_paths = [f'modules/cache/datatx/{value}.png' for value in dice_values]
        merged_image_path = "modules/cache/datatx/merged_dice.png"
        if all(os.path.exists(path) for path in image_paths):
            merge_dice_images_triangle(
                image_paths, 0, "", merged_image_path, 
                mode="round", total_tai=total_tai, total_xiu=total_xiu, 
                total_chan=total_chan, total_le=total_le, dice_sum=dice_sum,
                tai_or_xiu=tai_or_xiu,
                chan_or_le=chan_or_le
            )
            client.sendLocalImage(
                imagePath=merged_image_path,
                message="",
                thread_id=thread_id,
                thread_type=thread_type,
                width=1000,
                height=600,
                ttl=60000
            )
            try:
                os.remove(merged_image_path)
            except Exception as e:
                print(f"Lỗi xóa file ảnh {merged_image_path}: {e}")
        else:
            client.sendMessage(Message(text="\n❌ Không thể hiển thị hình ảnh kết quả do thiếu hình ảnh xúc xắc."), thread_id=thread_id, thread_type=thread_type, ttl=20000)
        time.sleep(2)
        if result_image_path and os.path.exists(result_image_path):
            # Mở ảnh vừa tạo ra
            merged_image = Image.open(result_image_path)
            img_width, img_height = merged_image.size  # Lấy đúng kích thước ảnh thực tế

            print(f"Kích thước ảnh thực tế: {img_width} x {img_height}")  # Kiểm tra log

            # Gửi ảnh với kích thước chính xác
            client.sendLocalImage(
                imagePath=result_image_path,
                message=Message(text="📊 Kết quả vòng cược chi tiết:"),
                thread_id=thread_id,
                thread_type=thread_type,
                width=img_width,  # Dùng kích thước ảnh thật
                height=img_height,  # Dùng kích thước ảnh thật
                ttl=60000
            )
            try:
                os.remove(result_image_path)
            except Exception as e:
                print(f"Lỗi xóa file {result_image_path}: {e}")
    run_async(delayed_round_display)
    
    decrement = random.randint(5, 10)
    jackpot_data["counter"] -= decrement
    print(f"Sau vòng, counter giảm đi {decrement} và hiện tại counter = {jackpot_data['counter']}")
    if jackpot_data["counter"] <= 0:
        if jackpot_data.get("participants"):
            winner_id = random.choice(jackpot_data["participants"])
            money_data[str(winner_id)] += jackpot_data["pool"]
            save_money_data(money_data)
            info_response = client.fetchUserInfo(winner_id)
            profiles = info_response.unchanged_profiles or info_response.changed_profiles
            winner_name = profiles.get(winner_id, {}).get("zaloName", "Không xác định")
            jackpot_message = (
                f"🎉 CHÚC MỪNG {winner_name} ĐÃ NỔ HŨ 🎉\n"
                f"💰 Bạn nhận được {format_money(jackpot_data['pool'])} từ Hũ may mắn!"
            )
            client.sendMessage(Message(text=jackpot_message), thread_id=thread_id, thread_type=thread_type, ttl=180000)
        jackpot_data["pool"] = 0
        jackpot_data["counter"] = 100
        jackpot_data["participants"] = []
    save_jackpot_data(jackpot_data)
    
    current_round = None

# -------------------------------
# Hàm xử lý lệnh chơi Tài Xỉu kiểu "ngay lập tức"
def handle_taixiu_command(message, message_object, thread_id, thread_type, author_id, client):
    global current_round
    if current_round is not None:
        handle_taixiu_bet_command(message, message_object, thread_id, thread_type, author_id, client)
        return

    client.sendReaction(message_object, "✅", thread_id, thread_type, reactionType=75)
    text = message.split()
    money_data = load_money_data()
    jackpot_data = load_jackpot_data()
    response_message = ""
    
    if len(text) not in [3, 5]:
        guide_image_path = "modules/cache/images/taixiuhelp.png"
        if os.path.exists(guide_image_path):
            client.sendLocalImage(
                imagePath=guide_image_path,
                message=Message(text=(
    "🌟 HƯỚNG DẪN CHƠI TÀI XỈU 🎲\n"
    "  • Không cần đăng kí tài khoản\n"
    "  • Gõ tx daily nhận tiền chơi\n"
    "  • Gõ on để mở chế độ chơi nhiều người\n"
    "────────────────────────────\n"
    "📜 LUẬT CHƠI:\n"
    "  • Hệ thống sẽ tung 3 viên xúc xắc trong mỗi ván.\n"
    "  • Tổng điểm quyết định kết quả:\n"
    "    - 3-10 điểm → ❎ Xỉu\n"
    "    - 11-18 điểm → ✅ Tài\n"
    "  • Phân loại Chẵn/Lẻ:\n"
    "    - Tổng điểm chia hết cho 2 → ✅ Chẵn\n"
    "    - Tổng điểm không chia hết cho 2 → ❎ Lẻ\n"
    "────────────────────────────\n"
    "💰 CƯỢC:\n"
    "  • Cược đơn:\n"
    "    - Cú pháp: txiu <tài/xỉu/chẵn/lẻ> <số tiền/all/%số tiền>\n"
    "    - Ví dụ: txiu tài 10000 | txiu lẻ all | txiu xỉu 50%\n"
    "    - Bạn chỉ được đặt một loại cược duy nhất (Tài, Xỉu, Chẵn hoặc Lẻ).\n"
    "  • Cược kết hợp:\n"
    "    - Cú pháp: txiu <tài/xỉu> <số tiền/all/%số tiền> <chẵn/lẻ> <số tiền/all/%số tiền>\n"
    "    - Ví dụ: txiu tài 10000 chẵn 5000\n"
    "    - Đặt cược cùng lúc cả Tài/Xỉu và Chẵn/Lẻ.\n"
    "    - Số dư phải đủ để thực hiện cả hai cược.\n"
    "────────────────────────────\n"
    "📊 LỆNH KHÁC:\n"
    "  • soi: Xem thông tin soi cầu của phiên hiện tại.\n"
    "  • xemphientruoc: Xem kết quả của 100 ván chơi trước đó.\n"
    "  • lichsu: Xem lịch sử chiến tích của bạn.\n"
    "  • dudoan: Xem dự đoán kết quả kế tiếp\n"
)),
                thread_id=thread_id,
                thread_type=thread_type,
                width=1000,
                height=600,
                ttl=60000
            )
        return

    # Nếu nhập lệnh kết hợp (5 phần)
    if len(text) == 5:
        choice_tx = text[1].lower()
        bet_tx_input = text[2].lower()
        choice_ce = text[3].lower()
        bet_ce_input = text[4].lower()
        if choice_tx not in ["tài", "xỉu"] or choice_ce not in ["chẵn", "lẻ"]:
            client.replyMessage(Message(text="❌ Lệnh không hợp lệ! Phần cược phải là: txiu <tài/xỉu> <số tiền/all/%> <chẵn/lẻ> <số tiền/all/%>"),
                                message_object, thread_id, thread_type, ttl=20000)
            return
        current_balance = money_data.get(str(author_id), 0)
        bet_tx = parse_bet_amount(bet_tx_input, current_balance)
        bet_ce = parse_bet_amount(bet_ce_input, current_balance)
        if bet_tx is None or bet_ce is None:
            client.replyMessage(Message(text="❌ Số tiền cược không hợp lệ."),
                                message_object, thread_id, thread_type, ttl=20000)
            return
        total_bet = bet_tx + bet_ce
        if total_bet > current_balance:
            client.replyMessage(Message(text="❌ Số dư không đủ cho cả hai cược."),
                                message_object, thread_id, thread_type, ttl=20000)
            return
        money_data[str(author_id)] = current_balance - total_bet
        save_money_data(money_data)
        if author_id not in jackpot_data.get("participants", []):
            jackpot_data.setdefault("participants", []).append(author_id)
        save_jackpot_data(jackpot_data)
        dice_values = [random.randint(1, 6) for _ in range(3)]
        total_points = sum(dice_values)
        result_tx = "tài" if total_points >= 11 else "xỉu"
        result_ce = "chẵn" if total_points % 2 == 0 else "lẻ"
        current_history = load_current_soicau_data()
        current_history.append({
            "dice": dice_values,
            "sum": total_points,
            # Chỉ lưu "Tài" hoặc "Xỉu" vào trường "result"
            "result": result_tx.capitalize()  # Hoặc tai_or_xiu.capitalize()
        })
        save_current_soicau_data(current_history)

        win_tx = (choice_tx == result_tx)
        win_ce = (choice_ce == result_ce)
        result_lines = []
        net_change_total = 0
        if win_tx:
            winnings = bet_tx * 5
            jackpot_contribution = int(winnings * 0.05)
            net_win = winnings - jackpot_contribution
            money_data[str(author_id)] += net_win
            result_lines.append(f"✅ {choice_tx.capitalize()} thắng: +{format_money(net_win)} (đóng góp {format_money(jackpot_contribution)} cho Hũ)")
            net_change_tx = net_win
            jackpot_data["pool"] += jackpot_contribution
        else:
            result_lines.append(f"⛔ {choice_tx.capitalize()} thua: -{format_money(bet_tx)}")
            net_change_tx = -bet_tx
        if win_ce:
            winnings = bet_ce * 5
            jackpot_contribution = int(winnings * 0.05)
            net_win = winnings - jackpot_contribution
            money_data[str(author_id)] += net_win
            result_lines.append(f"✅ {choice_ce.capitalize()} thắng: +{format_money(net_win)} (đóng góp {format_money(jackpot_contribution)} cho Hũ)")
            net_change_ce = net_win
            jackpot_data["pool"] += jackpot_contribution
        else:
            result_lines.append(f"⛔ {choice_ce.capitalize()} thua: -{format_money(bet_ce)}")
            net_change_ce = -bet_ce
        net_change_total = net_change_tx + net_change_ce
        save_money_data(money_data)
        save_jackpot_data(jackpot_data)
        # Thông báo đặt cược thành công
        author_name = get_user_name(client, author_id)
        client.sendMessage(
            Message(text=f"✅ {author_name}, bạn đã đặt cược thành công {format_money(bet_tx)} vào {choice_tx.capitalize()} và {format_money(bet_ce)} vào {choice_ce.capitalize()}"),
            thread_id=thread_id,
            thread_type=thread_type,
            ttl=30000
        )

        history_data = load_history_data()
        username = get_user_name(client, author_id)
        record_tx = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            "bet": bet_tx,
            "choice": choice_tx,
            "dice": dice_values,
            "total_points": total_points,
            "result": result_tx.capitalize(),
            "outcome": "Thắng" if win_tx else "Thua",
            "net_change": net_change_tx,
            "balance": money_data.get(str(author_id), 0)
        }
        record_ce = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            "bet": bet_ce,
            "choice": choice_ce,
            "dice": dice_values,
            "total_points": total_points,
            "result": result_ce.capitalize(),
            "outcome": "Thắng" if win_ce else "Thua",
            "net_change": net_change_ce,
            "balance": money_data.get(str(author_id), 0)
        }
        user_history = history_data.get(username, [])
        user_history.append(record_tx)
        user_history.append(record_ce)
        history_data[username] = user_history
        save_history_data(history_data)
        author_name = get_user_name(client, author_id)
        mention = Mention(author_id, length=len(author_name), offset=0)
        balance = money_data.get(str(author_id), 0)
        if balance < 100_000:
            rank_title = "🌱 Tay trắng"
        elif balance < 1_000_000:
            rank_title = "🆕 Người mới vào nghề"
        elif balance < 10_000_000:
            rank_title = "🔰 Tập sự Tài Xỉu"
        elif balance < 50_000_000:
            rank_title = "📈 Con bạc tiềm năng"
        elif balance < 100_000_000:
            rank_title = "💼 Dân chơi có số má"
        elif balance < 500_000_000:
            rank_title = "💰 Cao thủ Tài Xỉu"
        elif balance < 1_000_000_000:
            rank_title = "🏆 Đại gia khu vực"
        elif balance < 10_000_000_000:
            rank_title = "💎 Triệu phú Tài Xỉu"
        elif balance < 50_000_000_000:
            rank_title = "🔥 Huyền thoại đỏ đen"
        elif balance < 100_000_000_000:
            rank_title = "👑 Thánh nhân cờ bạc"
        else:
            rank_title = "💎 Vua Tài Xỉu"
        progress = int((100 - jackpot_data["counter"]) / 10)
        progress_bar = "█" * progress + "░" * (10 - progress)
        response_message = (
            f"{author_name}\n"
            f"🏆 Danh hiệu: {rank_title}\n"
            f"🎰 Hũ may mắn: {format_money(jackpot_data['pool'])}\n"
            f"📈 Tiến trình nổ hũ: [{progress_bar}] {100 - jackpot_data['counter']}%\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🎲 Xúc xắc: {dice_values[0]} - {dice_values[1]} - {dice_values[2]}\n"
            f"🔢 Tổng điểm: {total_points}\n"
            f"✅ Kết quả Tài/Xỉu: {result_tx.capitalize()}\n"
            f"✅ Kết quả Chẵn/Lẻ: {result_ce.capitalize()}\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n" +
            "\n".join(result_lines) +
            f"\n━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💸 Biến động số dư: {'+' if net_change_total >= 0 else ''}{format_money(net_change_total)}\n"
            f"💰 Số dư hiện tại: {format_money(money_data.get(str(author_id), 0))}"
        )
        gif_path = "modules/cache/gif/giftxvipp.gif"
        run_async(client.sendLocalGif,
                  gifPath=gif_path,
                  thumbnailUrl=None,
                  thread_id=thread_id,
                  thread_type=thread_type,
                  width=1000,
                  height=600,
                  ttl=6000)
        def delayed_send_image():
            time.sleep(8)
            image_paths = [f'modules/cache/datatx/{dice_values[0]}.png',
                           f'modules/cache/datatx/{dice_values[1]}.png',
                           f'modules/cache/datatx/{dice_values[2]}.png']
            merged_image_path = "modules/cache/datatx/merged_dice.png"
            if all(os.path.exists(path) for path in image_paths):
                merge_dice_images_triangle(image_paths, 0, "", merged_image_path, mode="individual", dice_sum=total_points,
                    tai_or_xiu=result_tx.capitalize(),
                    chan_or_le=result_ce.capitalize())
                client.sendLocalImage(
                    imagePath=merged_image_path,
                    message=Message(text=response_message),
                    thread_id=thread_id,
                    thread_type=thread_type,
                    width=1000,
                    height=600,
                    ttl=60000
                )
                try:
                    os.remove(merged_image_path)
                except Exception as e:
                    print(f"Lỗi xóa file {merged_image_path}: {e}")
            else:
                client.replyMessage(Message(text="\n❌ Không thể hiển thị hình ảnh kết quả do thiếu hình ảnh xúc xắc."),
                                    message_object, thread_id, thread_type, ttl=20000)
        run_async(delayed_send_image)
        return
    else:
        # Xử lý lệnh đơn
        if text[1].lower() not in ["tài", "xỉu", "chẵn", "lẻ"]:
            response_message = (
                "❌ Lệnh không hợp lệ !\n"
                "Chỉ được chọn: tài, xỉu, chẵn, hoặc lẻ\n"
                "→ Ví dụ: txiu tài 10000 hoặc txiu lẻ 5000"
            )
            client.replyMessage(Message(text=response_message), message_object, thread_id, thread_type, ttl=20000)
            return
        choice = text[1].lower()
        current_balance = money_data.get(str(author_id), 0)
        if text[2].lower() == "all":
            bet_amount = current_balance
        elif text[2].endswith('%'):
            try:
                percent = float(text[2][:-1])
                if 1 <= percent <= 100:
                    bet_amount = int(current_balance * (percent / 100))
                else:
                    response_message = "❌ Phần trăm phải từ 1% đến 100%."
                    bet_amount = 0
            except ValueError:
                response_message = "❌ Phần trăm cược không hợp lệ. Vui lòng nhập lại (ví dụ: 50%)"
                bet_amount = 0
        else:
            try:
                bet_amount = int(text[2])
            except ValueError:
                response_message = "❌ Số tiền cược không hợp lệ. Không nhập dấu phẩy ( , )"
                bet_amount = 0
        if bet_amount > current_balance:
            response_message = (
                "❌ Số dư không đủ để đặt cược.\n"
                "→ Vui lòng nhập 'tx daily' để nhận tiền miễn phí."
            )
            client.replyMessage(Message(text=response_message), message_object, thread_id, thread_type, ttl=20000)
            return
        elif bet_amount <= 0:
            response_message = (
                "❌ Số tiền cược phải lớn hơn 0.\n"
                "→ Kiểm tra lại số dư và số tiền bạn nhập.\n"
                "→ Nhập tx daily để nhận tiền miễn phí."
            )
            client.replyMessage(Message(text=response_message), message_object, thread_id, thread_type, ttl=20000)
            return
        money_data[str(author_id)] = current_balance - bet_amount
        if author_id not in jackpot_data.get("participants", []):
            jackpot_data.setdefault("participants", []).append(author_id)
        author_name = get_user_name(client, author_id)
        client.sendMessage(
            Message(text=f"✅ {author_name}, bạn đã đặt cược thành công {format_money(bet_amount)} vào {choice.capitalize()}."),
            thread_id=thread_id,
            thread_type=thread_type,
            ttl=10000
        )
        dice_values = [random.randint(1, 6) for _ in range(3)]
        total_points = sum(dice_values)
        dice_sum = total_points
        tai_or_xiu = "Tài" if dice_sum >= 11 else "Xỉu"
        chan_or_le = "Chẵn" if dice_sum % 2 == 0 else "Lẻ"
        if choice in ["tài", "xỉu"]:
            result = "Xỉu" if 3 <= total_points <= 10 else "Tài"
        else:
            result = "Chẵn" if total_points % 2 == 0 else "Lẻ"
        result_tx = "tài" if total_points >= 11 else "xỉu"    
        win_condition = (choice == result.lower())
        outcome = "✅ Bạn đã thắng" if win_condition else "⛔ Bạn đã thua"
        current_history = load_current_soicau_data()
        # Sau khi sửa:
        current_history.append({
            "dice": dice_values,
            "sum": total_points,
            "result": result,  # Sử dụng biến result đã xác định ở trên
            "result_tx": result_tx  # Nếu cần, giữ nguyên nếu có dùng đến
        })

        if len(current_history) >= 100:
            save_old_soicau_data(current_history)
            current_history = []
        save_current_soicau_data(current_history)
        jackpot_contribution = 0
        if win_condition:
            winnings = bet_amount * 5
            jackpot_contribution = int(winnings * 0.05)
            net_win = winnings - jackpot_contribution
            money_data[str(author_id)] += net_win
            response = f"✅ Đã cộng {format_money(net_win)} vào số dư \n✅ Đóng góp {format_money(jackpot_contribution)} cho Hũ"
            jackpot_data["pool"] += jackpot_contribution
        else:
            response = f"🚫 Đã trừ {format_money(bet_amount)} khỏi số dư"
        save_money_data(money_data)
        save_jackpot_data(jackpot_data)
        username = get_user_name(client, author_id)
        history_data = load_history_data()
        user_history = history_data.get(username, [])
        record = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            "bet": bet_amount,
            "choice": choice,
            "dice": dice_values,
            "total_points": total_points,
            "result": result,
            "outcome": outcome,
            "net_change": net_win if win_condition else -bet_amount,
            "balance": money_data.get(str(author_id), 0)
        }
        user_history.append(record)
        history_data[username] = user_history
        save_history_data(history_data)
        print("Jackpot data: pool =", jackpot_data["pool"],
              ", counter =", jackpot_data["counter"],
              ", participants =", jackpot_data["participants"])
        author_name = get_user_name(client, author_id)
        mention = Mention(author_id, length=len(author_name), offset=0)
        balance = money_data.get(str(author_id), 0)
        if balance < 100_000:
            rank_title = "🌱 Tay trắng"
        elif balance < 1_000_000:
            rank_title = "🆕 Người mới vào nghề"
        elif balance < 10_000_000:
            rank_title = "🔰 Tập sự Tài Xỉu"
        elif balance < 50_000_000:
            rank_title = "📈 Con bạc tiềm năng"
        elif balance < 100_000_000:
            rank_title = "💼 Dân chơi có số má"
        elif balance < 500_000_000:
            rank_title = "💰 Cao thủ Tài Xỉu"
        elif balance < 1_000_000_000:
            rank_title = "🏆 Đại gia khu vực"
        elif balance < 10_000_000_000:
            rank_title = "💎 Triệu phú Tài Xỉu"
        elif balance < 50_000_000_000:
            rank_title = "🔥 Huyền thoại đỏ đen"
        elif balance < 100_000_000_000:
            rank_title = "👑 Thánh nhân cờ bạc"
        else:
            rank_title = "💎 Vua Tài Xỉu"
        progress = int((100 - jackpot_data["counter"]) / 10)
        progress_bar = "█" * progress + "░" * (10 - progress)
        data_trave = (
            f"{author_name}\n"
            f"🏆 Danh hiệu: {rank_title}\n"
            f"🎰 Hũ may mắn: {format_money(jackpot_data['pool'])}\n"
            f"📈 Tiến trình nổ hũ: [{progress_bar}] {100 - jackpot_data['counter']}%\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💸 Bạn đã đặt cược: {format_money(bet_amount)} vào {choice.capitalize()}\n"
            f"🎲 Khui: {dice_values[0]} - {dice_values[1]} - {dice_values[2]}\n"
            f"🔢 Tổng điểm: {total_points} ({result})\n"                
            "━━━━━━━━━━━━━━━━━━━━━━\n"               
            f"{outcome}\n"
            f"{response}\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"            
            f"💰 Số dư hiện tại:\n"
            f"💵 {format_money(money_data.get(str(author_id), 0))}\n"
            "━━━━━━━━━━━━━━━━━━━━━━"
        )
        gui = Message(
            text=data_trave,
            style=MultiMsgStyle([
                MessageStyle(offset=0, length=len(data_trave), style="font", size=12, auto_format=False, color="blue"),
                MessageStyle(offset=0, length=len(data_trave), style="italic", auto_format=False, color="green")
            ]),
            mention=mention
        )
        gif_path = "modules/cache/gif/giftxvipp.gif"
        run_async(client.sendLocalGif,
                  gifPath=gif_path,
                  thumbnailUrl=None,
                  thread_id=thread_id,
                  thread_type=thread_type,
                  width=1000,
                  height=600,
                  ttl=6000)
        def delayed_send_image():
            time.sleep(8)
            image_paths = [f'modules/cache/datatx/{dice_values[0]}.png',
                           f'modules/cache/datatx/{dice_values[1]}.png',
                           f'modules/cache/datatx/{dice_values[2]}.png']
            merged_image_path = "modules/cache/datatx/merged_dice.png"
            if all(os.path.exists(path) for path in image_paths):
                merge_dice_images_triangle(image_paths, bet_amount, choice, merged_image_path, mode="individual", dice_sum=dice_sum,
                    tai_or_xiu=tai_or_xiu,
                    chan_or_le=chan_or_le)
                client.sendLocalImage(
                    imagePath=merged_image_path,
                    message=gui,
                    thread_id=thread_id,
                    thread_type=thread_type,
                    width=1000,
                    height=600,
                    ttl=60000
                )
                try:
                    os.remove(merged_image_path)
                except Exception as e:
                    print(f"Lỗi xóa file {merged_image_path}: {e}")
            else:
                client.replyMessage(Message(text="\n❌ Không thể hiển thị hình ảnh kết quả do thiếu hình ảnh xúc xắc."),
                                    message_object, thread_id, thread_type, ttl=20000)
        run_async(delayed_send_image)
        decrement = random.randint(5, 10)
        jackpot_data["counter"] -= decrement
        print(f"Sau lượt chơi, counter giảm đi {decrement} và hiện tại counter =", jackpot_data["counter"])
        save_jackpot_data(jackpot_data)
        if jackpot_data["counter"] <= 0:
            if jackpot_data.get("participants"):
                winner_id = random.choice(jackpot_data["participants"])
                money_data[str(winner_id)] += jackpot_data["pool"]
                save_money_data(money_data)
                info_response = client.fetchUserInfo(winner_id)
                profiles = info_response.unchanged_profiles or info_response.changed_profiles
                winner_name = profiles.get(winner_id, {}).get("zaloName", "Không xác định")
                jackpot_message = (
                    f"🎉 CHÚC MỪNG {winner_name} ĐÃ NỔ HŨ 🎉\n"
                    f"💰 Bạn nhận được {format_money(jackpot_data['pool'])} từ Hũ may mắn!"
                )
                client.sendMessage(Message(text=jackpot_message), thread_id=thread_id, thread_type=thread_type, ttl=180000)
            jackpot_data["pool"] = 0
            jackpot_data["counter"] = 100
            jackpot_data["participants"] = []
            save_jackpot_data(jackpot_data)
        if response_message:
            client.replyMessage(Message(text=response_message), message_object, thread_id, thread_type, ttl=60000)

# -------------------------------
# Các hàm xử lý lệnh khác (soi, xemphientruoc, dsnohu, dudoan, lichsu)
def handle_soicau_command(message, message_object, thread_id, thread_type, author_id, client):
    current_history = load_current_soicau_data()
    if not current_history:
        client.sendMessage(Message(text="❌ Chưa có dữ liệu soi cầu ở phiên hiện tại."),
                           thread_id=thread_id, thread_type=thread_type, ttl=20000)
        return
    soicau_image_path = create_soicau_image(current_history)
    if os.path.exists(soicau_image_path):
        client.sendLocalImage(
            imagePath=soicau_image_path,
            message=Message(text="Phiên soi cầu hiện tại\nSoạn : xemphientruoc để xem phiên trước đó"),
            thread_id=thread_id,
            thread_type=thread_type,
            width=1000,
            height=500,
            ttl=60000
        )
    else:
        client.sendMessage(Message(text="❌ Lỗi khi tạo ảnh soi cầu."),
                           thread_id=thread_id, thread_type=thread_type, ttl=20000)

def handle_xemphientruoc_command(message, message_object, thread_id, thread_type, author_id, client):
    old_history = load_old_soicau_data()
    if not old_history:
        client.sendMessage(Message(text="❌ Không có dữ liệu phiên trước."),
                           thread_id=thread_id, thread_type=thread_type, ttl=20000)
        return
    soicau_image_path = create_soicau_image(old_history)
    if os.path.exists(soicau_image_path):
        client.sendLocalImage(
            imagePath=soicau_image_path,
            message=Message(text="Phiên soi cầu trước:"),
            thread_id=thread_id,
            thread_type=thread_type,
            width=800,
            height=480,
            ttl=60000
        )
    else:
        client.sendMessage(Message(text="❌ Lỗi khi tạo ảnh phiên trước."),
                           thread_id=thread_id, thread_type=thread_type, ttl=20000)

def handle_listjackpot_command(message, message_object, thread_id, thread_type, author_id, client):
    jackpot_data = load_jackpot_data()
    participants = jackpot_data.get("participants", [])
    if not participants:
        client.sendMessage(Message(text="Hiện chưa có người chơi nào tham gia nổ hũ."),
                           thread_id=thread_id, thread_type=thread_type, ttl=60000)
        return

    response_lines = ["DANH SÁCH NGƯỜI CHƠI CÓ KHẢ NĂNG NỔ HŨ:"]
    for idx, pid in enumerate(participants, start=1):
        info_response = client.fetchUserInfo(pid)
        profiles = info_response.unchanged_profiles or info_response.changed_profiles
        name = profiles.get(pid, {}).get("zaloName", "Không xác định")
        response_lines.append(f"{idx}. {name}")
    client.sendMessage(Message(text="\n".join(response_lines)),
                       thread_id=thread_id, thread_type=thread_type, ttl=60000)

def weighted_prediction(history):
    weighted_tai = weighted_xiu = total_weight = 0
    for i, item in enumerate(reversed(history), start=1):
        weight = 1 / i
        total_weight += weight
        if item['result'] == 'Tài':
            weighted_tai += weight
        else:
            weighted_xiu += weight
    return weighted_tai / total_weight, weighted_xiu / total_weight

def handle_dudoan_command(message, message_object, thread_id, thread_type, author_id, client):
    history = load_current_soicau_data()
    if not history or len(history) < 10:
        client.sendMessage(Message(text="❌ Dữ liệu chưa đủ (ít hơn 10 ván) để đưa ra dự đoán khách quan. Hãy chơi thêm vài ván nữa!"),
                           thread_id=thread_id, thread_type=thread_type, ttl=20000)
        return

    total = len(history)
    prob_tai, prob_xiu = weighted_prediction(history)
    confidence = abs(prob_tai - prob_xiu)
    threshold = 0.1
    if confidence < threshold:
        predicted = "Cân bằng"
        reasons = [
            "ván chơi gần đây cho thấy sự cân bằng giữa 'Tài' và 'Xỉu', không đủ bằng chứng để chọn bên nào.",
            "số liệu thống kê cho thấy cả hai đều xuất hiện tương đương.",
            "xu hướng của các ván chơi khá đồng đều."
        ]
    else:
        predicted = "Tài" if prob_tai > prob_xiu else "Xỉu"
        if predicted == "Tài":
            reasons = [
                "những ván gần đây cho thấy 'Tài' xuất hiện thường xuyên hơn.",
                "số liệu cho thấy 'Tài' có lợi thế rõ ràng.",
                "xu hướng của các ván chơi gần đây nghiêng về 'Tài'."
            ]
        else:
            reasons = [
                "các kết quả mới nhất cho thấy 'Xỉu' chiếm ưu thế.",
                "số liệu cho thấy 'Xỉu' có lợi thế hơn.",
                "xu hướng thống kê cho thấy 'Xỉu' đang dẫn đầu."
            ]
    chosen_reason = random.choice(reasons)
    response = (
        f"Dựa vào {total} ván với Tài {prob_tai*100:.1f}% và Xỉu {prob_xiu*100:.1f}%, "
        f"tôi dự đoán {predicted} vì {chosen_reason} "
        f"và độ tự tin dự đoán là {confidence*100:.1f}%."
    )
    client.sendMessage(Message(text=response),
                       thread_id=thread_id, thread_type=thread_type, ttl=30000)

def handle_history_command(message, message_object, thread_id, thread_type, author_id, client):
    parts = message.split()
    target_username = ' '.join(parts[1:]).strip()[1:] if len(parts) >= 2 and parts[1].startswith('@') else \
                      (get_user_name(client, author_id) if len(parts) < 2 else ' '.join(parts[1:]).strip())
    
    history_data = load_history_data()
    user_history = history_data.get(target_username, [])
    
    if not user_history:
        response_message = f"❌ Người dùng '{target_username}' chưa có lịch sử chiến tích nào."
        client.replyMessage(Message(text=response_message), message_object, thread_id, thread_type, ttl=60000)
        return

    total_games = len(user_history)
    wins = sum(1 for record in user_history if record.get('net_change', 0) > 0)
    losses = sum(1 for record in user_history if record.get('net_change', 0) < 0)
    win_rate = (wins / total_games) * 100 if total_games > 0 else 0
    money_won = sum(record.get('net_change', 0) for record in user_history if record.get('net_change', 0) > 0)
    money_lost = sum(-record.get('net_change', 0) for record in user_history if record.get('net_change', 0) < 0)
    
    response_message = (
        f"📜 LỊCH SỬ CHIẾN TÍCH:\n"
        f"👤 {target_username}\n"
        f"🎲 Game: Tài Xỉu\n"
        f"────────────────────────\n"
        f"📊 Tổng số trận: {total_games}\n"
        f"✅ Trận thắng: {wins}\n"
        f"❌ Trận thua: {losses}\n"
        f"📈 Tỉ lệ thắng: {win_rate:.2f}%\n"
        f"💰 Tiền thắng: {format_money(money_won)}\n"
        f"💸 Tiền thua: {format_money(money_lost)}\n"
        f"────────────────────────"
    )
    client.sendMessage(Message(text=response_message),
                       thread_id=thread_id, thread_type=thread_type, ttl=60000)

# -------------------------------
# Mapping lệnh đến các hàm xử lý
def get_mitaizl():
    return {
        'txiu': handle_taixiu_command,
        'taixiu': handle_taixiu_command,
        'soi': handle_soicau_command,
        'xemphientruoc': handle_xemphientruoc_command,
        'dsnohu': handle_listjackpot_command,
        'dudoan': handle_dudoan_command,
        'lichsu': handle_history_command,
        'on': handle_taixiu_on_command
    }
