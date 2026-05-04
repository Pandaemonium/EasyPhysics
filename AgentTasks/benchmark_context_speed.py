import time
import os
import asyncio
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage

def get_repo_text():
    # Define a few paths to your actual project files to build real context
    files_to_read = [
        r"C:\Projects\EasyPhysics\Accessible Physics Project Plan.md",
        r"c:\Projects\EasyPhysics\Docusaurus_Architecture_Plan.md",
        r"c:\Projects\EasyPhysics\AgentTasks\wiki_topics_backlog.md",

    ]
    
    repo_text = ""
    for filepath in files_to_read:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                repo_text += content + "\n\n"
                print(f"[Debug] Read {len(content)} characters from {os.path.basename(filepath)}")
        except Exception as e:
            print(f"[Debug] Could not read {filepath}: {e}")
            
    # Fallback just in case
    if not repo_text.strip():
        print("[Debug] Falling back to default short text.")
        repo_text = "The universe is a vast geometric structure. "
        
    return repo_text

def main():
    model_name = "qwen3:8b"
    # Testing a range of context sizes to find where VRAM spilling occurs
    context_sizes = [512*8, 512*9, 512*10]
    
    print(f"Starting Speed vs Context Size Benchmark for {model_name}")
    print("=" * 60)
    
    # Load the actual text from your repository to form the base context
    base_text = get_repo_text()

    for ctx in context_sizes:
        print(f"\nTesting context size: {ctx} tokens...")
        try:
            # Calculate roughly how many characters we need to fill the context.
            print("  -> [Debug] Constructing massive prompt...")
            target_prompt_chars = int((ctx - 1000) * 3.5)
            
            # Stuff the prompt with the repo text until it reaches the target size
            massive_context = base_text * (target_prompt_chars // len(base_text) + 1)
            massive_context = massive_context[:target_prompt_chars]
            


            # Initialize model with the specific context size limit
            print(f"  -> [Debug] Initializing ChatOllama with num_ctx={ctx}...")
            llm = ChatOllama(
                model=model_name,
                temperature=0.2,
                num_ctx=ctx,
                num_predict=512,   # important: do not leave output unbounded
                keep_alive=0,      # unload after each run to avoid retained runners / fragmentation
            )

            prompt = (
                "/no_think\n\n"
                + massive_context
                + "\n\nBased on the text above, write a 2-paragraph summary of the pedagogical goals and architecture."
            )
            # Append the actual instruction at the very end
            print(f"  -> [Debug] Prompt constructed. Total characters: {len(prompt)}")
            
            print("  -> [Debug] Sending request to Ollama! Watch Task Manager now...")
            start_time = time.time()
            
            try:
                # Using asyncio to enforce a timeout in case of silent hangs
                response = asyncio.run(asyncio.wait_for(
                    llm.ainvoke([HumanMessage(content=prompt)]),
                    timeout=600  # 10-minute timeout
                ))
            except asyncio.TimeoutError:
                print("\n  -> [Error] Request timed out after 10 minutes. Ollama likely hung due to VRAM limits.")
                break
            end_time = time.time()
            print("  -> [Debug] Response received successfully!")
            
            # Extract the exact metrics from the Ollama engine
            metadata = response.response_metadata
            eval_count = metadata.get('eval_count', 0)
            eval_duration_ns = metadata.get('eval_duration', 0)
            prompt_eval_count = metadata.get('prompt_eval_count', 0)
            prompt_eval_duration_ns = metadata.get('prompt_eval_duration', 0)
            
            if eval_duration_ns > 0:
                # Ollama returns durations in nanoseconds
                tps = (eval_count / eval_duration_ns) * 1e9
            else:
                # Fallback calculation if metadata is missing
                total_time = end_time - start_time
                tps = eval_count / total_time if total_time > 0 else 0
                
            if prompt_eval_duration_ns > 0:
                prompt_tps = (prompt_eval_count / prompt_eval_duration_ns) * 1e9
            else:
                prompt_tps = 0

            print(f"  -> Prompt Size: {prompt_eval_count} tokens")
            print(f"  -> Prompt Reading Speed: {prompt_tps:.2f} tokens/second")
            print(f"  -> Generated: {eval_count} tokens")
            print(f"  -> Generation Speed: {tps:.2f} tokens/second")
            print(f"  -> Total Time: {end_time - start_time:.2f} seconds")
            
        except Exception as e:
            print(f"  -> FAILED at {ctx} context size.")
            print(f"  -> Reason: {e}\n  -> (You likely ran out of VRAM at this size!)")
            break # Stop testing larger contexts if this one crashed

if __name__ == "__main__":
    main()