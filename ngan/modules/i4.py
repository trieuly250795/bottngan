from zlapi import ZaloAPIException
from zlapi.models import *
from datetime import datetime
from config import PREFIX

des = {
    'tác giả': "Rosy",
    'mô tả': "Bot hỗ trợ quản lý nhóm Zalo chuyên nghiệp, cung cấp thông tin chi tiết về thành viên và nhóm.",
    'tính năng': [
        "📌 Hiển thị thông tin tài khoản Zalo của thành viên.",
        "👤 Trích xuất chi tiết như ID, tên, giới tính, ngày sinh, số điện thoại,...",
        "🔍 Kiểm tra trạng thái hoạt động, thiết bị đăng nhập (Web, PC, Mobile).",
        "📊 Theo dõi thời gian tạo tài khoản, cập nhật lần cuối, lần truy cập gần nhất.",
        "🛡️ Kiểm tra trạng thái tài khoản (hoạt động, bị khóa, tài khoản kinh doanh).",
        "🎨 Gửi tin nhắn với định dạng đẹp, màu sắc tùy chỉnh.",
        "⚙️ Tích hợp phản ứng tin nhắn khi nhập lệnh."
    ],
    'cách sử dụng': [
        f"📝 Nhập `{PREFIX}infouser` để xem thông tin tài khoản của chính bạn.",
        f"🔎 Nhập `{PREFIX}infouser @tag` để xem thông tin của thành viên được tag.",
        f"🆔 Nhập `{PREFIX}infouser <ID>` để kiểm tra tài khoản bằng ID Zalo.",
        "🚀 Bot sẽ phản hồi với thông tin đầy đủ và định dạng rõ ràng.",
        "⚠️ Nếu có lỗi xảy ra, bot sẽ hiển thị thông báo kèm hướng dẫn xử lý."
    ]
}

def send_message_with_style(client, text, thread_id, thread_type, color="#000000", font_size="6"):
    """
    Gửi tin nhắn với định dạng màu sắc và cỡ chữ.
    """
    if not text:
        return  # Tránh gửi tin nhắn rỗng

    base_length = len(text)
    adjusted_length = base_length + 355  # Đảm bảo áp dụng style cho toàn bộ tin nhắn
    style = MultiMsgStyle([
        MessageStyle(
            offset=0,
            length=adjusted_length,
            style="color",
            color=color,
            auto_format=False,
        ),
        MessageStyle(
            offset=0,
            length=adjusted_length,
            style="font",
            size=6,
            auto_format=False
        )
    ])
    client.send(Message(text=text, style=style), thread_id=thread_id, thread_type=thread_type, ttl=60000)


def handle_infouser_command(message, message_object, thread_id, thread_type, author_id, client):
    # Gửi phản ứng ngay khi người dùng soạn đúng lệnh
    action = "✅"
    client.sendReaction(message_object, action, thread_id, thread_type, reactionType=75)
    msg_error = "🔴 Có lỗi xảy ra\n| Không thể lấy thông tin tài khoản Zalo!"
    try:
        if message_object.mentions:
            author_id = message_object.mentions[0]['uid']
        elif message[9:].strip().isnumeric():
            author_id = message[9:].strip()
        elif message.strip() == f"{PREFIX}infouser":
            author_id = author_id
        else:
            send_message_with_style(client, msg_error, thread_id, thread_type)
            return

        msg = ""
        multistyle = []
        try:
            # Lấy thông tin người dùng từ API
            info_response = client.fetchUserInfo(author_id)
            profiles = info_response.unchanged_profiles or info_response.changed_profiles
            info = profiles[str(author_id)]
            
            # In kết quả ra terminal để kiểm tra (debug)
            print("Kết quả API trả về thông tin người dùng:", info)
            
            # --- THÔNG TIN CƠ BẢN ---
            card_title = "📝 𝐓𝐡𝐨̂𝐧𝐠 𝐓𝐢𝐧 𝐓𝐚̀𝐢 𝐊𝐡𝐨𝐚̉𝐧 𝐙𝐚𝐥𝐨"
            msg += f"{card_title}\n{'-' * len(card_title)}\n"
            multistyle.append(MessageStyle(offset=0, length=len(msg), style="bold"))
            
            msg += f"🆔 𝐈𝐃 𝐧𝐠𝐮̛𝐨̛̀𝐢 𝐝𝐮̀𝐧𝐠: {info.userId}\n"
            multistyle.append(MessageStyle(offset=len(msg) - len(f"🆔 ID người dùng: {info.userId}\n"),
                                            length=len(f"🆔 ID người dùng: {info.userId}\n"), style="color", color="40ff00"))
            msg += f"🆕 𝐓𝐞̂𝐧 đ𝐚̆𝐧𝐠 𝐧𝐡𝐚̣̂𝐩: {info.username}\n"
            multistyle.append(MessageStyle(offset=len(msg) - len(f"🆕 Tên đăng nhập: {info.username}\n"),
                                            length=len(f"🆕 Tên đăng nhập: {info.username}\n"), style="color", color="40ff00"))
            
            msg += f"👤 𝐓𝐞̂𝐧 𝐙𝐚𝐥𝐨: {info.zaloName}\n"
            multistyle.append(MessageStyle(offset=len(msg) - len(f"👤 Tên Zalo: {info.zaloName}\n"),
                                            length=len(f"👤 Tên Zalo: {info.zaloName}\n"), style="color", color="40ff00"))
            
            # --- THÔNG TIN CÁ NHÂN ---
            gender = "Nam" if info.gender == 0 else "Nữ" if info.gender == 1 else "Không xác định"
            msg += f"🚻 𝐆𝐢𝐨̛́𝐢 𝐭𝐢́𝐧𝐡: {gender}\n"
            multistyle.append(MessageStyle(offset=len(msg) - len(f"🆔 Giới tính: {gender}\n"),
                                            length=len(f"🆔 Giới tính: {gender}\n"), style="color", color="40ff00"))
            dob = info.dob or info.sdob or "Ẩn"
            if isinstance(info.dob, int):
                dob = datetime.fromtimestamp(info.dob).strftime("%d/%m/%Y")
            msg += f"🎂 𝐒𝐢𝐧𝐡 𝐧𝐡𝐚̣̂𝐭: {dob}\n"
            multistyle.append(MessageStyle(offset=len(msg) - len(f"🎂 Sinh nhật: {dob}\n"),
                                            length=len(f"🎂 Sinh nhật: {dob}\n"), style="color", color="40ff00"))
            msg += f"🎂 𝐍𝐠𝐚̀𝐲 𝐬𝐢𝐧𝐡 (sdob): {info.sdob}\n"
            multistyle.append(MessageStyle(offset=len(msg) - len(f"🎂 Ngày sinh (sdob): {info.sdob}\n"),
                                            length=len(f"🎂 Ngày sinh (sdob): {info.sdob}\n"), style="color", color="40ff00"))
            msg += f"📑 𝐓𝐢𝐞̂̉𝐮 𝐬𝐮̛̉: {info.status or 'Default'}\n"
            multistyle.append(MessageStyle(offset=len(msg) - len(f"🚻 Tiểu sử: {info.status or 'Default'}\n"),
                                            length=len(f"🚻 Tiểu sử: {info.status or 'Default'}\n"), style="color", color="40ff00"))
            
            # --- THÔNG TIN LIÊN HỆ ---
            phone = info.phoneNumber or "Ẩn"
            if author_id == client.uid:
                phone = "Ẩn"
            msg += f"📞 𝐒𝐨̂́ đ𝐢𝐞̣̂𝐧 𝐭𝐡𝐨𝐚̣𝐢: {phone}\n"
            multistyle.append(MessageStyle(offset=len(msg) - len(f"📞 Số điện thoại: {phone}\n"),
                                            length=len(f"📞 Số điện thoại: {phone}\n"), style="color", color="40ff00"))                                                
            
            # --- THÔNG TIN THỜI GIAN ---
            create_time = info.createdTs
            if isinstance(create_time, int):
                create_time = datetime.fromtimestamp(create_time).strftime("%H:%M %d/%m/%Y")
            else:
                create_time = "Không xác định"
            msg += f"📅 𝐓𝐡𝐨̛̀𝐢 𝐠𝐢𝐚𝐧 𝐭𝐚̣𝐨 𝐭𝐚̀𝐢 𝐤𝐡𝐨𝐚̉𝐧: {create_time}\n"
            multistyle.append(MessageStyle(offset=len(msg) - len(f"📅 Thời gian tạo tài khoản: {create_time}\n"),
                                            length=len(f"📅 Thời gian tạo tài khoản: {create_time}\n"), style="color", color="40ff00"))
            last_action = info.lastActionTime
            if isinstance(last_action, int):
                last_action = datetime.fromtimestamp(last_action / 1000).strftime("%H:%M %d/%m/%Y")
            else:
                last_action = "Không xác định"
            msg += f"📅 𝐋𝐚̂̀𝐧 𝐭𝐫𝐮𝐲 𝐜𝐚̣̂𝐩 𝐜𝐮𝐨̂́𝐢: {last_action}\n"
            multistyle.append(MessageStyle(offset=len(msg) - len(f"📅 Lần truy cập cuối: {last_action}\n"),
                                            length=len(f"📅 Lần truy cập cuối: {last_action}\n"), style="color", color="40ff00"))
            last_update = info.lastUpdateTime
            if isinstance(last_update, int):
                if last_update > 1e11:
                    last_update = datetime.fromtimestamp(last_update / 1000).strftime("%H:%M %d/%m/%Y")
                else:
                    last_update = datetime.fromtimestamp(last_update).strftime("%H:%M %d/%m/%Y")
            msg += f"📆 𝐂𝐚̣̂𝐩 𝐧𝐡𝐚̣̂𝐭 𝐜𝐮𝐨̂́𝐢: {last_update}\n"
            multistyle.append(MessageStyle(offset=len(msg) - len(f"📆 Cập nhật cuối: {last_update}\n"),
                                            length=len(f"📆 Cập nhật cuối: {last_update}\n"), style="color", color="40ff00"))
            
            # --- THÔNG TIN SỬ DỤNG ---
            windows_status = '🟢 Đang dùng' if info.isActivePC == 1 else '🔴 Không dùng'
            msg += f"💻 𝐌𝐚́𝐲 𝐭𝐢́𝐧𝐡: {windows_status}\n"
            multistyle.append(MessageStyle(offset=len(msg) - len(f"💻 Máy tính: {windows_status}\n"),
                                            length=len(f"💻 Máy tính: {windows_status}\n"), style="color", color="40ff00"))
            web_status = '🟢 Đang dùng' if info.isActiveWeb == 1 else '🔴 Không dùng'
            msg += f"🌐 𝐖𝐞𝐛: {web_status}\n"
            multistyle.append(MessageStyle(offset=len(msg) - len(f"🌐 Web: {web_status}\n"),
                                            length=len(f"🌐 Web: {web_status}\n"), style="color", color="40ff00"))
            active_status = "Đang hoạt động" if info.isActive == 1 else "Không hoạt động"
            msg += f"✅ 𝐓𝐫𝐚̣𝐧𝐠 𝐭𝐡𝐚́𝐢 𝐡𝐨𝐚̣𝐭 đ𝐨̣̂𝐧𝐠: {active_status}\n"
            multistyle.append(MessageStyle(offset=len(msg) - len(f"✅ Trạng thái hoạt động: {active_status}\n"),
                                            length=len(f"✅ Trạng thái hoạt động: {active_status}\n"), style="color", color="40ff00"))
            
            # --- TRẠNG THÁI TÀI KHOẢN VÀ KINH DOANH ---
            account_state = '✅ Còn hoạt động' if info.isBlocked == 0 else '🔒 Đã bị khóa'
            msg += f"🔄 𝐓𝐫𝐚̣𝐧𝐠 𝐭𝐡𝐚́𝐢 𝐭𝐚̀𝐢 𝐤𝐡𝐨𝐚̉𝐧: {account_state}\n"
            multistyle.append(MessageStyle(offset=len(msg) - len(f"🔄 Trạng thái tài khoản: {account_state}\n"),
                                            length=len(f"🔄 Trạng thái tài khoản: {account_state}\n"), style="color", color="40ff00"))
            business = "Có" if info.bizPkg and info.bizPkg.get("label") else "Không"
            msg += f"💼 𝐊𝐢𝐧𝐡 𝐝𝐨𝐚𝐧𝐡: {business}\n"
            multistyle.append(MessageStyle(offset=len(msg) - len(f"💼 Kinh doanh: {business}\n"),
                                            length=len(f"💼 Kinh doanh: {business}\n"), style="color", color="40ff00"))
            
            # --- THÔNG TIN KỸ THUẬT BỔ SUNG ---
            msg += f"🔑 𝐌𝐚̃ 𝐊𝐞𝐲: {info.key}\n"
            multistyle.append(MessageStyle(offset=len(msg) - len(f"🔑 Mã Key: {info.key}\n"),
                                            length=len(f"🔑 Mã Key: {info.key}\n"), style="color", color="40ff00"))
            msg += f"🌀 𝐋𝐨𝐚̣𝐢: {info.type}\n"
            multistyle.append(MessageStyle(offset=len(msg) - len(f"🌀 Loại: {info.type}\n"),
                                            length=len(f"🌀 Loại: {info.type}\n"), style="color", color="40ff00"))
            valid_status = "Có" if info.isValid == 1 else "Không"
            msg += f"✅ 𝐇𝐨̛̣𝐩 𝐥𝐞̣̂: {valid_status}\n"
            multistyle.append(MessageStyle(offset=len(msg) - len(f"✅ Hợp lệ: {valid_status}\n"),
                                            length=len(f"✅ Hợp lệ: {valid_status}\n"), style="color", color="40ff00"))
            msg += f"🆔 𝐊𝐡𝐨́𝐚 𝐧𝐠𝐮̛𝐨̛̀𝐢 𝐝𝐮̀𝐧𝐠: {info.userKey}\n"
            multistyle.append(MessageStyle(offset=len(msg) - len(f"🆔 Khóa người dùng: {info.userKey}\n"),
                                            length=len(f"🆔 Khóa người dùng: {info.userKey}\n"), style="color", color="40ff00"))
            account_status_str = "Còn hoạt động" if info.accountStatus == 0 else "Khác"
            msg += f"🔄 𝐓𝐫𝐚̣𝐧𝐠 𝐭𝐡𝐚́𝐢 𝐓𝐊: {account_status_str}\n"
            multistyle.append(MessageStyle(offset=len(msg) - len(f"🔄 Trạng thái TK: {account_status_str}\n"),
                                            length=len(f"🔄 Trạng thái TK: {account_status_str}\n"), style="color", color="40ff00"))
            msg += f"📄 𝐓𝐡𝐨̂𝐧𝐠 𝐭𝐢𝐧 𝐎𝐀: {info.oaInfo or 'Không có'}\n"
            multistyle.append(MessageStyle(offset=len(msg) - len(f"📄 Thông tin OA: {info.oaInfo or 'Không có'}\n"),
                                            length=len(f"📄 Thông tin OA: {info.oaInfo or 'Không có'}\n"), style="color", color="40ff00"))
            msg += f"👤 𝐂𝐡𝐞̂́ đ𝐨̣̂ 𝐧𝐠𝐮̛𝐨̛̀𝐢 𝐝𝐮̀𝐧𝐠: {info.user_mode}\n"
            multistyle.append(MessageStyle(offset=len(msg) - len(f"👤 Chế độ người dùng: {info.user_mode}\n"),
                                            length=len(f"👤 Chế độ người dùng: {info.user_mode}\n"), style="color", color="40ff00"))
            msg += f"🌐 𝐈𝐃 𝐭𝐨𝐚̀𝐧 𝐜𝐚̂̀𝐮: {info.globalId}\n"
            multistyle.append(MessageStyle(offset=len(msg) - len(f"🌐 ID toàn cầu: {info.globalId}\n"),
                                            length=len(f"🌐 ID toàn cầu: {info.globalId}\n"), style="color", color="40ff00"))
            msg += f"🔔 𝐓𝐫𝐚̣𝐧𝐠 𝐭𝐡𝐚́𝐢 𝐎𝐀: {info.oa_status or 'Không có'}\n"
            multistyle.append(MessageStyle(offset=len(msg) - len(f"🔔 Trạng thái OA: {info.oa_status or 'Không có'}\n"),
                                            length=len(f"🔔 Trạng thái OA: {info.oa_status or 'Không có'}\n"), style="color", color="40ff00"))
          # --- THÔNG TIN HÌNH ẢNH ---
            msg += f"🖼️ 𝐀̉𝐧𝐡 đ𝐚̣𝐢 𝐝𝐢𝐞̣̂𝐧: {info.avatar}\n"
            multistyle.append(MessageStyle(offset=len(msg) - len(f"🖼️ Ảnh đại diện: {info.avatar}\n"),
                                            length=len(f"🖼️ Ảnh đại diện: {info.avatar}\n"), style="color", color="40ff00"))
            msg += f"🖼️ 𝐀̉𝐧𝐡 𝐛𝐢̀𝐚: {info.cover}\n"
            multistyle.append(MessageStyle(offset=len(msg) - len(f"🖼️ Ảnh bìa: {info.cover}\n"),
                                            length=len(f"🖼️ Ảnh bìa: {info.cover}\n"), style="color", color="40ff00"))
            msg += f"🖼️ 𝐀̉𝐧𝐡 𝐧𝐞̂̀𝐧: {info.bgavatar or 'Không có'}\n"
            multistyle.append(MessageStyle(offset=len(msg) - len(f"🖼️ Ảnh nền: {info.bgavatar or 'Không có'}\n"),
                                            length=len(f"🖼️ Ảnh nền: {info.bgavatar or 'Không có'}\n"), style="color", color="40ff00"))
            
            # Gửi tin nhắn đã được style
            send_message_with_style(client, msg, thread_id, thread_type)
        
        except ZaloAPIException as e:
            print(f"Lỗi khi lấy thông tin người dùng: {e}")
    except ZaloAPIException as e:
        error_message = Message(text="Đã xảy ra lỗi")
        client.sendMessage(error_message, thread_id, thread_type)
    except Exception as e:
        error_message = Message(text="Đã xảy ra lỗi")
        client.sendMessage(error_message, thread_id, thread_type)


def get_mitaizl():
    return {
        'i4': handle_infouser_command
    }
