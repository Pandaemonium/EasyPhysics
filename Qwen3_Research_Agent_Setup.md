# Autonomous Local Research & Drafting Agent Setup

Building a continuous, self-correcting research agent requires a system that can plan, execute web searches, synthesize information, evaluate its own work, and loop back if information is missing. 

The optimal stack for this is **Qwen3** (for fast, local inference) orchestrated by **LangGraph** (for stateful, cyclical agent logic).

---

## 1. The Technology Stack

*   **Local LLM (Qwen3):** Qwen3 has recently made waves in the open-source community because its Mixture-of-Experts (MoE) variants (like `qwen3:30b-a3b`) are incredibly fast [6]. Despite being a 30B model, it only uses a subset of parameters (e.g., 3B) per token, making it run at blazing speeds on standard hardware while rivaling proprietary models [6]. 
*   **LLM Server (Ollama):** The easiest way to serve Qwen3 locally. It exposes an OpenAI-compatible API that LangGraph can communicate with [15].
*   **Orchestrator (LangGraph):** Unlike standard LangChain which runs linearly, LangGraph models applications as state machines (graphs) [1]. It allows for persistent memory, cyclic loops, and conditional decision-making [1], [3]. This is essential for continuous research where an agent might need to loop back to the internet if a draft is incomplete [14].
*   **Search Tools:** `Tavily` or `DuckDuckGoSearchRun` to provide the LLM with real-time web access.

---

## 2. Graph Architecture

We will design our LangGraph workflow as a "Research Team" [7], [8]. The graph requires a **State** to pass information between nodes, and several specialized **Nodes** (Agents):

1.  **Planner:** Takes the user's prompt and generates a structured outline/research plan [7], [9].
2.  **Searcher:** Receives the plan, generates targeted web queries, executes the web search tools, and appends the raw data to the state [14].
3.  **Writer:** Synthesizes the raw search results into a clean markdown article [7], [9].
4.  **Critic/Reviewer:** Evaluates the draft against the original plan [7], [8]. If the draft is missing context or has hallucinations, it routes the graph *back* to the Searcher [8]. If the draft is complete, it ends the graph.

---

## 3. Implementation Guide

### Step 1: Environment Setup
Ensure you have Ollama installed, then pull the Qwen3 model [6], [15]:
```bash
ollama pull qwen3:8b-q4_K_M  # Or qwen3:30b-a3b if your machine has ~16GB+ VRAM
ollama serve

pip install langgraph langchain-ollama langchain-community duckduckgo-search
```

### Step 2: Define the Graph State
LangGraph uses a `TypedDict` to maintain the memory of the workflow [7], [10].
```python
from typing import TypedDict, List

class ResearchState(TypedDict):
    topic: str
    plan: str
    search_results: List[str]
    draft: str
    feedback: str
    revisions: int
```

### Step 3: Define the Agent Nodes
Initialize the local Qwen3 model and write the functions that will act as your graph nodes [15].
```python
from langchain_ollama import ChatOllama
from langchain_community.tools import DuckDuckGoSearchRun

llm = ChatOllama(model="qwen3:8b-q4_K_M", temperature=0)
search_tool = DuckDuckGoSearchRun()

def planner_node(state: ResearchState):
    prompt = f"Create a 3-point research plan for the topic: {state['topic']}"
    plan = llm.invoke(prompt).content
    return {"plan": plan, "search_results": [], "revisions": 0}

def searcher_node(state: ResearchState):
    # Use the plan to search the web
    query = f"Latest information on: {state['topic']}"
    results = search_tool.invoke(query)
    current_results = state.get("search_results", [])
    current_results.append(results)
    return {"search_results": current_results}

def writer_node(state: ResearchState):
    prompt = f"Write an article based on this plan:\n{state['plan']}\n\nUsing this data:\n{state['search_results']}"
    draft = llm.invoke(prompt).content
    return {"draft": draft}

def critic_node(state: ResearchState):
    prompt = f"Review this draft for completeness against the topic '{state['topic']}'. Draft: {state['draft']}. Does it need more research? Reply only with YES or NO."
    feedback = llm.invoke(prompt).content.strip().upper()
    revisions = state.get("revisions", 0) + 1
    return {"feedback": feedback, "revisions": revisions}
```

### Step 4: Map the Graph and Define the Loop
Connect the nodes and implement the conditional logic [1], [7] that allows for continuous research.
```python
from langgraph.graph import StateGraph, END

# 1. Initialize Graph
workflow = StateGraph(ResearchState)

# 2. Add Nodes
workflow.add_node("planner", planner_node)
workflow.add_node("searcher", searcher_node)
workflow.add_node("writer", writer_node)
workflow.add_node("critic", critic_node)

# 3. Define Conditional Routing
def should_continue(state: ResearchState):
    # Stop if it passes review or if we've hit a revision limit
    if "YES" in state["feedback"] and state["revisions"] < 3:
        return "search_more"
    return "finish"

# 4. Connect the Edges
workflow.set_entry_point("planner")
workflow.add_edge("planner", "searcher")
workflow.add_edge("searcher", "writer")
workflow.add_edge("writer", "critic")

workflow.add_conditional_edges(
    "critic",
    should_continue,
    {
        "search_more": "searcher",  # Loops back to do more research!
        "finish": END
    }
)

# 5. Compile and Run
app = workflow.compile()

final_state = app.invoke({"topic": "The economic impact of autonomous AI agents"})
print(final_state["draft"])
```

This architecture acts as an infinite-while loop of continuous self-improvement until the "Critic" is satisfied or the revision limit is reached, giving you high-quality AI articles entirely completely offline and locally!