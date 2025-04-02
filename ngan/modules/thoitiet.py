import requests
from zlapi.models import Message
import time
from datetime import datetime
import pytz

des = {
    'tác giả': "Rosy",
    'mô tả': "Lấy và hiển thị thông tin thời tiết",
    'tính năng': [
        "📨 Lấy thông tin thời tiết hiện tại và dự báo từ API WeatherAPI.",
        "🔄 Chuyển đổi thời gian từ UTC sang giờ Việt Nam.",
        "🌡 Hiển thị thông tin chi tiết về nhiệt độ, độ ẩm, gió, chỉ số UV, và chất lượng không khí.",
        "🌅 Hiển thị thông tin về mặt trời mọc, mặt trời lặn, và giai đoạn mặt trăng.",
        "🔔 Thông báo lỗi cụ thể nếu có vấn đề xảy ra khi xử lý yêu cầu."
    ],
    'hướng dẫn sử dụng': [
        "📩 Gửi lệnh thoitiet <khu vực> để nhận thông tin thời tiết của khu vực đó.",
        "📌 Ví dụ: thoitiet Hà Nội để nhận thông tin thời tiết của Hà Nội.",
        "✅ Nhận thông báo trạng thái và kết quả ngay lập tức."
    ]
}

apikey = "661d5464a34d4a91a9f121133251301"  # Thay thế với API key của bạn
vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')  # Múi giờ Việt Nam

def fetch_weather(area, retries=3):
    try:
        # Gửi yêu cầu tới API WeatherAPI với ngôn ngữ tiếng Việt
        response = requests.get(
            f"http://api.weatherapi.com/v1/forecast.json?key={apikey}&q={requests.utils.quote(area)}&days=1&aqi=yes&alerts=no&lang=vi"
        )
        response.raise_for_status()
        data = response.json()

        # Kiểm tra lỗi trong dữ liệu trả về
        if 'error' in data:
            return f"Không tìm thấy địa điểm {area}!"

        # Lấy thông tin thời tiết hiện tại và dự báo
        current = data.get('current', {})
        forecast = data.get('forecast', {}).get('forecastday', [])[0]

        # Xử lý thời gian cập nhật (được trả về theo UTC)
        last_updated_utc = current.get('last_updated', '')
        if last_updated_utc:
            last_updated = datetime.strptime(last_updated_utc, '%Y-%m-%d %H:%M')
            last_updated = pytz.utc.localize(last_updated).astimezone(vn_tz)
            last_updated_str = last_updated.strftime('%H:%M, %d/%m/%Y')
        else:
            last_updated_str = "Không có thông tin"

        # Lấy các thông tin chi tiết về thời tiết
        temp_c = current.get('temp_c', 'Không có thông tin')
        temp_f = current.get('temp_f', 'Không có thông tin')
        humidity = current.get('humidity', 'Không có thông tin')
        wind_kph = current.get('wind_kph', 'Không có thông tin')
        wind_dir = current.get('wind_dir', 'Không có thông tin')
        condition_text = current.get('condition', {}).get('text', 'Không có thông tin')
        real_feel_c = current.get('feelslike_c', 'Không có thông tin')
        uv_index = current.get('uv', 'Không có thông tin')
        air_quality = current.get('air_quality', {}).get('pm10', 'Không có thông tin')
        sunrise = forecast.get('astro', {}).get('sunrise', 'Không có thông tin')
        sunset = forecast.get('astro', {}).get('sunset', 'Không có thông tin')
        moon_phase = forecast.get('astro', {}).get('moon_phase', 'Không có thông tin')

        msg = (
            f"[ Thời tiết {area} ]\n"
            f"Thời tiết hiện tại: {condition_text}\n"
            f"🌡 Nhiệt độ: {temp_c}°C ({temp_f}°F)\n"
            f"💧 Độ ẩm: {humidity}%\n"
            f"🌬 Gió: {wind_kph} km/h hướng {wind_dir}\n"
            f"🌡 Cảm giác nhiệt: {real_feel_c}°C\n"
            f"☀️ Chỉ số UV: {uv_index}\n"
            f"🌀 Chỉ số chất lượng không khí (PM10): {air_quality}\n"
            f"🌅 Mặt trời mọc: {sunrise}\n"
            f"🌇 Mặt trời lặn: {sunset}\n"
            f"🌙 Giai đoạn mặt trăng: {moon_phase}\n"
            f"🌅 Dự báo hôm nay: {forecast.get('day', {}).get('condition', {}).get('text', 'Không có thông tin')}\n"
            f"🕒 Thời gian cập nhật: {last_updated_str}\n"
        )
        return msg

    except requests.exceptions.RequestException:
        if retries > 0:
            time.sleep(1)
            return fetch_weather(area, retries - 1)
        return "Đã có lỗi xảy ra khi lấy dữ liệu thời tiết!"

def handle_weather_command(message, message_object, thread_id, thread_type, author_id, client):
    # Gửi phản ứng xác nhận khi nhận lệnh
    action = "✅"
    client.sendReaction(message_object, action, thread_id, thread_type, reactionType=75)
    
    text = message.split()
    if len(text) < 2:
        error_message = Message(text="Vui lòng nhập khu vực cần xem thời tiết.")
        client.sendMessage(error_message, thread_id, thread_type)
        return

    area = " ".join(text[1:])
    weather_info = fetch_weather(area)
    client.replyMessage(Message(text=f"{weather_info}"), message_object, thread_id, thread_type)

def get_mitaizl():
    return {
        'thoitiet': handle_weather_command
    }
