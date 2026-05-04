import os
import re
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_community.tools import DuckDuckGoSearchRun

# ==========================================
# 1. Setup & Configuration
# ==========================================
MODELS = [
    "qwen3:8b",
    "gemma2:9b-instruct-q4_0",
    "llama3.1:8b-instruct-q4_K_M"
]

search_tool = DuckDuckGoSearchRun()

OUTPUT_DIR = r"c:\Projects\EasyPhysics\AgentTasks\benchmark_results"
os.makedirs(OUTPUT_DIR, exist_ok=True)

STYLE_GUIDE = """
# CORE PEDAGOGICAL PHILOSOPHY
You are a visionary physics educator writing an accessible curriculum. Your mission is to demystify the universe.
- Demystify: Physics is NOT mysterious, strange, or magical. It is straightforward, mechanical, and intuitive.
- No "Spookiness": Never frame quantum mechanics or relativity as "weird." Explain them as natural, logical consequences of underlying geometry and wave mechanics.
- Analogies over Equations: Use everyday analogies (e.g., guitar strings for superposition, pixels for quantum granularity). Make the reader feel smart.
- Concept over History: Explain HOW the universe works right now based on symmetry and geometry. Skip historical narratives of who discovered what and when.
- Tone: Engaging, empowering, and accessible to a 9th-grader, without infantilizing them.

# LEXICON & FORMATTING RULES
1. Translate standard jargon into intuitive terms using our custom React component: <Term intuitive="Space-Occupier" jargon="Fermion" definition="..." />
2. Preferred Lexicon: Fermion -> Space-Occupier, Boson -> Messenger, Quark -> Bound Fractional-Charger, Weak Force -> Identity-Shifting Interaction, Higgs Field -> Inertial Drag Field.
3. MDX Requirement: Always include `import Term from '@site/src/components/Term';` at the top of your markdown files.
"""

def slugify(text: str) -> str:
    return re.sub(r'[\W_]+', '-', text.lower()).strip('-')

def main():
    # We will test all three models on this single conceptual topic
    topic = "The invariant interval: the one measurement everyone in the universe agrees on"
    
    print(f"Starting model benchmark for topic: '{topic}'\n")
    
    for model_name in MODELS:
        print(f"--- Testing Model: {model_name} ---")
        try:
            # Initialize the specific model
            llm = ChatOllama(model=model_name, temperature=0.7, top_p=0.8, num_ctx=4096)
            
            # Phase 1: Planner
            print("  -> [planner] Generating outline...")
            planner_prompt = f"Create a 3-point structural outline for an accessible high school physics wiki article about: {topic}."
            messages = [SystemMessage(content=STYLE_GUIDE), HumanMessage(content=planner_prompt)]
            plan = llm.invoke(messages).content
            
            # Phase 2: Searcher
            print("  -> [searcher] Searching DuckDuckGo...")
            query = f"Latest physics explanations of: {topic}"
            try:
                search_results = search_tool.invoke(query)[:2000]
            except Exception:
                search_results = "Search failed."
                
            # Phase 3: Writer
            print("  -> [writer] Drafting article...")
            writer_prompt = f"Write an engaging wiki article based on this plan:\n{plan}\n\nUsing this data:\n{search_results}\n\nWrite in Markdown."
            messages = [SystemMessage(content=STYLE_GUIDE), HumanMessage(content=writer_prompt)]
            draft = llm.invoke(messages).content
            
            # Save to a model-specific folder
            filepath = os.path.join(OUTPUT_DIR, f"{slugify(model_name)}_{slugify(topic)}.mdx")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"---\ntitle: {topic} ({model_name})\n---\n\n{draft}")
                
            print(f"  -> Saved draft to: {filepath}\n")
            
        except Exception as e:
            print(f"  -> Error running {model_name}: {e}. (Did you pull the model via Ollama?)\n")

if __name__ == "__main__":
    main()