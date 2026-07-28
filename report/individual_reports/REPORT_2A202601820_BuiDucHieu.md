# Individual Report: Lab 3 - Chatbot vs ReAct Agent

## Student Information

- **Student Name:** Bùi Đức Hiếu
- **Student ID:** 2A202601820
- **Role:** Role 2 - Tool Engineer
- **Date:** 2026-07-28

---

# I. Technical Contribution (15 Points)

Trong dự án này, tôi đảm nhận vai trò **Role 2 (Tool Engineer)**.

Nhiệm vụ chính của tôi là thiết kế, hiện thực và tối ưu hóa toàn bộ hệ thống Công cụ (Tools) cùng Cơ sở dữ liệu ứng viên cho ReAct Agent. Các file chịu trách nhiệm chính bao gồm:
- **`src/tools.py`**: Định nghĩa 06 công cụ chính, schemas, docstrings và cơ chế tự ghi dữ liệu.
- **`src/data/data.py`**: Cơ sở dữ liệu Python của kho CV (`CV_REPOSITORY`) và bảng tra cứu mã alias (`CANDIDATE_ALIASES`).
- **`src/data/candidates.json`**: Kho dữ liệu định dạng JSON hỗ trợ lưu trữ trạng thái tuyển dụng vĩnh viễn mà không làm ngắt kết nối web app.

---

## Modules Implemented

### 1. Hệ thống 06 Tool Chuẩn Nghiệp Vụ Tuyển Dụng (`src/tools.py`)

Tôi đã xây dựng 06 công cụ cho Agent gọi trong vòng lặp ReAct, tuân thủ nghiêm ngặt nguyên tắc **Zero-Crash Policy** (mọi hàm đều được bọc `try-except` để luôn trả về thông báo dạng chuỗi thay vì dừng chương trình):

| Tên Tool | Mô tả chức năng | Đột phá / Cải tiến chính |
|:---|:---|:---|
| `search_candidates` | Tìm kiếm ứng viên dựa trên từ khóa trong Mô tả công việc (JD). | HR không cần nhớ mã CV; tự động tìm kiếm trên kho 23+ ứng viên và hiển thị kèm thuộc tính `status`. |
| `get_candidate_profile` | Truy vấn chi tiết hồ sơ CV theo Mã ứng viên (`candidate_id`). | Tự động xử lý mã alias cũ (`CAND001` ➔ `CV1023`); trả về đầy đủ Họ tên, Email, Kinh nghiệm, Học vấn và Trạng thái CRM. |
| `screen_resume` | Sàng lọc và đánh giá độ phù hợp của CV so với vị trí tuyển dụng. | Tích hợp trực tiếp **Gemini AI** (`google.genai`) để chấm Match Score, phân tích điểm mạnh/yếu, ra kết luận ĐẠT/KHÔNG ĐẠT và tự động cập nhật `status`. |
| `check_interviewer_availability` | Tra cứu lịch rảnh của Người phỏng vấn theo ngày. | Hỗ trợ phân lịch cho Chị Mai (HR Manager) và Anh Tuấn (Tech Lead) cho hình thức phỏng vấn Offline. |
| `schedule_interview` | Xếp lịch hẹn phỏng vấn ứng viên. | **Ép buộc 100% hình thức phỏng vấn OFFLINE** tại phòng họp cố định (`Phòng họp 302, Tòa nhà VinUni`), tạo mã `INT-OFFLINE-{cid}-2026` và cập nhật `status`. |
| `send_interview_invitation` | Gửi thư mời phỏng vấn tự động qua Email cho ứng viên. | Đóng gói chi tiết thời gian, địa điểm offline và xác nhận trạng thái gửi thành công (Delivered - 200 OK), cập nhật `status`. |

---

### 2. Quản Lý Thuộc Tính Trạng Thái `status` Và Lưu Trữ Vĩnh Viễn

Theo yêu cầu nghiệp vụ thực tế, các công cụ không chỉ lấy dữ liệu tĩnh mà phải theo dõi và cập nhật trạng thái vòng đời của ứng viên (**Candidate Lifecycle Status**):

- **Mới nộp hồ sơ** ➔ **Đã qua sơ tuyển (ĐẠT)** (bởi `screen_resume`)
- **Đã qua sơ tuyển (ĐẠT)** ➔ **Đã hẹn phỏng vấn Offline (thời gian)** (bởi `schedule_interview`)
- **Đã hẹn phỏng vấn Offline** ➔ **Đã gửi thư mời phỏng vấn Offline (Chờ phỏng vấn)** (bởi `send_interview_invitation`)

---

## Code Highlights

### Trích đoạn 1: Hàm `screen_resume` tích hợp Gemini AI và tự động cập nhật `status` (`src/tools.py`)

```python
def screen_resume(candidate_id: str, job_position: str = "Backend Python Developer") -> str:
    try:
        if not candidate_id or not isinstance(candidate_id, str):
            return "LỖI DỮ LIỆU: Thiếu mã ứng viên hợp lệ (candidate_id)."

        cid = _resolve_candidate_id(candidate_id)
        if cid not in CV_REPOSITORY:
            return f"LỖI KHÔNG TÌM THẤY: Không thể sàng lọc. Không có dữ liệu cho ứng viên '{candidate_id}'..."

        cv = CV_REPOSITORY[cid]
        target_job = job_position.strip() if job_position else cv["position"]
        api_key = os.getenv("GEMINI_API_KEY")

        # Gọi Gemini AI đánh giá trực tiếp nếu có API key
        if api_key:
            try:
                from google import genai
                client = genai.Client(api_key=api_key)
                model_name = os.getenv("LLM_MODEL") or "gemini-2.0-flash-lite"
                res = client.models.generate_content(model=model_name, contents=prompt_eval)
                if res.text and res.text.strip():
                    ai_text = res.text.strip()
                    if "KHÔNG ĐẠT" in ai_text.upper() or "THẤT BẠI" in ai_text.upper():
                        cv["status"] = "Không đạt sơ tuyển (Bị loại)"
                    else:
                        cv["status"] = "Đã qua sơ tuyển (ĐẠT)"
                    
                    _save_cv_repository() # Lưu vĩnh viễn vào file candidates.json
                    return f"🔍 [KẾT QUẢ SÀNG LỌC BẰNG GEMINI AI CHO MÃ {cid}]:\n...\n{ai_text}"
            except Exception:
                pass
```

### Trích đoạn 2: Cơ chế tự động ghi dữ liệu ra JSON tránh đứt kết nối Web Streaming (`src/tools.py`)

```python
def _save_cv_repository():
    """Lưu tự động toàn bộ kho CV (CV_REPOSITORY) vào file candidates.json trên ổ đĩa (tránh làm Flask restart)."""
    try:
        json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "candidates.json")
        data_payload = {
            "CV_REPOSITORY": CV_REPOSITORY,
            "CANDIDATE_ALIASES": CANDIDATE_ALIASES,
        }
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data_payload, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ [WARNING] Không thể lưu file candidates.json: {e}")
```

---

# II. Debugging Case Study (10 Points)

Trong quá trình phát triển hệ thống Tool cho Agent, tôi đã gặp và giải quyết 02 sự cố kỹ thuật phức tạp:

## Case Study 1: Bảo mật API Key & Tích hợp trực tiếp Gemini AI trong `screen_resume`

### 1. Vấn đề (Problem Description)
Ban đầu, kiểm tra API key có đoạn code lộ chìa khóa mẫu `if api_key and api_key != "your_gemini_api_key_here":`, gây kém chuyên nghiệp và thiếu an toàn. Đồng thời hàm `screen_resume` chỉ nhận kết quả ĐẠT/KHÔNG ĐẠT giả định từ bên ngoài thay vì tự đánh giá.

### 2. Nguyên nhân (Root Cause)
Đoạn code mẫu chưa được dọn dẹp biến môi trường và hàm `screen_resume` chưa kết nối trực tiếp với SDK `google.genai` để đọc prompt đánh giá `SCREEN_RESUME_PROMPT` từ `src/prompts.py`.

### 3. Giải pháp & Kết quả (Solution & Verification)
- Làm sạch điều kiện kiểm tra API Key: `api_key = os.getenv("GEMINI_API_KEY")`.
- Đưa trực tiếp `genai.Client` vào trong `screen_resume()`. Khi Agent gọi tool này, Gemini AI sẽ tự nhận thông tin CV và vị trí công việc để ra báo cáo chi tiết gồm Match Score, phân tích kỹ năng và kết luận ĐẠT/KHÔNG ĐẠT.

---

## Case Study 2: Sự cố đứt kết nối Web Streaming do Flask Auto-Reloader khi ghi đè file Python

### 1. Vấn đề (Problem Description)
Khi chạy demo trên giao diện Web (`python src/web_app.py`), lúc Agent gọi `screen_resume` hoặc `schedule_interview`, giao diện lập tức hiện lỗi:  
`"Không kết nối được tới server demo. Kiểm tra terminal đang chạy python src/web_app.py chưa, rồi thử lại."`

### 2. Nguyên nhân (Root Cause)
Khi tool cập nhật thuộc tính `status`, hàm lưu cũ đã ghi đè trực tiếp vào file Python `src/data/data.py`. Do Flask chạy ở chế độ **`debug=True`**, trình quản lý `stat` của Flask phát hiện file `.py` trong dự án bị thay đổi ➔ **Flask lập tức khởi động lại (restart server) ngay giữa lúc đang phản hồi luồng Live Streaming (`/api/compare/stream`)**, làm ngắt kết nối HTTP giữa client và server.

### 3. Giải pháp & Kết quả (Solution & Verification)
- **Tách dữ liệu ra file JSON**: Chuyển toàn bộ cơ sở dữ liệu kho CV và hàm `_save_cv_repository()` sang ghi vào file `src/data/candidates.json`.
- **Cập nhật `src/data/data.py`**: Chuyển sang nạp dữ liệu động từ `candidates.json`.
- **Kết quả**: Do Flask reloader chỉ theo dõi các file `.py`, việc ghi file `.json` hoàn toàn không làm trộm restart server. Luồng phản hồi ReAct Agent trên giao diện Web chạy mượt mà 100% từ Thought ➔ Action ➔ Observation ➔ Final Answer mà không bị rớt mạng.

---

# III. Reflection & Retrospective (5 Points)

## 1. Bài học kinh nghiệm (Lessons Learned)
- **Thiết kế Tool cho AI Agent đòi hỏi tư duy phòng thủ (Defensive Programming)**: Các tool mà Agent gọi bắt buộc phải trả về chuỗi thông báo lỗi rõ ràng thay vì quăng Exception (throw error), giúp Agent biết tự điều chỉnh hành vi ở Thought tiếp theo.
- **Phân tách Dữ liệu Động và Mã Nguồn (Data & Code Decoupling)**: Không bao giờ cho phép ứng dụng Web sửa đổi trực tiếp các file mã nguồn `.py` trong runtime khi đang bật Auto-Reloader, thay vào đó cần sử dụng các định dạng dữ liệu chuẩn như JSON/SQLite.

## 2. Điểm hài lòng về đóng góp cá nhân
- Xây dựng thành công **06 Tool hoàn chỉnh** với Docstring chuẩn hóa, hỗ trợ đầy đủ quy trình từ tìm kiếm, sàng lọc AI, xếp lịch offline cho đến gửi email.
- Mở rộng kho dữ liệu CV lên **23+ ứng viên thực tế**, phủ đủ các vị trí công nghệ (Python, Java Senior 5 năm, Data Analyst, DevOps, Fullstack...), giúp ReAct Agent đáp ứng xuất sắc 100% các Test Cases trong hệ thống đánh giá.
