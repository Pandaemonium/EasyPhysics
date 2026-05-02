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
llm = ChatOllama(model="qwen3:8b-q4_K_M", temperature=0.7, top_p=0.8)
search_tool = DuckDuckGoSearchRun()

OUTPUT_DIR = r"c:\Projects\EasyPhysics\AgentTasks\generated_articles"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# The definitive rules engine for your multi-agent system
STYLE_GUIDE = """
CRITICAL LEXICON & STYLE RULES:
1. Never use 'fermion' or 'boson' as primary nouns. Use 'Space-Occupier' and 'Force-Carrier/Messenger'.
2. Never use 'quark' or 'gluon' as primary nouns. Use 'Bound Fractional-Charger' and 'Strong-Force Carrier'.
3. Never use 'weak force'. Use 'Identity-Shifting Interaction' or 'Transmutation Force'.
4. Never use 'Higgs Field' without clarifying it is an 'Inertial Drag Field' (it creates inertial resistance, NOT viscous friction).
5. The FIRST usage of an intuitive term MUST be followed by the historical jargon in parentheses. E.g., Space-Occupier (fermion).
6. Avoid the historical narrative and chronological discovery dates.
7. Ground all explanations in symmetry, geometry, and Noether's Theorem. No complex math.
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
    plan = llm.invoke().content
    return {"plan": plan, "search_results":, "revisions": 0}

def searcher_node(state: ResearchState):
    query = f"Latest physics explanations of: {state['topic']}"
    try:
        results = search_tool.invoke(query)
        results = results[:2000] # Truncate to prevent local context window explosion
    except Exception:
        results = "Search failed."
    return {"search_results": [results]}

def writer_node(state: ResearchState):
    feedback_context = ""
    if state.get('revisions', 0) > 0:
        feedback_context = f"\n\nCRITIC FEEDBACK TO IMPLEMENT:\nAccuracy: {state['accuracy_feedback']}\nAccessibility: {state['accessibility_feedback']}"

    prompt = f"Write an engaging wiki article based on this plan:\n{state['plan']}\n\nUsing this data:\n{state['search_results']}{feedback_context}\n\nWrite in Markdown."
    
    draft = llm.invoke().content
    return {"draft": draft}

def accuracy_critic_node(state: ResearchState):
    prompt = f"Review this draft for scientific accuracy:\n{state['draft']}\n\nAre the first-principles of physics (like symmetry, conservation, and inertial resistance vs viscous drag) accurate? If perfect, reply EXACTLY with 'PASS'. If not, provide short, specific correction instructions."
    feedback = llm.invoke().content
    return {"accuracy_feedback": feedback}

def accessibility_critic_node(state: ResearchState):
    prompt = f"Review this draft against our lexicon:\n{state['draft']}\n\nDid the writer strictly follow the lexicon (e.g., using 'Space-Occupier' instead of 'fermion')? If perfect, reply EXACTLY with 'PASS'. If not, list the forbidden jargon used."
    feedback = llm.invoke().content
    return {"accessibility_feedback": feedback}

def router_node(state: ResearchState):
    # This node joins the parallel critics and increments the revision counter
    return {"revisions": state.get("revisions", 0) + 1}

def should_continue(state: ResearchState):
    # Check if both critics approved the draft
    accuracy_pass = "PASS" in state.get("accuracy_feedback", "").upper()
    accessibility_pass = "PASS" in state.get("accessibility_feedback", "").upper()

    if accuracy_pass and accessibility_pass:
        return "finish"
    elif state["revisions"] >= 3: # Circuit breaker to prevent infinite loops
        return "finish"
    else:
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

# Parallel Execution: Writer sends draft to BOTH critics simultaneously
workflow.add_edge("writer", "accuracy_critic")
workflow.add_edge("writer", "accessibility_critic")

# Both critics must finish before the router node executes
workflow.add_edge("accuracy_critic", "router")
workflow.add_edge("accessibility_critic", "router")

# Loop back to the WRITER (not the searcher) to fix mistakes
workflow.add_conditional_edges("router", should_continue, {"revise": "writer", "finish": END})

app = workflow.compile()

# ==========================================
# 4. Batch Execution Logic
# ==========================================
def slugify(text: str) -> str:
    return re.sub(r'+', '-', text.lower()).strip('-')

def main():
    topics_to_generate =

    print(f"Starting batch generation for {len(topics_to_generate)} articles...")
    for topic in topics_to_generate:
        print(f"\n--- Generating article: {topic} ---")
        final_state = app.invoke({"topic": topic}, {"recursion_limit": 15})
        
        filepath = os.path.join(OUTPUT_DIR, f"{slugify(topic)}.mdx")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"---\ntitle: {topic}\n---\n\n{final_state['draft']}")
            
        print(f"Saved completed draft to: {filepath}")

if __name__ == "__main__":
    main()