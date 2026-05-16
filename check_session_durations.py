import json
from pathlib import Path

def analyze_llm_times():
    base_dir = Path("AgentTasks/generated_articles")
    success_times = []
    
    if not base_dir.exists():
        print(f"Directory {base_dir} not found.")
        return

    for log_file in base_dir.rglob("logs/events_*.jsonl"):
        with open(log_file, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip(): continue
                try:
                    data = json.loads(line)
                    if data.get("event") == "llm_success":
                        success_times.append({
                            "node": data.get("node"),
                            "elapsed": data.get("elapsed_seconds"),
                            "chars": data.get("response_chars")
                        })
                except json.JSONDecodeError:
                    continue

    if not success_times:
        print("No successful LLM calls found in the logs yet.")
        return

    times = [x["elapsed"] for x in success_times if x["elapsed"] is not None]
    
    print(f"Total successful calls analyzed: {len(times)}")
    print(f"Average time: {sum(times)/len(times):.2f} seconds")
    print(f"Maximum time: {max(times):.2f} seconds")
    print(f"Minimum time: {min(times):.2f} seconds")
    
    print("\nLongest 5 calls:")
    longest = sorted(success_times, key=lambda x: x["elapsed"] or 0, reverse=True)[:5]
    for item in longest:
        print(f"- {item['node']}: {item['elapsed']}s (generated {item['chars']} chars)")

if __name__ == "__main__":
    analyze_llm_times()
