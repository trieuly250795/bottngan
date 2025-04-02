from zlapi.models import Message
import time
import random
import os
import json
import requests
from PIL import Image, ImageDraw, ImageFont

start_time = time.time()
des = {
    'version': "1.0.2",
    'credits': "Nguyễn Đức Tài",
    'description': "𝕏𝕖𝕟 𝕥𝕙𝕠̛̀𝕚 𝕘𝕚𝕒𝕟 𝕓𝕠𝕥 𝕙𝕠𝕒̣𝕥 𝕕𝕠𝕟𝕘"
}

def random_color():
    return (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

def add_text_to_image(uptime_text, additional_text):
    img = Image.open('nen.jpg')  # Đường dẫn đến ảnh nền
    draw = ImageDraw.Draw(img)
    
    font_path = "UTM AvoBold_Italic.ttf"  # Đường dẫn đến font chữ
    font_size = 60
    try:
        font = ImageFont.truetype(font_path, font_size)
    except IOError:
        font = ImageFont.load_default()
    
    # Chọn màu ngẫu nhiên cho chữ
    fill_color = random_color()
    
    # Vẽ thông điệp bổ sung ở trên cùng
    additional_bbox = draw.textbbox((0, 0), additional_text, font=font)
    additional_width = additional_bbox[2] - additional_bbox[0]  
    additional_height = additional_bbox[3] - additional_bbox[1]  

    additional_x = (img.width - additional_width) / 2  
    additional_y = 20  # Vị trí cách cạnh trên một khoảng nhỏ

    draw.text((additional_x, additional_y), additional_text, fill=fill_color, font=font)

    # Vẽ thông điệp uptime ở giữa
    bbox = draw.textbbox((0, 0), uptime_text, font=font)
    text_width = bbox[2] - bbox[0]  
    text_height = bbox[3] - bbox[1]  

    # Tính toán vị trí để canh giữa nội dung uptime
    text_x = (img.width - text_width) / 2  
    text_y = (img.height - text_height) / 2  # Canh giữa theo chiều dọc

    draw.text((text_x, text_y), uptime_text, fill=fill_color, font=font)
    
    output_path = 'output.png'
    img.save(output_path)
    
    return output_path

def handle_uptime_command(message, message_object, thread_id, thread_type, author_id, client):
    current_time = time.time()
    uptime_seconds = int(current_time - start_time)

    days = uptime_seconds // (24 * 3600)
    uptime_seconds %= (24 * 3600)
    hours = uptime_seconds // 3600
    uptime_seconds %= 3600
    minutes = uptime_seconds // 60
    seconds = uptime_seconds % 60

    uptime_message = f". "
    additional_text = "V Tuấn"
    
    message_to_send = Message(text=uptime_message)
    
    try:
        tt = add_text_to_image(uptime_message, additional_text)
        client.sendLocalImage(tt, thread_id, thread_type, width=1920, height=1080, message=None, custom_payload=None, ttl=60000)
        
    except requests.exceptions.RequestException as e:
        error_message = Message(text=f"Đã xảy ra lỗi khi gọi API: {str(e)}")
        client.sendMessage(error_message, thread_id, thread_type, ttl=60000)
    except Exception as e:
        error_message = Message(text=f"Đã xảy ra lỗi: {str(e)}")
        client.sendMessage(error_message, thread_id, thread_type, ttl=60000)

def get_mitaizl():
    return {
        'maqr': handle_uptime_command
    }