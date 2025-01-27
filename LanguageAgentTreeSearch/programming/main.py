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
def get_top_level_categories(description, num_categories=5):
    prompt_content = (
        f"Given this context:\n\n{description}\n\n"
        f"Return exactly {num_categories} major categories in valid JSON array form, e.g.:\n"
        '["Category1", "Category2", ..., "CategoryN"]\n'
    )
    raw_output = openai_chat_completion(prompt_content)
    print("\n[LLM Response for Top-Level Categories]\n", raw_output)

    try:
        categories = json.loads(raw_output)
        if not isinstance(categories, list):
            categories = []
    except:
        categories = []
    return categories

# ------------------------------------------------------------------
# Step 2: Ask the LLM for subcategories of a given category
# ------------------------------------------------------------------
def get_subcategories(category, num_subcategories=3):
    prompt_content = (
        f"For the category '{category}', list {num_subcategories} subcategories in valid JSON, e.g.:\n"
        '["Sub1", "Sub2", "Sub3"]\n'
    )
    raw_output = openai_chat_completion(prompt_content)
    print(f"\n[LLM Response for Subcategories of '{category}']\n", raw_output)

    try:
        subs = json.loads(raw_output)
        if not isinstance(subs, list):
            subs = []
    except:
        subs = []
    return subs

# ------------------------------------------------------------------
# For demonstration, a small "FractalSorter2D" class that can
#  insert categories incrementally and do a final pivot-based sort.
# ------------------------------------------------------------------
class FractalSorter2D:
    def __init__(self, prompt_text=None):
        """
        Optionally store a 'prompt_text' as the 'origin' label.
        """
        self.prompt_text = prompt_text or "Origin"
        self.labels = []
        self.label_to_index = {}
        self.matrix = None

    def initialize_origin(self):
        """
        Begin with a 1x1 matrix containing the 'origin' category (self.prompt_text).
        """
        origin_label = self.prompt_text
        self.labels = [origin_label]
        self.label_to_index = {origin_label: 0}
        self.matrix = np.array([[1.0]])  # A single cell at diagonal=1.0
        print(f"[Initialize Origin] '{origin_label}' as pivot.")
        self._print_current_structure()

    def insert_placeholder(self, placeholder_label="Placeholder"):
        """
        Optionally insert a dummy label (placeholder) so that
        the pivot can later be pinned at index=2.
        """
        old_size = len(self.labels)
        new_size = old_size + 1
        self.labels.append(placeholder_label)
        self.label_to_index[placeholder_label] = new_size - 1

        new_matrix = np.zeros((new_size, new_size))
        new_matrix[:old_size, :old_size] = self.matrix

        for i in range(new_size):
            new_matrix[i, i] = 1.0

        # For demonstration, link placeholder to origin with a super-low weight
        # so it doesn't significantly affect the fractal sort.
        origin_idx = 0
        placeholder_idx = self.label_to_index[placeholder_label]
        new_matrix[origin_idx, placeholder_idx] = 0.01
        new_matrix[placeholder_idx, origin_idx] = 0.01

        self.matrix = new_matrix
        print(f"[Insert Placeholder] '{placeholder_label}' inserted at index={placeholder_idx}.")
        self._print_current_structure()

    def insert_category_and_subs(self, category, sub_list):
        """
        Insert a new top-level category plus its subcategories.
        Subcategories get a weight <= parent's weight.
        """
        insert_labels = [category] + sub_list
        old_size = len(self.labels)
        new_size = old_size + len(insert_labels)

        for lbl in insert_labels:
            self.labels.append(lbl)
            self.label_to_index[lbl] = len(self.labels) - 1

        new_matrix = np.zeros((new_size, new_size))
        new_matrix[:old_size, :old_size] = self.matrix

        for i in range(new_size):
            new_matrix[i, i] = 1.0

        # Link new category to Origin (index=0) with some decreasing base_weight
        origin_index = 0
        cat_idx = self.label_to_index[category]
        base_weight = 0.8 - (len(self.labels) - 2) * 0.05
        base_weight = max(base_weight, 0.3)
        new_matrix[origin_index, cat_idx] = base_weight
        new_matrix[cat_idx, origin_index] = base_weight
        print(f"Link (Origin -> {category}) = {base_weight:.2f}")

        # Subcategories get weights in [0.3..0.6] but <= base_weight
        for sub in sub_list:
            sub_idx = self.label_to_index[sub]
            sub_weight = random.uniform(0.3, 0.6)
            sub_weight = min(sub_weight, base_weight)
            new_matrix[cat_idx, sub_idx] = sub_weight
            new_matrix[sub_idx, cat_idx] = sub_weight
            print(f"Sub ({category} -> {sub}) = {sub_weight:.2f}")

        self.matrix = new_matrix
        print(f"[Insert Category + Subs] Inserted '{category}' + {len(sub_list)} subcategories.")
        self._print_current_structure()

    def fractal_sort_2d(self, start=2, end=None):
        """
        2D pivot-based sorting, beginning at start=2 so:
          - The 'Origin' at row/col=0 remains untouched,
          - row/col=1 can remain a placeholder or dummy,
          - The first pivot is row/col=2, ensuring top-cats appear in col>=3.
        """
        if end is None:
            end = len(self.labels)
        if end - start <= 1:
            return

        pivot_index = start
        sub_indices = list(range(start + 1, end))
        def compare_func(idx):
            return self.matrix[idx, pivot_index]
        sub_indices.sort(key=compare_func, reverse=True)

        block_order = [start] + sub_indices
        new_order = list(range(0, start)) + block_order + list(range(end, len(self.labels)))
        self._reorder_labels(new_order)

        boundary = self._find_boundary(start, end)
        print(f"Pivot at row/col={start}, boundary={boundary}")

        self.fractal_sort_2d(boundary + 1, end)

    def _reorder_labels(self, new_order):
        current_labels = [self.labels[i] for i in new_order]
        index_map = {old_idx: new_idx for new_idx, old_idx in enumerate(new_order)}
        size = len(self.labels)
        new_mat = np.zeros((size, size))

        for old_r in range(size):
            for old_c in range(size):
                r = index_map[old_r]
                c = index_map[old_c]
                new_mat[r, c] = self.matrix[old_r, old_c]

        self.labels = current_labels
        self.label_to_index = {lbl: i for i, lbl in enumerate(self.labels)}
        self.matrix = new_mat

    def _find_boundary(self, start, end):
        if start >= end:
            return start
        pivot_col = start
        pivot_val = self.matrix[start, pivot_col]
        threshold_factor = 0.4
        boundary = start

        for row_idx in range(start + 1, end):
            val = self.matrix[row_idx, pivot_col]
            if val >= threshold_factor * pivot_val:
                boundary = row_idx
            else:
                break
        return boundary

    def _print_current_structure(self):
        print("Current Labels:", self.labels)
        n = len(self.labels)
        limit = min(n, 5)
        for i in range(limit):
            row_vals = " ".join(f"{self.matrix[i,j]:.2f}" for j in range(limit))
            print(f"  Row {i:2d}: {row_vals}")

    def show_map(self):
        print("\n=== Final FIM Matrix & Labels ===")
        print("Labels in final order:")
        for i, lbl in enumerate(self.labels):
            print(f" {i}: {lbl}")

        print("\nMatrix:")
        for i, row_data in enumerate(self.matrix):
            row_str = " ".join(f"{val:.2f}" for val in row_data)
            print(f"{i:2d}: {row_str}")

# ------------------------------------------------------------------
# Visualization
# ------------------------------------------------------------------
def visualize_matrix(matrix, labels):
    plt.figure(figsize=(7, 6))
    plt.imshow(matrix, cmap='viridis', aspect='auto')
    plt.colorbar(label="Weight")
    plt.xticks(range(len(labels)), labels, rotation=90)
    plt.yticks(range(len(labels)), labels)
    plt.title("Fractal Sorted Matrix (pivot at row/col=2)")
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

    # 2. Prompt for 4 more categories to add incrementally
    main_description = (
        "Now let's define 4 more categories for HPC interpretability."
        "Return exactly 4 major categories in valid JSON array form."
    )
    more_cats = get_top_level_categories(main_description, num_categories=4)

    # 3. Initialize FIM with the origin pivot
    sorter = FractalSorter2D()
    sorter.initialize_origin()

    # 4. For each of these 4 categories, retrieve subcategories and insert
    #    one category at a time (plus its subcategories).
    for cat in more_cats:
        subs = get_subcategories(cat, num_subcategories=3)
        sorter.insert_category_and_subs(cat, subs)

    # 5. Once everything is inserted, do a final fractal sort
    sorter.fractal_sort_2d()
    sorter.show_map()

    # 6. Visualize the matrix
    visualize_matrix(sorter.matrix, sorter.labels)

    # Example HPC measurement
    total_blocks = len(sorter.labels)
    # Suppose we only access half
    accessed_blocks = total_blocks // 2
    skip_factor = 1.0 - (accessed_blocks / total_blocks)
    cost = 1.0 - skip_factor

    print(f"\nHPC Skip Factor Simulation:")
    print(f"  Accessed {accessed_blocks} of {total_blocks} blocks.")
    print(f"  skip_factor = {skip_factor:.2f}, HPC cost ≈ {cost:.2f}")

if __name__ == "__main__":
    main()