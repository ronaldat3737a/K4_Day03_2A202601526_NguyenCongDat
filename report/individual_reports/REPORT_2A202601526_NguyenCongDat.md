# Individual Report: Lab 3 - Chatbot vs ReAct Agent

## Student Information

- **Student Name:** Nguyễn Công Đạt
- **Student ID:** 2A202601526
- **Date:** 2026-07-28

---

# I. Technical Contribution (15 Points)

Trong dự án này, tôi đảm nhận vai trò **Role 4 (Core Developer / Integrator)**.

Nhiệm vụ chính của tôi là tích hợp các module (**Tools**, **Prompts**) thành một hệ thống **ReAct Loop** hoàn chỉnh và xây dựng giao diện web để trình diễn hệ thống.

## Modules Implemented

- `src/app.py` (ReAct Loop Logic)
- `src/web_app.py` (Flask API & Streamlit Streaming UI)

---

## Code Highlights

Tôi đã xây dựng cơ chế **Hybrid Router** để phân luồng câu hỏi, giúp tiết kiệm chi phí API đối với các câu hỏi đơn giản không cần gọi Tool.

```python
# Trích xuất từ src/app.py - Logic phân luồng

def gen():
    # Giao diện chat chỉ hiện 1 câu trả lời (agent),
    # bỏ nhánh baseline khỏi luồng live để giảm
    # một lượt gọi LLM không cần thiết.

    for ev in run_react_agent_stream(question, provider):
        yield event(ev)

    yield event({"type": "done"})
```

### Documentation

Code của tôi hoạt động như một **"nhạc trưởng"** điều phối toàn bộ Agent.

Hàm `run_react_agent_stream()` thực hiện các bước:

1. Khởi tạo LLM.
2. Nạp **System Prompt**.
3. Duy trì vòng lặp `while`.
4. Phân tích phản hồi của LLM.
5. Tìm **Action**.
6. Gọi Tool tương ứng trong `AVAILABLE_TOOLS` (`src/tools.py`).
7. Ghép **Observation** vào lịch sử hội thoại.
8. Tiếp tục vòng suy luận cho đến khi sinh **Final Answer**.

---

# II. Debugging Case Study (10 Points)

Trong quá trình tích hợp hệ thống và chạy thử các Test Case của **Role 1**, tôi phát hiện một lỗi logic nghiêm trọng trong luồng ReAct.

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

Tôi đã cập nhật **String Parser** trong `src/app.py`.

Cơ chế mới hoạt động như sau:

- Khi phát hiện chuỗi `Action:`
- Parser lập tức **split** chuỗi.
- Bỏ qua toàn bộ phần văn bản phía sau (bao gồm Final Answer giả mạo).
- Bắt buộc Agent:
  1. Thực thi Tool.
  2. Nhận Observation thực tế.
  3. Tiếp tục vòng ReAct.
  4. Sau đó mới được phép sinh Final Answer.

Nhờ đó Agent luôn kết luận dựa trên dữ liệu thật thay vì suy diễn.

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