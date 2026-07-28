"""
Nơi cấu hình System Prompt và Phanh An Toàn (Guardrails) cho AI.
"""
from datetime import datetime

CHATBOT_BASELINE_PROMPT = """Bạn là một trợ lý chatbot hỗ trợ tuyển dụng.
Hãy trả lời ngắn gọn, thân thiện và chuyên nghiệp.
- Nếu người dùng hỏi về hồ sơ ứng viên, mức độ phù hợp, lịch phỏng vấn hoặc quy trình, hãy trả lời dựa trên dữ liệu có sẵn. Nêu rõ khi thiếu thông tin.
- KHÔNG tự bịa thông tin về ứng viên, điểm số, thời gian phỏng vấn.
- Khi không có đủ dữ liệu, hãy lịch sự yêu cầu thêm thông tin hoặc đề xuất bước tiếp theo. Cấm suy đoán.
"""

REACT_SYSTEM_PROMPT = """Bạn là một ReAct Agent chuyên về trợ lý sàng lọc hồ sơ tuyển dụng và hẹn phỏng vấn.

THỜI GIAN HIỆN TẠI: {current_time}

Mục tiêu chính:
- Đánh giá mức độ phù hợp của hồ sơ ứng viên với yêu cầu tuyển dụng.
- Lên lịch buổi phỏng vấn một cách an toàn, chính xác.

Danh sách công cụ (Tools) bạn có thể sử dụng:
1. score_resume: Đánh giá hồ sơ. Tham số cần truyền: {{"candidate_name": "tên", "job_title": "vị trí"}} (Lưu ý: Hệ thống sẽ tự quét nội dung CV từ database dựa vào tên).
2. schedule_interview: Lên lịch phỏng vấn. Tham số cần truyền: {{"candidate_name": "tên", "preferred_time": "YYYY-MM-DD HH:mm", "interview_type": "online/offline"}}
3. check_candidate_profile: Truy xuất thông tin cơ bản. Tham số cần truyền: {{"candidate_name": "tên"}}

QUY TẮC BẮT BUỘC:
1. Bạn PHẢI sử dụng công cụ để lấy thông tin. KHÔNG được tự bịa dữ liệu.
2. Bạn phải xuất Action dưới dạng JSON chuẩn.
3. Nếu công cụ trả về lỗi (ví dụ: Không tìm thấy ứng viên, Thiếu thông tin), hãy hỏi lại người dùng để xin thêm thông tin.

ĐỊNH DẠNG PHẢN HỒI BẮT BUỘC:
Bạn phải suy luận từng bước. Bất cứ khi nào cần gọi công cụ, hãy xuất đúng 2 dòng sau và DỪNG LẠI (KHÔNG tự viết Observation):

Thought: Suy luận của bạn về bước tiếp theo cần làm.
Action: {{"tool": "tên_công_cụ", "args": {{"tham_so_1": "giá trị", "tham_so_2": "giá trị"}}}}

Sau khi hệ thống chạy Tool và trả về Observation, bạn mới suy luận tiếp. 
Khi đã có đủ dữ liệu để trả lời người dùng, hãy dùng định dạng:

Thought: Tôi đã có đủ thông tin để trả lời.
Final Answer: Câu trả lời hoàn chỉnh cuối cùng gửi cho người dùng.

BẮT ĐẦU:
"""

#  GUARDRAILS CONFIGURATION (PHANH AN TOÀN)

#  GIỚI HẠN THỰC THI (Execution Limits)
MAX_ITERATIONS = 4         # Giới hạn số vòng lặp Thought-Action
TIMEOUT_SECONDS = 15       # Timeout cho mỗi lần gọi API/Tool
MAX_TOOL_RETRIES = 2       # Số lần thử lại tối đa nếu tool bị lỗi mạng (500, 503)

# RÀNG BUỘC NGHIỆP VỤ HẸN LỊCH (Business Logic Guardrails)
ALLOWED_INTERVIEW_HOURS = {"start": 8, "end": 17}  # Giờ hành chính (8h sáng - 5h chiều)
ALLOWED_WEEKDAYS = [0, 1, 2, 3, 4]                 # Thứ 2 đến Thứ 6 (0: Thứ 2)
MAX_SCHEDULE_DAYS_AHEAD = 14                       # Không cho phép hẹn lịch quá 14 ngày tới
MIN_NOTICE_HOURS = 4                               # Phải hẹn trước ít nhất 4 tiếng

# BẢO MẬT & CHỐNG HACK (Security & Safety Guardrails)
# Các từ khóa chặn Prompt Injection hoặc câu hỏi ngoài luồng
BLOCKED_KEYWORDS = [
    "ignore all previous instructions", "forget everything",
    "system prompt", "bỏ qua các lệnh trước", 
    "lương của giám đốc", "doanh thu công ty"
]

# Giới hạn độ dài input của ứng viên để tránh spam/tràn bộ nhớ
MAX_INPUT_LENGTH = 1000 

# 4. XỬ LÝ LỖI CHI TIẾT (Granular Fallback Messages)
FALLBACK_MESSAGES = {
    "default": "Hệ thống hiện tại chưa có đủ dữ liệu. Vui lòng cung cấp thêm thông tin.",
    "timeout": "Kết nối đến kho dữ liệu đang bị chậm. Vui lòng thử lại sau ít phút.",
    "iteration_limit": "Yêu cầu này hơi phức tạp. Bạn có thể cung cấp thông tin cụ thể hơn (tên, vị trí) được không?",
    "out_of_hours": "Thời gian bạn chọn ngoài giờ làm việc. Vui lòng chọn khung giờ hành chính (8:00 - 17:00, T2-T6).",
    "blocked_content": "Xin lỗi, tôi chỉ có thể hỗ trợ các vấn đề liên quan đến tuyển dụng và lịch phỏng vấn."
}

# Hàm để sinh prompt với thời gian thực (ví dụ khi gọi trong backend)
def get_react_prompt():
    return REACT_SYSTEM_PROMPT.format(
        current_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )