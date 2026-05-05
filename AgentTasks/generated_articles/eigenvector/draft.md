# Eigenvector

## The core idea  
Eigenvectors are **direction-keepers** {eigenvectors}: they only stretch, shrink, or reverse direction when a **linear transformation** is applied. Think of them as "special directions" where a transformation acts simply, like pushing or pulling along a line. For example, a negative eigenvalue would flip the direction (e.g., compressing a spring in the opposite direction), while a positive eigenvalue would scale it without flipping.

> **Note**: This concept applies specifically to **linear transformations** (e.g., scaling, rotation, shearing), not all types of transformations. Non-linear transformations (e.g., bending, folding) do not preserve the eigenvector property.

---

## Why this matters  
Eigenvectors simplify complex transformations by isolating directions where the transformation behaves predictably. This concept is foundational in physics (e.g., quantum states {eigenstates}), engineering, computer graphics, and data science.  

For authoritative confirmation, see *Gilbert Strang's "Introduction to Linear Algebra"* (2009), which explains how eigenvectors capture the "invariant directions" of linear transformations.  

---

## The simple picture  
[Diagram idea: A spring stretched along its axis (eigenvector) vs. twisted (non-eigenvector)]  
Imagine stretching a spring along its length. The spring’s direction stays the same—it only stretches. This is an eigenvector: the transformation (stretching) acts like a "slider" along that line. If the spring were compressed (negative eigenvalue), its direction would reverse, but it would still remain aligned with the axis.

---

## The more precise picture  
Eigenvectors satisfy the equation:  
$$
A \cdot \mathbf{v} = \lambda \cdot \mathbf{v}
$$  
- **A**: The linear transformation (e.g., a matrix).  
- **v**: The eigenvector (direction-keeper).  
- **λ**: The scaling factor (how much the vector stretches/shrinks, or reverses direction if negative).  

**Example**:  
If A is a matrix that stretches space by 2x along the x-axis, then the vector (1, 0) is an eigenvector with λ = 2.  
```  
A = [[2, 0],  
     [0, 1]]  
v = [1, 0]  
A·v = [2, 0] = 2·[1, 0] → λ = 2  
```  
If A instead flips the x-axis (λ = -1), the vector (1, 0) would become (-1, 0), reversing direction while staying aligned with the axis.

---

## Common misconceptions  
- ❌ "Eigenvectors are only for matrices."  
  → Eigenvectors apply to **any linear transformation**, not just matrices. Matrices are just one way to represent linear transformations (see Strang, 2009).  
- ❌ "All vectors are eigenvectors."  
  → Only specific vectors (direction-keepers) satisfy the eigenvector condition.  
- ❌ "Eigenvectors change direction slightly."  
  → They **only** scale or reverse direction; they never rotate unpredictably.  

---

## How this connects to the rest of physics  
- **Quantum mechanics**: Quantum states {eigenstates} are eigenvectors of operators (e.g., energy or momentum).  
- **Engineering**: Eigenvectors describe modes of vibration in structures.  
- **Computer graphics**: They simplify 3D transformations (e.g., rotating objects around an axis).  
- **Data science**: Principal component analysis (PCA) uses eigenvectors to find patterns in data.  

---

## Recap  
- Eigenvectors are **direction-keepers** {eigenvectors} that only scale or reverse direction under a **linear transformation**.  
- They simplify complex systems by isolating predictable directions.  
- Key equation: $ A \cdot \mathbf{v} = \lambda \cdot \mathbf{v} $.  
- Avoid common traps: eigenvectors aren’t limited to matrices, not all vectors are eigenvectors, and they only scale or reverse direction—never rotate unpredictably.  

> **Further reading**: For deeper exploration of linear transformations and eigenvectors, see *Gilbert Strang's "Introduction to Linear Algebra"* (2009) or *David Lay's "Linear Algebra and Its Applications"* (2018).