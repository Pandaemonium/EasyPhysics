import os
from pathlib import Path

def analyze_ollama_logs():
    # Default path for Ollama server logs on Windows
    log_path = Path(os.path.expanduser("~")) / "AppData" / "Local" / "Ollama" / "server.log"
    
    if not log_path.exists():
        print(f"Log file not found at: {log_path}")
        return
        
    # Keywords commonly associated with Intel Arc / SYCL / LLM crashes
    keywords = ["error", "fatal", "panic", "sycl", "level zero", "ze_", "device lost", "timeout", "exception"]
    
    print(f"Analyzing {log_path} for GPU/crash related keywords...\n")
    
    matches = []
    try:
        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
            
        # Scan the last 10,000 lines to catch recent issues without scanning gigabytes of history
        for line in lines[-10000:]:
            if any(k in line.lower() for k in keywords):
                matches.append(line.strip())
                
        if not matches:
            print("No obvious errors or SYCL/Level Zero issues found in the recent logs.")
        else:
            print(f"Found {len(matches)} suspicious lines in the recent log tail. Here are the last 20:\n")
            for match in matches[-20:]:
                print(match)
                
    except Exception as e:
        print(f"Error reading log file: {e}")

if __name__ == "__main__":
    analyze_ollama_logs()
