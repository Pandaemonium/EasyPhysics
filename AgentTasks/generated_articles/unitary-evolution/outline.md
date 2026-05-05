```markdown
# Unitary Evolution

## 1. Scope
This article explains **unitary evolution** as the lawful way quantum states change over time, preserving total probability. It focuses on:
- The role of unitary operators in time evolution
- How quantum systems differ from classical systems in this regard
- The mathematical structure that ensures probability conservation

## 2. Out of Scope
This article will **not** explain:
- The Schrödinger equation itself (saved for a later article)
- Measurement collapse or decoherence (covered in separate articles)
- Speculative topics like quantum gravity or interpretations of quantum mechanics

## 3. Prerequisite Concepts
- Quantum states as vectors in Hilbert space
- Superposition and probability amplitudes
- Operators and eigenstates
- Basic familiarity with complex numbers

## 4. Core Intuition
Quantum systems evolve in a way that **preserves total probability**. Unlike classical systems, where information can be lost (e.g., a particle hitting a wall), quantum evolution is **reversible and deterministic**. Think of it as a rotation in a complex space: the "length" of the state vector (which represents total probability) never changes.

## 5. Suggested Descriptive Names
- **Probability-preserving transformation** {unitary transformation}
- **Time-translation symmetry** {unitary evolution}
- **Reversible state flow** {unitary operator}
- **Conserved probability path** {unitary dynamics}

## 6. Common Misconceptions to Avoid
- ❌ "Unitary evolution is just a mathematical trick" – It's a fundamental law of nature.
- ❌ "Quantum systems behave like classical systems" – Probabilities are conserved, not deterministic.
- ❌ "Unitary evolution is irreversible" – Unitary operators have inverse counterparts (unlike dissipative processes).

## 7. Section-by-Section Outline
### 7.1 What is Unitary Evolution?
- Introduce as the "quantum version of time evolution"
- Contrast with classical systems (e.g., a ball rolling downhill)

### 7.2 The Unitary Operator
- Explain how states evolve via U|ψ⟩ = |ψ(t)⟩
- Emphasize that U preserves the "length" of the state vector (probability conservation)

### 7.3 The Hamiltonian Connection
- Link to energy (H) via U = e^{-iHt/ħ}
- Simplify: "Energy dictates the direction of evolution"

### 7.4 Conservation of Probability
- Show math: ⟨ψ(t)|ψ(t)⟩ = 1 always
- Contrast with classical systems where probabilities can "leak"

### 7.5 Implications for Reversibility
- Explain how unitary evolution allows "undoing" time
- Contrast with irreversible processes in thermodynamics

## 8. Optional Diagram Ideas
- **Hilbert Space Rotation**: A vector (state) rotating in a complex plane, with arrows showing unitary transformations.
- **Probability Conservation**: A pie chart showing total probability remains 100% over time.
- **Classical vs Quantum Paths**: Side-by-side diagrams showing how classical systems can lose probability, while quantum systems preserve it.

## 9. Optional Minimal Math
- **Unitary Operator**:  
  `|ψ(t)⟩ = U|ψ(0)⟩`  
  *This means the state at time t is the original state transformed by U.*

- **Probability Conservation**:  
  `⟨ψ(t)|ψ(t)⟩ = ⟨ψ(0)|U†U|ψ(0)⟩ = ⟨ψ(0)|ψ(0)⟩ = 1`  
  *U†U = I (identity) ensures the "length" of the state vector never changes.*

- **Hamiltonian Link**:  
  `U = e^{-iHt/ħ}`  
  *Energy (H) determines the "speed" and direction of evolution.*
```