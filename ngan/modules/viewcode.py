import os
import requests
from config import ADMIN
from zlapi.models import Message
from PIL import Image, ImageDraw, ImageFont
from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import HtmlFormatter
from bs4 import BeautifulSoup

des = {
    'tác giả': "Rosy",
    'mô tả': "Hiển thị nội dung lệnh dưới dạng hình ảnh",
    'tính năng': [
        "📨 Đọc nội dung lệnh từ file Python.",
        "🎨 Tạo hình ảnh hiển thị nội dung lệnh với hiệu ứng gradient.",
        "🖼️ Định dạng văn bản với màu sắc và kích thước font chữ.",
        "🔍 Kiểm tra quyền admin trước khi thực hiện lệnh.",
        "🔔 Thông báo lỗi cụ thể nếu cú pháp lệnh không chính xác hoặc giá trị không hợp lệ."
    ],
    'hướng dẫn sử dụng': [
        "📩 Gửi lệnh viewcode <tên lệnh> để hiển thị nội dung lệnh dưới dạng hình ảnh.",
        "📌 Ví dụ: viewcode unban để hiển thị nội dung lệnh unban dưới dạng hình ảnh.",
        "✅ Nhận thông báo trạng thái và kết quả ngay lập tức."
    ]
}


ADMIN_ID = ADMIN

def is_admin(author_id):
    return author_id == ADMIN_ID

def read_command_content(command_name):
    try:
        file_path = f"modules/{command_name}.py"
        
        if not os.path.exists(file_path):
            return None
        
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        return str(e)

def create_image_from_code(code, command_name):
    fontcre = "modules/cache/Roboto_Condensed-Regular.ttf"
    fontlenh = "modules/cache/Roboto_SemiCondensed-Light.ttf"

    highlighted_soup = highlight_code(code)
    code_lines = code.splitlines()

    line_height = 30
    line_offset = 80

    temp_img = Image.new('RGBA', (1, 1))
    temp_draw = ImageDraw.Draw(temp_img)
    temp_font = ImageFont.truetype(fontcre, 30)  # Đổi từ font_path thành fontcre

    max_width = max(temp_draw.textlength(line, font=temp_font) for line in code_lines) + 170
    img_width = max(3000, max_width)

    img_width = int(img_width)
    img_height = int(line_offset + len(code_lines) * line_height + 60)

    background_color = (30, 30, 30)
    header_color = (50, 50, 50)

    background = Image.new('RGBA', (img_width, img_height), background_color)
    draw = ImageDraw.Draw(background)

    header_height = 50
    draw.rectangle([(0, 0), (img_width, header_height)], fill=header_color)

    header_font = ImageFont.truetype(fontcre, 38)  # Đổi từ font_path thành fontcre
    mitai_text = "ROSY PROJECT"

    mitai_text_width = temp_draw.textlength(mitai_text, font=header_font)
    mitai_text_x = (img_width - mitai_text_width) // 2 + 3

    mitai_text_bbox = draw.textbbox((0, 0), mitai_text, font=header_font)
    mitai_text_height = mitai_text_bbox[3] - mitai_text_bbox[0]

    mitai_text_y = (header_height - mitai_text_height) // 2

    draw.text((mitai_text_x, 10), mitai_text, font=header_font, fill=(100, 100, 100))
    dot_radius_outer = 12
    dot_radius_inner = 8
    dot_spacing = 20
    dots_x_start = 30

    dot_positions = [
        (dots_x_start, 25),
        (dots_x_start + 2 * dot_radius_outer + dot_spacing, 25),
        (dots_x_start + 4 * dot_radius_outer + 2 * dot_spacing, 25)
    ]
    dot_colors = [(255, 59, 48), (40, 205, 65), (255, 190, 0)]
    inner_dot_color = header_color

    for pos, border_color in zip(dot_positions, dot_colors):
        draw.ellipse([pos[0] - dot_radius_outer, pos[1] - dot_radius_outer,
                      pos[0] + dot_radius_outer, pos[1] + dot_radius_outer], fill=border_color)

        draw.ellipse([pos[0] - dot_radius_inner, pos[1] - dot_radius_inner,
                      pos[0] + dot_radius_inner, pos[1] + dot_radius_inner], fill=inner_dot_color)

    draw.text((mitai_text_x, 10), mitai_text, font=header_font, fill=(100, 100, 100))

    command_font = ImageFont.truetype(fontlenh, 25)  # Đổi từ font_path thành fontlenh
    command_text = f"{command_name}.py"

    command_text_width = temp_draw.textlength(command_text, font=command_font)
    python_logo_width = 24
    tab_padding = 20
    tab_width = int(command_text_width + python_logo_width + tab_padding * 3)
    tab_height = 50
    tab_color = background_color
    corner_radius = 15

    tab_x = dots_x_start + 4 * dot_radius_outer + 2 * dot_spacing + 40
    tab_y = (header_height - tab_height) // 2 + 10

    draw.rounded_rectangle([(tab_x, tab_y), (tab_x + tab_width, tab_y + tab_height)], radius=corner_radius, fill=tab_color)

    python_logo_path = "modules/cache/python-logo.png"
    if os.path.exists(python_logo_path):
        python_logo = Image.open(python_logo_path)
        python_logo = python_logo.resize((25, 25))
        background.paste(python_logo, (tab_x + tab_padding, tab_y + 8), python_logo)

    draw.text((tab_x + python_logo_width + tab_padding * 2, tab_y + 0), command_text, font=command_font, fill=(255, 255, 255))

    y_offset = line_offset + header_height

    code_font = ImageFont.truetype(fontcre, 25)  # Đổi từ font_path thành fontcre
    line_font = ImageFont.truetype(fontcre, 25)  # Đổi từ font_path thành fontcre

    for i, line in enumerate(code_lines):
        line_number = f"{i + 1:2}"
        draw.text((10, y_offset), line_number, font=line_font, fill=(220, 220, 220))

        highlighted_line = highlight(line, PythonLexer(), HtmlFormatter())
        soup_line = BeautifulSoup(highlighted_line, 'html.parser')

        leading_spaces = len(line) - len(line.lstrip(' '))
        x_offset = 60 + leading_spaces * draw.textlength(' ', font=code_font)

        spans = soup_line.find_all('span')
        last_end_index = 0

        for span in spans:
            token_text = span.get_text()
            token_color = get_color_for_token_type(span)

            start_index = line.find(token_text, last_end_index)
            if start_index > last_end_index:
                space_text = line[last_end_index:start_index]
                draw.text((x_offset, y_offset), space_text, font=code_font, fill=(220, 220, 220))

                x_offset += draw.textlength(space_text, font=code_font)

            draw.text((x_offset, y_offset), token_text, font=code_font, fill=token_color)

            x_offset += draw.textlength(token_text, font=code_font)
            last_end_index = start_index + len(token_text)

        if last_end_index < len(line):
            remaining_space = line[last_end_index:]
            draw.text((x_offset, y_offset), remaining_space, font=code_font, fill=(220, 220, 220))

        y_offset += line_height

    image_path = "modules/cache/anh.png"
    background.save(image_path)
    return image_path, img_width, img_height

def highlight_code(code):
    formatter = HtmlFormatter()
    highlighted_code = highlight(code, PythonLexer(), formatter)
    soup = BeautifulSoup(highlighted_code, "html.parser")
    return soup

def get_color_for_token_type(span):
    color_map = {
        'k': (0, 255, 255),
        'n': (255, 232, 255),
        's': (255, 255, 107),
        'c': (173, 216, 230),
        'o': (225, 225, 225),
        'p': (0, 255, 0),
        'm': (233, 51, 35),
    }
    if 'class' in span.attrs:
        token_type = span['class'][0][0]
        return color_map.get(token_type, (220, 220, 220))
    return (220, 220, 220)

def handle_viewcode_command(message, message_object, thread_id, thread_type, author_id, client):
    lenhcanlay = message.split()

    if len(lenhcanlay) < 2:
        error_message = Message(text="Vui lòng nhập tên lệnh cần lấy.")
        client.replyMessage(error_message, message_object, thread_id, thread_type)
        return

    command_name = lenhcanlay[1].strip()

    if not is_admin(author_id):
        response_message = "• Bạn không đủ quyền hạn để sử dụng lệnh này."
        message_to_send = Message(text=response_message)
        client.replyMessage(message_to_send, message_object, thread_id, thread_type)
        return

    command_content = read_command_content(command_name)
    
    if command_content is None:
        response_message = f"Lệnh '{command_name}' không được tìm thấy trong các module."
        message_to_send = Message(text=response_message)
        client.replyMessage(message_to_send, message_object, thread_id, thread_type)
        return

    try:
        image_path, img_width, img_height = create_image_from_code(command_content, command_name)

        if os.path.exists(image_path):
            message_text = f"Đây là nội dung của lệnh ( {command_name} )mà bạn đã yêu cầu:"

            styled_message = Message(text=message_text)

            client.sendLocalImage(
                image_path, 
                message=styled_message,  # Thêm nội dung cho hình ảnh
                thread_id=thread_id,
                thread_type=thread_type,
                width=img_width,
                height=img_height,
                ttl=60000
            )
            os.remove(image_path)

    except Exception as e:
        response_message = f"Có lỗi xảy ra: {str(e)}"
        message_to_send = Message(text=response_message)
        client.replyMessage(message_to_send, message_object, thread_id, thread_type)
def get_mitaizl():
    return {
        'viewcode': handle_viewcode_command
    }