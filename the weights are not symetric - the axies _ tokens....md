# Zero-to-One Demo: Self-Legending Fractal Identity Matrix (FIM) with LLM Synergy

This repository hosts a **minimal, self-contained** demonstration of a **2D pivot-based Fractal Identity Matrix (FIM)** that is:

1.  **Self-Legending**: The final map is its own explanation (each pivot is labeled; sub-block boundaries are explicit).
2.  **Driven by an LLM as “Reasoning Electricity”**: The LLM handles:
    *   **Data Mock** (e.g., generating category embeddings or adjacency).
    *   **Pivot logic** (ranking relationships among categories).
    *   **Interpretability** (final explanation of HPC savings or skip factor).
3.  **Estimates HPC Savings**: For each query, we measure how many sub-blocks are skipped in the fractal-sorted matrix—translating directly into a simplified HPC cost reduction.

## Overview

The core approach implements a **symmetrical** pivot-based 2D sorting:

1.  We have an \( n \times n \) **symmetric** matrix of relationships among \( n \) categories. (In this corrected version, we use a matrix where weights are not necessarily symmetrical, but the order of categories along rows and columns is kept symmetrical).
2.  We pick an **origin cell** \\((r, c)\\), and swap rows and columns to move it to \\((start, start)\\) by row & column swaps.
3.  We **sort** the submatrix \\((start+1..end, start+1..end)\\) by the pivot's first column in descending order, performing **symmetrical row/col operations**. This maintains the same categories along each axis.
4.  We find a boundary \\(k\\) marking the sub-block of significant weights.
5.  We **recursively** apply the same procedure in the leftover submatrix \\((k+1..end, k+1..end)\\).
6.  Once fully sorted, the diagonal sub-blocks hold “clusters” of high adjacency, smaller sub-sub-blocks inside—**fractal** self-similarity emerges.

**Result**: A **fractal-sorted** matrix that both **reveals** hierarchical structure *and* provides large skip factors for queries, enabling interpretability and HPC cost savings.

## Requirements

1.  **\( n \times n \) Matrix:**
    *   Rows and columns represent the same set of \( n \) categories.
    *   The LLM can **mock** adjacency values or they can be derived from embeddings.
    *   **Weights do not need to be symmetrical, but the order of categories along rows and columns is kept symmetrical.**
2.  **Pivot Sorting (2D):**
    *   **Symmetrical Swaps:** When rows are swapped, the corresponding columns *must* also be swapped to maintain the same category order on both axes.
    *   **Block Boundaries:** Track sub-block boundaries after each pivot step.
3.  **LLM** as the Ranking / Reasoning Engine:
    *   The LLM decides the relative adjacency if needed (“Which row is bigger relative to pivot?”).
    *   The LLM also produces an interpretability text for HPC skip factor at query time.
4.  **Static Data** (for zero-to-one simplicity):
    *   We can re-run the pivot sort each time we change data if needed, but the minimal version has static data.
5.  **HPC Cost**:
    *   We define a skip factor as the fraction of sub-blocks or columns *not* visited during query resolution. HPC cost is estimated as \\(1 - \text{skipFactor}\\).
    *   The LLM can produce final statements about how many sub-blocks were “skipped,” thus saving energy.

## Quick Algorithm Sketch

### 1. Start with an \( n \times n \) Matrix

*   Let the LLM or some mock function fill out `matrix[i][j]` (where `i, j = 0..n-1`) with values representing relationships between categories.

### 2. Pick an “Origin” Cell, Move to \((start, start)\)

*   Usually, we pick the cell \((start, start)\) or we pick a random cell inside the sub-block.
*   **Swap rows** \((r, start)\) and **swap columns** \((c, start)\) so that the pivot cell is now at the top-left of the sub-block.
*   **Crucially, maintain the row/column label correspondence.**

### 3. Sort the Submatrix by Pivot's First Column

*   Sort rows \(start+1..end\) in descending order of their values in the pivot column.
*   **Simultaneously, perform the *same swaps* on the columns** to maintain the symmetrical order of categories along both axes.

### 4. Find Boundary \(k\)

*   Identify the last row in which the value in the pivot column exceeds a threshold. This defines sub-block \(start+1..k\).

### 5. Recurse

*   Recursively apply steps 2-5 to the submatrix \(k+1..end, k+1..end\).

### 6. Output & Self-Legend

*   We store each pivot with a short label, e.g., “PivotDoc(3) at row/col 3, block boundary = k.”
*   The final list of sub-block boundaries or row/column order is the **“self-legending map.”**

## File Stubs

### `fimsort.py`

```python
class FractalSorter2D:
    def __init__(self, matrix, labels=None):
        """
        matrix: n x n adjacency matrix (list of lists) - weights NOT assumed to be symmetrical
        labels: labels for each row/col (must be the same for rows and cols)
        """
        self.matrix = matrix
        self.n = len(matrix)
        self.order = list(range(self.n))  # Keep a single order for both rows and cols
        self.blocks = []
        self.labels = labels or [f"Cat{i}" for i in range(self.n)]

    def fractal_sort_2d(self, start=0, end=None):
        """
        Pivot-based sorting with symmetrical row/col swaps to maintain the same category order.
        """
        if end is None:
            end = self.n
        if end - start <= 1:
            return

        # 1. Select pivot (e.g., (start, start))
        pivot = start

        # 2. Sort submatrix based on pivot column (descending order)
        # Use a key function that accesses the matrix using the current order
        def key_func(index):
            return self.matrix[self.order[index]][self.order[pivot]]

        sub_order = self.order[start + 1:end]
        sub_order.sort(key=key_func, reverse=True)
        self.order[start + 1:end] = sub_order

        # 3. Find boundary k (end of significant sub-block)
        k = self._find_boundary(start, end)

        # 4. Store sub-block boundary
        self.blocks.append((start, k))

        # 5. Recurse
        self.fractal_sort_2d(k + 1, end)

    def _find_boundary(self, start, end):
        """
        Finds the boundary k based on a threshold (simplified for demo).
        """
        k = start
        pivot_col = self.order[start]
        for idx in range(start + 1, end):
            if self.matrix[self.order[idx]][pivot_col] > 0.2:  # Example threshold
                k = idx
            else:
                break
        return k

    def _swap(self, i, j):
        """Swaps elements i and j in the order list."""
        self.order[i], self.order[j] = self.order[j], self.order[i]

    def show_map(self):
        """
        Prints the final order and block boundaries - the 'self-legending map'.
        """
        print(f"=== {self.label} ===")
        print("Order:", [self.labels[i] for i in self.order])
        print("Blocks:", [(self.order[s], self.order[e]) for s, e in self.blocks])

    def query(self, query_label):
        """
        Mock query processing:
          - Find blocks relevant to query_label
          - Estimate HPC cost based on skipped blocks
          - Generate an explanation using the LLM
        """
        relevant_blocks = []
        for start, end in self.blocks:
            block_labels = [self.labels[self.order[i]] for i in range(start, end + 1)]
            if query_label in block_labels:
                relevant_blocks.append((start, end))

        total_blocks = len(self.blocks)
        skip_factor = 1.0 - len(relevant_blocks) / total_blocks if total_blocks > 0 else 0
        cost = 1.0 - skip_factor

        explanation = self.llm.generate_text(
            f"Query: '{query_label}'. Based on the FIM structure, "
            f"I accessed blocks: {[(self.order[s], self.order[e]) for s, e in relevant_blocks]} "
            f"and skipped {total_blocks - len(relevant_blocks)} blocks. "
            f"The estimated HPC cost is {cost:.2f}."
        )

        return {
            "cost": cost,
            "explanation": explanation
        }

````

main_demo.py
```Python

def main():
    llm = MockLLM()

    # Example labels for the categories
    labels = ["Dog-Corgi", "Dog-Shepherd", "Cat-Persian", "Cat-Siamese", "Bird-Parrot"]

    # Generate the mock adjacency matrix
    matrix = llm.generate_mock_matrix(size=len(labels))

    # Initialize and sort the matrix
    sorter = FractalSorter2D(matrix, labels=labels)
    sorter.fractal_sort_2d()

    # Display the sorted matrix structure
    sorter.show_map()

    # Process a query
    query_result = sorter.query("Dog-Corgi")
    print("Query HPC cost:", query_result["cost"])
    print("Explanation:", query_result["explanation"])

```

HPC Skip Factor / Energy Savings
During queries:

We see how many sub-blocks are visited vs. total.
If we skip 80% of sub-blocks, HPC cost is 0.2.
This mock metric suffices to show how fractal skipping yields big “energy” gains.
Interpretability
The final structure is “the map,” so the system can produce a narrative:

"We pivoted around Cat-Siamese, found sub-block (Dog-Corgi, Dog-Shepherd) had high adjacency, ignoring (Cat-Persian, Bird-Parrot). HPC cost=0.3."

Final Notes & Limitations
For this zero-to-one example, we do not handle dynamic insertions or merges.
We do a simplified symmetrical row/col pivot approach with one threshold-based boundary.
The map is “self-legending” because each pivot + boundary is labeled in blocks, and that data is used to explain HPC cost.
The entire approach is small enough to illustrate synergy with an LLM, while letting the user see interpretability & cost benefits in plain text.




