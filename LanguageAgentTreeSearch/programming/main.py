import os
import openai
import json
import numpy as np
import matplotlib.pyplot as plt
from dotenv import load_dotenv
import random

# ------------------------------------------------------------------
# Utility: Load environment variables (like OPENAI_API_KEY) from .env
# ------------------------------------------------------------------
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# ------------------------------------------------------------------
# OpenAI Chat Completion Helper
# ------------------------------------------------------------------
def openai_chat_completion(prompt, model="gpt-4", temperature=0.7, max_tokens=300):
    response = openai.ChatCompletion.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are an LLM that generates hierarchical categories."},
            {"role": "user", "content": prompt},
        ],
        temperature=temperature,
        max_tokens=max_tokens
    )
    return response["choices"][0]["message"]["content"]

# ------------------------------------------------------------------
# Step 1: Ask the LLM for top-level categories
# ------------------------------------------------------------------
def get_top_level_categories(description, num_categories=3):
    """Mock function—replace or extend as needed."""
    return [f"TopCat{i}" for i in range(1, num_categories + 1)]

# ------------------------------------------------------------------
# Step 2: Ask the LLM for subcategories of a given category
# ------------------------------------------------------------------
def get_subcategories(cat_label, num_subcategories=2):
    """Mock function—replace or extend as needed."""
    return [f"{cat_label}_Sub{i}" for i in range(1, num_subcategories + 1)]

# ------------------------------------------------------------------
# For demonstration, a small "FractalSymSorter" class that can
# sort a matrix using a symmetrical pivot-based approach.
# ------------------------------------------------------------------
class FractalSymSorter:
    def __init__(self, matrix, labels=None):
        """
        matrix: n x n adjacency (not necessarily perfectly symmetric, 
                but we impose symmetrical ordering).
        labels: optional labels for each row/column.
        """
        self.matrix = np.array(matrix, dtype=float)
        self.n = len(self.matrix)
        if labels is None:
            labels = [f"Item{i}" for i in range(self.n)]
        self.labels = labels

    def fractal_sort_2d(self, start=0, end=None):
        """
        Symmetrical pivot-based sort for the submatrix [start..end-1],
        with 'start' as the pivot row/column.
        """
        if end is None:
            end = self.n
        if end - start <= 1:
            return  # no submatrix to sort

        pivot = start

        # 1) Sort the rows [start+1..end-1] by adjacency to pivot's column (descending).
        row_indices = list(range(start + 1, end))
        def pivot_adjacency(row_idx):
            return self.matrix[row_idx, pivot]
        row_indices.sort(key=pivot_adjacency, reverse=True)

        # 2) Reorder those rows, and reorder columns symmetrically.
        self._reorder_rows(start+1, row_indices)
        self._reorder_cols(start+1, row_indices)

        # 3) Identify boundary where adjacency > threshold * pivot_value.
        boundary = self._find_boundary(pivot, start+1, end)

        # 4) Recursively sort the pivot's sub-block [start+1..boundary].
        self.fractal_sort_2d(start+1, boundary+1)
        # 5) Recursively sort leftover [boundary+1..end].
        self.fractal_sort_2d(boundary+1, end)

    def _find_boundary(self, pivot, begin, end):
        """
        Returns the largest row i in [begin..end-1] such that
        matrix[i, pivot] >= threshold * matrix[pivot, pivot].
        """
        pivot_val = self.matrix[pivot, pivot]
        threshold = 0.4
        boundary = pivot
        for i in range(begin, end):
            if self.matrix[i, pivot] >= threshold * pivot_val:
                boundary = i
            else:
                break
        return boundary

    def _reorder_rows(self, block_start, new_row_order):
        """
        Reorder the rows [block_start..block_start+len(new_row_order)-1]
        to match new_row_order exactly.
        """
        full_indices = list(range(self.n))
        full_indices[block_start:block_start + len(new_row_order)] = new_row_order
        self._reindex(full_indices, axis='row')

    def _reorder_cols(self, block_start, new_col_order):
        """
        Reorder columns symmetrically with the same ordering used for rows.
        """
        full_indices = list(range(self.n))
        full_indices[block_start:block_start + len(new_col_order)] = new_col_order
        self._reindex(full_indices, axis='col')

    def _reindex(self, indices, axis='row'):
        """
        Reindex rows or columns of self.matrix according to 'indices',
        and keep labels consistent for row reindexing.
        """
        if axis == 'row':
            self.matrix = self.matrix[indices, :]
            self.labels = [self.labels[i] for i in indices]
        else:  # axis == 'col'
            self.matrix = self.matrix[:, indices]

    def show_matrix(self):
        """
        Print out the final matrix along with the label order.
        """
        print("\n=== Final Fractal-Sorted Matrix ===")
        for i, lbl in enumerate(self.labels):
            print(f"{i}: {lbl}")
        for i, row in enumerate(self.matrix):
            print(f"{i}: " + " ".join(f"{val:.2f}" for val in row))

# ------------------------------------------------------------------
# Manual incremental layout
# ------------------------------------------------------------------
class CustomPivotLayout:
    """
    Manual incremental layout:
    - 'Origin' at row/col=0
    - We start top-level categories at col=1 (each in the next_free_col)
    - Subcategories appended immediately after all top-level categories
    """
    def __init__(self, origin_label="Origin"):
        self.labels = [origin_label]
        self.label_to_idx = {origin_label: 0}
        self.matrix = np.array([[1.0]])
        # Start from col=1 for the first top-level cat to avoid out-of-range issues
        self.next_free_col = 1

    def _move_label(self, old_idx, new_idx):
        """
        Symmetrically swap row+col: old_idx ↔ new_idx.
        This ensures the label at old_idx is moved to new_idx in both rows and columns.
        """
        if old_idx == new_idx:
            return

        size = len(self.labels)
        row_perm = list(range(size))
        col_perm = list(range(size))

        row_perm[old_idx], row_perm[new_idx] = row_perm[new_idx], row_perm[old_idx]
        col_perm[old_idx], col_perm[new_idx] = col_perm[new_idx], col_perm[old_idx]

        new_mat = np.zeros_like(self.matrix)
        for r in range(size):
            for c in range(size):
                new_mat[r, c] = self.matrix[row_perm[r], col_perm[c]]
        self.matrix = new_mat

        new_labels = [self.labels[i] for i in row_perm]
        self.labels = new_labels
        self.label_to_idx = {lbl: i for i, lbl in enumerate(self.labels)}

    def insert_top_cat(self, cat_label):
        """
        Insert a new top-level category at self.next_free_col without adding subcategories.
        """
        print(f"\n[Top-Level Insert] '{cat_label}' at col={self.next_free_col}")
        old_size = len(self.labels)
        new_size = old_size + 1

        # Extend matrix & labels
        self.labels.append(cat_label)
        self.label_to_idx[cat_label] = len(self.labels) - 1

        new_mat = np.zeros((new_size, new_size))
        new_mat[:old_size, :old_size] = self.matrix
        new_mat[-1, -1] = 1.0
        self.matrix = new_mat

        origin_idx = 0
        cat_idx = self.label_to_idx[cat_label]
        base_weight = 0.8
        self.matrix[origin_idx, cat_idx] = base_weight
        self.matrix[cat_idx, origin_idx] = base_weight

        # Move the top-level cat to next_free_col
        self._move_label(cat_idx, self.next_free_col)

        # Advance next_free_col
        self.next_free_col += 1

    def insert_subcats(self, top_cat_label, subcats=None):
        """
        Insert subcategories for a given top-level category.
        Subcategories are added as a contiguous sorted block immediately after all top-level categories.
        """
        if subcats is None:
            subcats = []
        print(f"\n[Subcategories Insert] for '{top_cat_label}'")
        parent_idx = self.label_to_idx[top_cat_label]

        # Determine the insertion point (after all top-level categories)
        insertion_point = self.next_free_col

        for subcat in subcats:
            print(f"  Inserting subcategory '{subcat}' at position {insertion_point}")
            self.labels.append(subcat)
            self.label_to_idx[subcat] = insertion_point

            # Extend the matrix
            self.matrix = np.pad(self.matrix, ((0,1),(0,1)), 'constant', constant_values=0)
            self.matrix[insertion_point, insertion_point] = 1.0

            # Link subcategory with its parent
            self.matrix[parent_idx, insertion_point] = 0.5
            self.matrix[insertion_point, parent_idx] = 0.5

            # Advance insertion point
            insertion_point += 1

        # Update next_free_col to the new insertion_point
        self.next_free_col = insertion_point

    def show_map(self):
        """Print matrix and label layout."""
        print("\n=== Current Matrix & Labels ===")
        for i, lbl in enumerate(self.labels):
            print(f"{i}: {lbl}")
        print("")
        for i, row in enumerate(self.matrix):
            row_vals = " ".join(f"{val:.2f}" for val in row)
            print(f"{i} : {row_vals}")

# ------------------------------------------------------------------
# Visualization
# ------------------------------------------------------------------
def visualize_matrix(matrix, labels):
    """Simple matplotlib-based visualization."""
    plt.figure(figsize=(12, 12))
    plt.imshow(matrix, cmap="Blues", interpolation="nearest")
    plt.colorbar(label="Weight")
    plt.xticks(range(len(labels)), labels, rotation=90)
    plt.yticks(range(len(labels)), labels)
    plt.title("Fractal / Manual Layout")
    plt.tight_layout()
    plt.show()

# ------------------------------------------------------------------
# Main flow with incremental insertion
# ------------------------------------------------------------------
def main():
    if not openai.api_key:
        print("Error: OPENAI_API_KEY is not set.")
        return

    # 1. Prompt for an "origin" description
    origin_description = (
        "We want an HPC + interpretability scenario. Provide a single anchor as origin."
    )
    # We'll just treat the first prompt as a single 'origin' category
    # to demonstrate the idea. In real usage, you'd call get_top_level_categories
    # with num_categories=1 or parse it differently.
    origin_list = get_top_level_categories(origin_description, num_categories=1)
    if not origin_list:
        print("No origin returned—exiting.")
        return

    origin_category = origin_list[0]

    # 2. Prompt for 4 more top-level categories to add incrementally
    main_description = (
        "Now let's define 4 more top-level categories for HPC interpretability."
        "Return exactly 4 major categories in valid JSON array form."
    )
    more_cats = get_top_level_categories(main_description, num_categories=4)

    # 3. Initialize CustomPivotLayout with the origin pivot
    layout = CustomPivotLayout(origin_label=origin_category)

    # 4. Insert all top-level categories first
    for cat in more_cats:
        layout.insert_top_cat(cat)

    # 5. Insert subcategories for each top-level category in sorted blocks
    for cat in more_cats:
        subcats = get_subcategories(cat, num_subcategories=3)
        # Sort subcategories as needed; here we sort alphabetically
        subcats_sorted = sorted(subcats)
        layout.insert_subcats(cat, subcats_sorted)

    # 6. Show final layout and visualize
    layout.show_map()
    visualize_matrix(layout.matrix, layout.labels)

    # 7. HPC skip factor example
    total_blocks = len(layout.labels)
    accessed_blocks = total_blocks // 2
    skip_factor = 1.0 - (accessed_blocks / total_blocks)
    cost = 1.0 - skip_factor

    print(f"\nHPC Skip Factor Simulation:")
    print(f"  Accessed {accessed_blocks} of {total_blocks} blocks.")
    print(f"  skip_factor = {skip_factor:.2f}, HPC cost ≈ {cost:.2f}")

if __name__ == "__main__":
    main()