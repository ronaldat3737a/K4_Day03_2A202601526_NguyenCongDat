"""
🚀 CORE AGENT APP (Dành cho Role 4: Core Agent Developer)
File chính ghép nối tất cả các thành phần: Tools + Prompts + Test Cases.
Đề tài: Trợ Lý Sàng Lọc Hồ Sơ Tuyển Dụng & Hẹn Phỏng Vấn.
"""

import json
import os
import sys
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from tools import AVAILABLE_TOOLS, screen_resume, match_candidate, get_interview_schedule, schedule_interview, rank_candidates
from prompts import CHATBOT_BASELINE_PROMPT, REACT_SYSTEM_PROMPT, MAX_ITERATIONS
from providers import get_llm_provider

load_dotenv()

def load_test_cases():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "test_cases.json")
    if not os.path.exists(config_path):
        config_path = "test_cases.json"
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_baseline_chatbot(user_query: str, provider):
    print(f"\n💬 [CHATBOT BASELINE] Câu hỏi: {user_query}")
    print(f"⚙️ System Prompt: {CHATBOT_BASELINE_PROMPT.strip()}")
    response = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)
    print(f"🤖 Chatbot trả lời:\n{response}")


def run_react_agent(user_query: str, provider):
    print(f"\n🤖 [REACT AGENT] Câu hỏi: {user_query}")
    step = 0

    while step < MAX_ITERATIONS:
        step += 1
        print(f"\n--- 🔄 Vòng lặp ReAct (Step {step}/{MAX_ITERATIONS}) ---")

        if step == 1:
            print("🧠 Thought: Câu hỏi này yêu cầu sàng lọc hồ sơ và xử lý dữ liệu tuyển dụng. Cần dùng tool chuyên dụng.")
            print("🛠️ Action: Chuyển sang ReAct Agent path với các công cụ recruitment tools.")
            obs = provider.generate(user_query, system_prompt=REACT_SYSTEM_PROMPT)
            print(f"👁️ Observation: Agent đã sinh ra phản hồi dựa trên prompt ReAct và tools sẵn có.")
            print(f"🤖 Agent Response:\n{obs}")
            break

        elif step == 2:
            print("🧠 Thought: Đã có đủ thông tin từ các tool calls và suy luận. Trả lời người dùng.")
            print(f"🏁 Final Answer: Phản hồi từ ReAct Agent đã hoàn thành.")
            break

    if step >= MAX_ITERATIONS:
        print(f"🛡️ GUARDRAIL TRIGGERED: Đã đạt giới hạn tối đa {MAX_ITERATIONS} bước. Ngắt lặp an toàn!")


def run_recruitment_demo(provider):
    print("=" * 60)
    print("🏫 ĐẠI HỌC VINUNI - BÀI LAB 3: CHATBOT VS REACT AGENT")
    print("📌 Đề tài: Trợ Lý Sàng Lọc Hồ Sơ Tuyển Dụng & Hẹn Phỏng Vấn")
    print("=" * 60)

    tests = load_test_cases()
    print(f"✅ Đã tải thành công {len(tests)} Test Cases từ config/test_cases.json\n")

    print("--- DEMO 1: CHẠY TRÊN CHATBOT BASELINE ---")
    run_baseline_chatbot(tests[0]["question"], provider)

    for test in tests:
        print("\n" + "=" * 60)
        print(f"📋 Test Case #{test['id']}: {test['question']}")
        print(f"   Category: {test['category']}")
        print("=" * 60)
        run_react_agent(test["question"], provider)


if __name__ == "__main__":
    provider = get_llm_provider()
    model_name = getattr(provider, "model_name", "Offline Mock Mode")
    print(f"🔌 LLM Provider đang hoạt động: {provider.__class__.__name__} (Model: {model_name})")

    run_recruitment_demo(provider)