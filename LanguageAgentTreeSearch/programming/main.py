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
# OpenAI Chat Completion Helper with Enhanced Prompt Seed
# ------------------------------------------------------------------
def openai_chat_completion(prompt, model="gpt-4", temperature=0.3, max_tokens=150):
    """
    Sends a prompt to the OpenAI API and returns the response text.
    The system prompt includes context from the White Paper to guide responses.
    """
    system_prompt = (
        "You are an assistant integrated with the Fractal Identity Matrix (FIM) system. "
        "Your role is to provide similarity ratings between categories on a scale from 0 to 1, "
        "aligned with the principles outlined in the FIM White Paper. "
        "Ensure that your responses support the goals of reducing HPC overhead, enhancing interpretability, "
        "and maintaining a fractal, hierarchical structure in category relationships."
    )
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"[Error] LLM API call failed: {e}")
        return ""

# ------------------------------------------------------------------
# Step 1: Ask the LLM for top-level categories
# ------------------------------------------------------------------
def get_top_level_categories(description, num_categories=3):
    """Fetches top-level categories based on the provided description."""
    prompt = f"{description} Please provide exactly {num_categories} top-level categories in a JSON array of strings."
    response = openai_chat_completion(prompt, max_tokens=100)
    try:
        categories = json.loads(response)
        if isinstance(categories, list) and all(isinstance(cat, str) for cat in categories):
            return categories
        else:
            print(f"[Warning] Unexpected LLM response for top-level categories: {response}")
            return [f"TopCat{i}" for i in range(1, num_categories + 1)]
    except json.JSONDecodeError:
        print(f"[Warning] Failed to parse JSON for top-level categories. Response: {response}")
        return [f"TopCat{i}" for i in range(1, num_categories + 1)]

# ------------------------------------------------------------------
# Step 2: Ask the LLM for subcategories of a given category
# ------------------------------------------------------------------
def get_subcategories(parent_label, num_subcategories=3):
    """Fetches subcategories for a given parent category."""
    prompt = (
        f"Provide exactly {num_subcategories} subcategories for the category '{parent_label}'. "
        "Return them as a JSON array of strings, ensuring they align with the fractal, hierarchical structure "
        "designed to optimize HPC efficiency and interpretability as outlined in the FIM White Paper."
    )
    response = openai_chat_completion(prompt, max_tokens=100)
    try:
        subcategories = json.loads(response)
        if isinstance(subcategories, list) and all(isinstance(subcat, str) for subcat in subcategories):
            return subcategories
        else:
            print(f"[Warning] Unexpected LLM response for subcategories of '{parent_label}': {response}")
            return [f"{parent_label}_Sub{i}" for i in range(1, num_subcategories + 1)]
    except json.JSONDecodeError:
        print(f"[Warning] Failed to parse JSON for subcategories of '{parent_label}'. Response: {response}")
        return [f"{parent_label}_Sub{i}" for i in range(1, num_subcategories + 1)]

# ------------------------------------------------------------------
# Step 3: Assign Similarity Weights between Categories
# ------------------------------------------------------------------
def assign_similarity_weights(label_a, label_b):
    """
    Assigns a similarity weight between two categories using LLM.
    Returns a float between 0 and 1.
    """
    prompt = (
        f"Rate the similarity between the categories '{label_a}' and '{label_b}' on a scale from 0 to 1, "
        "where 0 means no similarity and 1 means identical. "
        "Provide only the numerical rating without additional text."
    )
    response = openai_chat_completion(prompt, max_tokens=10)
    try:
        weight = float(response)
        weight = max(0.0, min(1.0, weight))  # Clamp between 0 and 1
        print(f"[LLM] Similarity between '{label_a}' and '{label_b}': {weight}")
        return weight
    except ValueError:
        print(f"[Warning] Failed to parse similarity weight. Defaulting to random.")
        return random.uniform(0, 1)

# ------------------------------------------------------------------
# FractalSymSorter Class with Enhanced Weight Assignments
# ------------------------------------------------------------------
class FractalSymSorter:
    def __init__(self, matrix=None, labels=None, use_llm_weights=True):
        """
        Initializes the FractalSymSorter with an optional matrix and labels.
        """
        if matrix is None:
            self.matrix = np.array([[1.0]])  # Start with origin
        else:
            self.matrix = np.array(matrix)
        self.labels = labels if labels else []
        self.label_to_idx = {label: idx for idx, label in enumerate(self.labels)}
        self.use_llm_weights = use_llm_weights

    def _add_category_to_matrix(self, new_label):
        """
        Adds a new category to the matrix, expanding both rows and columns.
        """
        if new_label in self.label_to_idx:
            print(f"[Warning] Category '{new_label}' already exists in the matrix.")
            return

        old_size = self.matrix.shape[0]
        new_size = old_size + 1

        # Create a new matrix with zeros
        new_matrix = np.zeros((new_size, new_size))

        # Copy the existing matrix into the new matrix
        new_matrix[:old_size, :old_size] = self.matrix

        # Update the matrix
        self.matrix = new_matrix

        # Update labels and mapping
        self.labels.append(new_label)
        self.label_to_idx[new_label] = old_size

        print(f"[Matrix Update] Added '{new_label}' at index {old_size}")

    def insert_top_cat(self, label):
        """
        Inserts a top-level category and assigns weights to the origin.
        """
        self._add_category_to_matrix(label)
        if self.use_llm_weights:
            weight = assign_similarity_weights(self.labels[0], label)
        else:
            weight = random.uniform(0, 1)
        # Assign weight from origin to this category
        origin_idx = self.label_to_idx[self.labels[0]]
        cat_idx = self.label_to_idx[label]
        self.matrix[origin_idx, cat_idx] = weight
        print(f"[Top-Level Insert] '{label}' at col={cat_idx} with weight={weight}")

    def insert_subcats(self, parent_label, subcats):
        """
        Inserts subcategories under a parent category and assigns weights.
        """
        parent_idx = self.label_to_idx[parent_label]
        for subcat in subcats:
            self._add_category_to_matrix(subcat)
            if self.use_llm_weights:
                weight = assign_similarity_weights(parent_label, subcat)
            else:
                weight = random.uniform(0, 1)
            subcat_idx = self.label_to_idx[subcat]
            # Assign weight from parent to subcategory
            self.matrix[parent_idx, subcat_idx] = weight
            print(f"[Subcategory Insert] '{subcat}' under '{parent_label}' at col={subcat_idx} with weight={weight}")

        # After inserting all subcategories, assign weights among them
        self.assign_top_subcat_interactions(subcats)

    def assign_top_subcat_interactions(self, subcats):
        """
        Assigns similarity weights to the top 10% most significant subcategory interactions.
        """
        interactions = []
        for i in range(len(subcats)):
            for j in range(len(subcats)):
                if i != j:
                    label_a = subcats[i]
                    label_b = subcats[j]
                    interactions.append((label_a, label_b))

        # Shuffle to avoid any inherent ordering
        random.shuffle(interactions)

        # Assign weights to all interactions
        weights = {}
        for (a, b) in interactions:
            weight = assign_similarity_weights(a, b)
            weights[(a, b)] = weight

        # Determine the top 10% based on weights
        sorted_interactions = sorted(weights.items(), key=lambda item: item[1], reverse=True)
        top_k = max(1, int(0.10 * len(sorted_interactions)))  # Ensure at least one interaction
        top_interactions = sorted_interactions[:top_k]

        print(f"[Top Subcategory Interactions] Assigning weights to top {top_k} interactions out of {len(sorted_interactions)}")

        for ((a, b), weight) in top_interactions:
            idx_a = self.label_to_idx[a]
            idx_b = self.label_to_idx[b]
            self.matrix[idx_a, idx_b] = weight
            print(f"[Top Interaction] '{a}' -> '{b}' with weight={weight}")

    def show_map(self):
        """Prints the current matrix and label mapping."""
        print("\n=== Current Matrix & Labels ===")
        for idx, label in enumerate(self.labels):
            print(f"{idx}: {label}")
        print(self.matrix)

# ------------------------------------------------------------------
# Visualization Function
# ------------------------------------------------------------------
def visualize_matrix(matrix, labels):
    """
    Visualizes the adjacency matrix using matplotlib.
    """
    plt.figure(figsize=(12, 10))
    plt.imshow(matrix, cmap='viridis', interpolation='none')
    plt.colorbar(label='Similarity Weight')
    plt.xticks(ticks=range(len(labels)), labels=labels, rotation=90)
    plt.yticks(ticks=range(len(labels)), labels=labels)
    plt.title('FractalSymSorter Adjacency Matrix')
    plt.tight_layout()
    plt.show()

# ------------------------------------------------------------------
# Main Function
# ------------------------------------------------------------------
def main():
    # 1. Define the origin category
    origin_description = "Define the origin category for the FractalSymSorter based on HPC interpretability."
    origin_list = get_top_level_categories(origin_description, num_categories=1)
    if not origin_list:
        print("[Error] Failed to retrieve origin category.")
        return

    origin_category = origin_list[0]
    print(f"Origin Category: {origin_category}")

    # 2. Prompt for 4 more top-level categories to add incrementally
    main_description = (
        "Now let's define 4 more top-level categories for HPC interpretability, aligned with the Fractal Identity Matrix (FIM) objectives."
        " Return exactly 4 major categories in a valid JSON array of strings."
    )
    more_cats = get_top_level_categories(main_description, num_categories=4)
    print(f"Top-Level Categories: {more_cats}")

    # 3. Initialize FractalSymSorter with the origin pivot
    layout = FractalSymSorter(matrix=[[1.0]], labels=[origin_category], use_llm_weights=True)  # Set use_llm_weights=True to use LLM-based weights

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
    accessed_blocks = max(1, total_blocks // 20)  # Access top 1/20 of the blocks
    skip_factor = 1.0 - (accessed_blocks / total_blocks)
    cost = 1.0 - skip_factor

    print(f"\nHPC Skip Factor Simulation:")
    print(f"  Accessed {accessed_blocks} of {total_blocks} blocks.")
    print(f"  skip_factor = {skip_factor:.2f}, HPC cost ≈ {cost:.2f}")

if __name__ == "__main__":
    main()