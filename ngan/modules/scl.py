import os
import re
import time
import random
import requests
import yt_dlp
from zlapi import *
from zlapi.models import *
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from PIL import Image, ImageDraw, ImageFont
import urllib.parse

# Global lưu danh sách bài hát theo thread_id
song_search_results = {}

# Lưu trạng thái của mỗi thread_id: 
# (time_search_sent, has_selected, image_path, thread_type)
search_status = {}


# ---------------------------
# Các hàm hỗ trợ chung
# ---------------------------
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

def draw_gradient_text(draw, text, position, font, gradient_colors):
    """
    Vẽ text với hiệu ứng gradient (không dùng hiệu ứng bóng).
    """
    gradient = interpolate_colors(gradient_colors, text_length=len(text), change_every=4)
    x, y = position
    for i, char in enumerate(text):
        char_color = gradient[i]
        draw.text((x, y), char, font=font, fill=char_color)
        char_bbox = draw.textbbox((x, y), char, font=font)
        char_width = char_bbox[2] - char_bbox[0]
        x += char_width

def add_multicolor_rectangle_border(image, colors, border_thickness):
    new_w = image.width + 2 * border_thickness
    new_h = image.height + 2 * border_thickness
    border_img = Image.new("RGBA", (new_w, new_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(border_img)
    # Vẽ viền trên và dưới
    for x in range(new_w):
        color = get_gradient_color(colors, x / new_w)
        draw.line([(x, 0), (x, border_thickness - 1)], fill=color)
        draw.line([(x, new_h - border_thickness), (x, new_h - 1)], fill=color)
    # Vẽ viền trái và phải
    for y in range(new_h):
        color = get_gradient_color(colors, y / new_h)
        draw.line([(0, y), (border_thickness - 1, y)], fill=color)
        draw.line([(new_w - border_thickness, y), (new_w - 1, y)], fill=color)
    border_img.paste(image, (border_thickness, border_thickness), image)
    return border_img

def wrap_text(text, font, max_width, draw):
    """
    Tách một đoạn text thành nhiều dòng sao cho chiều rộng mỗi dòng không vượt quá max_width.
    """
    words = text.split()
    lines = []
    current_line = ""
    for word in words:
        test_line = current_line + (" " if current_line else "") + word
        bbox = draw.textbbox((0, 0), test_line, font=font)
        text_width = bbox[2] - bbox[0]
        if text_width <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    return lines

def add_circular_multicolor_border(image, colors, border_thickness):
    """
    Thêm viền tròn đa sắc mịn hơn quanh ảnh đã có định dạng tròn.
    Sử dụng kỹ thuật vẽ ở độ phân giải cao và thu nhỏ lại.
    Giả sử ảnh truyền vào là ảnh vuông có alpha channel.
    """
    scale = 4  # Hệ số tăng độ phân giải để anti-aliasing
    scaled_thickness = border_thickness * scale
    size = image.size  # Giả sử kích thước của ảnh: (w, h)
    new_size = (size[0] + 2 * border_thickness, size[1] + 2 * border_thickness)
    scaled_new_size = (new_size[0] * scale, new_size[1] * scale)

    # Tạo ảnh nền cho viền ở độ phân giải cao
    border_img_scaled = Image.new("RGBA", scaled_new_size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(border_img_scaled)

    # Vẽ viền: lặp qua từng offset (đã scale) và vẽ các cung nhỏ
    for offset in range(scaled_thickness):
        bbox = (offset, offset, scaled_new_size[0] - offset - 1, scaled_new_size[1] - offset - 1)
        for angle in range(360):
            color = get_gradient_color(colors, angle / 360)
            draw.arc(bbox, angle, angle + 1, fill=color, width=1)

    # Scale ảnh gốc lên độ phân giải cao
    image_scaled = image.resize((size[0] * scale, size[1] * scale), resample=Image.LANCZOS)
    # Dán ảnh gốc đã scale lên tại vị trí offset = scaled_thickness
    border_img_scaled.paste(image_scaled, (scaled_thickness, scaled_thickness), image_scaled)

    # Thu nhỏ ảnh viền về kích thước ban đầu
    border_img = border_img_scaled.resize(new_size, resample=Image.LANCZOS)
    return border_img    

def get_headers():
    user_agent = UserAgent()
    return {
        "User-Agent": user_agent.random,
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": 'https://soundcloud.com/',
        "Upgrade-Insecure-Requests": "1"
    }

def search_song_list(query):
    """
    Tìm kiếm bài hát trên SoundCloud và trả về danh sách tối đa 10 bài dưới dạng tuple:
    (url, title, cover_url, artist, duration, genre, release_date, play_count)
    """
    try:
        search_url = f'https://m.soundcloud.com/search?q={urllib.parse.quote(query)}'
        response = requests.get(search_url, headers=get_headers())
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        url_pattern = re.compile(r'^/[^/]+/[^/]+$')
        results = []
        # Duyệt qua các phần tử chứa thông tin bài hát
        for element in soup.select('div > ul > li > div'):
            a_tag = element.select_one('a')
            if a_tag and a_tag.has_attr('href'):
                relative_url = a_tag['href']
                if url_pattern.match(relative_url):
                    title = a_tag.get('aria-label', 'Không rõ')
                    url = 'https://soundcloud.com' + relative_url
                    img_tag = element.select_one('img')
                    cover_url = img_tag['src'] if img_tag and img_tag.has_attr('src') else None
                    artist = element.select_one('span').text if element.select_one('span') else "Không rõ"
                    duration = element.select_one('.sc-ministats-duration').text if element.select_one('.sc-ministats-duration') else "Không rõ"
                    genre = element.select_one('.sc-ministats-genre').text if element.select_one('.sc-ministats-genre') else "Không rõ"
                    release_date = element.select_one('.sc-ministats-release-date').text if element.select_one('.sc-ministats-release-date') else "Không rõ"
                    play_count = element.select_one('.sc-ministats-play-count').text if element.select_one('.sc-ministats-play-count') else "Không rõ"
                    results.append((url, title, cover_url, artist, duration, genre, release_date, play_count))
                if len(results) == 10:
                    break
        return results
    except Exception as e:
        print(f"Lỗi khi tìm kiếm bài hát: {e}")
        return []

def download(link):
    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'cache/downloaded_file.%(ext)s',
            'noplaylist': True,
            'quiet': True
        }
        os.makedirs('cache', exist_ok=True)
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(link, download=True)
            return ydl.prepare_filename(info_dict)
    except Exception as e:
        print(f"Lỗi khi tải âm thanh: {e}")
        return None

def upload_to_uguu(file_path):
    url = "https://uguu.se/upload"
    try:
        with open(file_path, 'rb') as file:
            files = {'files[]': (os.path.basename(file_path), file)}
            response = requests.post(url, files=files, headers=get_headers())
            response.raise_for_status()
            return response.json().get('files', [{}])[0].get('url')
    except Exception as e:
        print(f"Lỗi khi tải lên: {e}")
        return None

def delete_file(file_path):
    try:
        os.remove(file_path)
        print(f"Đã xóa tệp: {file_path}")
    except Exception as e:
        print(f"Lỗi khi xóa tệp: {e}")

# ---------------------------
# Các hàm hỗ trợ tạo ảnh (theo phong cách của lệnh tt)
# ---------------------------
def measure_text_size(font, text):
    try:
        mask = font.getmask(text)
        return mask.size
    except Exception as e:
        print("[ERROR] Lỗi trong measure_text_size:", e)
        return (0, 0)

def draw_rounded_rectangle(draw, xy, radius, fill, outline=None, width=1):
    try:
        x1, y1, x2, y2 = xy
        draw.pieslice([x1, y1, x1 + 2*radius, y1 + 2*radius], 180, 270, fill=fill, outline=outline)
        draw.pieslice([x2 - 2*radius, y1, x2, y1 + 2*radius], 270, 360, fill=fill, outline=outline)
        draw.pieslice([x1, y2 - 2*radius, x1 + 2*radius, y2], 90, 180, fill=fill, outline=outline)
        draw.pieslice([x2 - 2*radius, y2 - 2*radius, x2, y2], 0, 90, fill=fill, outline=outline)
        draw.rectangle([x1+radius, y1, x2-radius, y1+radius], fill=fill, outline=outline)
        draw.rectangle([x1, y1+radius, x2, y2-radius], fill=fill, outline=outline)
        draw.rectangle([x1+radius, y2-radius, x2-radius, y2], fill=fill, outline=outline)
    except Exception as e:
        print("[ERROR] Lỗi trong draw_rounded_rectangle:", e)

def add_solid_border(thumb, border_thickness=3, border_color=(255, 255, 255, 255)):
    try:
        original_size = thumb.size[0]
        new_size = original_size + 2*border_thickness
        border_img = Image.new("RGBA", (new_size, new_size), (0, 0, 0, 0))
        draw_border = ImageDraw.Draw(border_img, "RGBA")
        draw_border.ellipse((0, 0, new_size-1, new_size-1), fill=border_color)
        border_img.paste(thumb, (border_thickness, border_thickness), mask=thumb)
        return border_img
    except Exception as e:
        print("[ERROR] Lỗi trong add_solid_border:", e)
        return thumb

def create_song_list_image(songs, max_show=10):
    """
    Tạo ảnh danh sách bài hát theo phong cách tương tự ảnh mẫu,
    mỗi item bao gồm:
      - Ảnh bìa (nếu có), resize về 80x80 và bo tròn
      - Vòng tròn xanh chứa số thứ tự
      - Tiêu đề (màu trắng)
      - Tên nghệ sĩ (màu xám nhạt, dạng (@artist))
      - Một dòng thống kê (duration | play_count)
    """
    import io

    # Lấy tối đa max_show bài đầu
    songs_to_show = songs[:max_show]
    item_count = len(songs_to_show)

    # Thiết lập kích thước của mỗi item
    item_height = 100       # chiều cao cho mỗi item
    total_width = 700       # chiều rộng ảnh tổng
    total_height = item_height * item_count + 20

    # Màu nền và màu chữ
    background_color = (31, 31, 31)
    item_bg_color = (47, 47, 47)
    circle_color = (43, 170, 65)   # màu vòng tròn xanh
    color_title = (255, 255, 255)
    color_artist = (200, 200, 200)
    color_stats = (160, 160, 160)

    # Tạo ảnh nền tổng
    final_img = Image.new("RGB", (total_width, total_height), background_color)
    draw = ImageDraw.Draw(final_img)

    # Tải font (đường dẫn có thể cần chỉnh theo môi trường của bạn)
    try:
        font_title = ImageFont.truetype("font/Kanit-Medium.ttf", 24)
        font_artist = ImageFont.truetype("font/PublicSans-VariableFont_wght.ttf", 20)
        font_stats = ImageFont.truetype("font/PublicSans-VariableFont_wght.ttf", 18)
    except Exception as e:
        print("[ERROR] Lỗi khi load font:", e)
        font_title = ImageFont.load_default()
        font_artist = ImageFont.load_default()
        font_stats = ImageFont.load_default()

    # Hàm tạo ảnh bìa bo tròn từ URL
    def get_rounded_cover(cover_url, size=(80,80)):
        try:
            response = requests.get(cover_url, headers=get_headers(), timeout=10)
            response.raise_for_status()
            cover_img = Image.open(io.BytesIO(response.content)).convert("RGB")
            cover_img = cover_img.resize(size, Image.Resampling.LANCZOS)
            # Tạo mask tròn
            mask = Image.new("L", size, 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.ellipse((0, 0, size[0], size[1]), fill=255)
            cover_img.putalpha(mask)
            return cover_img
        except Exception as e:
            print(f"[ERROR] Lỗi tải/ xử lý ảnh bìa từ {cover_url}: {e}")
            return None

    # Hàm đo kích thước text
    def measure_text_size(font, text):
        try:
            mask = font.getmask(text)
            return mask.size
        except:
            return (0, 0)

    # Hàm vẽ hình chữ nhật bo góc
    def draw_rounded_rectangle(draw_obj, xy, radius, fill, outline=None, width=1):
        x1, y1, x2, y2 = xy
        draw_obj.pieslice([x1, y1, x1 + 2*radius, y1 + 2*radius], 180, 270, fill=fill, outline=outline)
        draw_obj.pieslice([x2 - 2*radius, y1, x2, y1 + 2*radius], 270, 360, fill=fill, outline=outline)
        draw_obj.pieslice([x1, y2 - 2*radius, x1 + 2*radius, y2], 90, 180, fill=fill, outline=outline)
        draw_obj.pieslice([x2 - 2*radius, y2 - 2*radius, x2, y2], 0, 90, fill=fill, outline=outline)
        draw_obj.rectangle([x1+radius, y1, x2-radius, y2], fill=fill, outline=outline)
        draw_obj.rectangle([x1, y1+radius, x2, y2-radius], fill=fill, outline=outline)

    for idx, song in enumerate(songs_to_show):
        # Tọa độ của mỗi item
        x1 = 10
        y1 = 10 + idx * item_height
        x2 = total_width - 10
        y2 = y1 + (item_height - 10)

        # Vẽ background của item với bo góc
        corner_radius = 10
        draw_rounded_rectangle(draw, (x1, y1, x2, y2), corner_radius, fill=item_bg_color)

        # Vẽ vòng tròn xanh chứa số thứ tự (vị trí bên trái)
        circle_radius = 22
        circle_center_x = x1 + circle_radius + 10
        circle_center_y = y1 + (item_height // 2)
        draw.ellipse(
            [
                circle_center_x - circle_radius,
                circle_center_y - circle_radius,
                circle_center_x + circle_radius,
                circle_center_y + circle_radius
            ],
            fill=circle_color
        )
        num_text = str(idx + 1)
        w_num, h_num = measure_text_size(font_stats, num_text)
        num_x = circle_center_x - w_num // 2
        num_y = circle_center_y - h_num // 2
        draw.text((num_x, num_y), num_text, fill=(255, 255, 255), font=font_stats)

        # Vị trí cho ảnh bìa (nếu có)
        cover_offset_x = circle_center_x + circle_radius + 10
        cover_offset_y = y1 + (item_height - 80) // 2  # căn giữa ảnh bìa theo chiều cao
        cover_img = None
        if song[2]:
            cover_img = get_rounded_cover(song[2], size=(80,80))
        if cover_img:
            final_img.paste(cover_img, (cover_offset_x, cover_offset_y), cover_img)

        # Thông tin bài hát
        title = song[1] or "Không rõ"
        artist = song[3] or "Không rõ"
        duration = song[4] or "N/A"
        play_count = song[7] or "N/A"

        # Tọa độ text: đặt bên phải của ảnh bìa (nếu có), nếu không thì bên cạnh vòng tròn
        text_x = cover_offset_x + (80 + 10) if cover_img else (circle_center_x + circle_radius + 10)
        text_y = y1 + 8

        # Dòng 1: Title (cắt bớt nếu quá dài)
        max_len_title = 55
        if len(title) > max_len_title:
            title = title[:max_len_title] + "..."
        draw.text((text_x, text_y), title, fill=color_title, font=font_title)

        # Dòng 2: (@artist)
        text_y += 30
        artist_str = f"(@{artist})"
        draw.text((text_x, text_y), artist_str, fill=color_artist, font=font_artist)

        # Dòng 3: Thống kê: duration và play_count
        text_y += 28
        stats_str = f"{duration}   {play_count}"
        draw.text((text_x, text_y), stats_str, fill=color_stats, font=font_stats)

    output_path = "song_list.jpg"
    try:
        final_img.save(output_path, "JPEG")
        print("[DEBUG] Đã lưu ảnh danh sách bài hát vào:", output_path)
    except Exception as e_save:
        print("[ERROR] Lỗi khi lưu ảnh:", e_save)

    return output_path

# ---------------------------
# Handler cho lệnh "scl" - Tìm kiếm bài hát và tạo ảnh danh sách
# ---------------------------
def handle_scl_command(message, message_object, thread_id, thread_type, author_id, client):
    content = message.strip().split()
    client.sendReaction(message_object, "✅", thread_id, thread_type, reactionType=75)
    if len(content) < 2:
        error_message = Message(text="🚫 Lỗi: Thiếu tên bài hát\n\nCú pháp: scl <tên bài hát>")
        client.replyMessage(error_message, message_object, thread_id, thread_type, ttl=60000)
        return
    query = ' '.join(content[1:])    
    
    song_list = search_song_list(query)
    if not song_list:
        error_message = Message(text="❌ Không tìm thấy bài hát nào phù hợp.")
        client.replyMessage(error_message, message_object, thread_id, thread_type)
        return

    # Lưu danh sách bài hát vào biến toàn cục để dùng cho lệnh "chon"
    song_search_results[thread_id] = song_list

    # Tạo ảnh danh sách bài hát thay vì gửi tin nhắn văn bản
    list_image_path = create_song_list_image(song_list, max_show=10)
    guide_msg = "Danh sách bài hát tìm được. Chọn bài bằng cách soạn:\n   s <số từ 1-10>\n   s 0 để hủy tìm kiếm."

    # Cập nhật trạng thái tìm kiếm
    search_status[thread_id] = (time.time(), False, list_image_path, thread_type)

    try:
        list_image_height = 100 * len(song_list) + 20
        response = client.sendLocalImage(
            list_image_path,
            message=Message(text=guide_msg),
            thread_id=thread_id,
            thread_type=thread_type,
            width=700,
            height=list_image_height,
            ttl=60000
        )
        msg_id = response.get('msgId')  # Lưu msgId từ phản hồi
        search_status[thread_id] = (*search_status[thread_id][:2], msg_id, thread_type)
        msg_id = response.get('msgId')  # Lưu msgId từ phản hồi
        search_status[thread_id] = (*search_status[thread_id][:2], msg_id, thread_type)
        print("[DEBUG] Đã lưu msgId của tin nhắn danh sách bài hát.")
    except Exception as e_img:
        print("[ERROR] Lỗi khi gửi ảnh danh sách:", e_img)

    # Sau 60 giây, xóa ảnh danh sách bài hát và không cho phép chọn nữa
    time.sleep(60)
    if thread_id in search_status:
        if not search_status[thread_id][1]:  # Nếu chưa chọn bài
            try:
                client.deleteGroupMsg(message_object['msgId'], author_id, message_object['cliMsgId'], thread_id)
                print("[DEBUG] Đã xóa ảnh danh sách bài hát sau 60 giây hết hạn.")
            except Exception as e:
                print("[ERROR] Lỗi khi xóa ảnh danh sách:", e)
            del search_status[thread_id]

# ---------------------------
# Handler cho lệnh "chon" - Chọn bài hát để tải về, xử lý cover, upload và gửi kết quả
# ---------------------------
# Kiểm tra người dùng có phải là người đã tìm kiếm không
def handle_chon_command(message, message_object, thread_id, thread_type, author_id, client):
    content = message.strip().split()

    # Kiểm tra nếu người dùng không phải người đã tìm kiếm
    if thread_id not in search_status or search_status[thread_id][1]:
        error_message = Message(text="🚫 Bạn không thể chọn vì danh sách đã hết hạn hoặc không phải người tìm kiếm.")
        client.replyMessage(error_message, message_object, thread_id, thread_type, ttl=60000)
        return
    
    # Nếu người dùng chọn "chon 0" thì xóa danh sách và thực hiện tìm kiếm mới
    if content[1] == '0':  # Người dùng chọn hủy danh sách
        try:
            client.deleteGroupMsg(search_status[thread_id][2], author_id, message_object['cliMsgId'], thread_id)
            print("[DEBUG] Đã xóa ảnh danh sách bài hát sau khi người dùng hủy.")
        except Exception as e:
            print("[ERROR] Lỗi khi xóa ảnh danh sách:", e)
        del search_status[thread_id]  # Hủy danh sách
        success_message = Message(text="🔄 Lệnh tìm kiếm đã được hủy. Bạn có thể thực hiện tìm kiếm mới.")
        client.replyMessage(success_message, message_object, thread_id, thread_type, ttl=60000)
        return



    try:
        index = int(content[1]) - 1
    except ValueError:
        error_message = Message(text="🚫 Lỗi: Số bài hát không hợp lệ.\nCú pháp: s <số từ 1-10>")
        client.replyMessage(error_message, message_object, thread_id, thread_type, ttl=60000)
        return

    song_list = song_search_results.get(thread_id)
    if index < 0 or index >= len(song_list):
        error_message = Message(text="🚫 Số bài hát không hợp lệ. Vui lòng chọn lại.")
        client.replyMessage(error_message, message_object, thread_id, thread_type, ttl=60000)
        return

    selected_song = song_list[index]
    url, title, cover, artist, duration, genre, release_date, play_count = selected_song

    # Đánh dấu là người dùng đã chọn bài
    search_status[thread_id] = (search_status[thread_id][0], True, search_status[thread_id][2], thread_type)

    # Xóa ảnh danh sách bài hát
    try:
        # Sử dụng msgId đã lưu để xóa ảnh danh sách
        client.deleteGroupMsg(search_status[thread_id][2], author_id, message_object['cliMsgId'], thread_id)
        print("[DEBUG] Đã xóa ảnh danh sách bài hát sau khi người dùng chọn.")
    except Exception as e:
        print("[ERROR] Lỗi khi xóa ảnh danh sách:", e)

    download_message = Message(text="🔽 Đang tải bài hát về...")
    client.replyMessage(download_message, message_object, thread_id, thread_type, ttl=20000)
    mp3_file = download(url)
    if not mp3_file:
        error_message = Message(text="🚫 Lỗi: Không thể tải file âm thanh.")
        client.replyMessage(error_message, message_object, thread_id, thread_type, ttl=60000)
        return

    upload_response = upload_to_uguu(mp3_file)
    if not upload_response:
        error_message = Message(text="🚫 Lỗi: Không thể tải lên Uguu.se.")
        client.replyMessage(error_message, message_object, thread_id, thread_type, ttl=60000)
        return

    info_text = (
        f"🎵 Bài Hát   : {title}\n"
        f"🎤 Nghệ sĩ   : {artist}\n"
        f"⏳ Độ dài    : {duration}\n"
        f"🎶 Thể loại  : {genre}\n"
        f"📅 Ngày     : {release_date}\n"
        f"🎧 Lượt     : {play_count}"
    )
    messagesend = Message(text=info_text)

    # Gửi thông tin bài hát và ảnh bìa nếu có
    if cover:
        try:
            cover_response = requests.get(cover, headers=get_headers())
            cover_filename = cover.rsplit("/", 1)[-1]
            with open(cover_filename, "wb") as file:
                file.write(cover_response.content)
            cover_image = Image.open(cover_filename).convert("RGB")
        except Exception as e:
            print(f"Lỗi khi xử lý ảnh bìa: {e}")
            cover_image = None

        if cover_image:
            cover_size = (200, 200)
            cover_image = cover_image.resize(cover_size)
            mask = Image.new("L", cover_size, 0)
            draw_mask = ImageDraw.Draw(mask)
            draw_mask.ellipse((0, 0, cover_size[0], cover_size[1]), fill=255)
            cover_image.putalpha(mask)
            gradient_colors = [(255, 0, 0), (255, 165, 0), (255, 255, 0),
                               (0, 255, 0), (0, 0, 255), (75, 0, 130), (148, 0, 211)]
            cover_border_thickness = 5
            cover_image = add_circular_multicolor_border(cover_image, gradient_colors, cover_border_thickness)
            final_cover_size = (cover_size[0] + 2 * cover_border_thickness, cover_size[1] + 2 * cover_border_thickness)
            text_area_width = 300
            cover_margin_left = 20
            cover_margin_top = 20
            cover_width = final_cover_size[0]
            spacing_between = 20
            combined_width = cover_margin_left + cover_width + spacing_between + text_area_width
            combined_image = Image.new("RGB", (combined_width, 240), color="black")
            combined_image.paste(cover_image, (cover_margin_left, cover_margin_top), cover_image)
            draw = ImageDraw.Draw(combined_image)
            try:
                font_title = ImageFont.truetype(os.path.abspath("modules/Font/NotoSans-Bold.ttf"), 25)
                font_normal = ImageFont.truetype(os.path.abspath("modules/Font/NotoSans-Bold.ttf"), 20)
            except Exception as e:
                font_title = ImageFont.load_default()
                font_normal = ImageFont.load_default()
            text_x = cover_margin_left + cover_width + spacing_between
            text_y = 10
            max_line_width = text_area_width - 20
            for idx, raw_line in enumerate(info_text.split("\n")):
                if raw_line.strip() == "":
                    text_y += 10
                    continue
                current_font = font_title if idx == 0 else font_normal
                wrapped_lines = wrap_text(raw_line, current_font, max_line_width, draw)
                for line in wrapped_lines:
                    draw_gradient_text(draw, line, (text_x, text_y), current_font, gradient_colors)
                    bbox = draw.textbbox((text_x, text_y), line, font=current_font)
                    line_height = bbox[3] - bbox[1]
                    text_y += line_height + 4
            border_thickness = 10
            combined_image = combined_image.convert("RGBA")
            combined_image = add_multicolor_rectangle_border(combined_image, gradient_colors, border_thickness)
            combined_image = combined_image.convert("RGB")
            combined_filename = "combined_cover.jpg"
            combined_image.save(combined_filename)
            client.sendLocalImage(combined_filename, thread_id, thread_type, width=combined_width, height=240, ttl=120000000)
            delete_file(combined_filename)
            delete_file(cover_filename)
        else:
            client.replyMessage(messagesend, message_object, thread_id, thread_type)
    else:
        client.replyMessage(messagesend, message_object, thread_id, thread_type)

    client.sendRemoteVoice(voiceUrl=upload_response, thread_id=thread_id, thread_type=thread_type, ttl=120000000)
    delete_file(mp3_file)

# ---------------------------
# Trả về dict mapping các lệnh tới hàm xử lý
# ---------------------------
def get_mitaizl():
    return {
        'scl': handle_scl_command,
        's': handle_chon_command
    }
