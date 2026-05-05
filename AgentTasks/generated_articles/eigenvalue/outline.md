```markdown
# Eigenvalue

## 1. Scope: What This Article Explains  
This article explains **eigenvalues** as scalars that describe how certain vectors are stretched or compressed by linear transformations. It connects eigenvalues to physical systems like vibrations, rotations, and quantum states, emphasizing their role in simplifying complex interactions.

---

## 2. Out of Scope: What This Article Does *Not* Explain  
- Advanced linear algebra (e.g., eigenvalue algorithms, generalized eigenvectors)  
- Quantum mechanics specifics (e.g., operators, measurement postulates)  
- Non-linear systems or eigenvalues in non-square matrices  

---

## 3. Prerequisite Concepts  
- **Vectors** (as arrows with direction and magnitude)  
- **Linear transformations** (e.g., rotations, stretches, projections)  
- **Matrices** (as tools to represent transformations)  
- **Basic physics systems** (e.g., forces, oscillations, rotations)  

---

## 4. Core Intuition  
Eigenvalues are **scaling factors** that tell you how much a vector is stretched or squashed when a transformation is applied—*without changing its direction*. Think of them as "special magnification levels" for specific directions in space.  
- **Example**: A rubber band stretched uniformly in one direction has an eigenvalue of 2 (doubling length) for that direction.  
- **Physical analogy**: A spinning top’s axis of rotation has an eigenvalue of 1 (no stretching) under rotational symmetry.  

---

## 5. Suggested Descriptive Names with Standard Terms in Braces  
- **Direction-specific scale {eigenvalue}**  
- **Stability factor {eigenvalue}** (in systems like pendulums)  
- **Transformation anchor {eigenvalue}** (for vectors that resist rotation/stretching)  
- **Resonance multiplier {eigenvalue}** (in vibrating systems)  

---

## 6. Common Misconceptions to Avoid  
- ❌ "Eigenvalues only apply to matrices."  
  → Eigenvalues apply to *linear operators* (matrices are a common representation).  
- ❌ "Eigenvalues are always real numbers."  
  → Eigenvalues can be complex (e.g., rotational systems) or zero (e.g., degenerate states).  
- ❌ "Eigenvectors are the same as eigenvalues."  
  → Eigenvectors are the directions; eigenvalues are the scaling factors.  

---

## 7. Section-by-Section Outline  
### **Section 1: What Is an Eigenvalue?**  
- Define eigenvalues as "scaling factors" for vectors under transformations.  
- Use a rubber band example: stretching a vector without rotating it.  
- Introduce the equation: **A·v = λ·v** (explain symbols in plain language).  

### **Section 2: Eigenvalues in Physics**  
- **Vibrations**: Eigenvalues determine natural frequencies (e.g., a guitar string’s modes).  
- **Rotations**: Eigenvalues describe axes of symmetry (e.g., a spinning top’s axis).  
- **Quantum systems**: Eigenvalues correspond to measurable outcomes (e.g., energy levels).  

### **Section 3: Finding Eigenvalues**  
- Simplified steps:  
  1. Subtract λ from the transformation matrix.  
  2. Solve for λ where the determinant is zero.  
- Use a 2x2 matrix example (e.g., stretching a grid).  

### **Section 4: Why Eigenvalues Matter**  
- Simplify complex systems by focusing on "special directions" (e.g., principal axes).  
- Connect to real-world applications: stress analysis, image compression, quantum mechanics.  

---

## 8. Optional Diagram Ideas  
- **Diagram 1**: A vector being stretched by a matrix, showing eigenvectors (arrows) and eigenvalues (labels).  
- **Diagram 2**: A spinning top with labeled eigenvalue 1 for its rotation axis.  
- **Diagram 3**: A grid transformed by a matrix, highlighting eigenvectors (unchanged direction).  

---

## 9. Optional Minimal Math  
- **Equation**: $ A \cdot \mathbf{v} = \lambda \cdot \mathbf{v} $  
  - **A**: Transformation (matrix or operator)  
  - **v**: Eigenvector (direction)  
  - **λ**: Eigenvalue (scaling factor)  
- **Example**: For a 2x2 matrix, solving $ \det(A - \lambda I) = 0 $ finds eigenvalues.  
- **Explanation**: The determinant equation ensures the transformation "fails" to stretch the vector, leaving it unchanged (except scaled).  

---  
``` 

This outline balances conceptual clarity with physical intuition, avoiding overwhelming math while grounding eigenvalues in relatable examples.