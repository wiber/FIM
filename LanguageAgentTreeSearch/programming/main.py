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
def openai_chat_completion(prompt, model="gpt-4", temperature=0.3, max_tokens=10):
    """
    Sends a prompt to the OpenAI API and returns the response text.
    """
    response = openai.ChatCompletion.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are an assistant that rates similarity between two categories on a scale from 0 to 1."},
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
    # In a real implementation, you would use the `openai_chat_completion` function
    # to fetch top-level categories based on the description.
    return [f"TopCat{i}" for i in range(1, num_categories + 1)]

# ------------------------------------------------------------------
# Step 2: Ask the LLM for subcategories of a given category
# ------------------------------------------------------------------
def get_subcategories(cat_label, num_subcategories=2):
    """Mock function—replace or extend as needed."""
    # In a real implementation, you would use the `openai_chat_completion` function
    # to fetch subcategories based on the parent category label.
    return [f"{cat_label}_Sub{i}" for i in range(1, num_subcategories + 1)]

# ------------------------------------------------------------------
# For demonstration, a small "FractalSymSorter" class that can
# sort a matrix using a symmetrical pivot-based approach.
# ------------------------------------------------------------------
class FractalSymSorter:
    def __init__(self, matrix, labels=None, use_llm_weights=False):
        """
        matrix: n x n adjacency (not necessarily perfectly symmetric, 
                but we impose symmetrical ordering).
        labels: optional labels for each row/column.
        use_llm_weights: bool indicating whether to use LLM for weight assignments.
        """
        self.matrix = np.array(matrix, dtype=float)
        self.n = len(self.matrix)
        if labels is None:
            labels = [f"Item{i}" for i in range(self.n)]
        self.labels = labels
        self.label_to_idx = {label: idx for idx, label in enumerate(self.labels)}
        self.use_llm_weights = use_llm_weights
        self.next_free_col = self.n  # Initialize to current size

    def get_weight(self, parent_label, child_label):
        """
        Retrieves the similarity weight between two categories.
        If use_llm_weights is True, fetches from LLM; otherwise, assigns randomly.
        """
        if self.use_llm_weights and openai.api_key:
            prompt = (
                f"Rate the similarity between '{parent_label}' and '{child_label}' "
                f"on a scale from 0 to 1, where 1 is extremely similar and 0 is not similar at all."
            )
            weight_str = openai_chat_completion(prompt)
            try:
                weight = float(weight_str.strip())
                weight = min(max(weight, 0.0), 1.0)  # Clamp between 0 and 1
            except ValueError:
                print(f"  [Warning] Unable to parse weight from LLM response. Assigning default weight 0.5.")
                weight = 0.5
        else:
            # Assign a random weight between 0.5 and 1.0 for stronger relationships
            weight = round(random.uniform(0.5, 1.0), 2)
        
        print(f"  Similarity weight between '{parent_label}' and '{child_label}': {weight}")
        return weight

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

        origin_idx = 0  # Assuming origin is at index 0
        cat_idx = self.label_to_idx[cat_label]
        similarity_weight = self.get_weight(self.labels[origin_idx], cat_label)
        self.matrix[origin_idx, cat_idx] = similarity_weight
        self.matrix[cat_idx, origin_idx] = similarity_weight

        # No need to move labels since top categories are inserted at the end

        # Advance next_free_col
        self.next_free_col += 1

    def insert_subcats(self, parent_label, subcats):
        """
        Insert subcategories for a given top-level category in sorted blocks.
        """
        print(f"\n[Inserting Subcategories for '{parent_label}']")

        # Retrieve parent index
        parent_idx = self.label_to_idx[parent_label]

        # Assign weights to subcategories
        subcats_with_weights = []
        for subcat in subcats:
            weight = self.get_weight(parent_label, subcat)
            subcats_with_weights.append((subcat, weight))

        # Sort subcategories by weight descending
        subcats_sorted = sorted(subcats_with_weights, key=lambda x: x[1], reverse=True)

        # Insert subcategories in sorted order
        for subcat, weight in subcats_sorted:
            self._add_subcategory(parent_label, subcat, weight)

    def _add_subcategory(self, parent_label, subcat_label, weight):
        """
        Helper method to add a single subcategory with a given weight.
        """
        print(f"  Adding Subcategory '{subcat_label}' for '{parent_label}' with weight {weight}")
        old_size = len(self.labels)
        new_size = old_size + 1

        # Extend matrix & labels
        self.labels.append(subcat_label)
        self.label_to_idx[subcat_label] = len(self.labels) - 1

        new_mat = np.zeros((new_size, new_size))
        new_mat[:old_size, :old_size] = self.matrix
        new_mat[-1, -1] = 1.0
        self.matrix = new_mat

        parent_idx = self.label_to_idx[parent_label]
        subcat_idx = self.label_to_idx[subcat_label]

        # Assign similarity weights
        self.matrix[parent_idx, subcat_idx] = weight
        self.matrix[subcat_idx, parent_idx] = weight

        # Optionally, you can assign weights between subcategories if needed

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
    print(f"Origin Category: {origin_category}")

    # 2. Prompt for 4 more top-level categories to add incrementally
    main_description = (
        "Now let's define 4 more top-level categories for HPC interpretability."
        " Return exactly 4 major categories."
    )
    more_cats = get_top_level_categories(main_description, num_categories=4)
    print(f"Top-Level Categories: {more_cats}")

    # 3. Initialize CustomPivotLayout with the origin pivot
    layout = FractalSymSorter(matrix=[[1.0]], labels=[origin_category], use_llm_weights=False)  # Set use_llm_weights=True to use LLM-based weights

    # 4. Insert all top-level categories first
    for cat in more_cats:
        layout.insert_top_cat(cat)

    # 5. Insert subcategories for each top-level category in sorted blocks
    for cat in more_cats:
        subcats = get_subcategories(cat, num_subcategories=3)
        layout.insert_subcats(cat, subcats)

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