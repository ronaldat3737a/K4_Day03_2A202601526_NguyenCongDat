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
    ROUTER_PROMPT,
    REACT_SYSTEM_PROMPT,
    MAX_ITERATIONS,
    SAFE_FALLBACK_MESSAGE,
    BLOCKED_KEYWORDS,
    MAX_INPUT_LENGTH,
    BLOCKED_INPUT_MESSAGE,
)
from providers import get_llm_provider

load_dotenv()

NEEDS_TOOL_MARKER = "NEEDS_TOOL"

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


def run_baseline_chatbot_stream(user_query: str, provider):
    """Dựng Chatbot gốc (Baseline): 1 lượt LLM, không tool. Yield từng đoạn text (streaming) khi provider hỗ trợ."""
    print(f"\n💬 [CHATBOT BASELINE] Câu hỏi: {user_query}")
    for chunk in provider.generate_stream(user_query, system_prompt=CHATBOT_BASELINE_PROMPT):
        yield chunk


def run_baseline_chatbot(user_query: str, provider) -> str:
    """Bản không-streaming, dùng cho CLI: gom hết chunk lại thành 1 câu trả lời."""
    response = "".join(run_baseline_chatbot_stream(user_query, provider))
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


def run_react_agent_stream(user_query: str, provider):
    """
    Vòng lặp ReAct Agent thật: gọi LLM -> parse Action -> thực thi Tool thật -> chèn Observation -> lặp lại.
    Dừng khi có Final Answer hợp lệ hoặc chạm Guardrail MAX_ITERATIONS.

    Generator yield event dict theo từng mốc, để UI hiển thị live suy nghĩ + tool đang được chọn:
      {"type": "step_start", "step": n}
      {"type": "thought_chunk", "step": n, "text": "..."}      (nhiều lần, streaming raw LLM output)
      {"type": "step_done", "step": n, "thought", "action", "observation", "is_error"}
      {"type": "step_error", "step": n, "thought", "observation"}   (parse lỗi định dạng)
      {"type": "final", "final_answer": "...", "guardrail_triggered": bool}

    Trước khi vào loop, có 1 bước ĐỊNH TUYẾN NHANH (Hybrid Decision, Mục 6 CODELAB): thử trả lời thẳng
    bằng ROUTER_PROMPT (rẻ, không kèm hướng dẫn tool). Chỉ khi model tự báo NEEDS_TOOL mới rơi vào ReAct
    loop nhiều bước bên dưới — tránh câu hỏi dễ phải chờ qua nhiều lượt gọi LLM không cần thiết.
      {"type": "fast_chunk", "text": "..."}   (câu trả lời trực tiếp, streaming, không cần tool)
      {"type": "fast_done"}
      {"type": "route_tool"}                  (đã xác định cần tool, chuyển sang ReAct loop đầy đủ)
    """
    # Guardrail bảo mật đầu vào: chặn prompt injection rõ ràng / input quá dài trước khi tốn lượt gọi LLM nào.
    lowered_query = user_query.lower()
    if len(user_query) > MAX_INPUT_LENGTH or any(k in lowered_query for k in BLOCKED_KEYWORDS):
        print(f"\n🛡️ [INPUT GUARDRAIL] Chặn câu hỏi vi phạm: {user_query[:80]}...")
        yield {"type": "fast_chunk", "text": BLOCKED_INPUT_MESSAGE}
        yield {"type": "fast_done"}
        return

    print(f"\n🧭 [ROUTER] Câu hỏi: {user_query}")
    buffer = ""
    decided = None  # None chưa quyết, "direct" hoặc "tool"
    for chunk in provider.generate_stream(user_query, system_prompt=ROUTER_PROMPT):
        if decided is None:
            buffer += chunk
            if len(buffer.strip()) >= len(NEEDS_TOOL_MARKER):
                if buffer.strip().upper().startswith(NEEDS_TOOL_MARKER):
                    decided = "tool"
                    break
                decided = "direct"
                yield {"type": "fast_chunk", "text": buffer}
        else:
            yield {"type": "fast_chunk", "text": chunk}

    if decided is None:
        # Stream kết thúc trước khi buffer đủ dài để so khớp marker -> câu trả lời trực tiếp rất ngắn.
        decided = "tool" if buffer.strip().upper().startswith(NEEDS_TOOL_MARKER) else "direct"
        if decided == "direct":
            yield {"type": "fast_chunk", "text": buffer}

    if decided == "direct":
        print(f"🚀 [FAST PATH] Trả lời trực tiếp, không cần tool.")
        yield {"type": "fast_done"}
        return

    print(f"🛠️ [ROUTER] Câu hỏi cần dữ liệu/hành động thật -> chuyển sang ReAct loop đầy đủ.")
    yield {"type": "route_tool"}

    print(f"\n🤖 [REACT AGENT] Câu hỏi: {user_query}")
    history = ""
    step = 0

    while step < MAX_ITERATIONS:
        step += 1
        print(f"\n--- 🔄 Vòng lặp ReAct (Step {step}/{MAX_ITERATIONS}) ---")
        yield {"type": "step_start", "step": step}

        prompt = f"Câu hỏi của người dùng: {user_query}\n{history}"
        accumulated = ""
        for chunk in provider.generate_stream(prompt, system_prompt=REACT_SYSTEM_PROMPT):
            accumulated += chunk
            yield {"type": "thought_chunk", "step": step, "text": chunk}
        llm_output = accumulated.strip()

        # QUAN TRỌNG: ưu tiên Action thật trước Final Answer. Nếu model vừa viết Action vừa tự
        # bịa Observation/Final Answer trong cùng 1 lượt (vi phạm quy tắc "không tự bịa Observation"),
        # ta vẫn chạy tool thật và bỏ qua phần Final Answer tự bịa đó — bắt buộc phải có bằng chứng thật.
        action = parse_action(llm_output)

        if action is None and "final answer" in llm_output.lower():
            match = re.search(r"final answer:?\s*(.*)", llm_output, re.IGNORECASE | re.DOTALL)
            final_answer = match.group(1).strip() if match else llm_output
            print(f"🧠 {llm_output}")
            print(f"🏁 Final Answer: {final_answer}")
            yield {"type": "final", "final_answer": final_answer, "guardrail_triggered": False}
            return

        if action is None:
            # Parse Error — coi như một Observation lỗi để LLM tự sửa ở lượt sau (Failure Mode: Malformed Args)
            print(f"🧠 LLM trả lời không đúng định dạng:\n{llm_output}")
            error_obs = "LỖI: Không đọc được Action hợp lệ. Hãy dùng đúng định dạng Action: ten_cong_cu[tham_so1, tham_so2]."
            history += f"\n{llm_output}\nObservation: {error_obs}"
            yield {"type": "step_error", "step": step, "thought": llm_output, "action": None, "observation": error_obs, "is_error": True}
            continue

        tool_name, args = action
        thought = llm_output.split('Action:')[0].strip()
        print(f"🧠 {thought}")
        print(f"🛠️ Action: {tool_name}{args}")

        obs = execute_tool(tool_name, args)
        print(f"👁️ Observation: {obs}")

        history += f"\nThought: (bước {step})\nAction: {tool_name}{args}\nObservation: {obs}"
        yield {
            "type": "step_done",
            "step": step,
            "thought": thought,
            "action": f"{tool_name}{args}",
            "observation": obs,
            "is_error": obs.strip().upper().startswith("LỖI"),
        }

    print(f"🛡️ GUARDRAIL TRIGGERED: Đã đạt giới hạn tối đa {MAX_ITERATIONS} bước.")
    print(f"🏁 Safe Fallback: {SAFE_FALLBACK_MESSAGE}")
    yield {"type": "final", "final_answer": SAFE_FALLBACK_MESSAGE, "guardrail_triggered": True}


def run_react_agent(user_query: str, provider) -> dict:
    """Bản không-streaming, dùng cho CLI: gom kết quả generator thành 1 dict {final_answer, trace, guardrail_triggered}."""
    trace = []
    final_answer = None
    guardrail_triggered = False
    fast_buffer = ""
    for ev in run_react_agent_stream(user_query, provider):
        if ev["type"] == "fast_chunk":
            fast_buffer += ev["text"]
        elif ev["type"] == "fast_done":
            final_answer = fast_buffer.strip()
        elif ev["type"] in ("step_done", "step_error"):
            trace.append({k: v for k, v in ev.items() if k != "type"})
        elif ev["type"] == "final":
            final_answer = ev["final_answer"]
            guardrail_triggered = ev["guardrail_triggered"]
    return {"final_answer": final_answer, "trace": trace, "guardrail_triggered": guardrail_triggered}


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
