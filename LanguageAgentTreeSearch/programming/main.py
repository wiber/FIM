import os
import openai
import json
import numpy as np
import matplotlib.pyplot as plt
from dotenv import load_dotenv
import random
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
        "Welcome to the Fractal Identity Matrix (FIM) Integration Prompt. "
        "This guide enables the Language Model (LLM) to utilize FIM principles for effective problem space subdivision. "
        "By acting as a working memory proprioception, the LLM will optimize operations to reduce HPC costs using the FIM skip formula. "
        "The expected improvement in relevance is achieved when the LLM efficiently performs proprioception for working memory in an interpretable way. "
        "Focus on creating relevancy through energy efficiency and interpretability, extending these principles to embody the direction of the problem space. "
        "FIM acts as AI's internal body sense, organizing data into self-similar submatrices for efficient retrieval. "
        "The goal is to reduce unnecessary data processing, lowering HPC costs and enhancing performance. "
        "Use the FIM skip formula: FI = (c/t)^n, where c is the subset of relevant categories, t is the total categories, and n is the number of dimensions. "
        "Ensure each decision is transparent and traceable within the FIM structure, fostering a synergy between energy efficiency and interpretability. "
        "Emphasize cognitive economy, where the LLM's ability to efficiently allocate cognitive resources enhances trust and interpretability, moving away from the traditional 'black box' model. "
        "While not every response needs to perfectly address these aspects, increasing their presence in LLM outputs can significantly enhance user trust and system transparency."
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

def assign_similarity_weights_batch(comparisons):
    """
    Assigns similarity weights for a batch of category pairs using LLM.
    Returns a dictionary of weights.
    """
    # Create a prompt that includes all comparisons
    prompt = "Rate the similarity for the following category pairs on a scale from 0 to 1:\n"
    for idx, (label_a, label_b) in enumerate(comparisons):
        prompt += f"{idx + 1}. From '{label_a}' to '{label_b}'\n"

    prompt += "Provide only the numerical ratings in the same order, separated by commas."

    response = openai_chat_completion(prompt, max_tokens=50)
    try:
        # Parse the response into a list of weights
        weights = [float(w.strip()) for w in response.split(',')]
        # Clamp weights between 0 and 1
        weights = [max(0.0, min(1.0, w)) for w in weights]
        return {pair: weight for pair, weight in zip(comparisons, weights)}
    except Exception as e:
        print(f"[Error] Failed to parse batch similarity weights: {e}")
        # Return random weights if parsing fails
        return {pair: random.uniform(0, 1) for pair in comparisons}

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
        self.block_indices = []  # To store indices where new blocks start

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
        self.matrix[cat_idx, origin_idx] = weight  # Transpose the assignment
        print(f"[Top-Level Insert] from '{self.labels[0]}' to '{label}' at row={cat_idx} with weight={weight}")

        # Track the index where the new block ends
        self.block_indices.append(cat_idx + 1)

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
            self.matrix[subcat_idx, parent_idx] = weight
            print(f"[Subcategory Insert] from '{parent_label}' to '{subcat}' at row={subcat_idx} with weight={weight}")

        # After inserting all subcategories, assign weights among them
        self.assign_top_interactions(subcats)

        # Track the index where the new block ends
        self.block_indices.append(self.label_to_idx[subcats[-1]] + 1)

    def assign_top_interactions(self, categories, top_n=20):
        """
        Assigns similarity weights to the top N most significant interactions, including both intra-category and inter-category.
        """
        interactions = []
        num_categories = len(categories)

        # Include all possible pairs for top-level and subcategories
        for i in range(num_categories):
            for j in range(i + 1, num_categories):  # Ensure no duplicate pairs and no self-comparison
                label_a = categories[i]
                label_b = categories[j]
                interactions.append((label_a, label_b))

        # Shuffle to avoid any inherent ordering
        random.shuffle(interactions)

        # Batch assign weights to all interactions
        weights = assign_similarity_weights_batch(interactions)

        # Determine the top N based on weights
        sorted_interactions = sorted(weights.items(), key=lambda item: item[1], reverse=True)
        top_interactions = sorted_interactions[:top_n]

        # Track block indices
        if top_n < num_categories:
            step = max(1, num_categories // top_n)
            for i in range(step, num_categories, step):
                self.block_indices.append(i)

        for ((a, b), weight) in top_interactions:
            idx_a = self.label_to_idx[a]
            idx_b = self.label_to_idx[b]
            self.matrix[idx_a, idx_b] = weight
            print(f"[Top Interaction] from '{a}' to '{b}' with weight={weight}")

    def show_map(self):
        """Prints the current matrix and label mapping."""
        print("\n=== Current Matrix & Labels ===")
        for idx, label in enumerate(self.labels):
            print(f"{idx}: {label}")
        print(self.matrix)

    def get_block_indices(self):
        return self.block_indices

    def assign_weights_to_first_submatrix(self):
        """
        Assigns weights to the first submatrix on the diagonal using the LLM.
        """
        # Determine the range of indices for the first submatrix
        num_top_categories = 4  # Assuming there are 4 top-level categories
        submatrix_start = 1  # Start after the origin
        submatrix_end = submatrix_start + num_top_categories

        # Construct the prompt with the submatrix and labels
        prompt = (
            "Given the following submatrix and labels, assign weights to the causal relationships. "
            "Focus on identifying and highlighting significant interactions that are stronger than average. "
            "Consider the context of each category and its potential impact on others:\n"
        )
        submatrix = self.matrix[submatrix_start:submatrix_end, submatrix_start:submatrix_end]
        prompt += "Submatrix:\n"
        prompt += "\n".join(["\t".join(map(str, row)) for row in submatrix]) + "\n"
        prompt += "Labels:\n"
        prompt += ", ".join(self.labels[submatrix_start:submatrix_end]) + "\n"
        prompt += "Please provide the weights for the causal relationships between these categories."

        # Send the prompt to the LLM
        response = openai_chat_completion(prompt, max_tokens=100)

        try:
            # Parse the response into a dictionary of weights
            weights = json.loads(response)
            for (label_a, label_b), weight in weights.items():
                idx_a = self.label_to_idx[label_a]
                idx_b = self.label_to_idx[label_b]
                self.matrix[idx_a, idx_b] = weight
                print(f"[LLM Assignment] Weight between '{label_a}' and '{label_b}': {weight}")
        except json.JSONDecodeError:
            print(f"[Warning] Failed to parse LLM response for first submatrix weights. Response: {response}")

    def create_submatrix_map(self):
        """
        Creates a map of submatrices with a naming convention using coordinates.
        """
        num_top_categories = 4  # Assuming there are 4 top-level categories
        submatrix_map = {}

        for i in range(1, num_top_categories + 1):
            for j in range(1, num_top_categories + 1):
                if i != j:
                    # Create a notation for the submatrix, starting from the first child of origin
                    notation = f"{chr(64 + i)}{chr(64 + j)}"
                    submatrix_map[notation] = (i, j)
                    print(f"Submatrix {notation}: Interaction between '{self.labels[i]}' and '{self.labels[j]}'")

        return submatrix_map

# ------------------------------------------------------------------
# Visualization Function
# ------------------------------------------------------------------
def log_significant_interactions(matrix, labels, submatrix_bounds, threshold=0.5):
    """
    Logs the most significant interactions in the matrix.
    """
    num_categories = len(labels)
    for i in range(num_categories):
        for j in range(num_categories):
            weight = matrix[i, j]
            if weight > threshold:  # Only log significant weights
                # Determine submatrix coordinates
                submatrix_label = None
                for label, (start, end) in submatrix_bounds.items():
                    if start <= i <= end and start <= j <= end:
                        submatrix_label = label
                        break

                # Determine if the interaction is at the top level
                top_level_interaction = (i < num_categories // 2) and (j < num_categories // 2)

                interaction_info = (
                    f"Interaction: '{labels[i]}' to '{labels[j]}', "
                    f"Weight: {weight:.2f}, "
                    f"Absolute Coordinate: ({i}, {j}), "
                    f"Submatrix: {submatrix_label if not top_level_interaction else 'Top-Level'}"
                )
                logging.info(interaction_info)
                print(interaction_info)

def visualize_matrix(matrix, labels, block_indices):
    """
    Visualizes the adjacency matrix using matplotlib, with lines to indicate submatrix boundaries.
    """
    plt.figure(figsize=(12, 10))
    plt.imshow(matrix, cmap='viridis', interpolation='none')
    plt.colorbar(label='Similarity Weight')
    plt.xticks(ticks=range(len(labels)), labels=labels, rotation=90)
    plt.yticks(ticks=range(len(labels)), labels=labels)
    plt.title('FractalSymSorter Adjacency Matrix')

    # Dictionaries to store submatrix indices
    top_level_indices = {}
    subcategory_indices = {}
    submatrix_bounds = {}  # New dictionary to store submatrix bounds

    # Draw lines to indicate submatrix boundaries and add labels
    num_top_categories = 4  # Assuming there are 4 top-level categories
    for idx, index in enumerate(block_indices):
        plt.axhline(y=index - 0.5, color='white', linestyle='--', linewidth=0.5)
        plt.axvline(x=index - 0.5, color='white', linestyle='--', linewidth=0.5)
        # Use the label corresponding to the top-level category, starting from the first child of origin
        label_idx = idx % num_top_categories  # Start from the first top-level category
        if label_idx < len(labels):
            plt.text(index - 0.5, index - 0.5, f"{chr(65 + label_idx)} {labels[label_idx + 1]}", color='white', fontsize=8, ha='center', va='center', rotation=0)
            
            # Determine if the index is for a top-level category or subcategory
            if idx < num_top_categories:
                top_level_indices[labels[label_idx + 1]] = index
                logging.info(f"Top-Level Submatrix boundary drawn for label: {labels[label_idx + 1]} at index: {index}")
            else:
                subcategory_indices[labels[label_idx + 1]] = index
                logging.info(f"Subcategory Submatrix boundary drawn for label: {labels[label_idx + 1]} at index: {index}")

    # Calculate submatrix bounds
    sorted_sub_indices = sorted(subcategory_indices.values())
    start_index = max(top_level_indices.values()) + 1  # Start after the last top-level category
    for i, sub_label in enumerate(sorted(subcategory_indices.keys())):
        end_index = subcategory_indices[sub_label]
        submatrix_bounds[sub_label[0]] = (start_index, end_index)
        start_index = end_index + 1  # Update start for the next submatrix
        logging.info(f"Submatrix bounds for {sub_label[0]}: start={submatrix_bounds[sub_label[0]][0]}, end={submatrix_bounds[sub_label[0]][1]}")

    # Place submatrix labels (e.g., "AA", "AB", "AC") using the submatrix indices
    for sub_label_x, x_index in subcategory_indices.items():
        for sub_label_y, y_index in subcategory_indices.items():
            # Adjust the coordinates by moving one unit up and to the left
            x_coord = x_index - 1
            y_coord = y_index - 1
            # Create the submatrix label
            submatrix_label = f"{sub_label_x[0]}{sub_label_y[0]}"
            # Place the label at the adjusted coordinates
            plt.text(x_coord, y_coord, submatrix_label, color='red', fontsize=10, ha='center', va='center')
            logging.info(f"Placed submatrix label '{submatrix_label}' at adjusted coordinates ({x_coord}, {y_coord})")

    # Place top-level category interaction labels
    top_level_keys = list(top_level_indices.keys())
    for i, label_x in enumerate(top_level_keys):
        for j, label_y in enumerate(top_level_keys):
            if i != j or i == j:  # Include diagonal for "AA", "BB", etc.
                # Use the exact coordinates from the top_level_indices
                x_coord = top_level_indices[label_x] - 1
                y_coord = top_level_indices[label_y] - 1
                # Create the top-level interaction label
                top_level_label = f"{label_x[0]}{label_y[0]}"
                # Place the label at the adjusted coordinates
                plt.text(x_coord, y_coord, top_level_label, color='red', fontsize=10, ha='center', va='center')
                logging.info(f"Placed top-level interaction label '{top_level_label}' at adjusted coordinates ({x_coord}, {y_coord})")

    plt.tight_layout()
    plt.show()

    # Log the dictionaries for later access
    logging.info(f"Top-Level Indices: {top_level_indices}")
    logging.info(f"Subcategory Indices: {subcategory_indices}")
    logging.info(f"Submatrix Bounds: {submatrix_bounds}")

    # Print the dictionaries
    print("Top-Level Indices:", top_level_indices)
    print("Subcategory Indices:", subcategory_indices)
    print("Submatrix Bounds:", submatrix_bounds)

    # Log significant interactions
    log_significant_interactions(matrix, labels, submatrix_bounds)

    return top_level_indices, subcategory_indices, submatrix_bounds

# ------------------------------------------------------------------
# Main Function
# ------------------------------------------------------------------
def print_weight_info(matrix, labels, submatrix_map):
    """
    Prints the weight information with absolute and submatrix coordinates.
    """
    num_categories = len(labels)
    num_top_categories = 3  # Assuming there are 3 top-level categories
    for i in range(num_categories):
        for j in range(num_categories):
            weight = matrix[i, j]
            if weight > 0:  # Only print non-zero weights
                # Determine submatrix coordinates
                top_cat_i = i // (num_top_categories + 1)
                subcat_i = i % (num_top_categories + 1)
                top_cat_j = j // (num_top_categories + 1)
                subcat_j = j % (num_top_categories + 1)
                
                # Use "O" for origin and "A-C" for top-level categories
                top_label_i = "O" if top_cat_i == 0 else chr(64 + top_cat_i)
                top_label_j = "O" if top_cat_j == 0 else chr(64 + top_cat_j)
                
                submatrix_coord = f"{top_label_i}{subcat_i + 1}{top_label_j}{subcat_j + 1}"
                interaction_notation = f"{top_label_i}{top_label_j}={weight:.2f}"
                
                print(f"Weight: {weight:.2f} at Absolute Coordinate: ({i}, {j}), Submatrix Coordinate: {submatrix_coord}, Interaction: '{labels[i]}' to '{labels[j]}', Notation: {interaction_notation}")

def append_submatrix_notation_to_labels(labels):
    """
    Appends submatrix notation to each label.
    """
    updated_labels = []
    num_top_categories = 3  # Assuming there are 3 top-level categories
    for idx, label in enumerate(labels):
        if idx == 0:
            notation = "O"  # Origin
        elif 1 <= idx <= num_top_categories:
            notation = chr(64 + idx)  # A, B, C for top-level categories
        elif idx == num_top_categories + 1:
            notation = "D"  # Last top-level category
        else:
            notation = ""  # No notation for subcategories
        
        updated_labels.append(f"{notation} {label}".strip())
    return updated_labels

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

    # 6. Highlight the top 20 most significant interactions, including inter-category
    all_categories = layout.labels  # Consider all categories for inter-category interactions
    layout.assign_top_interactions(all_categories, top_n=20)

    # 7. Assign weights to the first submatrix on the diagonal
    layout.assign_weights_to_first_submatrix()

    # Create a submatrix map and print the interactions
    submatrix_map = layout.create_submatrix_map()

    # Append submatrix notation to labels
    layout.labels = append_submatrix_notation_to_labels(layout.labels)

    # Print weight information with coordinates
    print_weight_info(layout.matrix, layout.labels, submatrix_map)

    # Show final layout and visualize with labeled submatrix boundaries
    layout.show_map()
    block_indices = layout.get_block_indices()
    visualize_matrix(layout.matrix, layout.labels, block_indices)

    # 9. HPC skip factor example
    total_blocks = len(layout.labels)
    accessed_blocks = max(1, total_blocks // 20)  # Access top 1/20 of the blocks
    skip_factor = 1.0 - (accessed_blocks / total_blocks)
    cost = 1.0 - skip_factor

    print(f"\nHPC Skip Factor Simulation:")
    print(f"  Accessed {accessed_blocks} of {total_blocks} blocks.")
    print(f"  skip_factor = {skip_factor:.2f}, HPC cost ≈ {cost:.2f}")

if __name__ == "__main__":
    main()