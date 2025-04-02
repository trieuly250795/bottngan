import random
from zlapi import ZaloAPI
from zlapi.models import Message

des = {
    'tác giả': "Rosy",
    'mô tả': "Module bói bài ngẫu nhiên, dự đoán tương lai dựa trên bộ bài Tây.",
    'tính năng': [
        "🃏 Rút ngẫu nhiên một lá bài từ bộ bài Tây",
        "🔮 Cung cấp dự đoán tương lai dựa trên lá bài được rút",
        "✨ Mỗi lá bài có một ý nghĩa riêng về tình yêu, sự nghiệp, tài chính và cuộc sống",
        "🛠️ Tích hợp phản hồi trực tiếp trong bot chat"
    ],
    'hướng dẫn sử dụng': "Dùng lệnh 'boi' để rút một lá bài ngẫu nhiên và nhận dự đoán tương lai."
}

# Danh sách các lá bài
suits = ['Cơ', 'Rô', 'Chuồn', 'Bích']
ranks = ['Át', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']

# Danh sách kết quả bói toán cho từng lá bài
fortune_dict = {
    'Át Cơ': "Tình yêu đang đến gần, bạn sẽ có một mối quan hệ mới đầy hứa hẹn.",
    '2 Cơ': "Cơ hội sẽ đến, hãy chuẩn bị sẵn sàng để nắm bắt.",
    '3 Cơ': "Sự nghiệp của bạn đang tiến triển, nhưng đừng quên chăm sóc sức khỏe.",
    '4 Cơ': "Một thử thách lớn đang đến, nhưng bạn sẽ vượt qua được.",
    '5 Cơ': "Tình yêu đang tràn ngập, hãy tận hưởng những khoảnh khắc ngọt ngào.",
    '6 Cơ': "Một quyết định quan trọng sẽ đến, hãy lắng nghe trái tim mình.",
    '7 Cơ': "Hãy thận trọng với những lời khuyên từ người khác, bạn có thể làm chủ tình huống.",
    '8 Cơ': "Sự nghiệp của bạn đang thăng tiến, nhưng cần có sự kiên nhẫn.",
    '9 Cơ': "Một điều gì đó bất ngờ sẽ xảy ra, nhưng bạn sẽ đủ thông minh để đối phó.",
    '10 Cơ': "Một sự kiện quan trọng sẽ đến trong gia đình bạn, hãy chuẩn bị.",
    'J Cơ': "Tình yêu sẽ gặp thử thách, nhưng sự kiên nhẫn của bạn sẽ được đền đáp.",
    'Q Cơ': "Một cơ hội tài chính sẽ xuất hiện, hãy tận dụng thời gian này.",
    'K Cơ': "Một người có ảnh hưởng mạnh sẽ giúp đỡ bạn trong công việc.",
    'Át Rô': "Một thử thách tài chính đang đến, nhưng bạn sẽ tìm cách giải quyết.",
    '2 Rô': "Đừng sợ hãi khi phải đối mặt với sự thay đổi, nó sẽ mang lại cơ hội mới.",
    '3 Rô': "Hãy cẩn thận trong các quyết định liên quan đến tiền bạc.",
    '4 Rô': "Bạn đang đi đúng hướng, hãy tiếp tục theo đuổi mục tiêu của mình.",
    '5 Rô': "Một mối quan hệ cũ có thể sẽ tái hợp trong thời gian gần.",
    '6 Rô': "Công việc của bạn sẽ gặp phải một số khó khăn, nhưng bạn sẽ học hỏi được rất nhiều.",
    '7 Rô': "Hãy chú ý đến sức khỏe, đừng để công việc chiếm hết thời gian của bạn.",
    '8 Rô': "Tình bạn sẽ mang lại cho bạn sự hỗ trợ quý giá trong thời gian sắp tới.",
    '9 Rô': "Một cuộc gặp gỡ quan trọng sẽ mở ra cơ hội nghề nghiệp cho bạn.",
    '10 Rô': "Sự nghiệp của bạn đang trên đà phát triển, nhưng bạn cần phải tập trung hơn.",
    'J Rô': "Bạn sẽ gặp một người có khả năng giúp đỡ bạn trong việc giải quyết vấn đề.",
    'Q Rô': "Hãy cẩn thận với những kẻ xấu, đừng để họ lợi dụng sự tin tưởng của bạn.",
    'K Rô': "Sự nghiệp của bạn sẽ gặp thành công lớn trong thời gian tới.",
    'Át Chuồn': "Một người bạn cũ sẽ xuất hiện và mang lại cho bạn những lời khuyên quý báu.",
    '2 Chuồn': "Tình yêu sẽ đến bất ngờ, bạn sẽ cảm thấy hạnh phúc và bình yên.",
    '3 Chuồn': "Đây là thời điểm thích hợp để đầu tư vào một dự án mới.",
    '4 Chuồn': "Công việc sẽ đột ngột gặp khó khăn, nhưng đừng lo, bạn sẽ vượt qua.",
    '5 Chuồn': "Hãy lắng nghe tiếng nói từ bên trong, nó sẽ chỉ cho bạn con đường đúng.",
    '6 Chuồn': "Một người có ảnh hưởng sẽ giúp đỡ bạn vượt qua giai đoạn khó khăn.",
    '7 Chuồn': "Một sự kiện sẽ làm thay đổi cuộc đời bạn, hãy chuẩn bị tinh thần.",
    '8 Chuồn': "Một cuộc hành trình mới đang đợi bạn, đừng ngần ngại bắt đầu.",
    '9 Chuồn': "Một vấn đề cũ sẽ được giải quyết trong thời gian tới.",
    '10 Chuồn': "Đừng vội quyết định, hãy suy nghĩ kỹ trước khi hành động.",
    'J Chuồn': "Tình yêu sẽ có một bước tiến mới, nhưng cần phải có sự thấu hiểu.",
    'Q Chuồn': "Một cuộc gặp gỡ bất ngờ sẽ thay đổi cách nhìn của bạn về cuộc sống.",
    'K Chuồn': "Sự nghiệp của bạn đang lên, nhưng đừng quên chăm sóc sức khỏe.",
    'Át Bích': "Một giai đoạn khó khăn sẽ qua đi, bạn sẽ thấy ánh sáng phía cuối con đường.",
    '2 Bích': "Hãy chăm sóc những mối quan hệ xung quanh, chúng sẽ giúp bạn trong thời gian tới.",
    '3 Bích': "Một quyết định quan trọng sẽ đến, hãy suy nghĩ thật kỹ trước khi hành động.",
    '4 Bích': "Tình yêu có thể sẽ gặp thử thách, nhưng đừng lo lắng, bạn sẽ vượt qua.",
    '5 Bích': "Một thay đổi lớn sẽ đến trong công việc, hãy sẵn sàng để đón nhận.",
    '6 Bích': "Tình bạn sẽ là điểm tựa vững chắc cho bạn trong thời gian khó khăn.",
    '7 Bích': "Một cơ hội tài chính sẽ đến, hãy cân nhắc kỹ trước khi quyết định.",
    '8 Bích': "Bạn sẽ gặp một thử thách lớn, nhưng hãy nhớ rằng bạn luôn mạnh mẽ.",
    '9 Bích': "Đây là thời gian thích hợp để bạn thực hiện những kế hoạch lâu dài.",
    '10 Bích': "Tình cảm của bạn đang phát triển mạnh mẽ, hãy trân trọng những gì đang có.",
    'J Bích': "Một điều gì đó rất đặc biệt sẽ xảy ra, hãy chuẩn bị tinh thần.",
    'Q Bích': "Một quyết định quan trọng sẽ thay đổi cuộc đời bạn, hãy hành động khôn ngoan.",
    'K Bích': "Bạn sẽ nhận được một phần thưởng xứng đáng cho những nỗ lực của mình."
}

def handle_joker_command(message, message_object, thread_id, thread_type, author_id, client):
    """
    Xử lý lệnh 'boi' để rút một lá bài ngẫu nhiên và cung cấp dự đoán tương lai.
    """
    try:
        # Chọn ngẫu nhiên một lá bài từ bộ bài
        chosen_suit = random.choice(suits)
        chosen_rank = random.choice(ranks)
        
        # Tạo kết quả bói toán dựa trên lá bài
        card = f"{chosen_rank} {chosen_suit}"
        fortune = fortune_dict.get(card, "Hãy tiếp tục đi trên con đường hiện tại, vận may sẽ đến với bạn.")
        
        # Tạo thông báo trả lời
        message_to_send = Message(text=f"Lá bài của bạn: {card}\nKết quả bói: {fortune}")
        client.replyMessage(message_to_send, message_object, thread_id, thread_type, ttl=120000)
    except Exception as e:
        error_message = Message(text=f"Đã xảy ra lỗi: {str(e)}")
        client.sendMessage(error_message, thread_id, thread_type)

def get_mitaizl():
    """
    Hàm trả về danh sách lệnh và hàm xử lý tương ứng.
    """
    return {
        'boi': handle_joker_command
    }
