import os
import random
import requests
import urllib.parse
from datetime import datetime
from unidecode import unidecode
from zlapi.models import Message, MultiMsgStyle, MessageStyle
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from io import BytesIO

# Global lưu trữ kết quả tìm kiếm video
video_search_results = {}
searchtt_status = {}

###########################
# TẠO ICON (nếu chưa có)
###########################
def create_icons():
    """
    Tạo folder 'icons' (nếu chưa có) và tạo các file icon views.png, like.png, comment.png.
    Mỗi icon là ảnh PNG kích thước 32x32 với background hình tròn và ký hiệu emoji ở giữa.
    """
    ICON_SIZE = 32
    icons_path = "icons"
    if not os.path.exists(icons_path):
        os.makedirs(icons_path)

    def create_icon(filename, text, bg_color, text_color):
        img = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        # Vẽ hình tròn nền
        draw.ellipse((0, 0, ICON_SIZE - 1, ICON_SIZE - 1), fill=bg_color)
        try:
            # Sử dụng font Arial (nếu có)
            font = ImageFont.truetype("arial.ttf", 20)
        except Exception as e:
            print("[WARNING] Không load được font Arial:", e)
            font = ImageFont.load_default()
        # Thay vì dùng draw.textsize, sử dụng textbbox để đo kích thước văn bản
        bbox = draw.textbbox((0, 0), text, font=font)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text(((ICON_SIZE - w) / 2, (ICON_SIZE - h) / 2), text, font=font, fill=text_color)
        img.save(os.path.join(icons_path, filename))

    create_icon("views.png", "👁", (100, 100, 100), (255, 255, 255))
    create_icon("like.png", "👍", (220, 20, 60), (255, 255, 255))
    create_icon("comment.png", "💬", (70, 130, 180), (255, 255, 255))
    print("[DEBUG] Tạo file icon thành công!")

# Tạo icon nếu chưa có file nào
create_icons()

#############################
# HÀM XỬ LÝ ẢNH VÀ GIAO DIỆN
#############################
def measure_text_size(font, text):
    """Đo kích thước (width, height) của text."""
    try:
        # Sử dụng font.getmask để lấy kích thước
        mask = font.getmask(text)
        return mask.size
    except Exception as e:
        print("[ERROR] measure_text_size:", e)
        return (0, 0)

def draw_rounded_rectangle(draw, xy, radius, fill, outline=None, width=1):
    """Vẽ hình chữ nhật với góc bo tròn."""
    try:
        x1, y1, x2, y2 = xy
        # Vẽ 4 góc bo tròn
        draw.pieslice([x1, y1, x1 + 2 * radius, y1 + 2 * radius], 180, 270, fill=fill, outline=outline)
        draw.pieslice([x2 - 2 * radius, y1, x2, y1 + 2 * radius], 270, 360, fill=fill, outline=outline)
        draw.pieslice([x1, y2 - 2 * radius, x1 + 2 * radius, y2], 90, 180, fill=fill, outline=outline)
        draw.pieslice([x2 - 2 * radius, y2 - 2 * radius, x2, y2], 0, 90, fill=fill, outline=outline)
        # Vẽ các cạnh
        draw.rectangle([x1 + radius, y1, x2 - radius, y2], fill=fill, outline=outline)
        draw.rectangle([x1, y1 + radius, x2, y2 - radius], fill=fill, outline=outline)
    except Exception as e:
        print("[ERROR] draw_rounded_rectangle:", e)

def add_solid_border(thumb, border_thickness=3, border_color=(255, 255, 255, 255)):
    """
    Tạo viền màu xung quanh ảnh tròn `thumb`.
    """
    try:
        original_size = thumb.size[0]  # giả sử ảnh vuông
        new_size = original_size + 2 * border_thickness

        border_img = Image.new("RGBA", (new_size, new_size), (0, 0, 0, 0))
        draw_border = ImageDraw.Draw(border_img, "RGBA")
        draw_border.ellipse((0, 0, new_size - 1, new_size - 1), fill=border_color)
        border_img.paste(thumb, (border_thickness, border_thickness), mask=thumb)
        return border_img
    except Exception as e:
        print("[ERROR] add_solid_border:", e)
        return thumb

def create_rounded_thumbnail(image, size=80):
    """
    Tạo ảnh thumbnail tròn với viền và hiệu ứng bóng.
    """
    try:
        thumb = image.resize((size, size), Image.Resampling.LANCZOS).convert("RGBA")
        # Tạo mask bo tròn
        mask = Image.new("L", (size, size), 0)
        draw_mask = ImageDraw.Draw(mask)
        draw_mask.ellipse((0, 0, size, size), fill=255)
        thumb.putalpha(mask)
        thumb = add_solid_border(thumb, border_thickness=5, border_color=(255, 255, 255, 255))
        # Tạo hiệu ứng bóng cho thumbnail
        shadow = thumb.filter(ImageFilter.GaussianBlur(3))
        shadow_offset = 4
        bg = Image.new("RGBA", (thumb.size[0] + shadow_offset, thumb.size[1] + shadow_offset), (0, 0, 0, 0))
        bg.paste(shadow, (shadow_offset, shadow_offset))
        bg.paste(thumb, (0, 0), mask=thumb)
        return bg
    except Exception as e:
        print("[ERROR] create_rounded_thumbnail:", e)
        return image

def create_gradient_background(width, height, top_color, bottom_color):
    """
    Tạo nền gradient từ top_color xuống bottom_color.
    """
    base = Image.new('RGB', (width, height), top_color)
    top = Image.new('RGB', (width, height), bottom_color)
    mask = Image.new('L', (width, height))
    mask_data = []
    for y in range(height):
        mask_data.extend([int(255 * (y / height))] * width)
    mask.putdata(mask_data)
    return Image.composite(top, base, mask)

def create_list_image(videos, max_show=10):
    """
    Tạo ảnh danh sách video với các cải tiến về khoảng cách, padding, màu sắc, font và hiệu ứng bóng.
    Trả về tuple (đường dẫn file ảnh, chiều cao ảnh).
    """
    print("[DEBUG] Current working directory:", os.getcwd())
    videos_to_show = videos[:max_show]
    item_count = len(videos_to_show)

    # Tăng chiều rộng của ảnh danh sách
    total_width = 1000  # giá trị mới, tăng từ 700px lên 1000px
    item_height = 160      # chiều cao mỗi item
    item_margin = 20       # khoảng cách giữa các item
    total_height = (item_height + item_margin) * item_count + item_margin

    # Tạo nền gradient
    final_img = create_gradient_background(total_width, total_height, (30, 30, 30), (50, 50, 50))
    draw = ImageDraw.Draw(final_img)

    # Load font và cài đặt màu sắc
    try:
        print("[DEBUG] Đang load font...")
        font_title = ImageFont.truetype("font/FrancoisOne-Regular.ttf", 24)
        font_stats = ImageFont.truetype("font/Kanit-Medium.ttf", 18)
        font_nickname = ImageFont.truetype("font/Kanit-Medium.ttf", 16)
        print("[DEBUG] Load font thành công!")
    except Exception as e:
        print("[ERROR] Lỗi khi load font:", e)
        font_title = ImageFont.load_default()
        font_stats = ImageFont.load_default()
        font_nickname = ImageFont.load_default()

    # Định nghĩa bảng màu
    CARD_COLOR = (40, 40, 40)
    SHADOW_COLOR = (0, 0, 0, 100)
    TITLE_COLOR = (255, 255, 255)
    NICK_COLOR = (180, 180, 180)
    STATS_COLOR = (220, 220, 220)

    # Đường dẫn icon
    ICON_SIZE = 20
    try:
        icon_views = Image.open("icons/views.png").resize((ICON_SIZE, ICON_SIZE), Image.Resampling.LANCZOS)
        icon_like = Image.open("icons/like.png").resize((ICON_SIZE, ICON_SIZE), Image.Resampling.LANCZOS)
        icon_comment = Image.open("icons/comment.png").resize((ICON_SIZE, ICON_SIZE), Image.Resampling.LANCZOS)
    except Exception as e:
        print("[ERROR] Lỗi khi load icon:", e)
        icon_views = icon_like = icon_comment = None

    for idx, video in enumerate(videos_to_show):
        try:
            # Tính toán vị trí item
            x1 = 10
            y1 = item_margin + idx * (item_height + item_margin)
            x2 = total_width - 10
            y2 = y1 + item_height

            # Vẽ bóng cho card (shadow)
            shadow_offset = 4
            draw_rounded_rectangle(
                draw,
                (x1 + shadow_offset, y1 + shadow_offset, x2 + shadow_offset, y2 + shadow_offset),
                radius=15,
                fill=SHADOW_COLOR
            )
            # Vẽ card nền
            draw_rounded_rectangle(draw, (x1, y1, x2, y2), radius=15, fill=CARD_COLOR)

            # Vẽ số thứ tự trong một vòng tròn
            circle_radius = 20
            circle_center_x = x1 + circle_radius + 15
            circle_center_y = y1 + item_height // 2
            circle_color = (57, 181, 74)
            circle_x1 = circle_center_x - circle_radius
            circle_y1 = circle_center_y - circle_radius
            circle_x2 = circle_center_x + circle_radius
            circle_y2 = circle_center_y + circle_radius
            draw.ellipse([circle_x1, circle_y1, circle_x2, circle_y2], fill=circle_color)
            num_text = str(idx + 1)
            w_num, h_num = measure_text_size(font_stats, num_text)
            draw.text((circle_center_x - w_num // 2, circle_center_y - h_num // 2),
                      num_text, fill=(255, 255, 255), font=font_stats)

            # Tải và vẽ ảnh thumbnail
            cover_url = video.get('cover', None)
            if cover_url:
                try:
                    resp = requests.get(cover_url, timeout=5)
                    resp.raise_for_status()
                    thumb_raw = Image.open(BytesIO(resp.content))
                    round_thumb = create_rounded_thumbnail(thumb_raw, size=80)
                    w_thumb, h_thumb = round_thumb.size
                    thumb_x = circle_x2 + 20  # tăng khoảng cách giữa số và thumbnail
                    thumb_y = y1 + (item_height - h_thumb) // 2
                    final_img.paste(round_thumb, (thumb_x, thumb_y), mask=round_thumb)
                except Exception as e_img:
                    print("[ERROR] Lỗi khi tải/dán cover_url:", cover_url, "- Error:", e_img)

            # Lấy thông tin text
            title = video.get('title', 'No Title')
            author_nickname = video.get('author', {}).get('nickname', '')
            play_count = video.get('play_count', 0)
            digg_count = video.get('digg_count', 0)
            comment_count = video.get('comment_count', 0)

            # Giới hạn độ dài tiêu đề
            max_len = 60
            if len(title) > max_len:
                title = title[:max_len] + "..."

            # Tọa độ text (bắt đầu sau thumbnail)
            # Với chiều rộng tăng, ta có thể đẩy text sang phải hơn
            text_start_x = circle_x2 + 140
            text_title_y = y1 + 15  # padding top
            draw.text((text_start_x, text_title_y), title, fill=TITLE_COLOR, font=font_title)

            text_nick_y = text_title_y + 30
            draw.text((text_start_x, text_nick_y), f"({author_nickname})", fill=NICK_COLOR, font=font_nickname)

            # Thống kê với icon
            stats_y = text_nick_y + 35
            stats_x = text_start_x
            icon_gap = 5
            current_x = stats_x

            if icon_views:
                final_img.paste(icon_views, (current_x, stats_y), mask=icon_views)
                current_x += ICON_SIZE + icon_gap
            views_text = f"{play_count:,}"
            draw.text((current_x, stats_y), views_text, fill=STATS_COLOR, font=font_stats)
            current_x += measure_text_size(font_stats, views_text)[0] + 20

            if icon_like:
                final_img.paste(icon_like, (current_x, stats_y), mask=icon_like)
                current_x += ICON_SIZE + icon_gap
            like_text = f"{digg_count:,}"
            draw.text((current_x, stats_y), like_text, fill=STATS_COLOR, font=font_stats)
            current_x += measure_text_size(font_stats, like_text)[0] + 20

            if icon_comment:
                final_img.paste(icon_comment, (current_x, stats_y), mask=icon_comment)
                current_x += ICON_SIZE + icon_gap
            comment_text = f"{comment_count:,}"
            draw.text((current_x, stats_y), comment_text, fill=STATS_COLOR, font=font_stats)

        except Exception as e_item:
            print(f"[ERROR] Lỗi khi vẽ item thứ {idx+1}:", e_item)

    output_path = "video_list.jpg"
    try:
        final_img.save(output_path, "JPEG")
        print("[DEBUG] Đã lưu ảnh danh sách video vào:", output_path)
    except Exception as e_save:
        print("[ERROR] Lỗi khi lưu ảnh:", e_save)

    return output_path, total_height

####################################
# HÀM XỬ LÝ LỆNH TIKTOK & CHỌN VIDEO
####################################
def handle_tiktok_command(message, message_object, thread_id, thread_type, author_id, client):
    """
    Lệnh: tt <từ khoá>
    1) Gọi API => lấy danh sách video
    2) Tạo ảnh danh sách => gửi ảnh
    3) Lưu list videos vào video_search_results[thread_id] để user chọn sau
    """
    action = "✅"
    try:
        client.sendReaction(message_object, action, thread_id, thread_type, reactionType=75)
    except Exception as e:
        print("[ERROR] Gửi reaction:", e)

    content = message.strip().split()
    if len(content) < 2:
        menu_message = "Hãy nhập 1 từ khoá để tìm kiếm video từ TikTok\nCú pháp: tt <từ khoá>"
        style = MultiMsgStyle([
            MessageStyle(offset=0, length=len(menu_message), style="color", color="#15a85f", auto_format=False),
            MessageStyle(offset=0, length=len(menu_message), style="font", size="16", auto_format=False),
        ])
        error_message = Message(text=menu_message, style=style)
        client.replyMessage(error_message, message_object, thread_id, thread_type, ttl=60000)
        return

    keyword = " ".join(content[1:]).strip()
    keyword = unidecode(keyword)

    try:
        encoded_keyword = urllib.parse.quote(keyword)
        search_url = f'https://api.sumiproject.net/tiktok?search={encoded_keyword}'
        print("[DEBUG] Gọi API TikTok với URL:", search_url)
        search_response = requests.get(search_url)
        search_response.raise_for_status()
        search_data = search_response.json()

        if search_data['code'] != 0 or not search_data.get('data') or not search_data['data'].get('videos'):
            error_message = Message(text="Không tìm thấy video TikTok phù hợp.")
            client.replyMessage(error_message, message_object, thread_id, thread_type, ttl=60000)
            return

        videos = search_data['data']['videos']
        if len(videos) == 0:
            error_message = Message(text="Không tìm thấy video TikTok nào với từ khoá này.")
            client.replyMessage(error_message, message_object, thread_id, thread_type, ttl=60000)
            return

        video_search_results[thread_id] = videos
        searchtt_status[thread_id] = {
            'has_searched': True,
            'msg_id': None,
            'search_time': datetime.now(),
            'user_id': author_id,
            'thread_type': thread_type,
            'has_selected': False
        }

        list_image_path, list_image_height = create_list_image(videos, max_show=10)
        guide_msg = (
            "Đây là danh sách video tìm được (có hiệu lực 60 giây).\n"
            "Hãy dùng lệnh: t <số> để chọn video. VD: t 1\n"
            "Nhập 't 0' để hủy tìm kiếm."
        )

        try:
            response = client.sendLocalImage(
                list_image_path,
                message=Message(text=guide_msg),
                thread_id=thread_id,
                thread_type=thread_type,
                width=1500,
                height=list_image_height,
                ttl=60000
            )
            msg_id = response.get('msgId')
            searchtt_status[thread_id]['msg_id'] = msg_id
            print("[DEBUG] Đã gửi ảnh danh sách video.")
        except Exception as e_img:
            print("[ERROR] Gửi ảnh danh sách:", e_img)

        if os.path.exists(list_image_path):
            try:
                os.remove(list_image_path)
                print("[DEBUG] Đã xoá file tạm:", list_image_path)
            except Exception as e_rm:
                print("[ERROR] Xoá file tạm:", e_rm)

    except requests.RequestException as e:
        print("[ERROR] API TikTok:", e)
        error_message = Message(text=f"Lỗi khi gọi API TikTok: {str(e)}")
        client.replyMessage(error_message, message_object, thread_id, thread_type, ttl=60000)

def handle_chon_command(message, message_object, thread_id, thread_type, author_id, client):
    """
    Lệnh: t <số>
    - Số 0 để hủy tìm kiếm.
    - Số 1-10 để chọn video tương ứng (chỉ cho phép chọn 1 lần).
    Sau khi chọn hoặc hủy, tin nhắn danh sách sẽ bị xoá.
    """
    content = message.strip().split()
    if len(content) < 2:
        client.replyMessage(Message(text="Vui lòng nhập số thứ tự (0 để hủy)\nVí dụ: t 1 hoặc t 0"),
                            message_object, thread_id, thread_type, ttl=30000)
        return

    try:
        index = int(content[1]) - 1  # chuyển về 0-based
    except ValueError:
        client.replyMessage(Message(text="Số thứ tự không hợp lệ! Vui lòng nhập số từ 0 đến 10"),
                            message_object, thread_id, thread_type, ttl=30000)
        return

    if thread_id not in video_search_results or thread_id not in searchtt_status:
        client.replyMessage(Message(text="Danh sách video đã hết hạn! Vui lòng tìm kiếm lại bằng lệnh: tt <từ khoá>"),
                            message_object, thread_id, thread_type, ttl=10000)
        return

    search_info = searchtt_status[thread_id]
    if (datetime.now() - search_info['search_time']).total_seconds() > 60:
        client.replyMessage(Message(text="Danh sách video đã hết hạn! Vui lòng tìm kiếm lại bằng lệnh: tt <từ khoá>"),
                            message_object, thread_id, thread_type, ttl=10000)
        if search_info.get('msg_id'):
            try:
                client.deleteGroupMsg(search_info['msg_id'], author_id, message_object['cliMsgId'], thread_id)
                print(f"[DEBUG] Đã xóa tin nhắn danh sách {search_info['msg_id']} (hết hạn)")
            except Exception as e_del:
                print(f"[ERROR] Xoá tin nhắn hết hạn:", e_del)
        del video_search_results[thread_id]
        del searchtt_status[thread_id]
        return

    if author_id != search_info['user_id']:
        client.replyMessage(Message(text="Chỉ người thực hiện tìm kiếm mới được chọn video."),
                            message_object, thread_id, thread_type, ttl=30000)
        return

    if index == -1:
        try:
            if search_info.get('msg_id'):
                client.deleteGroupMsg(search_info['msg_id'], author_id, message_object['cliMsgId'], thread_id)
                print(f"[DEBUG] Đã xóa tin nhắn danh sách {search_info['msg_id']} (hủy tìm kiếm)")
        except Exception as e:
            print(f"[ERROR] Xoá tin nhắn hủy:", e)
        del video_search_results[thread_id]
        del searchtt_status[thread_id]
        client.replyMessage(Message(text="✅ Đã hủy tìm kiếm thành công!"),
                            message_object, thread_id, thread_type, ttl=30000)
        return

    if search_info.get('has_selected'):
        client.replyMessage(Message(text="Bạn đã chọn video rồi! Vui lòng tìm kiếm lại nếu muốn chọn video khác."),
                            message_object, thread_id, thread_type, ttl=30000)
        return

    videos = video_search_results[thread_id]
    if index < 0 or index >= len(videos):
        client.replyMessage(Message(text=f"Số thứ tự phải từ 1 đến {len(videos)}"),
                            message_object, thread_id, thread_type, ttl=30000)
        return

    try:
        selected_video = videos[index]
        title = selected_video.get('title', 'No Title')
        cover_url = selected_video.get('cover')
        ai_dynamic_cover = selected_video.get('ai_dynamic_cover')
        origin_cover = selected_video.get('origin_cover')
        duration = selected_video.get('duration')
        play_url = selected_video.get('play')
        wmplay_url = selected_video.get('wmplay', None)
        music_url = selected_video.get('music')
        music_info = selected_video.get('music_info', {})
        music_title = music_info.get('title', '')
        music_author = music_info.get('author', '')
        author_nickname = selected_video.get('author', {}).get('nickname', '')
        play_count = selected_video.get('play_count', 0)
        digg_count = selected_video.get('digg_count', 0)
        comment_count = selected_video.get('comment_count', 0)
        share_count = selected_video.get('share_count', 0)
        download_count = selected_video.get('download_count', 0)
        size_kb = selected_video.get('size', 0)
        size_mb = size_kb / 1024

        user_info = client.fetchUserInfo(author_id)
        user_name = user_info.changed_profiles[author_id].zaloName

        video_info = (
            f"👤 {user_name} đã chọn video thứ {index+1}:\n"
            f"------------------------------\n"
            f"📜 Tiêu đề     : {title}\n"
            f"------------------------------\n"
            f"✍️ Tác giả     : @{author_nickname}\n"
            f"------------------------------\n"
            f"🌍 Khu vực     : {selected_video.get('region', 'N/A')}\n"
            f"📊 Kích cỡ     : {size_mb:.2f} MB\n"
            f"⏱️ Thời lượng  : {duration} giây\n"
            f"🎶 Nhạc        : {music_title} - {music_author}\n"
            f"👁️ Lượt xem    : {play_count:,}\n"
            f"👍 Thích       : {digg_count:,}\n"
            f"💬 Bình luận   : {comment_count:,}\n"
            f"🔄 Chia sẻ     : {share_count:,}\n"
            f"⬇️ Tải xuống   : {download_count:,}\n"
            f"------------------------------\n"
            f"📢 Quảng cáo   : {'Yes' if selected_video.get('is_ad') else 'No'}\n"
            f"🔗 Link tải nhạc nền: {music_url}\n"            
            f"------------------------------"
        )

        messagesend = Message(text=video_info)
        thumbnail_url = cover_url or origin_cover or ai_dynamic_cover or 'https://i.imgur.com/PfiuQSv.jpeg'

        try:
            client.sendRemoteVideo(
                play_url,
                thumbnail_url,
                duration=str(duration),
                message=messagesend,
                thread_id=thread_id,
                thread_type=thread_type,
                ttl=180000,
                width=1200,
                height=1600
            )
            print("[DEBUG] Đã gửi video thứ", index+1, "cho user.")
        except Exception as e_video:
            print("[ERROR] Gửi video:", e_video)
            error_message = Message(text=f"Lỗi khi gửi video: {str(e_video)}")
            client.replyMessage(error_message, message_object, thread_id, thread_type, ttl=60000)
            return

        searchtt_status[thread_id]['has_selected'] = True

    except Exception as e_sel:
        print("[ERROR] Xử lý chọn video:", e_sel)
        error_message = Message(text=f"Lỗi khi gửi video: {str(e_sel)}")
        client.replyMessage(error_message, message_object, thread_id, thread_type, ttl=60000)
    finally:
        if searchtt_status.get(thread_id) and searchtt_status[thread_id].get('msg_id'):
            try:
                client.deleteGroupMsg(searchtt_status[thread_id]['msg_id'], author_id, message_object['cliMsgId'], thread_id)
                print(f"[DEBUG] Đã xóa tin nhắn danh sách {searchtt_status[thread_id]['msg_id']}")
            except Exception as e_del:
                print(f"[ERROR] Xoá tin nhắn danh sách:", e_del)
        if thread_id in video_search_results:
            del video_search_results[thread_id]
        if thread_id in searchtt_status:
            del searchtt_status[thread_id]

def get_mitaizl():
    """
    Trả về dict { 'lệnh': hàm_xử_lý }
    """
    return {
        'tt': handle_tiktok_command,
        't': handle_chon_command
    }
