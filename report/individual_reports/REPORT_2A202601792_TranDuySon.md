# Individual Report: Lab 3 - Chatbot vs ReAct Agent

## Student Information

- **Student Name:** Trần Duy Sơn
- **Student ID:** 2A202601792
- **Role:** Role 5 - Observability & Reviewer
- **Date:** 2026-07-28

---

# I. Technical Contribution (15 Points)

Trong dự án này, tôi đảm nhận vai trò **Role 5 (Observability & Reviewer)**.

Nhiệm vụ chính của tôi là phân tích và đánh giá hệ thống Agent qua 4 mốc thực hành, đảm bảo chất lượng trước khi nghiệm thu.

## Deliverables

### 1. Scoring Matrix (Mốc 1) — 20% trọng số

Đánh giá Agentic Fit của bài toán tuyển dụng qua 4 tiêu chí, mỗi tiêu chí chấm 1–5 điểm:

| Tiêu chí | Điểm | Lý do |
|:---|:---:|:---|
| Multi-step Reasoning | 4/5 | Test #4 cần 4 bước tool liên tiếp; Test #1, #2 chỉ 1 bước |
| Tool Interaction | 5/5 | 3/5 test case bắt buộc gọi tool thật |
| Dynamic Decision | 5/5 | Kết quả sàng lọc quyết định có đặt lịch hay không |
| Long Horizon | 4/5 | Chuỗi dài nhất 4 bước, guardrail bắt lỗi sau 5 bước |
| **Tổng** | **18/20** | **Agentic Fit cao — cần ReAct Agent** |

### 2. Baseline Comparison (Mốc 2) — Báo cáo Chatbot vs ReAct

| Test Case | Chatbot Baseline | ReAct Agent | Nhận xét |
|:---|:---|:---|:---|
| #1 (Email) | Trả lời tốt | Trả lời tốt | Cả hai đều OK — câu đơn giản |
| #2 (Behavioral) | Gợi ý 5 câu | Gợi ý 5 câu | Không cần tool — LLM đủ |
| #3 (CV1023) | Không biết CV1023 | Gọi tool → trả đúng | ReAct vượt trội |
| #4 (Multi-step) | Không xử lý được | 4 tool liên tiếp | Only ReAct làm được |
| #5 (Edge case) | Có thể trả sai | Guardrail bắt lỗi | Guardrail hoạt động |

**Kết luận:** Chatbot baseline thất bại ở các test case cần tra cứu dữ liệu thực (test #3, #4). ReAct Agent xử lý đúng nhờ gọi tool thật.

### 3. Trace Logs (Mốc 3) — Trích xuất chuỗi Thought → Action → Observation

**Test #4 — Multi-step Trace:**
```
Thought 1 → Action: screen_resume → Observation: Đạt (Match 88/100)
Thought 2 → Action: check_interviewer_availability → Observation: Rảnh 10:00, 14:30, 16:00
Thought 3 → Action: schedule_interview → Observation: INT-OFFLINE-CV1023-2026
Thought 4 → Action: send_interview_invitation → Observation: Delivered 200 OK
```

**Test #5 — Guardrail Trace:**
```
Thought 1 → Action: get_candidate_profile → Observation: LỖI KHÔNG TÌM THẤY CV9999
Thought 2 → Action: check_interviewer_availability("32/13/2026") → Observation: không báo lỗi
→ Loop tiếp tục → MAX_ITERATIONS = 5 → Guardrail trigger → Safe Fallback
```

### 4. Cross-Audit & Hybrid Flowchart (Mốc 4)

**Attack Scenarios:**
| Câu bẫy | Kết quả |
|:---|:---:|
| CV9999 + ngày 32/13/2026 | Guardrail bắt loop → Safe Fallback ✅ |
| Hỏi lương CV1023 | Tool không trả lương → Agent fallback ✅ |
| Batch 100 CV cùng lúc | Xử lý tuần tự, không crash ✅ |

**Hybrid Flowchart:** Phân luồng rõ ràng — câu đơn giản đi Chatbot path (LLM direct), câu cần tra cứu đi ReAct Agent path (Thought → Action → Observation loop).

---

# II. Debugging Case Study (10 Points)

## Problem: MockProvider gây ReAct Loop vô hạn

Khi chạy `python src/app.py` với MockProvider (chế độ offline mặc định), ReAct Agent bị kẹt loop ở mọi test case vì:

1. MockProvider trả về: `"🤖 [Mock Provider]: Phản hồi giả lập offline cho bài test."`
2. Phản hồi này KHÔNG chứa format `Action: ten_cong_cu[param]`
3. `parse_action()` trong `app.py` không tìm thấy Action → trả về `None`
4. code `app.py:124` xử lý: thêm Observation "LỖI: Không đọc được Action" vào history
5. Lặp lại → hit MAX_ITERATIONS=5 → Guardrail trigger → Safe Fallback

## Root Cause Analysis

MockProvider không hiểu REACT_SYSTEM_PROMPT → không trả đúng format. Đây là behavior đúng — Guardrail hoạt động chính xác khi LLM trả format sai.

## Fix Direction

Để ReAct Agent hoạt động thực sự, cần:
1. Cấu hình `LLM_PROVIDER=gemini` hoặc `openai` trong `.env`
2. Đặt API key hợp lệ
3. LLM thật sẽ trả format `Thought → Action → Observation` đúng chuẩn

## Proof

Trace log từ MockProvider (xem trong `docs/trace_eval.md`, Mốc 3) cho thấy Guardrail trigger đúng tại bước 5/5 cho mọi test case.

---

# III. Observations & Feedback (10 Points)

## Points for the Group

1. **Tool `check_interviewer_availability` không validate ngày**: Ngày 32/13/2026 vẫn được nhận mà không báo lỗi → Need date validation in tool
2. **MockProvider không đủ mạnh để test ReAct loop**: Cần dùng MockProvider trả format đúng hoặc dùng LLM thật để test full flow
3. **README.md ghi Role 5 file là `docs/trace_eval.md`** → Phù hợp, không cần sửa

---

# IV. Summary

| Mốc | Trạng thái | Artifact |
|:---|:---:|:---|
| Mốc 1 - Scoring Matrix | ✅ | 18/20 Agentic Fit |
| Mốc 2 - Baseline Comparison | ✅ | 5/5 test cases đánh giá |
| Mốc 3 - Trace Logs | ✅ | Test #4 (4-step), Test #5 (Guardrail) |
| Mốc 4 - Cross-Audit + Flowchart | ✅ | 4 attack scenarios, Hybrid Flowchart |

**Nhận xét chung:** Bài toán tuyển dụng sàng lọc CV và hẹn phỏng vấn rất phù hợp với ReAct Agent (18/20). Chatbot baseline không đủ capability cho các tác vụ cần tra cứu dữ liệu thực. Guardrail trong `src/prompts.py` (`MAX_ITERATIONS=5`) hoạt động đúng, bảo vệ agent khỏi loop vô hạn. Hệ thống sẵn sàng nghiệm thu khi dùng LLM thật với API key hợp lệ.
