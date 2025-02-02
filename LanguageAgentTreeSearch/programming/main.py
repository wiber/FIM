import os
import openai
import json
import numpy as np
import matplotlib.pyplot as plt
from dotenv import load_dotenv
import random
import logging
import argparse
from matplotlib.patches import Rectangle
import sys

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ------------------------------------------------------------------
# Utility: Load environment variables (like OPENAI_API_KEY) from .env
# ------------------------------------------------------------------
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# LLM response cache
llm_cache = {}

# Function to cache LLM responses
def cache_llm_response(prompt, response):
    llm_cache[prompt] = response
    with open('llm_cache.json', 'w') as cache_file:
        json.dump(llm_cache, cache_file, indent=4)

# Function to get cached LLM response
def get_cached_llm_response(prompt):
    return llm_cache.get(prompt)

# Load existing cache if available
if os.path.exists('llm_cache.json'):
    with open('llm_cache.json', 'r') as cache_file:
        llm_cache = json.load(cache_file)

# Dictionary to track memory gradient usage
memory_gradient_usage = {
    "Immediate": 0,
    "Working": 0,
    "Long-Term": 0
}

# Dictionary to track inferred HPC costs
hpc_costs = {
    "Immediate": 0.1,
    "Working": 0.5,
    "Long-Term": 1.0
}

# Counter for LLM calls
llm_call_counter = 0

def increment_llm_call_counter():
    """
    Increments the LLM call counter and logs the call.
    """
    global llm_call_counter
    llm_call_counter += 1
    logging.info(f"LLM call #{llm_call_counter} made.")
    print(f"LLM call #{llm_call_counter} made.", flush=True)

def log_memory_usage(operation, memory_type):
    if memory_type in memory_gradient_usage:
        memory_gradient_usage[memory_type] += 1
        logging.info(f"Operation '{operation}' used {memory_type} memory.")
    else:
        logging.warning(f"Unknown memory type: {memory_type}")

def log_hpc_costs():
    total_cost = 0
    for memory_type, usage in memory_gradient_usage.items():
        cost = usage * hpc_costs[memory_type]
        total_cost += cost
        logging.info(f"HPC cost for {memory_type} memory: {cost:.2f} (Usage: {usage})")
    logging.info(f"Total inferred HPC cost: {total_cost:.2f}")
    return total_cost

def make_llm_call(prompt, memory_type="Immediate"):
    cached_response = get_cached_llm_response(prompt)
    if cached_response:
        logging.info(f"Using cached response for prompt: {prompt}")
        return cached_response

    increment_llm_call_counter()
    log_memory_usage("LLM Call", memory_type)
    response = openai_chat_completion(prompt)
    cache_llm_response(prompt, response)
    logging.info(f"LLM call made with {memory_type} memory.")
    print(f"LLM call made with {memory_type} memory.", flush=True)
    total_cost = log_hpc_costs()
    print(f"Total inferred HPC cost after LLM call: {total_cost:.2f}", flush=True)
    return response

def print_summary():
    print("\n=== Memory Gradient Usage ===", flush=True)
    for memory_type, usage in memory_gradient_usage.items():
        print(f"{memory_type}: {usage}", flush=True)

    print("\n=== HPC Costs ===", flush=True)
    total_cost = 0
    for memory_type, usage in memory_gradient_usage.items():
        cost = usage * hpc_costs[memory_type]
        total_cost += cost
        print(f"{memory_type} cost: {cost:.2f}", flush=True)

    print(f"\nTotal inferred HPC cost: {total_cost:.2f}", flush=True)
    return total_cost

def plot_matrix(matrix, labels):
    """
    Plots the adjacency matrix and overlays a bounding box defining the focus area.
    
    This function computes a "finability index" for the high-weight region within the 
    entire matrix. The finability index (FIM Focus) is defined as:
    
        FIM Focus = (L_focus / L_total)^2

    where:
      • L_total: Total dimension (side) of the square matrix.
      • L_focus: Maximum of the width or height of the bounding box.

    The threshold for high weight is set at 50% of the maximum value.
    
    In addition to the overall FIM Focus, this function prints a geometric interpretation
    of skip factors for several submatrices (e.g., A, B, C, D) defined by their start/end
    bounds. For a two-dimensional matrix the skip factor is computed as:

         Skip Factor = (submatrix_side / total_side)^2
                     = (submatrix_side^2) / (total_side^2)

    This demonstration is meant to show—using pure, inarguable geometry—that as a consequence
    of the Finability Index, a smaller submatrix represents only a fraction of the entire area.
    """
    # Create the matrix plot.
    plt.figure(figsize=(8, 6))
    plt.imshow(matrix, cmap='viridis', interpolation='none')
    plt.colorbar(label='Weight')
    plt.xticks(ticks=range(len(labels)), labels=labels, rotation=90)
    plt.yticks(ticks=range(len(labels)), labels=labels)
    plt.title('Adjacency Matrix')

    # --- FIM Bounding Box Logic ---
    threshold = matrix.max() * 0.5  # 50% of max weight is considered "high weight"
    indices = np.argwhere(matrix >= threshold)
    L_total = matrix.shape[0]  # Total dimensions (assumes square matrix)

    if indices.size > 0:
        # Find bounding indices where matrix values exceed the threshold.
        row_min, col_min = indices.min(axis=0)
        row_max, col_max = indices.max(axis=0)
        
        # Compute bounding box dimensions.
        width = col_max - col_min + 1
        height = row_max - row_min + 1
        L_focus = max(width, height)
        finability_index_focus = (L_focus / L_total) ** 2

        # Overlay bounding box on the plot.
        ax = plt.gca()
        rect = Rectangle((col_min - 0.5, row_min - 0.5), width, height,
                         edgecolor='red', facecolor='none', linewidth=2, linestyle='--')
        ax.add_patch(rect)

        # Annotate the plot with the computed finability index.
        plt.text(0.95, 0.05, f"FIM Focus: {finability_index_focus:.4f}",
                 transform=ax.transAxes,
                 fontsize=12, color="white", horizontalalignment="right",
                 bbox=dict(facecolor='red', alpha=0.5, edgecolor='none'))

        # Print narrative about the overall bounding box.
        info_text = (
            "=== Fractal Identity Matrix (FIM) Plot Annotation ===\n"
            f"Using threshold at 50% of max weight: {threshold:.2f}\n"
            f"Bounding Box: rows {row_min} to {row_max}, columns {col_min} to {col_max}\n"
            f"Width: {width}, Height: {height} -> Focus Range (max dimension): {L_focus}\n"
            f"Calculated Finability Index (squared focus ratio): {finability_index_focus:.4f}\n"
            "This represents the fraction of the matrix (squared) that is focused on versus scanning the whole matrix.\n"
        )
        print(info_text, flush=True)
        logging.info(info_text)
    else:
        print("No values found above the threshold for bounding box computation.", flush=True)
        logging.info("No values found above the threshold for bounding box computation.")

    # --- Additional: Geometric Skip Factor for Submatrices ---
    # These bounds come directly from our logs:
    #   For example, submatrix D is defined by start=15 and end=17.
    # The skip factor is computed as (end - start)^2 / (L_total)^2.
    submatrix_bounds = {
        "A": (6, 8),
        "B": (9, 11),
        "C": (12, 14),
        "D": (15, 17)
    }
    total_area = L_total ** 2  # Total matrix area = total_side^2
    print("--- Geometric Skip Factors for Submatrices (n=2) ---", flush=True)
    logging.info("--- Geometric Skip Factors for Submatrices (n=2) ---")
    for submatrix, (start, end) in submatrix_bounds.items():
        # Here we use (end - start) as the submatrix's linear side.
        sub_length = end - start  # For D: 17 - 15 = 2, for example.
        sub_area = sub_length ** 2    # Area of the submatrix (square of the side).
        skip_factor = sub_area / total_area  # Geometric skip factor (area ratio).
        msg = (
            f"Submatrix {submatrix}: start = {start}, end = {end}\n"
            f"  Linear length (end - start) = {end} - {start} = {sub_length}; Total dimension = {L_total}\n"
            f"  Submatrix area = (end - start)^2 = {sub_length}^2 = {sub_area}; Total matrix area = {L_total}^2 = {total_area}\n"
            f"  Skip factor (area ratio) = (submatrix_side)^2 / (total_side)^2 = {skip_factor:.4f}\n"
            f"  (This is pure geometry: the fraction of the matrix's area occupied by this submatrix.)\n"
        )
        # Print the skip factor immediately in each iteration.
        print(msg, flush=True)
        logging.info(msg)

    plt.tight_layout()
    plt.show()

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
        logging.error(f"[Error] LLM API call failed: {e}")
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
        print(f"[LLM] Similarity between '{label_a}' and '{label_b}': {weight}", flush=True)
        
        # Insert the call to track costing
        make_llm_call(prompt, memory_type="Immediate")
        
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

    # Insert the call to track costing for long-term memory
    make_llm_call(prompt, memory_type="Long-Term")

    response = openai_chat_completion(prompt, max_tokens=50)
    try:
        # Parse the response into a list of weights
        weights = [float(w.strip()) for w in response.split(',') if w.strip()]
        # Clamp weights between 0 and 1
        weights = [max(0.0, min(1.0, w)) for w in weights]
        return {pair: weight for pair, weight in zip(comparisons, weights)}
    except Exception as e:
        logging.error(f"[Error] Failed to parse batch similarity weights: {e}")
        logging.error(f"Response received: {response}")
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

        print(f"[Matrix Update] Added '{new_label}' at index {old_size}", flush=True)

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
        print(f"[Top-Level Insert] from '{self.labels[0]}' to '{label}' at row={cat_idx} with weight={weight}", flush=True)

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
            print(f"[Subcategory Insert] from '{parent_label}' to '{subcat}' at row={subcat_idx} with weight={weight}", flush=True)
            
            # Insert the call to track costing for working memory
            make_llm_call(f"Subcategory Insert from '{parent_label}' to '{subcat}'", memory_type="Working")

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
            print(f"[Top Interaction] from '{a}' to '{b}' with weight={weight}", flush=True)

            # Insert the call to track costing for long-term memory
            make_llm_call(f"Top Interaction from '{a}' to '{b}'", memory_type="Long-Term")

    def show_map(self):
        """Prints the current matrix and label mapping."""
        print("\n=== Current Matrix & Labels ===", flush=True)
        for idx, label in enumerate(self.labels):
            print(f"{idx}: {label}", flush=True)
        print(self.matrix, flush=True)

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
                print(f"[LLM Assignment] Weight between '{label_a}' and '{label_b}': {weight}", flush=True)
        except json.JSONDecodeError:
            print(f"[Warning] Failed to parse LLM response for first submatrix weights. Response: {response}", flush=True)

    def create_submatrix_map(self):
        submatrix_map = {}
        step = len(self.labels) // 4  # Example step size for submatrices
        for i, label in enumerate(self.labels):
            if i % step == 0:
                submatrix_map[label] = (i, i + step - 1)
        return submatrix_map

    def visualize_matrix(self):
        plt.figure(figsize=(12, 10))
        plt.imshow(self.matrix, cmap='viridis', interpolation='none')
        plt.colorbar(label='Similarity Weight')
        plt.xticks(ticks=range(len(self.labels)), labels=self.labels, rotation=90)
        plt.yticks(ticks=range(len(self.labels)), labels=self.labels)
        plt.title('FractalSymSorter Adjacency Matrix')

        # Define submatrix boundaries
        submatrix_bounds = self.create_submatrix_map()

        # Draw lines to indicate submatrix boundaries
        for label, (start, end) in submatrix_bounds.items():
            plt.axhline(y=start - 0.5, color='white', linestyle='--', linewidth=0.5)
            plt.axvline(x=start - 0.5, color='white', linestyle='--', linewidth=0.5)
            plt.axhline(y=end - 0.5, color='white', linestyle='--', linewidth=0.5)
            plt.axvline(x=end - 0.5, color='white', linestyle='--', linewidth=0.5)

        # Add red labels for top-left corner of each submatrix
        for label, (start, end) in submatrix_bounds.items():
            plt.text(start, start, label, color='red', fontsize=10, ha='center', va='center')

        plt.tight_layout()
        plt.show()

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
                print(interaction_info, flush=True)

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

    # Calculate submatrix bounds with a passed matrix size state
    sorted_sub_indices = sorted(subcategory_indices.values())
    matrix_size = len(labels)  # Passed variable for matrix size (e.g., number of labels)
    total_side = matrix_size  # Total matrix dimension (assumed to be square)

    # Maintain a state object that tracks matrix size, categories, submatrix bounds,
    # placed interactions, and a prefix dictionary.
    matrix_state = {
        "matrix_size": total_side,
        "categories": labels,
        "submatrix_bounds": {},       # To be updated with submatrix bounds as {key: (start, end)}
        "placed_interactions": {},    # To store placed interactions, e.g. {"CD": (3,4)}
        "prefix_dict": {}             # To store prefix mappings, e.g. {"CB2": "CD"}
    }

    # Define a function that updates and prints the current matrix state.
    def update_matrix_size_state(state):
        info = (
            f"Matrix Size: {state['matrix_size']}\n"
            f"Categories: {state['categories']}\n"
            f"Submatrix Bounds: {state['submatrix_bounds']}\n"
            f"Placed Interactions: {state['placed_interactions']}\n"
            f"Prefix Dict: {state['prefix_dict']}"
        )
        print(info, flush=True)
        logging.info(info)

    # Call the state update function initially.
    update_matrix_size_state(matrix_state)
    
    # Save a top-level placed interaction.
    matrix_state["placed_interactions"]["CD"] = (3, 4)
    print("Placed top-level interaction label 'CD' at adjusted coordinates (3, 4)", flush=True)
    logging.info("Placed top-level interaction label 'CD' at adjusted coordinates (3, 4)")
    
    # Add a prefix mapping; for example, "CB2" maps to "CD" (token label).
    matrix_state["prefix_dict"]["CB2"] = "CD"
    print("Added prefix mapping: CB2 -> CD", flush=True)
    logging.info("Added prefix mapping: CB2 -> CD")
    
    # Re-print state after adding interactions and prefix mapping.
    update_matrix_size_state(matrix_state)
    
    start_index = max(top_level_indices.values()) + 1  # Start index after the last top-level category
    for i, sub_label in enumerate(sorted(subcategory_indices.keys())):
        end_index = subcategory_indices[sub_label]
        key = sub_label[0]
        # Save submatrix bounds in our state object.
        matrix_state["submatrix_bounds"][key] = (start_index, end_index)

        # Update state by printing the current matrix state.
        update_matrix_size_state(matrix_state)
    
        # Compute the linear length of this submatrix.
        sub_length = end_index - start_index  
        # Compute the skip factor as (submatrix_side)^2 / (total_side)^2.
        skip_factor = (sub_length ** 2) / (total_side ** 2)
        focus_percent = skip_factor * 100.0  # Percentage of the full matrix that is focused on.
        skip_percent = 100.0 - focus_percent   # Percentage of the full matrix that is skipped.
    
        # Print the geometric comparison.
        print(f"Focus Area: {focus_percent:.2f}% of full matrix", flush=True)
        print(f"{skip_percent:.2f}% of data skipped.", flush=True)
        logging.info(f"Focus Area: {focus_percent:.2f}% of full matrix")
        logging.info(f"{skip_percent:.2f}% of data skipped.")
    
        print(
            f"Skip factor for submatrix {key}: ({end_index} - {start_index})^2 / ({total_side})^2 = {skip_factor:.4f}",
            flush=True
        )
        logging.info(f"Skip factor for submatrix {key}: ({end_index} - {start_index})^2 / ({total_side})^2 = {skip_factor:.4f}")
    
        start_index = end_index + 1  # Update start for the next submatrix.
        logging.info(f"Submatrix bounds for {key}: start={matrix_state['submatrix_bounds'][key][0]}, end={matrix_state['submatrix_bounds'][key][1]}")

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
    print("Top-Level Indices:", top_level_indices, flush=True)
    print("Subcategory Indices:", subcategory_indices, flush=True)
    print("Submatrix Bounds:", submatrix_bounds, flush=True)

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
                
                print(f"Weight: {weight:.2f} at Absolute Coordinate: ({i}, {j}), Submatrix Coordinate: {submatrix_coord}, Interaction: '{labels[i]}' to '{labels[j]}', Notation: {interaction_notation}", flush=True)

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

def process_multiple_batches(all_comparisons):
    """
    Processes multiple batches of category pairs.
    """
    for batch in all_comparisons:
        weights = assign_similarity_weights_batch(batch)
        # Do something with the weights
        print(weights, flush=True)

class MockLLM:
    def __init__(self, schedule_file):
        if os.path.exists(schedule_file):
            with open(schedule_file, 'r') as file:
                self.responses = json.load(file)
        else:
            self.responses = {}

    def get_response(self, prompt):
        return self.responses.get(prompt, "No mock response available.")

def real_llm_call(prompt):
    # Simulate a real LLM call
    response = f"Real LLM response for {prompt}"
    return response

def mock_llm_call(prompt, mock_llm):
    return mock_llm.get_response(prompt)

# ----- New Parallel Track: Dynamic Hierarchy Data Structure & Sorting -----

class CategoryNode:
    def __init__(self, name, weight=0.0, children=None):
        """
        A node representing a category in a hierarchy.
        
        Args:
            name (str): The category name.
            weight (float): A score used for sorting (e.g., relevance).
            children (list[CategoryNode]): Subcategories.
        """
        self.name = name
        self.weight = weight
        self.children = children if children is not None else []

    def add_child(self, child_node):
        """Add a subcategory."""
        self.children.append(child_node)

    def sort_children(self):
        """Sort subcategories based on their weight (descending)."""
        self.children.sort(key=lambda x: x.weight, reverse=True)

    def __repr__(self):
        return f"{self.name}({self.weight})"


class DynamicHierarchyBuilder:
    def __init__(self, top_level_nodes):
        """
        Build and manage a dynamic hierarchy of categories.
        
        This class will compute a one-dimensional, sorted axis order (for both rows and columns),
        along with block boundaries for each top-level category.
        
        Args:
            top_level_nodes (list[CategoryNode]): The top-level categories.
        """
        self.top_level_nodes = top_level_nodes
        self.axis_order = []     # Flattened list of nodes (top-level + subcategories).
        self.boundary_map = {}   # Map: top-level category name -> (start_index, end_index)

    def compute_axis_order(self):
        """
        Compute a one-dimensional axis ordering from the tree.
        
        Sort top-level nodes, have each
        top-level node precede its sorted children in the flattened list,
        and record their index boundaries.
        """
        # Sort the top-level nodes (e.g., by weight descending)
        self.top_level_nodes.sort(key=lambda node: node.weight, reverse=True)
        self.axis_order = []
        self.boundary_map = {}
        start_index = 0
        
        for top_node in self.top_level_nodes:
            top_node.sort_children()
            # The block consists of the top-level node first, then its children.
            block = [top_node] + top_node.children
            block_length = len(block)
            self.axis_order.extend(block)
            # Record boundaries: (start, end) where end is exclusive.
            self.boundary_map[top_node.name] = (start_index, start_index + block_length)
            start_index += block_length

        print("\n[Dynamic Hierarchy] Computed axis order:", flush=True)
        self.print_axis_order()
        print("\n[Dynamic Hierarchy] Computed boundary map:", flush=True)
        self.print_boundary_map()

    def print_axis_order(self):
        for idx, node in enumerate(self.axis_order):
            print(f"  Index {idx}: {node}", flush=True)

    def print_boundary_map(self):
        for top_name, (start, end) in self.boundary_map.items():
            print(f"  {top_name}: start={start}, end={end}", flush=True)

    def get_axis_labels(self):
        """Return a list of labels (names) in the computed order."""
        return [node.name for node in self.axis_order]

    def build_matrix(self):
        """
        Build a 2D weight matrix (as a NumPy array) for the current axis order.

        Even though the weight function here can be asymmetric,
        the axis ordering (i.e., the labels) remains symmetric.
        """
        n = len(self.axis_order)
        matrix = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                matrix[i, j] = self.compute_weight(self.axis_order[i], self.axis_order[j])
        return matrix

    def compute_weight(self, node_i, node_j):
        """
        Replace this with your own logic (or LLM call) on how to compute the weight between two categories.
        For demonstration we use a random value.
        """
        return random.uniform(0, 1)


def run_dynamic_hierarchy_demo():
    """
    Demonstrates the new dynamic hierarchical sorting track.
    Builds a hierarchy of categories, computes the axis ordering and boundaries,
    then constructs and visualizes the weight matrix.
    """
    print("\n==== Running Dynamic Hierarchy Demo ====", flush=True)
    
    # Define some top-level nodes and assign subcategories.
    top1 = CategoryNode("TopCat1", weight=0.9)
    top1.add_child(CategoryNode("TopCat1_Sub1", weight=0.85))
    top1.add_child(CategoryNode("TopCat1_Sub2", weight=0.80))
    
    top2 = CategoryNode("TopCat2", weight=0.8)
    top2.add_child(CategoryNode("TopCat2_Sub1", weight=0.75))
    top2.add_child(CategoryNode("TopCat2_Sub2", weight=0.70))
    top2.add_child(CategoryNode("TopCat2_Sub3", weight=0.65))
    
    top3 = CategoryNode("TopCat3", weight=0.85)
    top3.add_child(CategoryNode("TopCat3_Sub1", weight=0.80))
    
    top_levels = [top1, top2, top3]
    
    # Build the dynamic hierarchy.
    builder = DynamicHierarchyBuilder(top_levels)
    builder.compute_axis_order()
    
    axis_labels = builder.get_axis_labels()
    matrix_dynamic = builder.build_matrix()
    
    print("\n[Dynamic Hierarchy] Axis Labels:", axis_labels, flush=True)
    print("[Dynamic Hierarchy] Weight Matrix Shape:", matrix_dynamic.shape, flush=True)
    
    # Visualize using the already defined visualize_matrix() function.
    # This will show the matrix and draw white lines at the computed boundaries.
    visualize_matrix(matrix_dynamic, axis_labels, builder.boundary_map)


# ------------------------------------------------------------------
# Main Function
# ------------------------------------------------------------------
def main():
    print("Starting main function...", flush=True)  # Debugging print
    try:
        # 1. Define the origin category
        origin_description = "Define the origin category for the FractalSymSorter based on HPC interpretability."
        origin_list = get_top_level_categories(origin_description, num_categories=1)
        if not origin_list:
            print("[Error] Failed to retrieve origin category.", flush=True)
            return

        origin_category = origin_list[0]
        print(f"Origin Category: {origin_category}", flush=True)

        # 2. Prompt for 4 more top-level categories to add incrementally
        main_description = (
            "Now let's define 4 more top-level categories for HPC interpretability, aligned with the Fractal Identity Matrix (FIM) objectives."
            " Return exactly 4 major categories in a valid JSON array of strings."
        )
        more_cats = get_top_level_categories(main_description, num_categories=4)
        print(f"Top-Level Categories: {more_cats}", flush=True)

        # 3. Initialize FractalSymSorter with the origin pivot
        layout = FractalSymSorter(matrix=[[1.0]], labels=[origin_category], use_llm_weights=True)

        # 4. Insert all top-level categories first
        for cat in more_cats:
            layout.insert_top_cat(cat)

        # 5. Insert subcategories for each top-level category in sorted blocks
        for cat in more_cats:
            subcats = get_subcategories(cat, num_subcategories=3)
            layout.insert_subcats(cat, subcats)

        # 6. Highlight the top 20 most significant interactions, including inter-category
        all_categories = layout.labels
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
        accessed_blocks = max(1, total_blocks // 20)
        skip_factor = 1.0 - (accessed_blocks / total_blocks)
        cost = 1.0 - skip_factor

        print(f"\nHPC Skip Factor Simulation:", flush=True)
        print(f"  Accessed {accessed_blocks} of {total_blocks} blocks.", flush=True)
        print(f"  skip_factor = {skip_factor:.2f}, HPC cost ≈ {cost:.2f}", flush=True)

        # Example usage
        make_llm_call("Example prompt", memory_type="Immediate")
        total_cost = log_hpc_costs()
        print(f"Total LLM calls: {llm_call_counter}, Total inferred HPC cost: {total_cost:.2f}", flush=True)

        make_llm_call("Another prompt", memory_type="Working")
        total_cost = log_hpc_costs()
        print(f"Total LLM calls: {llm_call_counter}, Total inferred HPC cost: {total_cost:.2f}", flush=True)

        make_llm_call("Yet another prompt", memory_type="Long-Term")
        total_cost = log_hpc_costs()
        print(f"Total LLM calls: {llm_call_counter}, Total inferred HPC cost: {total_cost:.2f}", flush=True)

        # Print the summary of costs and memory usage
        total_cost = print_summary()
        print(f"Final Total LLM calls: {llm_call_counter}, Final Total inferred HPC cost: {total_cost:.2f}", flush=True)

        # Log the HPC costs
        log_hpc_costs()

        # Example matrix and labels for plotting
        matrix = np.random.rand(5, 5)
        labels = ["A", "B", "C", "D", "E"]
        plot_matrix(matrix, labels)

        # Print the total number of LLM calls
        print(f"Total LLM calls: {llm_call_counter}", flush=True)

        # Example usage of process_multiple_batches
        all_comparisons = [
            [("Category1", "Category2"), ("Category3", "Category4")],
            [("Category5", "Category6"), ("Category7", "Category8")],
        ]

        process_multiple_batches(all_comparisons)

        # At some point (or via a flag) we can call the dynamic demo:
        run_dynamic_hierarchy_demo()

    except Exception as e:
        logging.error(f"[Error] An error occurred in the main function: {e}", exc_info=True)
        print(f"[Error] An error occurred in the main function: {e}", flush=True)

if __name__ == "__main__":
    print("Executing script...", flush=True)  # Debugging print
    main()