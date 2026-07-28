"""
🚀 CORE AGENT APP (Dành cho Role 4: Core Agent Developer)
File chính ghép nối tất cả các thành phần: Tools + Prompts + Test Cases + Multi-Provider.
"""

import json
import os
import re
import sys
from dotenv import load_dotenv

# Đảm bảo import các module cùng thư mục src/ hoạt động mượt mà
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Đảm bảo in ra Tiếng Việt và Emojis không bị lỗi trên Windows Console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Import các thành phần từ file của Role 2, Role 3 & Multi-Provider Adapter
from tools import AVAILABLE_TOOLS
from prompts import (
    CHATBOT_BASELINE_PROMPT,
    REACT_SYSTEM_PROMPT,
    MAX_ITERATIONS,
    SAFE_FALLBACK_MESSAGE,
)
from providers import get_llm_provider

load_dotenv()

# Action: ten_cong_cu[tham_so_1, tham_so_2] — theo đúng định dạng REACT_SYSTEM_PROMPT yêu cầu
ACTION_PATTERN = re.compile(r"Action:\s*(\w+)\s*\[(.*?)\]", re.IGNORECASE | re.DOTALL)


def load_test_cases():
    """Đọc bộ test cases từ config/test_cases.json của Role 1"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "test_cases.json")

    # Fallback kiểm tra nếu file ở thư mục hiện tại
    if not os.path.exists(config_path):
        config_path = "test_cases.json"

    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_baseline_chatbot(user_query: str, provider) -> str:
    """
    Dựng Chatbot gốc (Baseline) không có công cụ.
    Một LLM call duy nhất, không được gọi tool.
    """
    print(f"\n💬 [CHATBOT BASELINE] Câu hỏi: {user_query}")
    response = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)
    print(f"🤖 Chatbot trả lời:\n{response}")
    return response


def parse_action(llm_output: str):
    """Tách tên tool + danh sách tham số thô từ dòng Action. None nếu không tìm thấy."""
    match = ACTION_PATTERN.search(llm_output)
    if not match:
        return None
    tool_name = match.group(1).strip()
    raw_args = match.group(2)
    # Tham số dạng 'a', 'b' hoặc "a", "b" -> tách theo dấu nháy trước, fallback tách theo dấu phẩy
    quoted = re.findall(r"'([^']*)'|\"([^\"]*)\"", raw_args)
    if quoted:
        args = [a or b for a, b in quoted]
    else:
        args = [p.strip() for p in raw_args.split(",") if p.strip()]
    return tool_name, args


def execute_tool(tool_name: str, args: list) -> str:
    """
    Thực thi tool thật, KHÔNG để LLM tự bịa Observation.
    Bắt cả 2 Failure Mode kinh điển: Unknown Tool và Malformed Args (Mục 5 CODELAB).
    """
    tool_fn = AVAILABLE_TOOLS.get(tool_name)
    if tool_fn is None:
        valid = ", ".join(AVAILABLE_TOOLS.keys())
        return f"LỖI: Tool '{tool_name}' không tồn tại. Các tool hợp lệ gồm: [{valid}]"
    try:
        return tool_fn(*args)
    except TypeError as e:
        return f"LỖI: Tham số không hợp lệ khi gọi '{tool_name}' (đã truyền {args}): {e}"
    except Exception as e:
        return f"LỖI HỆ THỐNG: Tool '{tool_name}' gặp sự cố khi thực thi: {e}"


def run_react_agent(user_query: str, provider) -> str:
    """
    Vòng lặp ReAct Agent thật: gọi LLM -> parse Action -> thực thi Tool thật -> chèn Observation -> lặp lại.
    Dừng khi có Final Answer hợp lệ hoặc chạm Guardrail MAX_ITERATIONS.
    """
    print(f"\n🤖 [REACT AGENT] Câu hỏi: {user_query}")
    history = ""
    step = 0

    while step < MAX_ITERATIONS:
        step += 1
        print(f"\n--- 🔄 Vòng lặp ReAct (Step {step}/{MAX_ITERATIONS}) ---")

        prompt = f"Câu hỏi của người dùng: {user_query}\n{history}"
        llm_output = provider.generate(prompt, system_prompt=REACT_SYSTEM_PROMPT).strip()

        # QUAN TRỌNG: ưu tiên Action thật trước Final Answer. Nếu model vừa viết Action vừa tự
        # bịa Observation/Final Answer trong cùng 1 lượt (vi phạm quy tắc "không tự bịa Observation"),
        # ta vẫn chạy tool thật và bỏ qua phần Final Answer tự bịa đó — bắt buộc phải có bằng chứng thật.
        action = parse_action(llm_output)

        if action is None and "final answer" in llm_output.lower():
            final_answer = llm_output.split(":", 1)[-1].strip() if ":" in llm_output else llm_output
            print(f"🧠 {llm_output}")
            print(f"🏁 Final Answer: {final_answer}")
            return final_answer

        if action is None:
            # Parse Error — coi như một Observation lỗi để LLM tự sửa ở lượt sau (Failure Mode: Malformed Args)
            print(f"🧠 LLM trả lời không đúng định dạng:\n{llm_output}")
            history += f"\n{llm_output}\nObservation: LỖI: Không đọc được Action hợp lệ. Hãy dùng đúng định dạng Action: ten_cong_cu[tham_so1, tham_so2]."
            continue

        tool_name, args = action
        print(f"🧠 {llm_output.split('Action:')[0].strip()}")
        print(f"🛠️ Action: {tool_name}{args}")

        obs = execute_tool(tool_name, args)
        print(f"👁️ Observation: {obs}")

        history += f"\nThought: (bước {step})\nAction: {tool_name}{args}\nObservation: {obs}"

    print(f"🛡️ GUARDRAIL TRIGGERED: Đã đạt giới hạn tối đa {MAX_ITERATIONS} bước.")
    print(f"🏁 Safe Fallback: {SAFE_FALLBACK_MESSAGE}")
    return SAFE_FALLBACK_MESSAGE


if __name__ == "__main__":
    print("==================================================")
    print("🏫 ĐẠI HỌC VINUNI - BÀI LAB 3: CHATBOT VS REACT AGENT")
    print("==================================================")

    # Khởi tạo Multi-Provider LLM Adapter (Đọc từ biến môi trường LLM_PROVIDER)
    provider = get_llm_provider()
    model_name = getattr(provider, "model_name", "Offline Mock Mode")
    print(f"🔌 LLM Provider đang hoạt động: {provider.__class__.__name__} (Model: {model_name})")

    tests = load_test_cases()
    print(f"✅ Đã tải thành công {len(tests)} Test Cases từ config/test_cases.json\n")

    for tc in tests:
        print("\n" + "=" * 60)
        print(f"📌 TEST CASE #{tc['id']} [{tc['category']}]")
        print("=" * 60)

        run_baseline_chatbot(tc["question"], provider)
        run_react_agent(tc["question"], provider)
