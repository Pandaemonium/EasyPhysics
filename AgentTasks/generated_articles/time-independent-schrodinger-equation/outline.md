# Time-independent Schrödinger equation  

---

## 1. Scope  
This article explains the **Time-independent Schrödinger equation (TISE)**, a cornerstone of quantum mechanics. It describes how to find **stationary states** (energy eigenstates) for systems with time-independent potentials. The article covers:  
- The mathematical form of the TISE.  
- How it separates spatial and temporal parts of the wavefunction.  
- Examples like the particle in a box and harmonic oscillator.  
- The physical meaning of energy eigenvalues and stationary states.  

---

## 2. Out of Scope  
This article does **not** explain:  
- The **time-dependent Schrödinger equation** (TDSE).  
- Time evolution of quantum states beyond stationary states.  
- Advanced systems like the hydrogen atom or spin.  
- Philosophical interpretations of quantum mechanics (e.g., wavefunction collapse).  

---

## 3. Prerequisite Concepts  
- **Wavefunction** {probability amplitude}: A mathematical description of a quantum system.  
- **Probability distribution**: The square of the wavefunction gives the likelihood of finding a particle.  
- **Energy eigenstates**: States where the energy is well-defined.  
- **Separation of variables**: A technique to split complex equations into simpler parts.  
- **Partial differential equations** (basic familiarity).  

---

## 4. Core Intuition  
The **Time-independent Schrödinger equation** is a simplified version of the full Schrödinger equation, used when the potential energy doesn’t change over time. It helps find **stationary states**—situations where the probability distribution of a particle doesn’t change, only its phase. These states correspond to **quantized energy levels**, like electrons in an atom.  

**Key idea**: The TISE lets us solve for the allowed energies and shapes of these stationary states, which are the "energy snapshots" of a quantum system.  

---

## 5. Suggested Descriptive Names with Standard Terms in Braces  
- **Energy Snapshot Equation** {Time-independent Schrödinger equation}  
- **Stationary State** {Energy eigenstate}  
- **Probability Map** {Wavefunction}  
- **Energy Level** {Quantized energy}  
- **Phase Arrow** {Complex phase}  

---

## 6. Common Misconceptions to Avoid  
- ❌ **"The TISE is a static equation."**  
  → It’s still a differential equation; it describes how the wavefunction behaves in space, not time.  
- ❌ **"Stationary states are static."**  
  → The wavefunction’s **phase** still changes over time, but the **probability distribution** remains fixed.  
- ❌ **"The wavefunction is a physical wave."**  
  → It’s a **probability amplitude**, not a physical entity.  

---

## 7. Section-by-Section Outline  
### **1. Introduction to the Time-independent Schrödinger Equation**  
- Why we need a simplified version of the Schrödinger equation.  
- What "time-independent" means in this context.  

### **2. Deriving the TISE from the General Schrödinger Equation**  
- How to separate time and space parts using separation of variables.  
- The mathematical form of the TISE:  
  $$ -\frac{\hbar^2}{2m} \nabla^2 \psi + V(x)\psi = E\psi $$  
  → Explain each term: kinetic energy, potential energy, and energy eigenvalue.  

### **3. Stationary States and Energy Eigenstates**  
- What makes a state "stationary" (probability distribution doesn’t change).  
- How energy eigenvalues arise from solving the TISE.  

### **4. Solving the TISE: Examples**  
- **Particle in a box**: Boundary conditions and quantized energy levels.  
- **Harmonic oscillator**: Oscillatory wavefunctions and equally spaced energy levels.  

### **5. Physical Meaning of Solutions**  
- How energy eigenvalues relate to observable quantities (e.g., electron transitions).  
- The role of boundary conditions in shaping wavefunctions.  

### **6. Applications and Key Takeaways**  
- Why the TISE is essential for understanding atomic and molecular structure.  
- Summary of how it bridges classical and quantum descriptions of energy.  

---

## 8. Optional Diagram Ideas  
- **Diagram 1**: Separation of variables in the Schrödinger equation (time vs. space).  
- **Diagram 2**: Particle in a box with wavefunctions and energy levels.  
- **Diagram 3**: Probability distribution for a stationary state (e.g., particle in a box).  
- **Diagram 4**: Comparison of time-dependent vs. time-independent solutions.  

---

## 9. Optional Minimal Math  
- **TISE equation**:  
  $$ -\frac{\hbar^2}{2m} \nabla^2 \psi + V(x)\psi = E\psi $$  
  → Explain that this equation finds the **allowed energies** $ E $ and corresponding **wavefunctions** $ \psi $.  
- **Boundary conditions**: For a particle in a box, $ \psi(0) = \psi(L) = 0 $, leading to quantized energy levels.  
- **Energy quantization**:  
  $$ E_n = \frac{n^2 \pi^2 \hbar^2}{2mL^2} $$  
  → Show how energy depends on quantum number $ n $ and physical parameters.  

--- 

This outline balances conceptual clarity with mathematical rigor, avoiding pitfalls while building on foundational knowledge.