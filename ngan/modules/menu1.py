import os
from zlapi.models import Message
import importlib
import time
from datetime import datetime

def handle_menu_command(message, message_object, thread_id, thread_type, author_id, client):
    menu_message = f"""
📄 𝐌𝐞𝐧𝐮 𝐌𝐞𝐝𝐢𝐚
━━━━━━━━━━━━━━━━━━━━━━━
 Soạn help + tên lệnh để xem mô tả
━━━━━━━━━━━━━━━━━━━━━━━
📷 𝙰̉𝚗𝚑 & 𝙷𝚒̀𝚗𝚑 𝚊̉𝚗𝚑
---------------------------------
 ┣━ 🖼 𝗴𝗮𝗶𝟭 — Ảnh gái xinh
 ┣━ 🖼 𝗴𝗮𝗶𝟮 — Ảnh gái ngọt ngào
 ┣━ 🖼 𝗴𝗶𝗿𝗹 — Ảnh gái phố
 ┣━ 🖼 𝗺𝗹𝗲𝗺 — Ảnh mông quyến rũ
 ┣━ 🖼 𝘀𝗲𝘅𝘆 — Ảnh nội y nóng bỏng
 ┣━ 🖼 𝗻𝘂𝗱𝗲 — Ảnh khỏa thân nghệ thuật
 ┣━ 🖼 𝗯𝗼𝗼𝗯𝗮 — Ảnh vếu siêu to
 ┣━ 🖼 𝘅𝘅𝘅𝗵𝘂𝗯 — Ảnh nóng 18+
 ┣━ 🖼 𝗷𝗮𝘃 — Ảnh thần tượng JAV
 ┣━ 🖼 𝗸𝗶𝘀𝘀 — Ảnh hôn lãng mạn
 ┣━ 🖼 𝗵𝗮𝗵𝗮 — Ảnh meme hài hước
 ┣━ 🖼 𝗼𝘁𝗮𝗸𝘂 — Ảnh wibu/anime
 ┗━ 🎭 𝗰𝗼𝘀𝟭𝟴 — Cosplay nóng bỏng
---------------------------------
🎥 𝚅𝚒𝚍𝚎𝚘 & 𝙲𝚕𝚒𝚙
---------------------------------
 ┣━ 🎬 𝗵𝗼𝘁𝗰𝗹𝗶𝗽 — Video gái xinh
 ┣━ 🎬 𝘃𝗱𝘅 — Video sex
 ┣━ 🎬 𝗵𝗲𝗻𝘁𝗮𝗶 — Video hentai
 ┣━ 🎬 𝘃𝗱𝟭𝟴 — Video 18+ đặc sắc
 ┣━ 🎬 𝘃𝗱𝟭𝟵 — Video 19+ siêu cấp
 ┣━ 🎬 𝗰𝘀𝗽𝗹𝗮𝘆 — Video cosplay nóng bỏng
 ┗━ 🎬 𝘃𝗱𝗴𝗮𝗶 — Video gái đẹp
"""

    
    # Thêm hành động phản hồi
    action = "✅ "
    client.sendReaction(message_object, action, thread_id, thread_type, reactionType=75)
    
    client.sendLocalImage(
        "wcmenu1.jpg",
        thread_id=thread_id,
        thread_type=thread_type,
        message=Message(text=menu_message),
        ttl=120000,
        width=1920,  # ví dụ: chiều rộng 1920 pixel
        height=1080  # ví dụ: chiều cao 1080 pixel
    )

def get_mitaizl():
    return {
        'menu1': handle_menu_command
    }
