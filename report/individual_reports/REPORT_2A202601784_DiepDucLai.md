# Individual Report: Lab 3 - Chatbot vs ReAct Agent

## Student Information

- **Student Name:** Diệp Đức Lai
- **Student ID:** 2A202601784
- **Role:** Role 1 - Product Architect (Test Case Design)
- **Date:** 2026-07-28

---

# I. Technical Contribution (15 Points)

Trong dự án này, tôi đảm nhận vai trò **Role 1 (Product Architect)**: chốt chủ đề bài toán và thiết kế bộ 5 Test Cases trong `config/test_cases.json`, đồng thời tham gia kiểm thử lại toàn bộ hệ thống ở các Mốc sau để đảm bảo test case luôn khớp với code thật của Role 2/3/4.

## Modules Implemented

- `config/test_cases.json` — thiết kế và tinh chỉnh lại 3 lần bộ 5 test case (2 câu đơn giản không cần tool, 2 câu multi-step cần tool, 1 câu bẫy Guardrail), theo đúng chủ đề #9 *"Trợ Lý Sàng Lọc Hồ Sơ Tuyển Dụng & Hẹn Phỏng Vấn"*.
- `docs/trace_eval.md` — rà soát và thay các trace minh hoạ/tưởng tượng (gọi tool không tồn tại trong code) bằng trace thật, lấy trực tiếp từ chạy `POST /api/compare/stream` với GPT-4o-mini.
- `docs/hybrid_flowchart.mermaid` — bổ sung file còn thiếu theo đúng path rubric yêu cầu (10% — Mục 5), trước đó sơ đồ chỉ nằm lồng trong `trace_eval.md`.

## Quá trình thiết kế Test Case (3 vòng lặp)

1. **Vòng 1 — Khung ban đầu**: 5 câu theo đúng tỷ lệ CODELAB yêu cầu, nhưng câu #1/#2 hỏi lý thuyết chung ("Quy trình tuyển dụng gồm mấy vòng?") — không thực tế vì HR vốn đã biết sẵn.
2. **Vòng 2 — Sửa câu đơn giản**: đổi câu #1/#2 thành việc LLM thật sự giúp được HR (soạn email mời phỏng vấn, gợi ý câu hỏi behavioral) thay vì hỏi thứ HR đã biết.
3. **Vòng 3 — Phát hiện lỗi thiết kế trước khi có bug thật**: nhận ra tool `screen_resume(candidate_id, ...)` bắt HR phải *biết trước* mã ứng viên cụ thể mới hỏi được — không đúng với cách HR thật sự làm việc (HR có JD, cần hệ thống tự tìm trong kho CV, không phải tự nhớ mã CV). Đề xuất và thiết kế lại luồng: thêm tool `search_candidates(job_description)` để tìm theo JD trước, sau đó mới `screen_resume` trên ứng viên tìm được. Viết lại câu #4 (chuỗi nhiều tool bắt đầu từ JD) và câu #5 (JD không khớp ứng viên nào trong kho — bẫy Guardrail thực tế hơn nhiều so với việc chỉ nhập một mã CV sai).

---

# II. Debugging Case Study (10 Points)

## Vấn đề: lỗi thiết kế (design bug), không phải lỗi runtime

Khác với các lỗi code thông thường phát hiện qua log/exception, lỗi tôi phát hiện nằm ở **tầng thiết kế test case / tool contract** trước khi có bất kỳ dòng code lỗi nào chạy: bộ test case ban đầu (và tool `screen_resume`) giả định HR luôn có sẵn mã ứng viên — một giả định sai với thực tế nghiệp vụ tuyển dụng.

- **Log Source**: Không có log lỗi kỹ thuật — phát hiện qua đọc lại câu hỏi test case #3/#4 và nhận ra câu hỏi tự nhiên của HR ("tôi muốn tuyển 1 backend dev, xem có ai phù hợp không") không thể map vào tool `screen_resume(candidate_id, ...)` vì người dùng không hề biết mã ứng viên.
- **Diagnosis**: Đây là lỗi thuộc nhóm "Agentic Fit" — thiết kế tool sai với luồng nghiệp vụ thật, không phải lỗi prompt hay lỗi parser. Nếu không sửa, toàn bộ Test Case #4 sẽ không bao giờ đại diện đúng cho cách HR thật sự tương tác với hệ thống.
- **Solution**: Đề xuất thêm tool `search_candidates(job_description)`, viết lại `config/test_cases.json` case #4/#5 để bắt đầu từ JD thay vì mã ứng viên có sẵn. Sau khi Role 2/4 triển khai, đã tự kiểm tra lại bằng cách chạy thật câu hỏi *"Tìm ứng viên phù hợp cho vị trí Backend Developer... từ kho CV hiện có"* — xác nhận Agent gọi đúng chuỗi `search_candidates → screen_resume → check_interviewer_availability → schedule_interview → send_interview_invitation`.

## Bug runtime phát hiện khi kiểm thử lại Mốc 3: Router phân loại sai

Khi test câu hỏi *"tôi muốn tuyển dụng 1 backend dev 1 năm kinh nghiệm xem có ai phù hợp không"*, hệ thống trả lời bằng lời khuyên quy trình tuyển dụng chung chung thay vì tìm trong kho CV — Router hiểu nhầm đây là câu hỏi lý thuyết.

- **Diagnosis**: `ROUTER_PROMPT` lúc đó dùng từ "cụ thể" khiến model nghĩ chỉ cần dữ liệu thật khi có mã ứng viên rõ ràng, bỏ sót trường hợp "tìm ứng viên phù hợp" mà không có mã.
- **Solution**: Viết lại `ROUTER_PROMPT` phân biệt rõ 2 nhóm (A: lý thuyết chung, B: cần dữ liệu thật kể cả khi không có mã cụ thể — liệt kê rõ "tìm/lọc/xem có ứng viên nào phù hợp" thuộc nhóm B). Test lại đúng câu hỏi trên — Router trả `NEEDS_TOOL`, Agent gọi đúng `search_candidates` rồi `screen_resume`.

---

# III. Personal Insights: Chatbot vs ReAct (10 Points)

1. **Reasoning**: Việc thiết kế test case buộc tôi phải suy nghĩ như một HR thật — và điều đó bộc lộ ngay điểm yếu của Chatbot: nó không thể "tra cứu" gì cả, chỉ có thể tư vấn chung chung. ReAct Agent với `Thought` block mới thực sự chia nhỏ được bài toán "tìm ai phù hợp" thành các bước tra cứu cụ thể.
2. **Reliability**: Test case tự thiết kế đôi khi vô tình bộc lộ lỗi hệ thống chưa lường trước (vd Router phân loại sai) — cho thấy giá trị của việc Role 1 không chỉ viết câu hỏi mà còn phải tự tay kiểm thử lại sau khi Role 2/3/4 code xong, chứ không dừng ở việc "viết xong là hết trách nhiệm".
3. **Observation**: Câu bẫy Guardrail (#5) hiệu quả nhất khi nó phản ánh đúng một tình huống thật (JD không khớp ứng viên nào trong kho) thay vì chỉ là lỗi cú pháp giả tạo (mã CV bịa, ngày sai định dạng) — Agent xử lý câu bẫy "thật" một cách tự nhiên và thuyết phục hơn nhiều.

---

# IV. Future Improvements (5 Points)

- **Scalability**: Bộ test case hiện chỉ có 5 câu cố định; nên có thêm một bộ test case "hồi quy" (regression) chạy tự động mỗi khi Role 2/3/4 đổi tool hoặc prompt, để Role 1 không phải tự tay dò lại thủ công như lần này.
- **Safety**: Thêm bước review chéo giữa Role 1 (viết test case) và Role 3 (viết prompt) trước khi code — để phát hiện lỗi thiết kế kiểu "tool giả định sai luồng nghiệp vụ" sớm hơn, thay vì phải tìm ra giữa chừng như trong dự án này.
- **Performance**: Ghi lại lịch sử các phiên bản test case (thay vì ghi đè trực tiếp `test_cases.json`) để dễ so sánh test case đã tiến hoá thế nào qua từng vòng lặp thiết kế.

---

# V. Summary

| Mốc | Trạng thái | Ghi chú |
|:---|:---:|:---|
| Mốc 1 - Chọn chủ đề & Test Case | ✅ Đã hoàn thành | Chủ đề #9, 5 test case theo đúng tỷ lệ CODELAB yêu cầu |
| Mốc 2 - Tinh chỉnh Test Case | ✅ Đã hoàn thành | Sửa câu #1/#2 cho thực tế hơn (soạn email, gợi ý câu hỏi) |
| Mốc 3 - Phát hiện & sửa lỗi thiết kế | ✅ Đã hoàn thành | Thêm luồng `search_candidates` theo JD thay vì bắt biết trước mã ứng viên |
| Mốc 4 - Kiểm thử lại toàn hệ thống | ✅ Đã hoàn thành | Phát hiện và giúp sửa bug Router phân loại sai; bổ sung `docs/hybrid_flowchart.mermaid` còn thiếu |

**Nhận xét chung**: Đóng góp lớn nhất của tôi không chỉ là viết 5 câu hỏi test case, mà là phát hiện **lỗi thiết kế nghiệp vụ** (tool bắt biết trước mã ứng viên) trước khi nó trở thành lỗi code khó sửa về sau — một dạng "debugging" xảy ra ở tầng yêu cầu/thiết kế, sớm hơn tầng code. Việc tự tay kiểm thử lại hệ thống ở các Mốc sau (thay vì chỉ giao test case rồi thôi) giúp phát hiện thêm 1 bug thật (Router phân loại sai) và bổ sung 1 file rubric còn thiếu.
