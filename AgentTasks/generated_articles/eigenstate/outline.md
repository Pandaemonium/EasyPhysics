```markdown
# Eigenstate

## 1. Scope
This article explains the concept of an **eigenstate** in quantum mechanics. It focuses on:
- What an eigenstate is: a state where a measurement yields a definite result.
- How eigenstates relate to physical observables (e.g., position, momentum, energy).
- Examples of eigenstates in simple systems (e.g., spin-½ particles, energy levels).
- The role of eigenstates in quantum measurements and superposition.

## 2. Out of Scope
This article does **not** explain:
- The mathematical formalism of operators, eigenvalue equations, or Dirac notation.
- Advanced topics like entanglement, quantum gates, or time evolution.
- Historical context or speculative interpretations (e.g., Copenhagen vs. Many-Worlds).

## 3. Prerequisite Concepts
- **Quantum states**: Systems exist in abstract states (e.g., wavefunctions).
- **Measurement**: Observing a system collapses its state to a specific outcome.
- **Superposition**: Systems can be in multiple states at once.
- **Probability**: Outcomes of measurements are probabilistic.

## 4. Core Intuition
An **eigenstate** is a "definite-answer state" {eigenstate} — a state where measuring a specific property (e.g., energy, spin) will always give the same result. Think of it as a "ready-to-measure" state: if a system is in an eigenstate of an observable, the measurement will "lock in" that value. Most quantum states are **superpositions** of eigenstates, meaning they’re "prepared" to yield multiple possible outcomes until measured.

## 5. Suggested Descriptive Names with Standard Terms in Braces
- **Definite-answer state** {eigenstate}
- **Measurement-ready state** {eigenstate}
- **Certainty state** {eigenstate}
- **Observable-specific state** {eigenstate}
- **Outcome-guarantee state** {eigenstate}

## 6. Common Misconceptions to Avoid
- ❌ "All quantum states are eigenstates": Most states are superpositions of eigenstates.
- ❌ "Eigenstates are only for position/momentum": Eigenstates exist for any observable (e.g., energy, spin).
- ❌ "Eigenstates are 'real' states": Eigenstates are mathematical tools to describe measurement outcomes, not physical entities.
- ❌ "Eigenstates are static": Eigenstates can evolve over time if the system’s Hamiltonian changes.

## 7. Section-by-Section Outline
### 1. Introduction: Quantum States and Measurement
- Recap: Systems exist in abstract states; measurements yield probabilistic outcomes.
- Introduce the idea of "definite-answer" states.

### 2. What is an Eigenstate?
- Definition: A state where measuring an observable yields a **guaranteed result**.
- Example: A spin-½ particle in the "up" state is an eigenstate of the spin operator.

### 3. Eigenstates and Observables
- Link eigenstates to physical properties (e.g., energy levels of an atom).
- Explain how eigenstates are tied to operators (e.g., Hamiltonian for energy).

### 4. Superposition vs. Eigenstates
- Contrast: A superposition is a mix of eigenstates; measurements "collapse" to one.
- Example: A photon in a superposition of vertical/horizontal polarization.

### 5. Why Eigenstates Matter
- They are the "building blocks" for quantum predictions.
- Without eigenstates, we couldn’t calculate probabilities of measurement outcomes.

### 6. Common Pitfalls and Clarifications
- Address misconceptions about eigenstates being "real" or "static".
- Emphasize that eigenstates are **observable-specific** (e.g., spin vs. position).

## 8. Optional Diagram Ideas
- **Diagram 1**: A quantum system in a superposition of two eigenstates (e.g., spin-up and spin-down), with a measurement "collapsing" it to one.
- **Diagram 2**: A particle in a box with energy eigenstates (quantum well), showing how measurements yield discrete energy levels.
- **Diagram 3**: A Venn diagram linking eigenstates, observables, and measurement outcomes.

## 9. Optional Minimal Math
- **Equation**:  
  $ \hat{A} | \psi \rangle = a | \psi \rangle $  
  - **Explanation**: If an operator $ \hat{A} $ (e.g., energy) acts on a state $ | \psi \rangle $ and gives the same state scaled by a value $ a $, then $ | \psi \rangle $ is an eigenstate of $ \hat{A} $ with eigenvalue $ a $.
- **Probability**:  
  If a system is in a superposition $ | \psi \rangle = c_1 | \phi_1 \rangle + c_2 | \phi_2 \rangle $, the probability of measuring $ \phi_1 $ is $ |c_1|^2 $.

```