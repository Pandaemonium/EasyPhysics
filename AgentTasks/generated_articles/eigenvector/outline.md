```markdown
# Eigenvector

## 1. Scope  
This article explains **eigenvectors** as special vectors that only change in magnitude (not direction) when a linear transformation is applied. It focuses on their conceptual role in physics and math, using intuitive examples and minimal math to build understanding.

---

## 2. Out of Scope  
- **Advanced linear algebra** (e.g., eigenvalues in abstract spaces, generalized eigenvectors).  
- **Quantum mechanics** (though eigenvectors are central there, this article avoids that context).  
- **Matrix diagonalization** or computational methods for finding eigenvectors.  

---

## 3. Prerequisite Concepts  
- **Vectors** (as arrows with direction and magnitude).  
- **Linear transformations** (e.g., stretching, rotating, shearing).  
- **Matrices** (as tools to represent transformations).  

---

## 4. Core Intuition  
Eigenvectors are **direction-keepers** {eigenvectors}:  
- When a transformation (like stretching or rotating) is applied, most vectors change direction.  
- Eigenvectors are the rare vectors that **only scale** (stretch/shrink) without rotating.  
- Think of them as "special directions" where the transformation acts simply: "pushing" or "pulling" along that line.  

---

## 5. Suggested Descriptive Names with Standard Terms in Braces  
| Intuitive Name              | Standard Term     |  
|----------------------------|-------------------|  
| Direction-keeper {eigenvector} |                   |  
| Scale-only vector {eigenvector} |                   |  
| Transformation-axis {eigenvector} |                   |  
| Unrotated vector {eigenvector} |                   |  

---

## 6. Common Misconceptions to Avoid  
- ❌ "Eigenvectors are only for matrices."  
  → Eigenvectors apply to **any linear transformation**, not just matrices.  
- ❌ "All vectors are eigenvectors."  
  → Only specific vectors (direction-keepers) satisfy the eigenvector condition.  
- ❌ "Eigenvectors change direction slightly."  
  → They **never** change direction; they only scale.  

---

## 7. Section-by-Section Outline  
### **Section 1: What is an Eigenvector?**  
- Introduce the idea of "direction-keepers" using a simple example (e.g., stretching a rubber band).  
- Define eigenvectors as vectors that only scale under a transformation.  

### **Section 2: The "Scale-Only" Rule**  
- Explain the mathematical condition: **A·v = λ·v** (where A is the transformation, v is the eigenvector, and λ is the scaling factor).  
- Use a diagram to show how eigenvectors don’t rotate.  

### **Section 3: Real-World Examples**  
- **Spring stretching**: The direction of the spring’s stretch is an eigenvector.  
- **Rotation around an axis**: The axis itself is an eigenvector (no rotation).  
- **Diagonalizing matrices**: Eigenvectors simplify complex transformations.  

### **Section 4: Why Eigenvectors Matter**  
- Link to physics: Quantum states {eigenstates} are eigenvectors of operators.  
- Mention applications in engineering, computer graphics, and data science.  

---

## 8. Optional Diagram Ideas  
1. **Transformation vs. Eigenvector**:  
   - A vector (arrow) transformed by a matrix (e.g., shearing).  
   - Highlight the eigenvector (same direction, different length).  
2. **Spring Example**:  
   - A spring stretched along its axis (eigenvector) vs. twisted (non-eigenvector).  
3. **Rotation Axis**:  
   - A 3D object rotating around an axis (eigenvector) vs. a vector off-axis.  

---

## 9. Optional Minimal Math  
**Equation**:  
$$
A \cdot \mathbf{v} = \lambda \cdot \mathbf{v}
$$  
- **A**: The transformation (matrix).  
- **v**: The eigenvector (direction-keeper).  
- **λ**: The scaling factor (how much the vector stretches/shrinks).  
- **Explanation**: This equation says the transformation A only scales v, without changing its direction.  

**Example**:  
If A is a matrix that stretches space by 2x along the x-axis, then the vector (1, 0) is an eigenvector with λ = 2.  
```  
A = [[2, 0],  
     [0, 1]]  
v = [1, 0]  
A·v = [2, 0] = 2·[1, 0] → λ = 2  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```  
```