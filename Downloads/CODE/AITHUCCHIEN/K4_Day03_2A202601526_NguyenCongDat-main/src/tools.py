"""
🛠️ TOOL REGISTRY & SCHEMAS (Dành cho Role 2: Tool & Spec Engineer)
Các công cụ dành riêng cho đề tài: Trợ Lý Sàng Lọc Hồ Sơ Tuyển Dụng & Hẹn Phỏng Vấn.
"""

def screen_resume(candidate_name: str, position: str = "Senior Developer") -> str:
    """
    Sàng lọc hồ sơ ứng viên dựa trên kinh nghiệm và kỹ năng.

    Args:
        candidate_name (str): Tên ứng viên cần sàng lọc.
        position (str): Vị trí tuyển dụng cần so khớp. Mặc định: "Senior Developer".

    Returns:
        str: Kết quả sàng lọc bao gồm điểm phù hợp (0-100) và nhận xét.
    """
    candidates_db = {
        "Nguyễn Văn A": {
            "experience_years": 5,
            "skills": ["Python", "Django", "PostgreSQL", "AWS", "Docker"],
            "education": "Đại học Bách Khoa",
            "target_position": "Senior Backend Developer",
            "score": 92,
            "verdict": "Rất phù hợp"
        },
        "Trần Thị B": {
            "experience_years": 2,
            "skills": ["JavaScript", "React", "TypeScript", "Tailwind CSS"],
            "education": "Đại học FPT",
            "target_position": "Frontend Developer",
            "score": 88,
            "verdict": "Phù hợp"
        },
        "Lê Văn C": {
            "experience_years": 0.5,
            "skills": ["Python", "Flask", "HTML", "CSS"],
            "education": "Cao đẳng CNTT",
            "target_position": "Junior Developer",
            "score": 65,
            "verdict": "Cần đào tạo thêm"
        },
        "Phạm Thị D": {
            "experience_years": 3,
            "skills": ["Java", "Spring Boot", "MySQL", "Kafka", "Redis"],
            "education": "Đại học Sư Phạm Kỹ Thuật",
            "target_position": "Backend Developer",
            "score": 90,
            "verdict": "Phù hợp"
        },
        "Hoàng Văn E": {
            "experience_years": 7,
            "skills": ["Python", "Machine Learning", "TensorFlow", "SQL", "Spark"],
            "education": "Thạc sĩ CNTT",
            "target_position": "Data Scientist",
            "score": 95,
            "verdict": "Rất phù hợp"
        }
    }

    name_lower = candidate_name.lower()
    for key, profile in candidates_db.items():
        if name_lower in key.lower() or key.lower() in name_lower:
            skills_str = ", ".join(profile["skills"])
            return (
                f"Sàng lọc hồ sơ: {candidate_name}\n"
                f"  - Vị trí: {profile['target_position']}\n"
                f"  - Kinh nghiệm: {profile['experience_years']} năm\n"
                f"  - Kỹ năng: {skills_str}\n"
                f"  - Điểm phù hợp: {profile['score']}/100\n"
                f"  - Đánh giá: {profile['verdict']}"
            )

    return f"LỖI: Không tìm thấy hồ sơ ứng viên '{candidate_name}'."


def match_candidate(skills_required: str, profile_skills: str) -> str:
    """
    So khớp kỹ năng ứng viên với yêu cầu công việc.

    Args:
        skills_required (str): Danh sách kỹ năng yêu cầu cho vị trí (phân tách bằng dấu phẩy).
        profile_skills (str): Danh sách kỹ năng của ứng viên (phân tách bằng dấu phẩy).

    Returns:
        str: Kết quả so khớp bao gồm kỹ năng trùng khớp và thiếu hụt.
    """
    req_skills = [s.strip().lower() for s in skills_required.split(",")]
    prof_skills = [s.strip().lower() for s in profile_skills.split(",")]

    matched = [s for s in req_skills if s in prof_skills]
    missing = [s for s in req_skills if s not in prof_skills]

    if not req_skills:
        return "LỖI: Danh sách kỹ năng yêu cầu không được để trống."

    match_rate = round(len(matched) / len(req_skills) * 100)

    return (
        f"Kết quả so khớp kỹ năng:\n"
        f"  - Kỹ năng yêu cầu: {', '.join(req_skills)}\n"
        f"  - Kỹ năng ứng viên: {', '.join(prof_skills)}\n"
        f"  - Trùng khớp ({match_rate}%): {', '.join(matched) if matched else 'Không có'}\n"
        f"  - Thiếu hụt: {', '.join(missing) if missing else 'Không thiếu'}"
    )


def get_interview_schedule(date: str = "") -> str:
    """
    Tra cứu lịch phỏng vấnavailable trong ngày được chỉ định.

    Args:
        date (str): Ngày cần kiểm tra lịch (định dạng DD/MM/YYYY). Mặc định: hôm nay.

    Returns:
        str: Danh sách khung giờ phỏng vấn available.
    """
    schedule_db = {
        "01/08/2026": ["09:00 - 10:00", "10:30 - 11:30", "14:00 - 15:00"],
        "02/08/2026": ["09:00 - 10:00", "13:00 - 14:00", "15:00 - 16:00"],
        "03/08/2026": ["10:00 - 11:00", "11:00 - 12:00", "14:30 - 15:30"],
    }

    if not date:
        date = "01/08/2026"

    if date in schedule_db:
        slots = schedule_db[date]
        return f"Lịch phỏng vấn ngày {date}:\n  - " + "\n  - ".join(slots)

    return f"LỖI: Không tìm thấy lịch phỏng vấn cho ngày '{date}'. Vui lòng chọn ngày khác."


def schedule_interview(candidate_name: str, date: str, time_slot: str) -> str:
    """
    Đặt lịch phỏng vấn cho ứng viên.

    Args:
        candidate_name (str): Tên ứng viên.
        date (str): Ngày phỏng vấn (DD/MM/YYYY).
        time_slot (str): Khung giờ phỏng vấn (VD: '09:00 - 10:00').

    Returns:
        str: Xác nhận đặt lịch thành công hoặc thông báo lỗi.
    """
    if not candidate_name or not date or not time_slot:
        return "LỖI: Thiếu thông tin bắt buộc (tên ứng viên, ngày, khung giờ)."

    if len(date.split("/")) != 3:
        return f"LỖI: Định dạng ngày không hợp lệ '{date}'. Vui lòng dùng DD/MM/YYYY."

    try:
        day, month, year = date.split("/")
        if int(day) > 31 or int(month) > 12:
            return f"LỖI: Ngày '{date}' không hợp lệ."
    except ValueError:
        return f"LỖI: Ngày '{date}' chứa giá trị không phải số."

    return (
        f"✅ Đặt lịch phỏng vấn thành công!\n"
        f"  - Ứng viên: {candidate_name}\n"
        f"  - Ngày: {date}\n"
        f"  - Khung giờ: {time_slot}\n"
        f"  - Trạng thái: Confirmed"
    )


def rank_candidates(candidates_data: str) -> str:
    """
    Xếp hạng ứng viên theo điểm số hoặc kỹ năng phù hợp.

    Args:
        candidates_data (str): Chuỗi dữ liệu ứng viên với điểm số (VD: 'Nguyễn Văn A:92, Trần Thị B:88').

    Returns:
        str: Bảng xếp hạng ứng viên theo thứ tự điểm giảm dần.
    """
    if not candidates_data.strip():
        return "LỖI: Dữ liệu ứng viên không được để trống."

    candidates = []
    for entry in candidates_data.split(","):
        entry = entry.strip()
        if ":" not in entry:
            continue
        try:
            name, score_str = entry.rsplit(":", 1)
            score = int(score_str.strip())
            candidates.append((name.strip(), score))
        except ValueError:
            continue

    if not candidates:
        return f"LỖI: Không thể phân tích dữ liệu '{candidates_data}'."

    candidates.sort(key=lambda x: x[1], reverse=True)

    result = "Bảng xếp hạng ứng viên:\n"
    for i, (name, score) in enumerate(candidates, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        result += f"  {medal} {name} - {score}/100\n"

    return result.strip()


AVAILABLE_TOOLS = {
    "screen_resume": screen_resume,
    "match_candidate": match_candidate,
    "get_interview_schedule": get_interview_schedule,
    "schedule_interview": schedule_interview,
    "rank_candidates": rank_candidates,
}