import os
import re
import operator
from typing import TypedDict, List, Annotated
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_community.tools import DuckDuckGoSearchRun
from langgraph.graph import StateGraph, END

# ==========================================
# 1. Setup & Configuration
# ==========================================
# Optimized parameters for Qwen3-8B in non-thinking instruct mode
llm = ChatOllama(model="qwen3:8b", temperature=0.3, top_p=0.8, num_ctx=16384, num_predict=2048, num_batch=64)
search_tool = DuckDuckGoSearchRun()

OUTPUT_DIR = r"c:\Projects\EasyPhysics\AgentTasks\generated_articles"
os.makedirs(OUTPUT_DIR, exist_ok=True)

LOG_DIR = r"c:\Projects\EasyPhysics\AgentTasks\logs"
os.makedirs(LOG_DIR, exist_ok=True)

def slugify(text: str) -> str:
    return re.sub(r'[\W_]+', '-', text.lower()).strip('-')

def log_interaction(topic: str, node_name: str, instruction: str, response: str):
    filepath = os.path.join(LOG_DIR, f"{slugify(topic)}.log")
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(f"\n{'='*40}\n")
        f.write(f"NODE: {node_name.upper()}\n")
        f.write(f"{'='*40}\n")
        f.write(f"INSTRUCTION/PROMPT:\n{instruction}\n\n")
        f.write(f"MODEL/TOOL RESPONSE:\n{response}\n")

# The definitive rules engine for your multi-agent system
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

# ==========================================
# 2. Graph State & Nodes
# ==========================================
class ResearchState(TypedDict):
    topic: str
    plan: str
    # operator.add ensures lists are merged safely during parallel node execution
    search_results: Annotated[List[str], operator.add]
    draft: str
    accuracy_feedback: str
    accessibility_feedback: str
    revisions: int

def planner_node(state: ResearchState):
    prompt = f"Create a 3-point structural outline for an accessible high school physics wiki article about: {state['topic']}."
    print("  -> [planner] Generating outline...")
    messages = [SystemMessage(content=STYLE_GUIDE), HumanMessage(content=prompt)]
    plan = llm.invoke(messages).content
    log_interaction(state['topic'], "planner", prompt, plan)
    return {"plan": plan, "search_results": [], "revisions": 0}

def searcher_node(state: ResearchState):
    query = f"Latest physics explanations of: {state['topic']}"
    print(f"  -> [searcher] Searching DuckDuckGo for: '{query}'...")
    try:
        results = search_tool.invoke(query)
        results = results[:2000] # Truncate to prevent local context window explosion
    except Exception:
        results = "Search failed."
    print("  -> [searcher] Search complete.")
    log_interaction(state['topic'], "searcher", f"Query: {query}", results)
    return {"search_results": [results]}

def writer_node(state: ResearchState):
    feedback_context = ""
    if state.get('revisions', 0) > 0:
        feedback_context = f"\n\nCRITIC FEEDBACK TO IMPLEMENT:\nAccuracy: {state['accuracy_feedback']}\nAccessibility: {state['accessibility_feedback']}"

    prompt = f"Write an engaging wiki article based on this plan:\n{state['plan']}\n\nUsing this data:\n{state['search_results']}{feedback_context}\n\nWrite in Markdown."
    
    print("  -> [writer] Drafting article (this may take a minute)...")
    messages = [SystemMessage(content=STYLE_GUIDE), HumanMessage(content=prompt)]
    draft = llm.invoke(messages).content
    log_interaction(state['topic'], "writer", prompt, draft)
    return {"draft": draft}

def accuracy_critic_node(state: ResearchState):
    prompt = f"Review this draft for scientific accuracy:\n{state['draft']}\n\nAre the first-principles of physics (like symmetry, conservation, and inertial resistance vs viscous drag) accurate? If perfect, reply EXACTLY with 'PASS'. If not, provide short, specific correction instructions."
    print("  -> [accuracy_critic] Evaluating scientific accuracy...")
    messages = [SystemMessage(content=STYLE_GUIDE), HumanMessage(content=prompt)]
    feedback = llm.invoke(messages).content
    log_interaction(state['topic'], "accuracy_critic", prompt, feedback)
    return {"accuracy_feedback": feedback}

def accessibility_critic_node(state: ResearchState):
    prompt = f"Review this draft against our pedagogical philosophy:\n{state['draft']}\n\nIs the tone empowering, intuitive, and free of 'mysterious/spooky' framing? Does it use everyday analogies instead of complex math? If perfect, reply EXACTLY with 'PASS'. If not, provide brief suggestions on how to make it more straightforward."
    print("  -> [accessibility_critic] Evaluating pedagogy and tone...")
    messages = [SystemMessage(content=STYLE_GUIDE), HumanMessage(content=prompt)]
    feedback = llm.invoke(messages).content
    log_interaction(state['topic'], "accessibility_critic", prompt, feedback)
    return {"accessibility_feedback": feedback}

def router_node(state: ResearchState):
    # This node joins the parallel critics and increments the revision counter
    return {"revisions": state.get("revisions", 0) + 1}

def should_continue(state: ResearchState):
    # Check if both critics approved the draft
    accuracy_pass = "PASS" in state.get("accuracy_feedback", "").upper()
    accessibility_pass = "PASS" in state.get("accessibility_feedback", "").upper()

    if accuracy_pass and accessibility_pass:
        print("  -> [router] Draft passed all checks. Finishing.")
        return "finish"
    elif state["revisions"] >= 3: # Circuit breaker to prevent infinite loops
        print(f"  -> [router] Max revisions reached ({state['revisions']}). Finishing.")
        return "finish"
    else:
        print(f"  -> [router] Critics requested changes. Looping back to writer (Revision {state['revisions']})...")
        return "revise"

# ==========================================
# 3. Build the LangGraph Workflow
# ==========================================
workflow = StateGraph(ResearchState)
workflow.add_node("planner", planner_node)
workflow.add_node("searcher", searcher_node)
workflow.add_node("writer", writer_node)
workflow.add_node("accuracy_critic", accuracy_critic_node)
workflow.add_node("accessibility_critic", accessibility_critic_node)
workflow.add_node("router", router_node)

workflow.set_entry_point("planner")
workflow.add_edge("planner", "searcher")
workflow.add_edge("searcher", "writer")

# Sequential Execution: Local LLMs struggle with parallel requests, so we run critics one after the other
workflow.add_edge("writer", "accuracy_critic")
workflow.add_edge("accuracy_critic", "accessibility_critic")
workflow.add_edge("accessibility_critic", "router")

# Loop back to the WRITER (not the searcher) to fix mistakes
workflow.add_conditional_edges("router", should_continue, {"revise": "writer", "finish": END})

app = workflow.compile()

# ==========================================
# 4. Batch Execution Logic
# ==========================================
def main():
    topics_to_generate = [

 "The pixelation of energy: why light comes in chunks",
 "Wave-particle duality explained as localized ripples",
 "Quantum superposition analogized as acoustic chords on a guitar string",
 "The Heisenberg Uncertainty Principle explained through wave mechanics, not observer effect",
 "Quantum entanglement as correlated waves, removing the 'spooky action' myth",
 "The double-slit experiment without the magic or mystery",
 "Quantum tunneling: how waves naturally bleed through barriers",
 "The Pauli Exclusion Principle: why you can't walk through walls",
 "Quantum spin: intrinsic angular momentum without the spinning top analogy",
 "Decoherence: why quantum overlap disappears in the macroscopic world",
 "The Feynman path integral: adding up every possible wave history",
 "Bell's Theorem: the geometric proof against hidden variables",
 "Quantum Zeno effect: how interaction freezes a wave's evolution",
    ]

    print(f"Starting batch generation for {len(topics_to_generate)} articles...")
    for topic in topics_to_generate:
        print(f"\n--- Generating article: {topic} ---")
        
        # Initialize a fresh log file for this run
        log_filepath = os.path.join(LOG_DIR, f"{slugify(topic)}.log")
        with open(log_filepath, "w", encoding="utf-8") as log_file:
            log_file.write(f"--- Execution Log for: {topic} ---\n")

        final_draft = ""
        # Stream the events so we can watch the agents work
        for event in app.stream({"topic": topic}, {"recursion_limit": 15}):
            for node_name, node_state in event.items():
                print(f"[Agent Update] Finished task: {node_name}")
                if "draft" in node_state:
                    final_draft = node_state["draft"]

        filepath = os.path.join(OUTPUT_DIR, f"{slugify(topic)}.mdx")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"---\ntitle: {topic}\n---\n\n{final_draft}")
            
        print(f"Saved completed draft to: {filepath}")

if __name__ == "__main__":
    main()