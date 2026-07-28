# Individual Report: Lab 3 - Chatbot vs ReAct Agent

## Student Information

- **Student Name:** Trần Bá Lợi
- **Student ID:** 2A202601316
- **Date:** 2026-07-28

---

# I. Technical Contribution (15 Points)

Trong dự án này, tôi đảm nhận vai trò **Role 3 (Prompt Engineer / Guardrail Designer)**.

Nhiệm vụ chính của tôi là xây dựng và tối ưu các prompt cho hệ thống AI, đặc biệt là file **`src/prompts.py`**, để agent có thể suy luận đúng theo kiểu ReAct và tránh đưa ra kết quả bịa đặt khi thiếu dữ liệu.

## Modules Implemented

- `src/prompts.py` (Baseline Chatbot Prompt + ReAct System Prompt + Guardrails)

---

## Code Highlights

Tôi đã thiết kế các prompt sao cho agent hoạt động theo hướng an toàn, rõ ràng và có kiểm soát hơn khi xử lý câu hỏi tuyển dụng.

```python
# Trích xuất từ src/prompts.py - Prompt chính cho ReAct Agent

REACT_SYSTEM_PROMPT = """Bạn là một ReAct Agent chuyên về trợ lý sàng lọc hồ sơ tuyển dụng và hẹn phỏng vấn.

THỜI GIAN HIỆN TẠI: {current_time}

Mục tiêu chính:
- Đánh giá mức độ phù hợp của hồ sơ ứng viên với yêu cầu tuyển dụng.
- Lên lịch buổi phỏng vấn một cách an toàn, chính xác.
"""
```

### Documentation

Vai trò của tôi chủ yếu là định hướng hành vi của Agent thông qua prompt.

Các bước tôi thực hiện gồm:

1. Viết **Baseline Chatbot Prompt** để chatbot trả lời ngắn gọn, chuyên nghiệp và không bịa thông tin.
2. Thiết kế **ReAct System Prompt** để agent suy luận theo đúng chuỗi Thought → Action → Observation.
3. Tạo **Guardrails** bằng cách giới hạn số vòng lặp (`MAX_ITERATIONS`) và thêm fallback message khi dữ liệu không đủ.
4. Đảm bảo agent không tự giả định thông tin ứng viên, điểm số hay lịch phỏng vấn khi không có bằng chứng thực tế.

---

# II. Debugging Case Study (10 Points)

Trong quá trình kiểm thử hệ thống và chạy các Test Case của **Role 1**, tôi phát hiện một lỗi logic quan trọng liên quan đến cách Agent suy luận khi thiếu dữ liệu thực tế.

## Problem Description

### Premature Final Answer Hallucination

Ở bước gửi thư mời phỏng vấn (**Test Case #4**), LLM sinh ra:

```text
Action: send_interview_invitation(...)
```

đồng thời tự sinh luôn:

```text
Final Answer:
Đã gửi email...
```

mặc dù Tool Python chưa hề được thực thi.

---

## Log Source

```text
Thought:
Đã có lịch, gửi thư mời cho ứng viên.

Action:
send_interview_invitation['CV1023', 'Phòng họp 302']

Final Answer:
Thư mời đã được gửi thành công tới ứng viên CV1023.
```

---

## Diagnosis

Nguyên nhân đến từ việc một số mô hình nhỏ (đặc biệt **GPT-4o-mini**) đôi khi vi phạm định dạng ReAct.

Thay vì chờ:

```text
Observation
```

Agent lại tự suy diễn rằng Tool chắc chắn thành công (ví dụ trả về **200 OK**) rồi sinh luôn kết luận cuối.

Điều này dẫn đến hiện tượng **Hallucination**.

---

## Solution

Tôi đã điều chỉnh prompt và guardrail để hạn chế hiện tượng Agent tự sinh kết luận trước khi có bằng chứng thực tế.

Cơ chế mới hoạt động như sau:

- Khi cần gọi tool, agent phải xuất Action theo định dạng rõ ràng.
- Nếu thiếu dữ liệu hoặc tool trả về lỗi, agent không được tự bịa kết quả.
- Prompt buộc agent dừng lại và sử dụng fallback message thay vì suy luận sai.
- Guardrail giới hạn vòng lặp để tránh lặp vô tận và giữ hệ thống an toàn.

Nhờ đó Agent luôn kết luận dựa trên bằng chứng hơn là suy diễn.

---

# III. Personal Insights: Chatbot vs ReAct (10 Points)

Sau khi so sánh trực tiếp thông qua API:

```text
/api/compare
```

tôi nhận thấy nhiều khác biệt quan trọng giữa Chatbot truyền thống và ReAct Agent.

---

## 1. Reasoning

Khối **Thought** đóng vai trò như một **Scratchpad (bộ nhớ ngắn hạn)**.

Nó buộc LLM phải chia nhỏ bài toán thành từng bước:

```text
Tìm CV
      ↓
Sàng lọc
      ↓
Kiểm tra lịch
      ↓
Đặt lịch
```

Trong khi đó:

- Chatbot Baseline thường trả lời chung chung.
- Hoặc từ chối xử lý các yêu cầu nhiều bước.

Ngược lại, ReAct Agent thực hiện từng bước một cách logic và tuần tự.

---

## 2. Reliability

Thực tế cho thấy Agent không phải lúc nào cũng tốt hơn Chatbot.

Đối với các câu hỏi đơn giản như:

> "Gợi ý 5 câu hỏi phỏng vấn."

Agent ban đầu vẫn cố gắng tìm Tool phù hợp để gọi.

Điều này:

- Làm tăng Token.
- Chậm hơn.
- Dễ phát sinh lỗi.

Đó là lý do tôi thiết kế thêm **Hybrid Router** để Agent bỏ qua ReAct Loop đối với các câu hỏi không cần Tool.

---

## 3. Observation

Theo tôi, **Observation** là yếu tố quan trọng nhất giúp chống Hallucination.

Khác với Chatbot:

- Tự bịa thời gian.
- Tự bịa lịch.

ReAct Agent chỉ đưa ra kết luận khi đã nhận dữ liệu từ:

```text
check_interviewer_availability
```

Nếu Observation báo lỗi (ví dụ không tìm thấy ứng viên), Agent có thể:

- Điều chỉnh tham số.
- Tự sửa sai.
- Hoặc thông báo chính xác cho người dùng.

---

# IV. Future Improvements (5 Points)

Để nâng cấp hệ thống lên mức **Production-Ready**, tôi đề xuất ba hướng phát triển sau.

---

## 1. Scalability

Chuyển từ vòng lặp `while` truyền thống sang framework dạng đồ thị như:

- LangGraph

Điều này sẽ hỗ trợ:

- Branching Workflow
- Checkpoint
- Resume Workflow
- Human Collaboration

---

## 2. Safety

Tích hợp cơ chế:

**Human-in-the-Loop (HITL)**

Đối với các Tool có rủi ro cao như:

- `schedule_interview`
- `send_interview_invitation`

Agent phải tạm dừng và yêu cầu HR xác nhận trước khi gọi API.

---

## 3. Performance

Xây dựng **Vector Database** để quản lý Tool.

Ví dụ:

- ChromaDB
- Pinecone

Khi hệ thống có hàng trăm Tool nghiệp vụ:

Thay vì đưa toàn bộ Schema vào System Prompt, Agent sẽ:

1. Semantic Search.
2. Truy xuất 3–5 Tool phù hợp nhất.
3. Chỉ nạp các Tool đó vào Context.

Giải pháp này giúp:

- Giảm Context Window.
- Tiết kiệm Token.
- Tăng tốc độ suy luận.
- Dễ mở rộng hệ thống trong tương lai.

---

# Conclusion

Thông qua quá trình phát triển Lab 3, tôi có cơ hội trực tiếp xây dựng và tích hợp một hệ thống **ReAct Agent** hoàn chỉnh, từ vòng lặp suy luận, cơ chế gọi Tool, giao diện Streaming đến tối ưu hiệu năng bằng Hybrid Router. Đồng thời, quá trình debug các lỗi Hallucination giúp tôi hiểu rõ hơn về cách LLM phối hợp với Tool và vai trò của Observation trong việc tạo ra các hệ thống AI đáng tin cậy. Những kinh nghiệm này là nền tảng quan trọng để phát triển các hệ thống Agentic AI ở quy mô lớn và sẵn sàng triển khai trong môi trường thực tế.