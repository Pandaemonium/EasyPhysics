```markdown
# Projection

## 1. Scope  
This article explains **projection** as a way to find how much of one vector lies in a specific direction. It covers:  
- The definition of projection as a **vector component**  
- How to calculate projection using **trigonometry**  
- Applications in physics (e.g., force components, velocity in directions)  
- The relationship between projection and the **dot product**  

---

## 2. Out of Scope  
This article does **not** explain:  
- Projection in **quantum mechanics** (e.g., wavefunction projections)  
- **Multi-dimensional projections** (e.g., projecting 3D vectors onto planes)  
- **Linear algebra** formalisms (e.g., matrix projections)  
- **Projection in signal processing** or machine learning  

---

## 3. Prerequisite Concepts  
- **Vectors** (magnitude and direction)  
- **Trigonometry** (sine, cosine, right triangles)  
- **Coordinate systems** (axes, directions)  
- **Dot product** (optional, for advanced connections)  

---

## 4. Core Intuition  
Projection is like asking: *"How much of this vector is pointing in this specific direction?"*  
- Imagine shining a light perpendicular to a wall: the **shadow** of a vector on the wall is its projection.  
- The projection is a **vector** in the target direction, with magnitude depending on the angle between the original vector and the direction.  
- The **shortest path** to understanding is to think of projection as "how much of A is aligned with B?"  

---

## 5. Suggested Descriptive Names with Standard Terms in Braces  
- **Shadow on a wall {projection}**  
- **Vector component {projected vector}**  
- **Directional emphasis {direction cosine}**  
- **Alignment measure {dot product}**  

---

## 6. Common Misconceptions to Avoid  
- ❌ **Projection is the same as magnitude**: No! Projection is a vector, not just a number.  
- ❌ **Projection depends on the vector's total length**: Yes, but only indirectly—projection depends on the angle and the vector's magnitude.  
- ❌ **Projection is always positive**: No! If the angle is obtuse, the projection can be negative (indicating opposite direction).  
- ❌ **Projection is the same as the dot product**: The dot product is the projection **multiplied by the target vector's magnitude**.  

---

## 7. Section-by-Section Outline  
### **Section 1: What is Projection?**  
- Introduce the shadow analogy  
- Define projection as the "component of a vector in a specific direction"  
- Use diagrams: vector, direction, and shadow  

### **Section 2: Calculating Projection**  
- Use trigonometry: projection = |A|cosθ  
- Explain the right triangle analogy (adjacent side)  
- Formula: **proj_B A = |A|cosθ** {vector projection}  
- Optional: Link to dot product (A · B = |A||B|cosθ)  

### **Section 3: Applications in Physics**  
- Force components: e.g., pulling a box at an angle  
- Velocity in directions: e.g., projectile motion  
- Work done: W = F_parallel × distance  

### **Section 4: Projection vs. Dot Product**  
- Clarify: projection is a **vector**, dot product is a **scalar**  
- Formula comparison:  
  - proj_B A = (A · B / |B|²) × B {vector projection}  
  - A · B = |A||B|cosθ {dot product}  

---

## 8. Optional Diagram Ideas  
1. **Shadow on a wall**: A vector pointing at an angle, with its shadow (projection) on a wall perpendicular to the light source.  
2. **Right triangle**: Original vector as hypotenuse, projection as adjacent side, and perpendicular component as opposite side.  
3. **Coordinate system**: Vector A with its projection on the x-axis and y-axis.  
4. **Force diagram**: A force vector split into horizontal and vertical components.  

---

## 9. Optional Minimal Math  
- **Projection magnitude**:  
  $$
  |\text{proj}_B A| = |A| \cos\theta
  $$  
  *Explanation*: The length of the projection depends on the angle between A and B.  
- **Vector projection**:  
  $$
  \text{proj}_B A = \left( \frac{A \cdot B}{|B|^2} \right) B
  $$  
  *Explanation*: Scales the unit vector in B's direction by the dot product of A and B.  

``` 

This outline balances intuition, math, and applications while avoiding advanced topics. The shadow analogy and right-triangle diagrams make abstract concepts tangible.