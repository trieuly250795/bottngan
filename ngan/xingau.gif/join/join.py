import requests

def joinGroup(group_id, imei, language="vi"):
    """
    Gửi yêu cầu tham gia một nhóm đến API của Zalo.

    Args:
        group_id (str): ID của nhóm cần tham gia.
        imei (str): IMEI của thiết bị dùng để xác thực.
        language (str): Ngôn ngữ phản hồi (mặc định: "vi").

    Returns:
        dict: Phản hồi từ API.
    """
    url = "https://tt-group-wpa.chat.zalo.me/api/group/join"
    payload = {
        "group_id": group_id,  # ID nhóm cần tham gia
        "imei": imei,          # IMEI thiết bị xác thực
        "language": language
    }
    headers = {
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, json=payload, headers=headers)

        # Log mã trạng thái và văn bản phản hồi từ API
        print("Status Code:", response.status_code)  # Mã trạng thái HTTP
        print("Response Text:", response.text)  # Văn bản phản hồi từ API

        response.raise_for_status()  # Kiểm tra lỗi HTTP

        # Nếu phản hồi có thể chuyển thành JSON
        try:
            return response.json()
        except ValueError as ve:
            # Trường hợp API trả về dữ liệu không phải JSON
            return {"error_code": 500, "error_message": f"Invalid JSON response: {ve}"}

    except requests.exceptions.RequestException as e:
        # Xử lý các lỗi liên quan đến yêu cầu HTTP
        return {"error_code": 500, "error_message": str(e)}

# Ví dụ gọi hàm joinGroup
group_id = "example_group_id"  # ID nhóm cần tham gia
imei = "example_imei"  # IMEI của thiết bị
result = joinGroup(group_id, imei)

print("Result:", result)  # In kết quả trả về từ API