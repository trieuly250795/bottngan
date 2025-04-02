from zlapi.models import Message, MessageStyle
import platform
import psutil
import cpuinfo
import time
from datetime import datetime, timezone, timedelta
import subprocess

# Thời điểm bot khởi chạy để tính thời gian hoạt động (uptime)
bot_start_time = time.time()

des = {
    'tác giả': "Rosy",
    'mô tả': "Kiểm tra thông tin hệ thống và thời gian hoạt động của bot",
    'tính năng': [
        "🔍 Lấy thông tin hệ thống như CPU, RAM, bộ nhớ đĩa, hệ điều hành, và trạng thái ping.",
        "⏱️ Tính thời gian hoạt động của bot (uptime).",
        "📅 Hiển thị thời gian hiện tại theo múi giờ Việt Nam.",
        "🖥️ Lấy thông tin chi tiết về loại RAM, tần số CPU và hệ điều hành.",
        "📊 Đo ping đến một máy chủ và đánh giá trạng thái ping.",
        "🔔 Thông báo kết quả kiểm tra và thời gian thực thi lệnh."
    ],
    'hướng dẫn sử dụng': [
        "📩 Gửi lệnh sys để kiểm tra thông tin hệ thống và thời gian hoạt động của bot.",
        "📌 Ví dụ: sys để nhận thông tin chi tiết về hệ thống và thời gian hoạt động của bot.",
        "✅ Nhận thông báo trạng thái và kết quả kiểm tra ngay lập tức."
    ]
}


def system_info():
    measure_start = time.time()
    vn_timezone = timezone(timedelta(hours=7))
    current_time = datetime.now(vn_timezone).strftime("%d-%m-%Y %H:%M:%S")
    cpu = cpuinfo.get_cpu_info()
    cpu_percent = psutil.cpu_percent(interval=1)
    cpu_physical_cores = psutil.cpu_count(logical=False)
    cpu_total_cores = psutil.cpu_count(logical=True)
    ram_info = psutil.virtual_memory()
    ram_used = ram_info.used / (1024 ** 3)
    ram_total = ram_info.total / (1024 ** 3)
    ram_available = ram_info.available / (1024 ** 3)
    ram_percent = ram_info.percent
    ram_type = get_ram_type()
    swap_info = psutil.swap_memory()
    swap_used = swap_info.used / (1024 ** 3)
    swap_total = swap_info.total / (1024 ** 3)
    swap_percent = swap_info.percent
    disk_info = psutil.disk_usage('/')
    disk_used = disk_info.used / (1024 ** 3)
    disk_total = disk_info.total / (1024 ** 3)
    system = platform.system()
    version = platform.version()
    ping_time = measure_ping()
    ping_status = evaluate_ping(ping_time)
    measure_end = time.time()
    execution_time = measure_end - measure_start
    _, rem = divmod(execution_time, 3600)
    minutes, seconds = divmod(rem, 60)
    
    info_text = f"""
🕒 Thời gian hiện tại: {current_time}
━━━━━━━━━━━━━━━━━━━━━━━━
💻 Thông tin CPU:
   ┣━ ⚙️ CPU: {cpu['brand_raw']}
   ┣━ 🔲 Loại CPU: {cpu['arch']}
   ┣━ 🔴 Số nhân vật lý: {cpu_physical_cores}
   ┣━ 🟡 Số nhân logic: {cpu_total_cores}
   ┣━ 📊 Tần số: {cpu['hz_actual_friendly']}
   ┗━ 📈 Sử dụng CPU: {cpu_percent}%
━━━━━━━━━━━━━━━━━━━━━━━━
🏷️Thông tin RAM:
   ┣━ 🟡 Đã dùng: {ram_used:.2f}GB / {ram_total:.2f}GB
   ┣━ 🟢 Khả dụng: {ram_available:.2f}GB
   ┣━ 🔴 Tỷ lệ RAM đã dùng: {ram_percent}%
   ┗━ 🏷️ Loại RAM: {ram_type}
━━━━━━━━━━━━━━━━━━━━━━━━
🏷️ Swap Memory (Bộ nhớ ảo):
   ┣━ 🟡 Đã dùng: {swap_used:.2f}GB / {swap_total:.2f}GB
   ┗━ 🔴 Tỷ lệ đã dùng: {swap_percent}%
━━━━━━━━━━━━━━━━━━━━━━━━
🗃️  Disk:
   ┗━ {disk_used:.2f}GB / {disk_total:.2f}GB
━━━━━━━━━━━━━━━━━━━━━━━━
🖥️  Thông tin hệ điều hành:
   ┣━ 🏷️ Hệ điều hành: {system}
   ┗━ 🏷️ Phiên bản: {version}
━━━━━━━━━━━━━━━━━━━━━━━━
🌐 Ping: {ping_time if ping_time is not None else "Không thể đo"} ms ({ping_status})
━━━━━━━━━━━━━━━━━━━━━━━━
⏱️  Thời gian lấy thông tin: {seconds:.2f} giây
"""

    return info_text

def get_ram_type():
    system = platform.system()
    if system == "Windows":
        try:
            output = subprocess.check_output("wmic memorychip get MemoryType", shell=True, universal_newlines=True)
            lines = output.splitlines()
            if len(lines) > 1:
                ram_type_code = lines[1].strip()
                if ram_type_code.isdigit():
                    ram_type_code = int(ram_type_code)
                    ram_types = {
                        0: "Unknown",
                        1: "Other",
                        2: "DRAM",
                        3: "Synchronous DRAM",
                        4: "Cache DRAM",
                        5: "EDO",
                        6: "EDRAM",
                        7: "VRAM",
                        8: "SRAM",
                        9: "RAM",
                        10: "ROM",
                        11: "Flash",
                        12: "EEPROM",
                        13: "FEPROM",
                        14: "EPROM",
                        15: "CDRAM",
                        16: "3DRAM",
                        17: "SDRAM",
                        18: "SGRAM",
                        19: "RDRAM",
                        20: "DDR",
                        21: "DDR2",
                        22: "DDR2 FB-DIMM",
                        24: "DDR3",
                        25: "FBD2",
                        26: "DDR4",
                    }
                    return ram_types.get(ram_type_code, "Unknown")
            return "Không thể xác định loại RAM"
        except Exception as e:
            return f"Lỗi khi lấy loại RAM: {str(e)}"
    elif system == "Linux":
        try:
            output = subprocess.check_output("dmidecode --type 17", shell=True, universal_newlines=True)
            for line in output.splitlines():
                if "Type:" in line and "Type Detail:" not in line:
                    return line.split(":")[1].strip()
            return "Không tìm thấy thông tin loại RAM"
        except Exception as e:
            return f"Lỗi khi lấy loại RAM: {str(e)}"
    return "Không thể xác định loại RAM"

def measure_ping(host="google.com"):
    try:
        output = subprocess.check_output(
            f"ping -n 1 {host}" if platform.system() == "Windows" else f"ping -c 1 {host}",
            shell=True, universal_newlines=True
        )
        for line in output.splitlines():
            if "time=" in line:
                ping_time = line.split("time=")[1].split("ms")[0].strip()
                return float(ping_time)
    except subprocess.CalledProcessError:
        return None

def evaluate_ping(ping_time):
    if ping_time is None:
        return "Không thể đo"
    elif ping_time < 50:
        return "Mượt"
    elif 50 <= ping_time < 150:
        return "Bình thường"
    else:
        return "Chậm"

def check_info(message, message_object, thread_id, thread_type, author_id, client):
    # Gửi phản ứng ngay khi người dùng soạn đúng lệnh
    action = "✅"
    client.sendReaction(message_object, action, thread_id, thread_type, reactionType=75)
    # Tính thời gian hoạt động của bot
    uptime_seconds = int(time.time() - bot_start_time)
    days = uptime_seconds // (24 * 3600)
    uptime_seconds %= (24 * 3600)
    hours = uptime_seconds // 3600
    uptime_seconds %= 3600
    minutes = uptime_seconds // 60
    seconds = uptime_seconds % 60
    uptime_message = f"Bot đã online: {days} NGÀY, {hours} GIỜ, {minutes} PHÚT, {seconds} GIÂY"
    
    sys_info = system_info()
    combined_info = f"{uptime_message}\n{sys_info}"
    
    font_style = MessageStyle(
        style="font",
        size="13",
        offset=0,
        length=len(combined_info),
        auto_format=False
    )
    final_message = Message(text=combined_info, style=font_style)
    client.sendMessage(final_message, thread_id, thread_type, ttl=60000)

def get_mitaizl():
    return {
        'sys': check_info
    }
