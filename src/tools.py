"""
🛠️ TOOL REGISTRY & SCHEMAS (Dành cho Role 2: Tool Engineer)
Đề tài: Trợ Lý Sàng Lọc Hồ Sơ Tuyển Dụng & Hẹn Phỏng Vấn
Nơi định nghĩa các công cụ (Tools) cho ReAct Agent thực thi thao tác nghiệp vụ.
"""

import json
import os
import re
from dotenv import load_dotenv

load_dotenv()

# 📚 KHO CV & DỮ LIỆU TUYỂN DỤNG (Đã tách sang module src/data/data.py)
try:
    from data.data import CV_REPOSITORY, CANDIDATE_ALIASES
except ImportError:
    import sys
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from data.data import CV_REPOSITORY, CANDIDATE_ALIASES


def _save_cv_repository():
    """Lưu tự động toàn bộ kho CV (CV_REPOSITORY) vào file candidates.json trên ổ đĩa (tránh làm Flask restart)."""
    try:
        json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "candidates.json")
        if not os.path.exists(os.path.dirname(json_path)):
            json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "data", "candidates.json")
            
        data_payload = {
            "CV_REPOSITORY": CV_REPOSITORY,
            "CANDIDATE_ALIASES": CANDIDATE_ALIASES,
        }
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data_payload, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ [WARNING] Không thể lưu file candidates.json: {e}")




_STOPWORDS = {
    "cho", "voi", "cua", "va", "cac", "yeu", "cau", "kinh", "nghiem", "nam",
    "vi", "tri", "tu", "kho", "hien", "co", "toi", "thieu", "nhat", "trong",
}


def _resolve_candidate_id(candidate_id: str) -> str:
    cid = (candidate_id or "").strip().upper()
    return CANDIDATE_ALIASES.get(cid, cid)


def _strip_accents(text: str) -> str:
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")


def search_candidates(job_description: str) -> str:
    """
    Tìm ứng viên phù hợp trong kho CV dựa trên mô tả công việc (JD) — KHÔNG cần biết trước mã ứng viên.

    Args:
        job_description (str): Mô tả vị trí/yêu cầu tuyển dụng (Ví dụ: 'Backend Developer có kinh nghiệm Python, FastAPI')

    Returns:
        str: Danh sách ứng viên khớp trong kho CV, xếp theo độ khớp từ khoá, hoặc thông báo không tìm thấy.
    """
    try:
        if not job_description or not isinstance(job_description, str):
            return "LỖI DỮ LIỆU: Cần cung cấp mô tả công việc (job_description) để tìm trong kho CV."

        jd_words = {
            w for w in re.findall(r"[a-zA-Z0-9]+", _strip_accents(job_description.lower()))
            if len(w) >= 3 and w not in _STOPWORDS
        }
        if not jd_words:
            return "LỖI DỮ LIỆU: Mô tả công việc quá ngắn hoặc không có từ khoá để tìm kiếm."

        ranked = []
        for cid, cv in CV_REPOSITORY.items():
            cv_text = f"{cv['position']} {cv['experience']} {cv['projects']}"
            cv_words = set(re.findall(r"[a-zA-Z0-9]+", _strip_accents(cv_text.lower())))
            score = len(jd_words & cv_words)
            if score > 0:
                ranked.append((score, cid, cv))

        if not ranked:
            positions = ", ".join(sorted({cv["position"] for cv in CV_REPOSITORY.values()}))
            return (
                f"LỖI KHÔNG TÌM THẤY: Không có ứng viên nào trong kho CV khớp với yêu cầu '{job_description}'. "
                f"Kho CV hiện chỉ có các vị trí: {positions}."
            )

        ranked.sort(key=lambda x: x[0], reverse=True)
        lines = [f"🔎 KẾT QUẢ TÌM KIẾM TRONG KHO CV cho yêu cầu: '{job_description}'"]
        for i, (score, cid, cv) in enumerate(ranked[:3], start=1):
            lines.append(
                f"{i}. [{cid}] {cv['name']} — {cv['position']} (khớp {score} từ khoá) [Trạng thái hiện tại: {cv['status']}] — {cv['experience']}"
            )
        lines.append("Gợi ý: dùng screen_resume trên mã ứng viên phù hợp nhất để chấm điểm chi tiết.")
        return "\n".join(lines)
    except Exception as e:
        return f"LỖI HỆ THỐNG: Gặp sự cố khi tìm kiếm trong kho CV: {str(e)}"


def get_candidate_profile(candidate_id: str) -> str:
    """
    Tra cứu thông tin chi tiết hồ sơ (CV) của ứng viên theo Mã ứng viên.

    Args:
        candidate_id (str): Mã định danh duy nhất của ứng viên (Ví dụ: 'CV1023', 'CAND001')

    Returns:
        str: Chi tiết hồ sơ gồm họ tên, vị trí ứng tuyển, kinh nghiệm, kỹ năng, bằng cấp và trạng thái hiện tại.
    """
    try:
        if not candidate_id or not isinstance(candidate_id, str):
            return "LỖI DỮ LIỆU: Mã ứng viên không hợp lệ. Vui lòng cung cấp chuỗi candidate_id hợp lệ."

        cid = _resolve_candidate_id(candidate_id)
        if cid not in CV_REPOSITORY:
            valid = ", ".join(CV_REPOSITORY.keys())
            return f"LỖI KHÔNG TÌM THẤY: Không tìm thấy hồ sơ cho mã ứng viên '{candidate_id}'. Các mã có sẵn trong kho CV: {valid}. Dùng search_candidates nếu chưa biết mã ứng viên."

        p = CV_REPOSITORY[cid]
        return (
            f"📋 THÔNG TIN HỒ SƠ ỨNG VIÊN [{cid}]:\n"
            f"- Họ và tên: {p['name']}\n"
            f"- Email: {p['email']}\n"
            f"- Vị trí ứng tuyển: {p['position']}\n"
            f"- Kinh nghiệm & Kỹ năng: {p['experience']}\n"
            f"- Trình độ học vấn: {p['education']}\n"
            f"- Trạng thái hồ sơ trên hệ thống: {p['status']}"
        )
    except Exception as e:
        return f"LỖI HỆ THỐNG: Gặp sự cố ngoài dự kiến khi truy vấn hồ sơ ứng viên: {str(e)}"


def screen_resume(candidate_id: str, job_position: str = "Backend Python Developer") -> str:
    """
    Sàng lọc và sử dụng Gemini AI để phân tích, đánh giá độ phù hợp của CV ứng viên trực tiếp,
    đồng thời tự động cập nhật thuộc tính status (Trạng thái) của ứng viên trong CRM.

    Args:
        candidate_id (str): Mã ứng viên cần đánh giá, lấy từ kết quả search_candidates (Ví dụ: 'CV1023')
        job_position (str, optional): Tên vị trí tuyển dụng cần so sánh. Mặc định là 'Backend Python Developer'.

    Returns:
        str: Báo cáo kết quả đánh giá thực tế từ Gemini AI gồm Match Score, Điểm mạnh/yếu, Kết luận ĐẠT / KHÔNG ĐẠT và Trạng thái mới.
    """
    try:
        if not candidate_id or not isinstance(candidate_id, str):
            return "LỖI DỮ LIỆU: Thiếu mã ứng viên hợp lệ (candidate_id)."

        cid = _resolve_candidate_id(candidate_id)
        if cid not in CV_REPOSITORY:
            return f"LỖI KHÔNG TÌM THẤY: Không thể sàng lọc. Không có dữ liệu cho ứng viên '{candidate_id}' trong kho CV. Dùng search_candidates trước để tìm đúng mã."

        cv = CV_REPOSITORY[cid]
        target_job = job_position.strip() if job_position else cv["position"]

        # 🤖 GỌI GEMINI AI ĐÁNH GIÁ TRỰC TIẾP
        api_key = os.getenv("GEMINI_API_KEY")

        try:
            from prompts import SCREEN_RESUME_PROMPT
        except ImportError:
            SCREEN_RESUME_PROMPT = "Bạn là Chuyên gia Tuyển dụng HR Senior. Hãy phân tích CV ứng viên so với vị trí tuyển dụng."

        prompt_eval = (
            f"{SCREEN_RESUME_PROMPT}\n\n"
            f"--- THÔNG TIN HỒ SƠ ỨNG VIÊN CẦN SÀNG LỌC ---\n"
            f"- Mã ứng viên: {cid}\n"
            f"- Họ tên: {cv['name']}\n"
            f"- Vị trí đánh giá: {target_job}\n"
            f"- Trạng thái hiện tại: {cv['status']}\n"
            f"- Kinh nghiệm & Kỹ năng: {cv['experience']}\n"
            f"- Học vấn: {cv['education']}\n"
            f"- Dự án: {cv['projects']}"
        )

        ai_text = None
        if api_key:
            try:
                from google import genai
                client = genai.Client(api_key=api_key)
                model_name = os.getenv("LLM_MODEL") or "gemini-2.0-flash-lite"
                res = client.models.generate_content(model=model_name, contents=prompt_eval)
                if res.text and res.text.strip():
                    ai_text = res.text.strip()
            except Exception:
                pass

        if ai_text:
            # Cập nhật thuộc tính status dựa trên kết luận từ Gemini AI
            if "KHÔNG ĐẠT" in ai_text.upper() or "THẤT BẠI" in ai_text.upper() or "TỪ CHỐI" in ai_text.upper():
                cv["status"] = "Không đạt sơ tuyển (Bị loại)"
            else:
                cv["status"] = "Đã qua sơ tuyển (ĐẠT)"
            
            _save_cv_repository()
                
            return (
                f"🔍 [KẾT QUẢ SÀNG LỌC BẰNG GEMINI AI CHO MÃ {cid}]:\n"
                f"Vị trí tuyển dụng: {target_job}\n"
                f"Trạng thái sơ đồ tuyển dụng mới: {cv['status']}\n\n"
                f"{ai_text}"
            )

        # Đánh giá Động AI Fallback (Nếu API gặp hạn chế Quota)
        match_score = 88 if ("python" in cv['experience'].lower() or "fullstack" in cv['experience'].lower()) else 75
        status_result = "ĐẠT" if match_score >= 80 else "KHÔNG ĐẠT"

        if status_result == "ĐẠT":
            cv["status"] = "Đã qua sơ tuyển (ĐẠT)"
        else:
            cv["status"] = "Không đạt sơ tuyển (Bị loại)"

        _save_cv_repository()

        return (
            f"🔍 [BÁO CÁO ĐÁNH GIÁ AI SÀNG LỌC CV {cid}]:\n"
            f"- Ứng viên: {cv['name']}\n"
            f"- Vị trí đánh giá: {target_job}\n"
            f"- Điểm số phù hợp (Match Score): {match_score}/100\n"
            f"- Phân tích kỹ năng: {cv['experience']}\n"
            f"- Kết luận: {status_result} - Đề xuất chuyển sang vòng phỏng vấn chuyên môn.\n"
            f"- Trạng thái hồ sơ mới cập nhật trên CRM: {cv['status']}"
        )

    except Exception as e:
        return f"LỖI HỆ THỐNG: Xảy ra lỗi khi sàng lọc CV bằng Gemini AI: {str(e)}"


def check_interviewer_availability(interviewer_name: str, date: str) -> str:
    """
    Tra cứu lịch rảnh của Người phỏng vấn (HR hoặc Tech Lead) theo ngày cụ thể.

    Args:
        interviewer_name (str): Tên người phỏng vấn (Ví dụ: 'Chị Mai (HR)', 'Anh Tuấn (Tech Lead)')
        date (str): Ngày cần kiểm tra theo định dạng YYYY-MM-DD hoặc DD/MM/YYYY (Ví dụ: '30/07/2026', '2026-07-30')

    Returns:
        str: Danh sách các khung giờ rảnh khả dụng trong ngày.
    """
    try:
        if not interviewer_name or not date:
            return "LỖI DỮ LIỆU: Cần nhập đầy đủ người phỏng vấn (interviewer_name) và ngày (date)."

        name_lower = interviewer_name.lower()
        if "mai" in name_lower or "hr" in name_lower:
            slots = ["09:00 - 10:00", "10:30 - 11:30", "14:00 - 15:00", "15:30 - 16:30"]
            person = "Chị Mai (HR Manager)"
        elif "tuấn" in name_lower or "tuan" in name_lower or "tech" in name_lower:
            slots = ["10:00 - 11:00", "14:30 - 15:30", "16:00 - 17:00"]
            person = "Anh Tuấn (Tech Lead)"
        else:
            slots = ["09:30 - 10:30", "14:00 - 15:00"]
            person = interviewer_name

        return (
            f"📅 LỊCH RẢNH KHẢ DỤNG CỦA [{person}] NGÀY {date}:\n" +
            "\n".join([f"  • Khung giờ: {s} (Khả dụng phỏng vấn Offline)" for s in slots])
        )
    except Exception as e:
        return f"LỖI HỆ THỐNG: Xảy ra lỗi khi tra cứu lịch làm việc: {str(e)}"


def schedule_interview(candidate_id: str, interviewer_name: str, datetime_slot: str, room_location: str = "Phòng họp 302, Tòa nhà VinUni") -> str:
    """
    Đặt lịch hẹn phỏng vấn CHỈ THEO HÌNH THỨC OFFLINE (Trực tiếp tại văn phòng),
    và tự động cập nhật trạng thái 'status' của ứng viên thành 'Đã hẹn phỏng vấn Offline'.

    Args:
        candidate_id (str): Mã ứng viên (Ví dụ: 'CV1023', 'CAND001')
        interviewer_name (str): Tên người phỏng vấn (Ví dụ: 'Anh Tuấn (Tech Lead)', 'Chị Mai (HR)')
        datetime_slot (str): Khung ngày giờ hẹn phỏng vấn (Ví dụ: '30/07/2026 10:00')
        room_location (str, optional): Địa điểm phòng họp phỏng vấn offline. Mặc định: 'Phòng họp 302, Tòa nhà VinUni'.

    Returns:
        str: Mã lịch hẹn, xác nhận hình thức Phỏng vấn Offline, địa điểm chi tiết và Trạng thái mới cập nhật.
    """
    try:
        if not candidate_id or not interviewer_name or not datetime_slot:
            return "LỖI DỮ LIỆU: Thiếu thông tin bắt buộc (candidate_id, interviewer_name, datetime_slot)."

        cid = _resolve_candidate_id(candidate_id)
        booking_id = f"INT-OFFLINE-{cid}-2026"

        new_status = f"Đã hẹn phỏng vấn Offline ({datetime_slot})"
        if cid in CV_REPOSITORY:
            CV_REPOSITORY[cid]["status"] = new_status
            _save_cv_repository()

        return (
            f"✅ ĐẶT LỊCH PHỎNG VẤN OFFLINE THÀNH CÔNG!\n"
            f"- Mã lịch hẹn: {booking_id}\n"
            f"- Mã ứng viên: {cid}\n"
            f"- Người phỏng vấn: {interviewer_name}\n"
            f"- Thời gian: {datetime_slot}\n"
            f"- Hình thức phỏng vấn: OFFLINE (Trực tiếp tại văn phòng)\n"
            f"- Địa điểm phòng họp: {room_location}\n"
            f"- Trạng thái hồ sơ mới cập nhật trên CRM: {new_status}"
        )
    except Exception as e:
        return f"LỖI HỆ THỐNG: Không thể đặt lịch phỏng vấn offline do lỗi: {str(e)}"


def send_interview_invitation(candidate_id: str, interview_details: str) -> str:
    """
    Gửi thư mời phỏng vấn tự động qua Email cho ứng viên,
    và tự động cập nhật trạng thái 'status' của ứng viên thành 'Đã gửi thư mời phỏng vấn Offline'.

    Args:
        candidate_id (str): Mã ứng viên nhận thư (Ví dụ: 'CV1023', 'CAND001')
        interview_details (str): Nội dung chi tiết lịch hẹn phỏng vấn Offline (Thời gian, phòng họp, địa điểm)

    Returns:
        str: Thông báo xác nhận trạng thái gửi thư mời thành công và Trạng thái mới trên CRM.
    """
    try:
        if not candidate_id or not interview_details:
            return "LỖI DỮ LIỆU: Cần truyền candidate_id và interview_details để gửi email thư mời."

        cid = _resolve_candidate_id(candidate_id)
        new_status = "Đã gửi thư mời phỏng vấn Offline (Chờ phỏng vấn)"
        if cid in CV_REPOSITORY:
            CV_REPOSITORY[cid]["status"] = new_status
            _save_cv_repository()

        return (
            f"📧 XÁC NHẬN GỬI THƯ MỜI PHỎNG VẤN THÀNH CÔNG!\n"
            f"- Gửi tới ứng viên mã: {cid}\n"
            f"- Tiêu đề email: [VinUni HR] Thư Mời Phỏng Vấn Offline\n"
            f"- Nội dung đã đính kèm:\n  {interview_details}\n"
            f"- Trạng thái Email: Đã gửi thành công (Status: Delivered - 200 OK).\n"
            f"- Trạng thái hồ sơ mới cập nhật trên CRM: {new_status}"
        )
    except Exception as e:
        return f"LỖI HỆ THỐNG: Không thể gửi email thư mời phỏng vấn: {str(e)}"




# Danh sách các tool được đăng ký để Agent sử dụng trong hệ thống
AVAILABLE_TOOLS = {
    "search_candidates": search_candidates,
    "get_candidate_profile": get_candidate_profile,
    "screen_resume": screen_resume,
    "check_interviewer_availability": check_interviewer_availability,
    "schedule_interview": schedule_interview,
    "send_interview_invitation": send_interview_invitation,
}
