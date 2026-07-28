# Group Report: Lab 3 - Production-Grade Agentic System

## Team Information

- **Team Name:** 5connguoi
- **Report Title:** Group Report - Lab 3: Production-Grade Agentic System
- **Deployment Date:** 2026-07-28

### Team Members

| STT | Họ và tên | Mã học viên | Vai trò trong nhóm |
|-----|-----------|-------------|--------------------|
| 1 | Nguyễn Công Đạt | 2A202601526 | Leader |
| 2 | Diệp Đức Lai | 2A202601784 | Member |
| 3 | Trần Bá Lợi | 2A202601316 | Member |
| 4 | Bùi Đức Hiếu | 2A202601820 | Member |
| 5 | Trần Duy Sơn | 2A202601792 | Member |


---

# 1. Executive Summary (Tóm tắt Thực thi)

Hệ thống **Agentic Sàng lọc CV và Hẹn lịch Phỏng vấn** được thiết kế nhằm tự động hóa toàn bộ quy trình tuyển dụng, thay thế hoàn toàn các thao tác tra cứu và xử lý thủ công của bộ phận HR.

## Kết quả đạt được

- **Success Rate:** **100%**
- **Scoring Matrix:** **20/20 điểm** trên **05 Test Cases** thực tế.

### Điểm nổi bật

ReAct Agent của nhóm vượt trội so với Chatbot Baseline khi thực hiện thành công chuỗi suy luận nhiều bước (**Multi-step Reasoning**) gồm:

```text
search_candidates
      ↓
screen_resume
      ↓
check_interviewer_availability
      ↓
schedule_interview
      ↓
send_interview_invitation
```

Tổng cộng **5 tool liên tiếp** mà không xảy ra hiện tượng **hallucination**.

Ngoài ra, kiến trúc **Hybrid Router** giúp:

- Không gọi Tool đối với các câu hỏi đơn giản.
- Giảm chi phí token.
- Tăng tốc độ phản hồi đáng kể.

---

# 2. System Architecture & Tooling (Kiến trúc hệ thống)

## 2.1 ReAct Loop

Hệ thống sử dụng framework **ReAct (Reasoning + Acting)**.

Quy trình xử lý:

1. **Thought**
   - LLM phân tích yêu cầu người dùng.
   - Ví dụ:
     > "Sàng lọc CV1023 và đặt lịch phỏng vấn."

2. **Action**
   - Sinh JSON chuẩn để gọi Tool phù hợp.

3. **Observation**
   - Tool Python thực thi.
   - Trả về dữ liệu thực.

Ví dụ:

- Match Score
- Lịch trống
- Trạng thái gửi Email

Chu trình lặp lại cho đến khi Agent có đủ dữ liệu để sinh:

> **Final Answer**

---

## 2.2 Tool Definitions

Các Tool được định nghĩa trong:

```text
src/tools.py
```

Toàn bộ Tool đều được bảo vệ bằng:

```python
try:
    ...
except:
    ...
```

để tránh crash toàn bộ hệ thống.

### Danh sách Tool

| Tool | Input | Chức năng |
|------|-------|-----------|
| get_candidate_profile | candidate_id | Lấy thông tin ứng viên |
| screen_resume | candidate_id, job_position | Gemini đánh giá CV và trả Match Score |
| check_interviewer_availability | interviewer_name, date | Kiểm tra lịch HR/Tech Lead |
| schedule_interview | candidate_id, interviewer_name, datetime_slot, room_location | Đặt lịch phỏng vấn |
| send_interview_invitation | candidate_id, interview_details | Gửi Email xác nhận |

---

## 2.3 LLM Providers Used

Hệ thống được thiết kế theo kiến trúc module hóa.

### Primary Model

- GPT-4o-mini
- Gemini-2.0-flash-lite (CV Evaluation)

Chịu trách nhiệm:

- ReAct Loop
- Semantic Reasoning
- CV Scoring

### Secondary / Backup

Offline Mock Mode

Trong quá trình Development:

- Không tiêu tốn Token
- Test UI nhanh
- Debug miễn phí

---

# 3. Telemetry & Performance Dashboard

Dựa trên trace logs từ API:

```text
/api/compare/stream
```

## Average Latency

### Fast Path

Khoảng:

```text
~1.2s
```

Nhờ Hybrid Router không gọi Tool.

---

### Full ReAct Loop

Khoảng:

```text
~8.5s
```

Cho testcase phải gọi:

- 5 Tools
- 6 vòng lặp

---

## Token Usage

### Câu hỏi đơn giản

```text
150 ~ 200 tokens
```

### Multi-step Task

```text
1500 ~ 2200 tokens
```

---

## Guardrail Budget

```text
MAX_ITERATIONS = 6
```

Đủ cho toàn bộ quy trình tuyển dụng.

---

# 4. Root Cause Analysis (RCA)

## Case Study

### Premature Final Answer Hallucination

### Input

> "...kiểm tra lịch rảnh của Anh Tuấn, đặt lịch và gửi thư mời."

---

### Observation

LLM tạo:

```text
Action:
send_interview_invitation(...)
```

đồng thời tự sinh luôn:

```text
Đã gửi email thành công.
```

mặc dù Tool chưa chạy.

---

### Root Cause

LLM:

- Không chờ Observation
- Tự suy diễn Email chắc chắn thành công

=> Hallucination.

---

### Resolution

Trong:

```text
src/app.py
```

đã sửa:

Nếu Agent sinh Action:

- Bắt buộc chạy Tool trước
- Bỏ qua Final Answer đi kèm

Chỉ sau khi nhận:

```text
Observation
```

ví dụ:

```text
200 OK
```

LLM mới được phép kết luận.

---

# 5. Ablation Studies & Experiments

## Experiment 1

### Prompt v1

Chatbot Baseline

↓

### Prompt v2

ReAct Agent

### Thay đổi

Từ:

```text
CHATBOT_BASELINE_PROMPT
```

sang:

```text
REACT_SYSTEM_PROMPT
```

Prompt mới yêu cầu:

```json
{
  "tool": "...",
  "args": { }
}
```

và bổ sung:

```text
current_time
```

vào context.

### Kết quả

Prompt v2:

- Không còn hallucination.
- Luôn gọi:

```text
check_interviewer_availability
```

trước khi đặt lịch.

Trong khi Prompt v1 thường:

- Tự nghĩ ra thời gian.
- Hoặc từ chối xử lý.

---

## Experiment 2

### Business Guardrails

Nhóm bổ sung:

```text
ALLOWED_INTERVIEW_HOURS
```

```text
08:00 - 17:00
```

```text
ALLOWED_WEEKDAYS
```

```text
Monday → Friday
```

```text
MIN_NOTICE_HOURS
```

```text
4 hours
```

### Kết quả

Giảm:

```text
100%
```

các lịch đặt sai quy định.

Agent chủ động:

- từ chối lịch cuối tuần
- từ chối lịch ban đêm

và trả về:

```text
FALLBACK_MESSAGES["out_of_hours"]
```

---

# 6. Production Readiness Review

## Security

- API Key lưu trong `.env`
- Quản lý bằng Environment Variables
- Chống Prompt Injection bằng:

```text
BLOCKED_KEYWORDS
```

Ví dụ:

```text
ignore all previous instructions
```

---

## Input Sanitization

Giới hạn:

```text
MAX_INPUT_LENGTH = 1000
```

Sử dụng:

```python
request.get_json(silent=True)
```

đồng thời loại bỏ khoảng trắng dư thừa.

---

## Guardrails

Giới hạn vòng lặp:

```text
MAX_ITERATIONS = 6
```

Giúp tránh:

- Infinite Loop
- Billing Cost tăng đột biến

Timeout cho mỗi Tool:

```text
TIMEOUT_SECONDS = 15
```

---

## Scaling & Cost Optimization

Ứng dụng kiến trúc:

```text
Hybrid Router
```

### Fast Path

- Không gọi Tool
- Tiết kiệm Token

### ReAct Path

Chỉ kích hoạt khi xử lý nghiệp vụ nhiều bước.

Trong quá trình xây dựng:

```text
/api/compare/stream
```

nhóm đã loại bỏ hoàn toàn nhánh Chatbot Baseline khỏi luồng thực thi.

### Kết quả

- Giảm **50%** số lượng request tới LLM.
- Giảm **50%** độ trễ.
- Tiết kiệm đáng kể chi phí Token.
- Cải thiện trải nghiệm Streaming theo thời gian thực.

---

# Conclusion

Hệ thống **Production-Grade Agentic System** của nhóm **5connguoi** đã đáp ứng đầy đủ các yêu cầu của một AI Agent hiện đại:

- ReAct Reasoning
- Multi-tool Orchestration
- Hybrid Routing
- Business Guardrails
- Prompt Injection Defense
- Streaming Response
- Production-ready Architecture

Kết quả thử nghiệm đạt **100% Success Rate**, hoàn thành toàn bộ **20/20 điểm** trên bộ Test Cases và sẵn sàng mở rộng cho các hệ thống tuyển dụng thực tế.