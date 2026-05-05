# Autonomous Local Research & Drafting Agent Setup

This document describes a practical setup for using a local Qwen3 model to draft, evaluate, and iteratively improve articles for the EasyPhysics wiki. The goal is not to create a fully autonomous publisher. The goal is to create a semi-autonomous editorial assistant that produces high-quality drafts, structured notes, claim lists, review artifacts, and revision suggestions for human editing.

The core use case is a concept-first physics wiki: articles should explain stable, accepted fundamental-physics concepts in accessible language, while preserving scientific rigor.

---

## 1. Core Philosophy

The system should support the heart of the EasyPhysics project:

* Teach the clean modern conceptual structure of physics first, not the historical path of discovery.
* Use standard physics accurately, but introduce jargon gently.
* Prefer intuitive teaching names with standard terms marked in braces, such as `space-occupier {fermion}` or `definite-answer state {eigenstate}`.
* Keep the braces as editorial markers so terms can be searched and standardized later.
* Avoid presenting physics as magic, spooky, or unknowable. When something is counterintuitive, explain the deeper structure that makes it lawful and understandable.
* Use analogies, diagrams, simple examples, and minimal math when helpful.
* When including math, explain what the math is doing in plain language.
* Prefer stable, accepted sources over novelty. Do not search for “latest explanations” unless the article is explicitly about a current/open research issue.

The workflow should generate useful editorial artifacts even when the draft is not yet publishable.

---

## 2. Recommended Technology Stack

### Local LLM: Qwen3 via Ollama

Use `qwen3:8b` as the local drafting and review model. It is strong enough to produce useful outlines, drafts, terminology candidates, and rubric-based reviews, while still being feasible on local hardware.

A larger model may improve quality, but the 8B model is a good starting point for throughput and experimentation.

### LLM Server: Ollama

Ollama is the easiest way to run local Qwen models and call them from Python through `langchain-ollama`.

Recommended base install:

```bash
ollama pull qwen3:8b
pip install langchain-ollama langchain-community duckduckgo-search pyyaml
```

### Orchestration: Simple Python Workflow First, LangGraph Later

LangGraph is useful for stateful, cyclic workflows. However, for the current EasyPhysics workflow, a plain Python script with durable per-article folders is easier to debug and more robust.

The article folder itself acts as the state machine.

LangGraph can be added later if the workflow becomes complex enough to need graph visualization, branch routing, or multi-agent state management.

### Search Tool

Use `DuckDuckGoSearchRun` for lightweight web search. Search is not the same thing as source verification, so the system should store search snippets as evidence candidates and then ask the model to compare claims against those snippets.

For physics articles, prefer stable searches such as:

```text
quantum superposition probability amplitude lecture notes
Noether theorem gauge symmetry university physics notes
Lagrangian mechanics least action textbook explanation
```

Avoid defaulting to:

```text
latest explanation of <topic>
```

unless the topic really deserves current-news treatment.

---

## 3. Article Directory Structure

Each article should get its own folder.

Example:

```text
generated_articles/
  quantum-superposition/
    article.yml
    outline.md
    draft.md
    final.mdx
    notes.md
    claims.json
    sources.json
    claim_checks.json
    term_candidates.json
    claim_extractor_raw.txt
    reviews/
      accessibility_round_001.json
      rigor_round_001.json
    history/
      draft_before_revision_2026-05-03_14-22-10.md
    logs/
      2026-05-03.log
      events_2026-05-03.jsonl
```

This is the most important architectural choice. The LLM should not have to remember the whole workflow. Every important step should leave a durable artifact.

---

## 4. Article State File

Each article should have an `article.yml` file.

Example:

```yaml
title: "Quantum superposition"
slug: "quantum-superposition"
status: "needs_revision"
finished: false
iteration_count: 3
accessibility_score: 8
rigor_score: 7
last_worked_on: "2026-05-03"
last_completed_pass: "2026-05-03_14-22-10"
needs:
  - accessibility_revision
  - rigor_revision
  - claim_review
current_draft: "draft.md"
```

The script can cycle through articles and skip anything with both:

```text
accessibility_score >= 9
rigor_score >= 9
```

This keeps scheduling simple.

---

## 5. Workflow Roles

The workflow should run one complete treatment of an article, save artifacts, then move on to the next article. It should not revise the same article forever in one pass.

Recommended roles:

### 1. Planner

Creates `outline.md`.

The outline should include:

* Scope
* Out-of-scope topics
* Prerequisites
* Core intuition
* Candidate intuitive names with standard terms in braces
* Common misconceptions
* Section-by-section outline
* Diagram ideas
* Optional minimal math

### 2. Writer

Creates or revises `draft.md`.

The writer should be the only truly required role. If the writer fails, the article pass should probably fail. If later roles fail, the article should still save the draft and continue as far as possible.

### 3. Term Collector

Creates or updates `term_candidates.json`.

Purpose: gather possible teaching names before the glossary is standardized.

Example:

```json
{
  "terms": [
    {
      "standard_term": "fermion",
      "candidate_name": "space-occupier",
      "context_quote": "space-occupier {fermion}",
      "usefulness": "Suggests why matter resists being stacked into the same state.",
      "risk": "Could imply fermions are tiny hard balls occupying literal volume."
    }
  ]
}
```

### 4. Claim Extractor

Creates `claims.json`.

This role identifies important scientific and explanatory claims that should be checked.

Example:

```json
{
  "claims": [
    {
      "id": "C001",
      "claim": "A Lagrangian summarizes a system's dynamics by assigning a quantity to each possible motion path.",
      "type": "definition",
      "importance": "high",
      "needs_external_check": true,
      "why_it_matter": "This is the article's central definition.",
      "suggested_search_query": "Lagrangian mechanics definition least action textbook explanation"
    }
  ]
}
```

Important: the extractor should never silently write an empty claim list just because JSON parsing failed. Save the raw output to `claim_extractor_raw.txt` and use fallback extraction if needed.

### 5. Source Finder

Creates or updates `sources.json`.

It should search claim-by-claim, not topic-by-topic. This produces better results than a broad query like “latest information on Lagrangian.”

### 6. Claim Checker

Creates `claim_checks.json`.

The claim checker should compare one claim, or a very small batch of claims, against the available search snippets.

Do not send all claims, all snippets, and the whole draft in one giant prompt. That is more likely to cause hangs and less likely to produce precise checks.

Example claim check:

```json
{
  "claim_checks": [
    {
      "id": "C001",
      "verdict": "mostly_supported",
      "severity": "low",
      "problem": "The wording is broadly correct but should clarify that the action, not the Lagrangian alone, is extremized.",
      "suggested_fix": "Say that the Lagrangian is integrated over time to form the action, and the physical path makes the action stationary.",
      "source_quality_note": "Search snippet appears consistent with standard mechanics references."
    }
  ],
  "summary": {
    "overall_claim_quality": "Partial claim check completed.",
    "unresolved_or_needs_qualification": 1,
    "highest_priority_fixes": [
      "Clarify that the action is what is extremized."
    ]
  }
}
```

### 7. Claim Revision

Revises `draft.md` only if there are serious claim-check issues.

### 8. Accessibility Judge

Creates `reviews/accessibility_round_###.json`.

Scores the article on a 1-10 accessibility rubric.

### 9. Rigor Judge

Creates `reviews/rigor_round_###.json`.

Scores the article on a 1-10 scientific rigor rubric.

### 10. Final MDX Writer

Creates `final.mdx` from `draft.md` plus frontmatter. This can be simple; exact MDX formatting can be cleaned up later.

---

## 6. Accessibility Rubric

Use a structured 1-10 rubric, not a vague PASS/FAIL.

```text
10 = Exceptional. A motivated high-schooler can follow the article's main arc without prior exposure. Jargon is introduced only after intuition. Examples are vivid. Math is explained as meaning, not just symbols. The article feels empowering and clear.

9 = Publishable with light human editing. The main idea is easy to follow; jargon is mostly controlled; analogies are helpful; sections flow logically; any math has a plain-language interpretation.

8 = Strong draft. Mostly clear, but has a few dense sections, unexplained terms, abrupt transitions, or analogies that need more setup.

7 = Useful but uneven. A motivated reader could learn from it, but several passages need simplification, clearer examples, or better sequencing.

6 = Borderline. The article contains useful explanations, but assumes too much background or uses too much jargon.

5 = Mixed. Some good paragraphs, but the structure or language would lose many target readers.

4 = Hard to follow. Mostly written for someone who already knows the subject.

3 = Very inaccessible. Dense, abstract, jargon-heavy, or poorly sequenced.

2 = Barely useful to the target audience.

1 = Fails the accessibility goal.
```

Accessibility judge priorities:

* Does the opening give the reader an intuitive foothold?
* Are standard terms introduced after meaning, not before?
* Are descriptive names useful rather than cutesy or misleading?
* Are analogies concrete and then carefully limited?
* Is any math explained in words?
* Does the article avoid “spooky/magic/weird” framing while still acknowledging counterintuitive ideas?
* Does each section make the next section easier?

---

## 7. Rigor Rubric

```text
10 = Exceptional. Scientifically accurate, well-qualified, and careful about analogy limits. No obvious misleading simplifications. Claims align with stable accepted physics.

9 = Publishable with light human editing. No major errors. A few details may need polishing, but the article is safe as an educational explanation.

8 = Strong draft. Mostly accurate but has minor imprecision, missing qualifications, or analogy risks.

7 = Useful but needs scientific review. Contains no catastrophic errors, but some claims are too loose, incomplete, or potentially misleading.

6 = Borderline. Several important corrections or qualifications are needed.

5 = Mixed. The article has valuable explanations but also significant inaccuracies or misleading framings.

4 = Scientifically weak. Multiple substantial errors or serious conceptual muddling.

3 = Very unreliable. The reader would likely learn incorrect physics.

2 = Mostly wrong or confused.

1 = Fails the rigor goal.
```

Rigor judge priorities:

* Are definitions compatible with standard physics?
* Are analogies technically safe, with their limits stated when necessary?
* Are quantum concepts distinguished correctly: amplitude vs probability, superposition vs ignorance, measurement vs ordinary looking, phase vs probability?
* Are field/particle/wave descriptions accurate enough for a beginner article?
* Are conservation, symmetry, force, energy, mass, and spin statements properly qualified?
* Does the article avoid replacing historical jargon with new misleading jargon?
* Are open questions distinguished from settled explanations?

---

## 8. Robustness and Failure Handling

The workflow should be fail-soft.

Recommended rule:

```text
Required role: writer
Optional roles: planner, term_collector, claim_extractor, source_finder, claim_checker, claim_revision, accessibility_judge, rigor_judge
```

If an optional role fails, log it and keep going. A mediocre draft plus review artifacts is more useful than losing the whole pass.

### Timeout Wrapper

Local model calls can sometimes hang rather than throw an exception, especially with long prompts or unstable GPU backends. Run each LLM call in a child process and terminate it if it exceeds a timeout.

Recommended starting values:

```python
LLM_OPTIONS = {
    "temperature": 0.25,
    "top_p": 0.85,
    "num_ctx": 8192,
    "num_predict": 2048,
    "num_batch": 32,
}

LLM_TIMEOUT_SECONDS = 8 * 60
LLM_MAX_RETRIES = 0
```

Why no retries during debugging? Because a stuck call can cost many minutes, and retrying the same backend state often repeats the failure. Once the system is stable, a single retry may be reasonable.

### Per-Node Output Caps

Some roles should produce short JSON, not long essays.

```python
NODE_OPTION_OVERRIDES = {
    "term_collector": {"num_predict": 768},
    "claim_extractor": {"num_predict": 1024},
    "claim_checker": {"num_predict": 768},
    "accessibility_judge": {"num_predict": 1024},
    "rigor_judge": {"num_predict": 1024},
}
```

### Smaller Claim Checking

Use smaller claim-check calls:

```python
MAX_CLAIMS_TO_SEARCH_PER_PASS = 2
MAX_SEARCH_RESULT_CHARS_PER_CLAIM = 1000
MAX_CONTEXT_CHARS = 24000
```

This is less ambitious per pass, but much more reliable.

---

## 9. Arc A750 / Ollama Stability Notes

On an Intel Arc A750, the main practical issue is not always raw VRAM capacity. Ollama may detect both the Arc GPU and the integrated Intel GPU, then count the iGPU’s shared memory as available GPU memory. This can lead Ollama to choose a context size that is too aggressive for stable use.

Symptoms seen in practice:

* The model “flatlines” and never returns.
* A large claim-checker prompt times out.
* Later smaller calls also time out, suggesting the server-side runner is stuck.
* Ollama server logs show GPU discovery problems or repeated runner starts.

Recommended debugging environment variables before starting Ollama:

```powershell
$env:OLLAMA_CONTEXT_LENGTH="8192"
$env:OLLAMA_NUM_PARALLEL="1"
$env:OLLAMA_KEEP_ALIVE="0"
$env:OLLAMA_DEBUG="1"
```

If Ollama is using both the iGPU and Arc A750, try forcing the Vulkan-visible device:

```powershell
$env:GGML_VK_VISIBLE_DEVICES="1"
```

If that does not select the Arc GPU, try:

```powershell
$env:GGML_VK_VISIBLE_DEVICES="0"
```

Then quit Ollama from the tray and restart it from the same PowerShell session:

```powershell
& "$env:LOCALAPPDATA\Programs\Ollama\ollama app.exe"
```

Check the server log at:

```powershell
explorer $env:LOCALAPPDATA\Ollama
```

Look for:

* `OLLAMA_CONTEXT_LENGTH`
* `KvSize`
* `BatchSize`
* `Vulkan0` / `Vulkan1`
* `failure during GPU discovery`
* `unable to refresh free memory`
* long `500` responses from `/api/chat`

The goal is to avoid accidental 32k context allocation and avoid splitting the model across the iGPU and the Arc A750 if that proves unstable.

---

## 10. Debug Logging

Every LLM call should log:

* Node name
* Prompt character count
* Approximate token count
* Response character count
* LLM options
* Start time
* End time
* Elapsed seconds
* Failure reason

Write two kinds of logs:

```text
logs/YYYY-MM-DD.log
logs/events_YYYY-MM-DD.jsonl
```

The JSONL event log is especially useful for finding patterns like:

```text
claim_checker always times out above ~5k approximate tokens
term_collector times out only after a previous claim_checker timeout
writer fails only when revising a long previous draft
```

Make sure JSONL writes a newline after each event:

```python
f.write(json.dumps(event, ensure_ascii=False) + "\n")
```

---

## 11. Common Implementation Pitfalls

### Silent JSON Parse Failures

If a JSON role returns malformed JSON, do not silently use an empty fallback.

Bad pattern:

```python
data = parse_json_loose(raw, {"claims": []})
claims = data.get("claims", [])
write_json(p.claims, {"claims": claims})
```

Better pattern:

* Save raw output to a file.
* Log the parse failure.
* Accept multiple plausible shapes, such as top-level lists or alternative keys.
* Use deterministic fallback extraction if the LLM output is unusable.

### Accidental `"/n"` Instead of `"\n"`

This is wrong:

```python
system = PROJECT_BRIEF + "/n" + NOMENCLATURE_GUIDE
```

This is correct:

```python
system = PROJECT_BRIEF + "\n\n" + NOMENCLATURE_GUIDE
```

### Newlines Converted Into Literal Line Breaks Inside Strings

This causes syntax errors:

```python
f.write("
" + "=" * 80 + "
")
```

This is correct:

```python
f.write("\n" + "=" * 80 + "\n")
```

### Overly Large Claim-Checker Prompts

Do not combine:

```text
all claims + all snippets + full draft
```

into one prompt. Use one claim or a small batch of claims.

---

## 12. Minimal Workflow Pseudocode

```python
def run_one_article_cycle(topic):
    p, state = load_article_state(topic)

    if article_is_passing(state):
        return state

    planner_role(p, state)              # optional
    writer_role(p, state)               # required
    term_collector_role(p, state)       # optional
    claim_extractor_role(p, state)      # optional, but should fall back
    source_finder_role(p, state)        # optional
    claim_checker_role(p, state)        # optional, small batches
    claim_revision_role(p, state)       # optional
    accessibility_judge_role(p, state)  # optional
    rigor_judge_role(p, state)          # optional
    final_mdx_role(p, state)

    update_article_status(p, state)
    return state
```

---

## 13. Recommended Next Improvements

### Add a Stable Glossary Source of Truth

For now, the system can generate creative candidate names. Later, create a controlled glossary file:

```yaml
fermion:
  preferred_name: "space-occupier"
  allowed_aliases:
    - "state-excluding particle"
  discouraged_names:
    - "solid particle"
  warning: "Avoid implying that fermions are tiny hard balls."
```

Then the writer can use the glossary as a source of truth.

### Add a Misconception Ledger

Create a project-level file such as:

```yaml
quantum_superposition:
  misconception: "Superposition means ordinary ignorance about which state the particle is really in."
  correction: "Superposition means the quantum state is built from multiple basis components with amplitudes and phases."

uncertainty_principle:
  misconception: "Uncertainty is mainly caused by bad instruments or disturbing the particle."
  correction: "A sharply localized wave necessarily contains a spread of wavelengths/momenta."
```

The rigor judge can check drafts against this ledger.

### Add Article Type Templates

Different content types need different structures:

* Glossary entry
* Concept article
* Lesson
* Mathematical tool article
* Misconception article
* Open question article

### Add Manual Review Notes

Keep `notes.md` in every article folder. The human editor can add article-specific feedback, and the next run can use it.

---

## 14. Summary

The best architecture is not a single “infinite research loop.” It is a durable editorial workflow:

```text
article folder → outline → draft → terms → claims → sources → claim checks → revision → accessibility score → rigor score → final.mdx
```

Each pass should leave behind useful artifacts, even if the draft is not finished.

The most important practical lessons so far:

* Use per-article folders.
* Make the writer required, but make most other roles fail-soft.
* Do claim checking in small batches.
* Save raw LLM output for JSON-producing roles.
* Use rubrics, not vague PASS/FAIL checks.
* Keep context and batch sizes conservative on Arc A750.
* Treat the local LLM as an editorial assistant, not an autonomous publisher.
