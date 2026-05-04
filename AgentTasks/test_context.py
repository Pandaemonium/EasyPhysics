import json
import os
import subprocess
import time
import urllib.request
import urllib.error

MODEL = "qwen3:8b"

FILES_TO_READ = [
    r"C:\Projects\EasyPhysics\Accessible Physics Project Plan.md",
    r"C:\Projects\EasyPhysics\Docusaurus_Architecture_Plan.md",
    r"C:\Projects\EasyPhysics\AgentTasks\wiki_topics_backlog.md",
]

def get_repo_text():
    repo_text = ""
    for filepath in FILES_TO_READ:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
                repo_text += content + "\n\n"
                print(f"[Debug] Read {len(content)} chars from {os.path.basename(filepath)}")
        except Exception as e:
            print(f"[Debug] Could not read {filepath}: {e}")
    return repo_text or "The universe is a vast geometric structure. "

def call_ollama(prompt, ctx):
    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "user",
                "content": prompt,
            }
        ],
        "think": False,
        "stream": False,
        "keep_alive": 0,
        "options": {
            "num_ctx": ctx,
            "num_predict": 256,
            "num_batch": 64,
            "temperature": 0.2,
        }
    }

    req = urllib.request.Request(
        "http://127.0.0.1:11434/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    
    

    try:
        with urllib.request.urlopen(req, timeout=900) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"[HTTP ERROR] {e.code} {e.reason}")
        print(body)
        raise

def main():
    base_text = get_repo_text()

    for ctx in [1024*16, 1024*20, 1024*24, 1024*28, 1024*32]:
        print(f"\n=== Testing num_ctx={ctx} ===")

        # Force unload before each run.
        subprocess.run(
            ["ollama", "stop", MODEL],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        time.sleep(5)

        target_prompt_chars = int((ctx - 1000) * 3.5)
        massive_context = base_text * (target_prompt_chars // len(base_text) + 1)
        massive_context = massive_context[:target_prompt_chars]

        prompt = (
            "/no_think\n\n"
            + massive_context
            + "\n\nBased on the text above, write a 2-paragraph summary of the pedagogical goals and architecture."
        )

        print(f"[Debug] Prompt chars: {len(prompt)}")
        start = time.time()

        try:
            result = call_ollama(prompt, ctx)
        except Exception as e:
            print(f"[ERROR] Failed at num_ctx={ctx}: {e}")
            break

        elapsed = time.time() - start
        msg = result.get("message", {}).get("content", "")
        print(f"[OK] Elapsed: {elapsed:.1f}s")
        print(f"[OK] Response chars: {len(msg)}")
        print(msg[:500])

if __name__ == "__main__":
    main()