# Self-Legending Fractal Matrix (FIM) – Zero-to-One Demo

This repository hosts a **minimal, self-contained** demonstration of a **2D pivot-based Fractal Identity Matrix (FIM)** that is:

1. **Self-Legending**: The final map is its own explanation (each pivot is labeled; sub-block boundaries are explicit).
2. **Driven by an LLM as “Reasoning Electricity”**: The LLM handles:
   - **Data mock** (e.g. generating category embeddings or adjacency).
   - **Pivot logic** (ranking relationships among categories).
   - **Interpretability** (final explanation of HPC savings or skip factor).
3. **Estimates HPC Savings**: For each query, we measure how many sub-blocks are skipped in the fractal-sorted matrix—translating directly into a simplified HPC cost reduction.

---

## Overview

The core approach implements a **symmetrical** pivot-based 2D sorting:
1. We have an \\( n \\times n \\) **symmetric** matrix of relationships among \\( n \\) categories.
2. We pick an **origin cell** \\((r, c)\\), swap that to \\((1,1)\\) by row & column swaps.
3. We **sort** the submatrix \\((2..n, 2..n)\\) by the pivot’s first column in descending order, doing symmetrical row/col operations.
4. We find a boundary \\(k\\) marking the sub-block of significant weights.
5. We **recursively** apply the same procedure in the leftover submatrix \\((k+1..n, k+1..n)\\).
6. Once fully sorted, the diagonal sub-blocks hold “clusters” of high adjacency, smaller sub-sub-blocks inside—**fractal** self-similarity emerges.

**Result**: A **fractal-sorted** matrix that both **reveals** hierarchical structure *and* provides large skip factors for queries, enabling interpretability and HPC cost savings.

---

## Requirements

1. **Symmetric Matrix** of Size \\( n \\times n \\):
   - The LLM can **mock** adjacency values or we can store them from a pre-defined set.
   - Each row/column label is a “category” (like `Dog1`, `Cat2`, etc.).
2. **Pivot Sorting** (2D):
   - Must keep row–column swaps symmetrical. (Swapping row i with row j means also swapping column i with column j).
   - Must track “block boundaries” after each pivot step.
3. **LLM** as the Ranking / Reasoning Engine:
   - The LLM decides the relative adjacency if needed (“Which row is bigger relative to pivot?”).
   - The LLM also produces an interpretability text for HPC skip factor at query time.
4. **No Dynamic Insert** (for zero-to-one simplicity):
   - We can re-run the pivot sort each time we change data if needed, but the minimal version has static data.
5. **HPC Cost**:
   - We define a skip factor as the fraction of sub-blocks or columns not visited during query resolution. HPC cost is \\(1 - \text{skipFactor}\\).
   - The LLM can produce final statements about how many sub-blocks were “skipped,” thus saving energy.

---

## Quick Algorithm Sketch

### 1. Start with an \\( n\\times n \\) Matrix
- Let the LLM or some mock function fill out `matrix[i][j]` (where `i, j = 0..n-1`) with symmetric adjacency weights.
  
### 2. Pick an “Origin” Cell, Move to \\((1,1)\\)
- Usually, we pick the cell \\((start, start)\\) or we pick a random cell inside the sub-block. 
- **Swap rows** \\((r, start)\\) and **swap columns** \\((c, start)\\) so that pivot cell is now at top-left of the sub-block.

### 3. Sort the Submatrix by Pivot’s First Column
- Sort rows \\((start+1..end)\\) in descending order of adjacency to the pivot. 
- Also sort columns \\((start+1..end)\\) the same way for symmetry.

### 4. Find Boundary \\(k\\)
- Identify the last row in which adjacency to pivot exceeds a threshold. This defines sub-block \\((start+1..k)\\). 

### 5. Recurse
- Recursively pivot-sort sub-block \\((k+1..end)\\).

### 6. Output & Self-Legend
- We store each pivot with a short label, e.g. “PivotDoc(3) at row/col 3, block boundary = k.” 
- The final list of sub-block boundaries or row/column order is the **“self-legending map.”**

---

## File Stubs

### `fimsort.py`

```python
class FractalSymSorter:
    def __init__(self, matrix, row_labels=None):
        """
        matrix: n x n symmetric adjacency (list of lists)
        row_labels: optional labels for each row/col
        """
        self.matrix = matrix
        self.n = len(matrix)
        self.row_order = list(range(self.n))
        self.col_order = list(range(self.n))
        self.blocks = []
        self.row_labels = row_labels or [f"Cat{i}" for i in range(self.n)]

    def fractal_sort_2d(self, start=0, end=None):
        # Implementation of pivot-based symmetrical row/col sorting
        # stores sub-block boundaries in self.blocks
        ...

    def show_map(self):
        # print final row_order, col_order, sub-block boundaries
        # interpret it as "self-legending"
        ...


demo_llm.py
python
Copy
Edit
class MockLLM:
    """
    Simple placeholder that can:
    1) Generate adjacency or doc strings
    2) Provide interpretive text
    3) Possibly decide which pivot is bigger, if needed
    """
    def generate_text(self, prompt):
        # Return a mock or simple text
        pass
main_demo.py
python
Copy
Edit
def main():
    llm = MockLLM()
    # Step1: generate adjacency
    matrix = generate_mock_matrix(llm, size=5)
    sorter = FractalSymSorter(matrix)
    sorter.fractal_sort_2d()
    sorter.show_map()

    # Step2: a query "What about dogs vs cats?"
    # HPC skip factor: let's assume we skip certain sub-blocks
    visited_count = 3
    total_blocks = len(sorter.blocks)
    skip_factor = (total_blocks - visited_count)/total_blocks
    cost = 1.0 - skip_factor

    final_expl = llm.generate_text(
       f"Explain HPC cost {cost:.2f} using sub-blocks {sorter.blocks}"
    )
    print("Query HPC cost:", cost)
    print("Interpretation:", final_expl)
HPC Skip Factor / Energy Savings
During queries:

We see how many sub-blocks are visited vs. total.
If we skip 80% of sub-blocks, HPC cost is 0.2.
This mock metric suffices to show how fractal skipping yields big “energy” gains.
Interpretability: The final structure is “the map,” so the system can produce a narrative:

"We pivoted around Cat3, found sub-block (Cat1, Cat2) had high adjacency, ignoring (Cat4, Cat5). HPC cost=0.3."

Final Notes & Limitations
For this zero-to-one example, we do not handle dynamic insertions or merges.
We do a simplified symmetrical row/col pivot approach with one threshold-based boundary.
The map is “self-legending” because each pivot + boundary is labeled in blocks, and that data is used to explain HPC cost.
The entire approach is small enough to illustrate synergy with an LLM, while letting the user see interpretability & cost benefits in plain text.
That’s enough to demonstrate the 2D FIM pivot sorting, “map is legend,” HPC skip factor, and LLM synergy in a single minimal codebase. Enjoy building your zero-to-one self-contained fractal matrix demo!

