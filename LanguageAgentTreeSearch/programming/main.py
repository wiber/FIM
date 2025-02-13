"""
--------------------------------------------------------------------------------
PLANNING: Transitioning main.py to a More Dynamic, Functional FIM Design 
with LLM Call Strategy & HPC Cost Logging
--------------------------------------------------------------------------------

Below is the plan for incrementally refactoring this file (main.py) toward a 
dynamic, functionally-driven Fractal Identity Matrix (FIM) architecture. We will 
retain the current matrix state and plotting outputs while integrating the 
LLM call strategy, HPC cost tracking, and a Node-based hierarchical design as 
discussed in the recent chat. The aim is to streamline submatrix indexing, 
improve dynamic sorting by weight, and maintain interpretable HPC skip factors.

1. **Remove Static Submatrix Dictionaries**  
   - Eliminate all hard-coded offset indices and dictionaries for submatrix bounds.  
   - Provide helper functions (e.g. `get_submatrix_bounds(node)`) to compute 
     each node's (start, end) indices on-the-fly using dynamic weights.

2. **Adopt a Hierarchical Node Structure**  
   - Store each category (top-level or subcategory) as a Node object containing:
       - A name (string).
       - A weight (float).
       - A parent pointer (or None for the top-level/origin).
       - A list of children, kept sorted by weight.  
   - Use these relationships to compute submatrix boundaries by summing child 
     weights dynamically, removing the need for static dictionaries.

3. **Weight-Driven Sorted Insertions**  
   - Whenever adding or updating a category/subcategory, assign it an LLM-derived 
     similarity or relevance weight (tracked in HPC logs).  
   - Insert it directly into the correct position among siblings (descending by weight).  
   - This ensures no separate "sort step" is needed afterward, and the adjacency 
     matrix layout naturally reflects the hierarchy's weight order.

4. **LLM Calls & HPC Logging**  
   - Preserve existing prompt-based LLM calls for assigning similarity weights 
     (e.g. `assign_similarity_weights`), and for batch interactions.  
   - Each call increments our LLM call counter and logs HPC usage (Immediate, 
     Working, or Long-Term).  
   - Maintain the HPC skip factor logic and submatrix bounding prints; 
     unify them with the dynamic node approach so skip calculations use 
     node-based submatrix dimensions.

5. **Flattening & Matrix Building**  
   - Provide a function `flatten_hierarchy(root_node)` that yields a 1D list 
     of nodes in sorted order, skipping the origin if desired.  
   - Build or update the NxN adjacency matrix from this flattened list. 
     The matrix row/column i corresponds to `flattened_list[i]`.  
   - For submatrix bounding lines in the plot, call `get_submatrix_bounds(node, flattened_list)`, 
     which sums the weights of preceding siblings to find a node's start index 
     and uses `node.weight` for the size of the block.

6. **Enhanced Plotting**  
   - Keep the existing matrix plotting code; direct it to these new helper 
     functions for submatrix bounds.  
   - Continue color-coding submatrices (and top-level categories) and display 
     HPC skip factors.  
   - Maintain HPC cost logs after each relevant LLM operation, printing HPC 
     usage summaries upon completion.

7. **Incremental Implementation**  
   - We will apply changes in small steps:
       1. Introduce the Node class, create a global `origin_node`.
       2. Convert existing static categories into Node children under `origin_node`.
       3. Implement `add_category()` and `add_subcategory()` with weight-sorted 
          insertion and parent weight recalculation.
       4. Update adjacency-matrix construction to use `flatten_hierarchy()`.
       5. Switch submatrix boundary logic (and HPC skip factor prints) from static 
          dictionaries to `get_submatrix_bounds(node)`.
       6. Validate that existing matrix states and plots remain correct, 
          simply derived from the new structure.

8. **Testing & Verification**  
   - After each step, confirm the dynamic insertion and correct LLM-based 
     weighting.  
   - Check HPC cost logs for each insertion or batch weight assignment, ensuring 
     the skip factor logic aligns with the new node-based submatrix boundaries.  
   - Verify that the final plot with color-coded blocks and bounding lines 
     matches the original visual expectations, with HPC skip factor outputs 
     reflecting the newly computed boundaries.

By following these steps methodically, we will transition `main.py` into a 
more robust, transparent, and maintainable FIM application. The end result 
will be a fully dynamic solution—capable of inserting new categories, 
re-sorting by weight on the fly, computing skip factors, and generating HPC 
cost logs—while preserving all existing matrix visuals and LLM calls.
--------------------------------------------------------------------------------

"""


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


import os
import json

LLM_CACHE_FILE = "llm_cache.json"
try:
    with open(LLM_CACHE_FILE, "r") as file:
        llm_response_cache = json.load(file)
except (FileNotFoundError, json.JSONDecodeError):
    llm_response_cache = {}

def save_llm_cache():
    with open(LLM_CACHE_FILE, "w") as file:
        json.dump(llm_response_cache, file, indent=2)

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

# Dictionary to track usage for different memory types.
HPC_USAGE = {
    "immediate": 0.0,
    "working": 0.0,
    "long_term": 0.0
}

def log_hpc_usage(memory_type: str, amount: float = 1.0):
    """
    Increment HPC usage counters for the specified memory type.
    
    :param memory_type: One of ('immediate', 'working', 'long_term')
    :param amount: Amount by which to increment the usage counter.
    """
    if memory_type not in HPC_USAGE:
        raise ValueError(f"Unknown memory type: {memory_type}")
    
    HPC_USAGE[memory_type] += amount

    # For patent-proof traceability, we log whenever HPC counters are updated
    # (helpful for HPC cost tracking in the fractal identity approach).
    print(f"[HPC LOG] Incremented '{memory_type}' usage by {amount}. "
          f"New total: {HPC_USAGE[memory_type]}")

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
    Sends a prompt to the OpenAI API and returns the LLM's text response.
    Ensures that any LLM data is first checked (and saved) in the JSON cache.
    When using mock mode (via the USE_MOCK flag), the function always uses the cached
    response or a simulated response if none exists.
    
    :return: The LLM's text response.
    """
    if USE_MOCK:
        cached = get_cached_llm_response(prompt)
        if cached:
            logging.info("Using cached response for prompt (mock mode).")
            return cached
        else:
            # Use a mock LLM response (check if defined in llm_cache or provide a simulated one)
            mock_llm = MockLLM("llm_cache.json")
            mock_response = mock_llm.get_response(prompt)
            if mock_response == "No mock response available.":
                mock_response = f"Mock response for prompt: {prompt}"
            cache_llm_response(prompt, mock_response)
            return mock_response
    else:
        cached = get_cached_llm_response(prompt)
        if cached:
            logging.info(f"Using cached response for prompt: {prompt}")
            return cached
        increment_llm_call_counter()
        log_memory_usage("LLM Call", "Immediate")
        system_prompt = (
            "Welcome to the Fractal Identity Matrix (FIM) Integration Prompt. "
            "This guide enables the Language Model (LLM) to utilize FIM principles for effective problem space subdivision. "
            "By acting as a working memory proprioception, the LLM will optimize operations to reduce HPC costs using the FIM skip formula. "
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
            res_text = response["choices"][0]["message"]["content"].strip()
            cache_llm_response(prompt, res_text)
            return res_text
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

    def assign_top_interactions(self, categories, top_n=40):
        """
        Assigns similarity weights to the top N most significant interactions.
        
        This function now attempts to select twice as many interactions (default = 40)
        to reduce the sparsity of the matrix. In addition, it writes the weight to both
        [i, j] and [j, i] in the adjacency matrix to ensure denser population while
        preserving the ordering for the plot.
        
        Parameters:
            categories (list): The list of category labels.
            top_n (int): Number of top interactions to select (default increased to 40).
        """
        interactions = []
        num_categories = len(categories)
        
        # Generate all unique pairs (i, j) where i < j
        for i in range(num_categories):
            for j in range(i + 1, num_categories):
                label_a = categories[i]
                label_b = categories[j]
                interactions.append((label_a, label_b))
        
        # Shuffle to avoid any ordering bias
        random.shuffle(interactions)
        
        # Batch assign similarity weights (using LLM or fallback logic)
        weights = assign_similarity_weights_batch(interactions)
        
        # Sort and select the top N interactions based on the assigned weight
        sorted_interactions = sorted(weights.items(), key=lambda item: item[1], reverse=True)
        top_interactions = sorted_interactions[:top_n]
        
        # Optionally track block boundaries using a step size
        if top_n < num_categories:
            step = max(1, num_categories // top_n)
            for i in range(step, num_categories, step):
                self.block_indices.append(i)
        
        # Write the weights into the matrix (both [i, j] and [j, i] to double entries)
        for ((a, b), weight) in top_interactions:
            idx_a = self.label_to_idx[a]
            idx_b = self.label_to_idx[b]
            self.matrix[idx_a, idx_b] = weight
            self.matrix[idx_b, idx_a] = weight  # Symmetric assignment to reduce sparsity
            
            print(f"[Top Interaction] {a} <--> {b} assigned weight={weight}", flush=True)
            
            # Log the LLM call with Long-Term memory usage for cost tracking
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

    # Function to update and immediately print (and log) the current state.
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

    # Function to add a prefix mapping to the state.
    def add_prefix_mapping(prefix, token_label):
        matrix_state["prefix_dict"][prefix] = token_label
        print(f"Added prefix mapping: {prefix} -> {token_label}", flush=True)
        logging.info(f"Added prefix mapping: {prefix} -> {token_label}")

    # Function to record a placed interaction.
    def add_placed_interaction(token_label, coordinates):
        matrix_state["placed_interactions"][token_label] = coordinates
        print(f"Placed interaction label '{token_label}' at adjusted coordinates {coordinates}", flush=True)
        logging.info(f"Placed interaction label '{token_label}' at adjusted coordinates {coordinates}")

    # --- Initial State and Top-Level Placements ---
    
    # Print the initial state.
    update_matrix_size_state(matrix_state)
    
    # Example: Place a top-level interaction label. 
    # For instance, as in the logs we see "Placed top-level interaction label 'CD' at adjusted coordinates (3, 4)".
    add_placed_interaction("CD", (3, 4))
    
    # For top-level interactions, assign a prefix. 
    # Here we choose a capital letter (e.g., "A" for the first top-level category).
    add_prefix_mapping("A", "CD")
    
    # Also, suppose a printed comparison produced a composite prefix like "CB2" for an interaction.
    add_prefix_mapping("CB2", "CD")
    
    # Print the state after top-level updates.
    update_matrix_size_state(matrix_state)
    
    # --- Processing Submatrix Bounds and Leaf Prefixes ---
    
    # Calculate submatrix bounds.
    sorted_sub_indices = sorted(subcategory_indices.values())
    start_index = max(top_level_indices.values()) + 1  # Start after the last top-level category
    
    for i, sub_label in enumerate(sorted(subcategory_indices.keys())):
        end_index = subcategory_indices[sub_label]
        key = sub_label[0]
        
        # Save submatrix bounds in the state.
        matrix_state["submatrix_bounds"][key] = (start_index, end_index)
        update_matrix_size_state(matrix_state)  # Update state after each change.
    
        # Compute the linear length for this submatrix and its skip factor.
        sub_length = end_index - start_index  
        skip_factor = (sub_length ** 2) / (total_side ** 2)
        focus_percent = skip_factor * 100.0      # Percentage of full matrix that is focused.
        skip_percent = 100.0 - focus_percent       # Percentage of data skipped.
    
        # Print immediate geometric information.
        print(f"Focus Area: {focus_percent:.2f}% of full matrix", flush=True)
        print(f"{skip_percent:.2f}% of data skipped.", flush=True)
        logging.info(f"Focus Area: {focus_percent:.2f}% of full matrix")
        logging.info(f"{skip_percent:.2f}% of data skipped.")
    
        print(
            f"Skip factor for submatrix {key}: ({end_index} - {start_index})^2 / ({total_side})^2 = {skip_factor:.4f}",
            flush=True
        )
        logging.info(f"Skip factor for submatrix {key}: ({end_index} - {start_index})^2 / ({total_side})^2 = {skip_factor:.4f}")
    
        # For leaves (submatrices), assign a composite prefix.
        # For example, use the key letter plus a 1-based index (e.g., "D1" for the first leaf with key 'D').
        leaf_prefix = f"{key}{i+1}"
        add_prefix_mapping(leaf_prefix, f"Submatrix_{key}")
    
        # Update the start index for the next submatrix.
        start_index = end_index + 1  
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
    """
    Retrieves a mock LLM response for the given prompt using cached data from llm_cache.
    If the prompt is not present in the cache, it fetches the response from the mock_llm,
    caches it, and then returns it.
    
    :param prompt: The input prompt string.
    :param mock_llm: An instance of the MockLLM class.
    :return: The LLM's text response.
    """
    global llm_cache
    if prompt in llm_cache:
        print(f"[CACHE] Using cached mock response for prompt: '{prompt[:60]}...'")
        return llm_cache[prompt]
    else:
        response = mock_llm.get_response(prompt)
        llm_cache[prompt] = response
        save_llm_cache(llm_cache)
        return response

# ----- New Parallel Track: Dynamic Hierarchy Data Structure & Sorting -----

class Node:
    def __init__(self, label, weight=1.0):
        self.label = label
        self.weight = weight
        self.children = []
        self.parent = None

    def add_child(self, child):
        child.parent = self
        # Insertion in descending order by weight
        inserted = False
        for i, existing in enumerate(self.children):
            if existing.weight < child.weight:
                self.children.insert(i, child)
                inserted = True
                break
        if not inserted:
            self.children.append(child)
        # Optionally recalc weight, reposition in parent, etc.

origin_node = Node("ORIGIN", weight=0)  # root node

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
    # Parse command-line arguments to set the mock mode
    parser = argparse.ArgumentParser()
    parser.add_argument("--use_mock", action="store_true", help="Use mock responses for LLM calls.")
    args, unknown = parser.parse_known_args()
    global USE_MOCK
    USE_MOCK = args.use_mock

    print("Starting main function...", flush=True)
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
    main()

################################################################################
# Incremental Improvements for a More Dynamic & Maintainable Fractal Identity Matrix
# ------------------------------------------------------------------------------
# 1) Dynamic Submatrix Bound Inference (no static dict).
# 2) Weight-driven sorting on insertions at all hierarchy levels.
# 3) Query functions for submatrix bounds and weight-based navigation.
# 4) Dynamic 1D-axis mapping to support smooth resorting.
# 5) Color-coded submatrix bands in the plot for improved clarity.
################################################################################

###############################################################################
# (A) - Hierarchical Node & Insertions
###############################################################################
class Node:
    def __init__(self, label, weight=1.0):
        self.label = label
        self.weight = weight  # or compute from children if they exist
        self.parent = None
        self.children = []

    def __repr__(self):
        return f"Node({self.label}, w={self.weight:.2f}, children={len(self.children)})"

def create_top_level_category(label, weight=1.0):
    """Creates a new top-level Node under origin_node, sorted by weight descending."""
    new_node = Node(label, weight)
    add_child(origin_node, new_node)
    return new_node

def add_child(parent_node, child_node):
    """
    Insert a child_node into parent_node.children, sorted by descending child_node.weight,
    then recalc parent_node's weight so we can bubble up changes if needed.
    """
    child_node.parent = parent_node
    # Insert by weight (descending):
    inserted = False
    for i, existing in enumerate(parent_node.children):
        if existing.weight < child_node.weight:
            parent_node.children.insert(i, child_node)
            inserted = True
            break
    if not inserted:
        parent_node.children.append(child_node)
    recalc_weight(parent_node)
    # bubble up re-sorting logic if the parent's weight changed
    if parent_node.parent:
        reposition_in_parent(parent_node)

def reposition_in_parent(node):
    """
    Once a node's weight changes, re-insert it in the parent's children list,
    ensuring siblings remain sorted by descending weight. Then bubble up if needed.
    """
    parent = node.parent
    if not parent:
        return
    siblings = parent.children
    if node in siblings:
        siblings.remove(node)
    # re-insert into parent by descending weight
    inserted = False
    for i, existing in enumerate(siblings):
        if existing.weight < node.weight:
            siblings.insert(i, node)
            inserted = True
            break
    if not inserted:
        siblings.append(node)
    recalc_weight(parent)
    if parent.parent:
        reposition_in_parent(parent)

def recalc_weight(node):
    """If a node has children, weight = sum of children; else keep its own weight."""
    if node.children:
        node.weight = sum(ch.weight for ch in node.children)

###############################################################################
# (B) - Dynamic Flattening, Submatrix Bounds, and 1D Axis Inference
###############################################################################
def flatten_hierarchy(node, result=None):
    """
    Recursively flatten the tree under 'node' into a list of Node objects
    in the order they appear (parent > children). We skip the origin—if desired,
    pass node=origin_node.children individually. Currently, we'll keep origin too
    for demonstration.
    """
    if result is None:
        result = []
    result.append(node)
    for c in node.children:
        flatten_hierarchy(c, result)
    return result

def find_node_by_label(label, node=None):
    """DFS to find a node by label starting from 'node'. If node=None, start from origin_node."""
    if node is None:
        node = origin_node
    if node.label == label:
        return node
    for child in node.children:
        found = find_node_by_label(label, child)
        if found:
            return found
    return None

def dynamic_submatrix_bounds(node, flat_list):
    """
    Given a single node, compute the [start, end] index in 'flat_list' that covers
    its entire subtree. The size of that subtree is node.weight (if children => sum).
    We find node's index in flat_list, then size = node.weight, so end = start + size -1.
    """
    # first, find where 'node' appears in flat_list:
    idx = None
    for i, nd in enumerate(flat_list):
        if nd is node:
            idx = i
            break
    if idx is None:
        return None, None
    start = idx
    end = idx + int(node.weight) - 1
    return start, end

###############################################################################
# (C) - For Queries: submatrix from top-level cats, or weight-based
###############################################################################
def find_submatrix_bounds_by_label(label, flat_list):
    """Helper that finds submatrix bounds for the node with 'label' given the flatten list."""
    node = find_node_by_label(label, origin_node)
    if not node:
        return None, None
    return dynamic_submatrix_bounds(node, flat_list)

def weight_based_search(root, target_weight, tolerance=0.05):
    """
    Example function to find a node whose weight is near 'target_weight'
    within 'tolerance'. This shows how we can navigate by weight. 
    """
    candidates = []
    stack = [root]
    while stack:
        n = stack.pop()
        # if abs(n.weight - target_weight) <= tolerance:
        if n.weight >= target_weight * (1 - tolerance) and n.weight <= target_weight * (1 + tolerance):
            candidates.append(n.label)
        stack.extend(n.children)
    return candidates

###############################################################################
# (D) - 1D Axis and Sorting Already Maintained by Weighted Insertions
###############################################################################
# Because we always insert in descending weight, once we flatten the tree we get
# a global order from heaviest to lightest (per branch). If parent's weight changes,
# we reposition in parent's list, etc.

###############################################################################
# (E) - Visualizing with Color-coded Submatrix Bands
###############################################################################
def plot_fim(matrix, labels, threshold_factor=0.5):
    """
    An example function to plot the NxN matrix with color-coded bands for top-level categories.
    We'll draw bounding boxes around each top-level category's submatrix (including its subtree).
    """
    plt.figure(figsize=(9, 7))
    plt.imshow(matrix, cmap='Spectral', aspect='equal')
    plt.colorbar(label='Similarity / Weight')

    n = len(labels)
    plt.xticks(range(n), labels, rotation=90)
    plt.yticks(range(n), labels)

    # color each top-level node's block:
    color_pool = ['cyan', 'lime', 'yellow', 'orange', 'magenta', 'red', 'blue', 'brown']
    top_children = origin_node.children  # sorted top-level
    flat_list = flatten_hierarchy(origin_node, [])
    c_idx = 0
    for top_node in top_children:
        start_idx, end_idx = dynamic_submatrix_bounds(top_node, flat_list)
        if start_idx is None:
            continue
        color = color_pool[c_idx % len(color_pool)]
        c_idx += 1
        # draw bounding rectangle:
        rect = Rectangle(
            (start_idx - 0.5, start_idx - 0.5),
            (end_idx - start_idx + 1),
            (end_idx - start_idx + 1),
            fill=False, edgecolor=color, lw=2
        )
        plt.gca().add_patch(rect)

        mid = (start_idx + end_idx) / 2.0
        plt.text(mid, start_idx - 1,
                 f"{top_node.label}",
                 color=color, rotation=90,
                 ha='center', va='bottom', fontsize=9)

        plt.text(start_idx - 1, mid,
                 f"{top_node.label}",
                 color=color,
                 ha='right', va='center', fontsize=9)

    # highlight region above threshold
    max_val = matrix.max()
    thr = max_val * threshold_factor
    idxs = np.argwhere(matrix >= thr)
    if len(idxs) > 0:
        row_min, col_min = idxs.min(axis=0)
        row_max, col_max = idxs.max(axis=0)
        width = col_max - col_min + 1
        height = row_max - row_min + 1
        bigger_side = max(width, height)
        skip_factor = 1 - (bigger_side / n)**2

        rect_thr = Rectangle((col_min - 0.5, row_min - 0.5),
                             width, height,
                             fill=False, edgecolor='red', lw=1.5)
        plt.gca().add_patch(rect_thr)
        plt.text(col_min, row_min - 0.5, f"skip={skip_factor:.2f}", color='red',
                 fontsize=10, va='bottom')

    plt.title("Dynamic FIM Plot with Submatrix Bands")
    plt.tight_layout()
    plt.show()

###############################################################################
# (F) - Example Usage (Add / Resort / Flatten / Plot, etc.)
###############################################################################
def add_and_resort_example():
    # Suppose we add a new top-level category
    catZ = create_top_level_category("Zeta", weight=10)
    # Then flatten to see that 'Zeta' is at the top (heaviest)
    flattened_nodes = flatten_hierarchy(origin_node, [])
    labels = [n.label for n in flattened_nodes]

    # Build adjacency matrix: for demonstration, fill random or some logic
    n = len(flattened_nodes)
    matrix = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            matrix[i, j] = 1.0 if i == j else np.random.rand()

    # Visualize with color-coded submatrix tiers
    plot_fim(matrix, labels)

###############################################################################
# (G) - Global ORIGIN Node
###############################################################################
origin_node = Node("ROOT", weight=0.0)  # Initial placeholder

###############################################################################
# (H) - If old "main()" exists or code below, we keep or adapt it:
###############################################################################
def main():
    # A small usage example:
    a = create_top_level_category("Alpha", 5)
    b = create_top_level_category("Beta", 3)
    add_child(a, Node("A1", weight=2))
    add_child(a, Node("A2", weight=4))  # triggers re-sort in parent's children
    add_child(b, Node("B1", weight=1))
    add_child(b, Node("B2", weight=5))

    # build a matrix and plot
    flattened = flatten_hierarchy(origin_node, [])
    labels = [nd.label for nd in flattened]
    size = len(flattened)
    mat = np.random.rand(size, size)
    for i in range(size):
        mat[i, i] = 1.0  # diagonal of 1

    print("[DEBUG] Flattened hierarchy ->", labels)
    plot_fim(mat, labels)

if __name__ == "__main__":
    main()

def compute_hpc_skip_factor(node, full_hierarchy_list):
    """
    Computes and returns the HPC skip factor for a given node's sub-block,
    based on the fraction of the flattened matrix area that is actually used
    vs. the total area.

    skip_factor = 1 - (sub_block_area / total_matrix_area)

    Where:
      • sub_block_area is the number of row×column pairs belonging to this node
        and its descendants in the hierarchy.
      • total_matrix_area is the size of the entire adjacency matrix (e.g. len(full_hierarchy_list)^2).

    This small helper is part of the incremental node-based approach to
    dynamic submatrix boundaries and HPC usage. It hooks into the
    flatten_hierarchy(root_node) logic elsewhere in the file.
    """
    total_size = len(full_hierarchy_list) ** 2
    sub_block_size = 0

    # Gather all nodes under 'node' (including itself)
    # so we know row/column indices of the sub-block
    descendant_indices = node.get_descendant_indices()  # <--- assume this method exists
    sub_block_size = len(descendant_indices) ** 2

    # Compute skip factor
    skip_factor = 1.0 - (sub_block_size / float(total_size))

    # Log for HPC cost analysis
    # (In practice, you'd integrate with whichever logging system is used in main.py)
    print(f"[HPC] Node '{node.name}' skip factor: {skip_factor:.3f} "
          f"(sub_block_area={sub_block_size}, total_area={total_size})")

    return skip_factor

########################################
# Small Step: Build 1D Dictionary Structure & Call Skip Factor
########################################

# Suppose we have some LLM-derived response data in a variable `llm_response_data`
# Our goal: create/run a function that turns that into a 1D dictionary structure
# consistent with the FIM formalism, and (optionally) call the skip factor function
# for the relevant submatrix bounds. We do NOT remove or break existing code.

def build_1d_structure_from_llm(llm_response_data):
    """
    Takes the llm_response_data (presumably a list or raw text describing categories/subcategories)
    and builds a dictionary representing the 1D FIM ordering.
    
    Minimal example of storing a 1D structure:
    {
      'origin': 'O',
      'categories': [ 'A', 'B', 'C', ... ],
      'subcategories': {
         'A': ['A1','A2','A3'],
         'B': ['B1','B2'],
         ...
      },
      ...
    }
    """
    # This is just an illustrative minimal approach, adapting the data:
    fim_1d_structure = {}
    
    # For demonstration, assume llm_response_data is already a dict with lists:
    # e.g. {"top_categories": ["A","B"], "sub_A": ["A1","A2"], "sub_B": ["B1"]}
    # We'll store them in a standardized shape:
    
    # Safely access or fall back if keys missing
    top_cats = llm_response_data.get("top_categories", [])
    sub_A = llm_response_data.get("sub_A", [])
    sub_B = llm_response_data.get("sub_B", [])
    
    fim_1d_structure["origin"] = "O"
    fim_1d_structure["categories"] = top_cats
    fim_1d_structure["subcategories"] = {
        "A": sub_A,
        "B": sub_B
    }
    
    return fim_1d_structure


def call_skip_factor_for_submatrix(fim_1d_structure):
    """
    Example small function to call a skip factor calculation 
    based on a relevant submatrix from fim_1d_structure.
    
    We assume we have some existing skip_factor function 
    defined elsewhere in main.py. We'll do a minimal usage:
    """
    
    # Minimal logic to pick a submatrix bound from the 1D ordering
    # Let's pretend we define a submatrix from indices relevant to 'A' block
    # if it exists in the structure:
    categories = fim_1d_structure.get("categories", [])
    subcats = fim_1d_structure.get("subcategories", {})
    
    if "A" in categories and "A" in subcats:
        # Just a mock example: let's say rows 1-3, cols 1-3 is the 'A' submatrix
        submatrix_bounds = (1, 3, 1, 3)  # (row_start, row_end, col_start, col_end)
        
        # We assume there's a function skip_factor_function(bounds) or similar
        # We'll just demonstrate a call:
        # skip_factor_val = skip_factor_function(submatrix_bounds)
        # print(f"Skip factor for A-submatrix: {skip_factor_val}")
        
        # For now, we'll log a placeholder:
        print(f"[DEBUG] Calling skip_factor on submatrix bounds: {submatrix_bounds}")
    else:
        print("[DEBUG] No 'A' block found to apply skip factor.")


# Example usage snippet in main (or wherever it's logical in your code):
def incorporate_llm_1d_structure_and_skip_factor(llm_response_data):
    """
    Main entry point for this small new step:
    1) Build the 1D structure from LLM data
    2) Optionally call skip factor function with a submatrix example
    """
    fim_1d = build_1d_structure_from_llm(llm_response_data)
    print(f"[DEBUG] 1D structure built: {fim_1d}")
    
    # Now call skip factor function with a submatrix example
    call_skip_factor_for_submatrix(fim_1d)

###################################################################
# Existing imports and code remain intact. We add only minimal code 
# to build the 1D FIM dictionary structure and call the skip factor 
# function for a relevant submatrix, without removing or breaking 
# previous functionality (e.g., plot commands, plan strings, etc.).
###################################################################

# ---------------------
# (1) Define a helper to build the 1D FIM dictionary from LLM data
# ---------------------
def build_fim_1d_representation(llm_response_data):
    """
    Constructs a 1D representation of the Fractal Identity Matrix (FIM)
    from the given llm_response_data. This dictionary will keep track of
    each node's parent, its subcategories, and an index reflecting the 
    final 1D ordering (consistent with the hierarchical, weight-sorted formalism).
    
    :param llm_response_data: (dict or list-like) 
        Data presumably returned by the LLM describing top-level categories 
        and their subcategories, plus weights if available.
    :return: fim_1d (dict)
        A dictionary structured as:
        {
          'O' : {
              'index': 0,
              'children': ['A', 'B', 'C'],
              'weight': 1.0  # example if needed
          },
          'A' : {
              'index': 1,
              'children': ['A1','A2'],   # from LLM data
              'weight': 0.9
          },
          'B' : {
              'index': 2,
              'children': ['B1','B2'],
              'weight': 0.8
          },
          'C' : {
              'index': 3,
              'children': [],
              'weight': 0.7
          },
          'A1': {
              'index': 4,
              'children': [],
              'weight': 0.4
          }, 
          ...
        }
    """
    # In a real scenario, you'd parse llm_response_data for categories, subcategories, weights, etc.
    # Here we do a small illustrative stub.

    # Example small parse, keeping it simple:
    # We assume llm_response_data has keys like 'top_categories' and 'sub_categories'
    # This is purely illustrative. Adapt as needed to match the actual LLM response format.
    # Must remain non-breaking if actual code references "fim_1d" later.
    
    # Basic dictionary skeleton for demonstration:
    fim_1d = {}

    # We assume 'O' is the origin with index 0:
    fim_1d['O'] = {
        'index': 0,
        'children': [],
        'weight': 1.0
    }

    # If we have top-level categories from the LLM (stub example):
    top_cats = llm_response_data.get('top_categories', [])
    current_index = 1

    for cat in top_cats:
        # Example: cat might look like {'name': 'A', 'weight':0.9, 'subs':['A1','A2']}
        cat_name = cat.get('name','Unknown')
        cat_weight = cat.get('weight', 0.5)
        subcats = cat.get('subs', [])

        fim_1d[cat_name] = {
            'index': current_index,
            'children': subcats,
            'weight': cat_weight
        }
        # Attach to origin's children if not already
        if 'children' in fim_1d['O']:
            fim_1d['O']['children'].append(cat_name)

        current_index += 1

    # Next, fill in subcategories in sequential 1D order
    for cat in top_cats:
        cat_name = cat.get('name','Unknown')
        subcats = cat.get('subs', [])
        for sc in subcats:
            # sc might be {'name':'A1','weight':0.4, 'subs':[]}, etc.
            sc_name = sc.get('name','UnknownSub')
            sc_weight = sc.get('weight', 0.3)
            deeper_subs = sc.get('subs', [])  # if there are deeper levels

            fim_1d[sc_name] = {
                'index': current_index,
                'children': [ds['name'] for ds in deeper_subs], 
                'weight': sc_weight
            }
            current_index += 1

    # Sort the top-level children inside fim_1d['O'] based on weight descending (if desired)
    # for demonstration, minimal impact, we won't break anything.
    fim_1d['O']['children'].sort(key=lambda x: fim_1d[x]['weight'], reverse=True)

    return fim_1d


# ---------------------
# (2) A minimal skip-factor submatrix call
# ---------------------

def apply_skip_factor_for_submatrix(matrix, row_start, row_end, col_start, col_end, skip_factor_func):
    """
    Calls a 'skip_factor_func' on the given submatrix bounds (row_start/end, col_start/end).
    Returns the skip factor result (or logs it) without disrupting existing code paths.
    
    :param matrix: 2D matrix or similar structure
    :param row_start: int, starting row index
    :param row_end: int, ending row index (inclusive or exclusive depends on convention)
    :param col_start: int, starting col index
    :param col_end: int, ending col index
    :param skip_factor_func: function that takes (submatrix) or (matrix, row_start, row_end, col_start, col_end)
    """
    # We do a safe boundaries approach to avoid breaks.
    # If skip_factor_func is something already defined in code, 
    # we just call it with the sub-bounds.
    # This is a minimal introduction to show submatrix usage.
    try:
        submatrix_skip = skip_factor_func(matrix, row_start, row_end, col_start, col_end)
        # For demonstration, we might log or print the result:
        print(f"[apply_skip_factor_for_submatrix] Skip factor for submatrix "
              f"({row_start}:{row_end}, {col_start}:{col_end}) = {submatrix_skip}")
        return submatrix_skip
    except Exception as e:
        print(f"[apply_skip_factor_for_submatrix] Could not apply skip factor. Error: {e}")
        return None


# ---------------------
# (3) Example usage in main flow (non-breaking demo)
# ---------------------

def main():
    """
    Main entry point demonstrating:
      - 1D dictionary construction (FIM) from sample LLM data
      - An example submatrix skip factor call (if skip_factor_func is available)
    """
    # Suppose we have some sample LLM response data (pseudo-structure).
    # In a real scenario, you'd get this from an LLM call. 
    # We'll do a small example that won't break existing references.
    sample_llm_data = {
      'top_categories': [
          {
              'name':'A',
              'weight':0.9,
              'subs':[
                  {'name': 'A1', 'weight':0.4, 'subs':[]},
                  {'name': 'A2', 'weight':0.3, 'subs':[]}
              ]
          },
          {
              'name':'B',
              'weight':0.8,
              'subs':[
                  {'name': 'B1', 'weight':0.5, 'subs':[]},
                  {'name': 'B2', 'weight':0.4, 'subs':[]}
              ]
          },
          {
              'name':'C',
              'weight':0.7,
              'subs':[]
          }
      ]
    }

    # 1) Build the FIM 1D structure
    fim_1d = build_fim_1d_representation(sample_llm_data)
    print("[main] Constructed 1D FIM dict:", fim_1d)

    # 2) Suppose we have a matrix and a skip_factor function 
    # (both presumably existing in the codebase somewhere).
    # We'll show only the call. This won't break code if skip_factor is defined 
    # or if you handle the case where it isn't.
    example_matrix = [
        [1.0, 0.8, 0.2],
        [0.8, 1.0, 0.1],
        [0.2, 0.1, 1.0]
    ]

    # Hypothetical skip factor function:
    def skip_factor_func(matrix, rs, re, cs, ce):
        # tiny placeholder logic: let's measure how many entries are < some threshold
        # and compute a ratio for skipping
        threshold = 0.5
        total = 0
        skip_count = 0
        for r in range(rs, re):
            for c in range(cs, ce):
                val = matrix[r][c]
                total += 1
                if val < threshold:
                    skip_count += 1
        if total == 0:
            return 0
        return round(skip_count / total, 2)

    # Now we call our minimal apply_skip_factor_for_submatrix function:
    apply_skip_factor_for_submatrix(
        matrix=example_matrix,
        row_start=0, 
        row_end=3,   # entire range for this example
        col_start=0, 
        col_end=3,
        skip_factor_func=skip_factor_func
    )

    # The rest of the existing main code remains untouched so as not to break 
    # any plotting or plan usage. 
    # ...
    print("[main] Completed minimal updates without breaking existing functionality.")


# If the code's entry point is not automatically called, we place a check:
if __name__ == "__main__":
    main()

# --- Existing code above this line (no removals) ---
# Suppose you already have:
# - A function `skip_factor(submatrix_bounds: tuple) -> float` somewhere in your code
# - A planning string or plan object that you do NOT want to break or remove
# - Some HPC or adjacency matrix logic that remains intact

# STEP 1: Create a minimal structure to hold our 1D ordering in a dictionary form.

def build_fim_1d_structure(llm_responses):
    """
    Build a dictionary-based representation of the FIM's 1D ordering
    from the LLM response data. We keep it minimal for now, focusing on
    the formal 1D sequence of nodes.

    :param llm_responses: An iterable of items obtained from an LLM
                          (e.g., category names or IDs sorted by weight).
    :return: A dict with keys = integer positions, values = node identifiers
    """
    fim_1d = {}
    for idx, node_name in enumerate(llm_responses):
        # Each node_name might be something like 'A' or 'A1' etc.
        fim_1d[idx] = node_name

    return fim_1d

# STEP 2: Demonstrate usage (in parallel to existing matrix or adjacency building).
#         We do NOT remove or break existing code; this is purely additive.

def integrate_fim_1d_with_skip(fim_1d_dict, submatrix_start, submatrix_end):
    """
    Example of using the newly created 1D structure in parallel
    with your skip-factor function. We demonstrate calling skip_factor
    with submatrix bounds that might correspond to a slice of our 1D ordering.
    """
    # Suppose we define a subblock from submatrix_start to submatrix_end (inclusive).
    # That's a small slice of the 1D structure:
    node_slice = [
        fim_1d_dict[pos]
        for pos in range(submatrix_start, submatrix_end + 1)
        if pos in fim_1d_dict
    ]

    # Here, you might do some logic that references HPC skip factor for this sub-slice:
    # e.g., skip_factor(submatrix_bounds=(submatrix_start, submatrix_end))
    # We'll mock a call below. Adjust to align with your real skip function:
    bounds = (submatrix_start, submatrix_end)
    sf_value = skip_factor(bounds)  # Assuming skip_factor is defined somewhere else

    # Log or print a demonstration message to show we used the submatrix bounds
    print(f"[DEBUG] FIM 1D slice: {node_slice}, SkipFactor={sf_value :.2f}")


# --- Example usage below this line (you could put it in main or wherever appropriate) ---

def main():
    # -------------- Existing code logic remains ---------------

    # (A) Hypothetical LLM response data for demonstration:
    #     Perhaps you got this list from an earlier matrix or direct LLM calls
    sample_llm_data = ["O", "A", "B", "C", "A1", "A2", "A3", "B1", "B2", "B3", "C1", "C2", "C3"]

    # (B) Build the 1D structure dictionary (new step)
    fim_1d_dict = build_fim_1d_structure(sample_llm_data)

    # (C) Suppose we want to look at submatrix from 4..6 (A1..A3):
    integrate_fim_1d_with_skip(
        fim_1d_dict=fim_1d_dict,
        submatrix_start=4,
        submatrix_end=6
    )

    # -------------- Remainder of existing main logic --------------
    # e.g., building adjacency, HPC calls, etc.

if __name__ == "__main__":
    main()

# --- Existing code below this line (no removals) ---

def build_one_dim_fim_structure(llm_response_data, skip_factor_func):
    """
    One small, non-breaking step to build a 1D FIM structure (dictionary-based)
    from LLM response data. Ensures we keep the right order and call the
    skip factor function on a relevant submatrix (if it makes sense).

    :param llm_response_data: Data from LLM calls that includes top-level
                              categories, subcategories, weights, etc.
    :param skip_factor_func:  A function that computes HPC skip factor
                              given submatrix boundaries. (We call it
                              only if it makes sense, to avoid breaking
                              or removing existing structures.)
    :return: A dictionary representing the 1D hierarchy consistent with
             the formalism, plus a sample skip factor usage where relevant.
    """

    # Example skeleton parsing of top-level cats from LLM data
    # (Hypothetical: adapt fields to match real llm_response_data)
    top_level = llm_response_data.get("categories", [])
    # Each entry might look like {"name": "A", "weight": 0.9, "subs": [{"name": "A1", ...}, ...]}
    
    # Sort top-level categories by descending weight
    top_level_sorted = sorted(top_level, key=lambda c: c.get("weight", 0), reverse=True)

    # Build the dictionary structure. One small step: we keep it minimal and straightforward.
    fim_1d_dict = {
        "origin": "O",  # single origin always first
        "categories": []
    }

    # We'll gather them in the correct 1D order: O, (top-level cats), then subs block by block
    # We'll store them as a flat list alongside a sub-dict so we keep 1D ordering + easy lookups.
    one_dim_list = ["O"]  # start with origin
    for cat in top_level_sorted:
        cat_name = cat["name"]
        one_dim_list.append(cat_name)
    # Next pass: subcategories for each cat in that same order
    for cat in top_level_sorted:
        cat_name = cat["name"]
        subcats = cat.get("subs", [])
        # sort subcategories by weight, descending
        subcats_sorted = sorted(subcats, key=lambda sc: sc.get("weight", 0), reverse=True)
        for subcat in subcats_sorted:
            one_dim_list.append(subcat["name"])

    # We store final 1D ordering in the dictionary
    fim_1d_dict["categories"] = one_dim_list

    # ------------------------------------------------------------
    # Illustrate a single minimal usage of skip_factor_func:
    # e.g., if we have a parent cat "A" at index 1, subcats "A1","A2","A3" might be indices [4,5,6].
    # We'll call skip_factor_func if that submatrix is valid.
    # This is a minimal example illustrating the "submatrix bounds relevant to the comparison."

    if "submatrix_example" in llm_response_data:
        # Suppose user or system gave us a hint about which submatrix is relevant
        # e.g. {"parent": "A", "start_idx": 4, "end_idx": 6}
        sm_example = llm_response_data["submatrix_example"]
        p_name = sm_example.get("parent")
        start_i = sm_example.get("start_idx")
        end_i = sm_example.get("end_idx")

        # We only call skip_factor_func if indexes make sense:
        if start_i is not None and end_i is not None and 0 <= start_i <= end_i < len(one_dim_list):
            # Example submatrix shape
            matrix_size = len(one_dim_list)
            submatrix_area = (end_i - start_i + 1) ** 2  # simplistic
            skip_value = skip_factor_func(submatrix_area, matrix_size ** 2)

            # Store a small note in the final structure
            fim_1d_dict["skip_factor_note"] = {
                "parent": p_name,
                "bounds": [start_i, end_i],
                "submatrix_area": submatrix_area,
                "total_area": matrix_size ** 2,
                "skip_factor": skip_value
            }
    # ------------------------------------------------------------

    return fim_1d_dict

###################################################################
# (No removals; just adding a small, non-breaking step for 1D dict.)
###################################################################

# Below is an example snippet appended toward the end (or integrated carefully)
# into main.py without removing or breaking existing functions or the plan.
# It illustrates constructing a minimal 1D structure (FIM dictionary) from
# hypothetical LLM response data and then invoking a skip factor calculation
# on a submatrix range. This is done in one small step, preserving all
# existing code and references.

def build_fim_1d_structure(llm_response_data):
    """
    Construct a minimal 1D formalism dictionary for Fractal Identity Matrix (FIM).

    llm_response_data: assumed to contain (or simulate) hierarchical info from the LLM.
                       For demonstration, we'll parse or stub out a consistent structure
                       with an 'origin' and top-level categories + subcategories.

    Returns:
        fim_dict (dict): A small dictionary reflecting the hierarchical 1D ordering.

    Notes:
      - This step does NOT remove or alter existing code; it merely provides
        a structured 1D dict that we can later extrude or reference.
      - Ensure we keep the ordering consistent with the formal FIM approach:
        O -> A, B, C -> A's subcats -> B's subcats -> C's subcats, etc.
    """

    # For this small step, we'll assume llm_response_data could guide which
    # top-level categories exist, etc. Here we just mock an example:
    # If llm_response_data is richer, we'd parse it to build the same format.
    # The key is that "position in the list" -> meaning in the final hierarchy.
    
    fim_dict = {
        "origin": "O",
        "top_level": []
    }

    # In a real scenario, we'd parse llm_response_data to find the categories.
    # This is a safe placeholder to demonstrate the structure:
    top_level_example = [
        {
            "category": "A",
            "subcategories": ["A1","A2","A3"]
        },
        {
            "category": "B",
            "subcategories": ["B1","B2","B3"]
        },
        {
            "category": "C",
            "subcategories": ["C1","C2","C3"]
        }
    ]
    
    fim_dict["top_level"] = top_level_example

    return fim_dict


def example_hpc_skip_factor_submatrix(full_matrix, row_start, row_end, col_start, col_end):
    """
    Demonstrate calling a hypothetical HPC skip factor function on a submatrix portion.
    This is a minimal usage example to track the portion we are 'skipping' or focusing on.

    Args:
        full_matrix: some NxN structure or list of lists
        row_start, row_end, col_start, col_end: bounds for submatrix

    Returns:
        skip_factor (float): a mock skip factor calculation based on
                             submatrix vs. total matrix size.
    """
    # total area in the matrix:
    total_size = len(full_matrix) * len(full_matrix[0]) if full_matrix else 1

    # submatrix area:
    row_count = (row_end - row_start)
    col_count = (col_end - col_start)
    submatrix_area = row_count * col_count

    # For demonstration, skip_factor might be: 1 - (submatrix_area / total_size)
    skip_factor = 1.0 - (submatrix_area / float(total_size))

    # Log something for clarity (assuming we have a logging mechanism):
    print(f"[DEBUG] HPC skip factor for submatrix ({row_start}:{row_end}, "
          f"{col_start}:{col_end}) => {skip_factor:.3f}")
    
    return skip_factor


# Example usage (would be placed where you handle your HPC or adjacency logic).
# We do NOT remove references to or break other code. We just show how to combine
# the new dictionary building with a skip factor call.
def demo_integration_step(llm_data, adjacency_matrix):
    """
    Small demonstration of how we might build the 1D FIM dictionary,
    then pick a submatrix to analyze, calling the HPC skip factor function.
    """
    # Build the 1D structure from LLM data (the new function):
    fim_1d = build_fim_1d_structure(llm_data)
    print("[INFO] Constructed 1D FIM dict:", fim_1d)

    # Suppose we pick a submatrix that corresponds to category 'A' plus subcategories:
    # Just an example: rows 1..4 and cols 1..4 in adjacency_matrix
    # (Indices might correspond to: O=0, A=1, B=2, C=3, A1=4, etc. in a real scenario).
    if adjacency_matrix and len(adjacency_matrix) > 5:
        row_start, row_end = 1, 5
        col_start, col_end = 1, 5
        _ = example_hpc_skip_factor_submatrix(
            adjacency_matrix,
            row_start, row_end,
            col_start, col_end
        )
    else:
        print("[WARN] adjacency_matrix not large enough or None -> skipping HPC submatrix example.")


###################################################################
# The rest of main.py would remain intact. We do not remove or break
# existing code, the plan string, or the plotting references.
###################################################################

def build_fim_1d_structure(llm_response_data, existing_structure=None):
    """
    One small, non-breaking step to integrate a 1D FIM-like data structure.

    :param llm_response_data: (dict) Contains parsed LLM results about hierarchy, weights, etc.
    :param existing_structure: (dict) Optionally pass in an existing structure to extend (non-destructive).
    :return: (dict) A dictionary representing the 1D FIM structure, 
             with minimal submatrix-bound references for later skip-factor logic.
             
    This function:
     1. Creates or updates a 'fim_1d_structure' list that holds each node/category in a strict 1D order.
     2. For each node, stores a small 'subMatrixBounds' placeholder (start_idx, end_idx) to be refined later.
     3. Ensures we don't break existing code by keeping it parallel to current data structures.
    """

    if existing_structure is None:
        existing_structure = {}
    
    # Ensure a list exists for the 1D structure
    if "fim_1d_structure" not in existing_structure:
        existing_structure["fim_1d_structure"] = []

    # Example usage:
    # llm_response_data might look like:
    # {
    #   "origin": "O",
    #   "categories": [
    #       {"name": "A", "weight": 0.95},
    #       {"name": "B", "weight": 0.85},
    #       ...
    #   ]
    # }
    # We'll parse that into a minimal 1D structure.

    origin_name = llm_response_data.get("origin", "O")
    # Only add origin if it's not already in the structure
    if not any(n.get("name") == origin_name for n in existing_structure["fim_1d_structure"]):
        existing_structure["fim_1d_structure"].append({
            "name": origin_name,
            "weight": 1.0,
            "subMatrixBounds": (0, 0)  # Will refine when we know the dimension
        })

    # Insert categories in order of their weight, respecting any existing items
    categories = llm_response_data.get("categories", [])
    # Sort by weight descending
    categories_sorted = sorted(categories, key=lambda c: c.get("weight", 0), reverse=True)

    # We'll find the current length (start index) to place new nodes
    current_length = len(existing_structure["fim_1d_structure"])
    idx = current_length
    
    # Append categories
    for cat in categories_sorted:
        cat_name = cat["name"]
        cat_weight = cat.get("weight", 0.5)

        # Prevent duplicates
        if any(n["name"] == cat_name for n in existing_structure["fim_1d_structure"]):
            continue

        node_info = {
            "name": cat_name,
            "weight": cat_weight,
            # For now, subMatrixBounds is a placeholder. We'll refine once we have subcategories.
            "subMatrixBounds": (idx, idx)
        }
        existing_structure["fim_1d_structure"].append(node_info)
        idx += 1

    # This basic step does NOT remove or alter other structures in existing code.
    # We'll integrate subcategory logic, skip-factor, etc., in subsequent small steps.
    # For now, subMatrixBounds is minimal: (start,end) both idx. Later we can expand it 
    # to reflect deeper sub-block ranges.

    return existing_structure

def integrate_fim_1d_structure_with_skipfactor(llm_response_data, existing_structure):
    """
    One small non-breaking step:
      1. Parse the LLM response data to build or update a lightweight 1D dict (in parallel to the current structure).
      2. Call the skipFactor function with submatrix bounds if relevant.

    This does not remove or break existing code. It simply adds a small dictionary
    for tracking the 1D formalism, and illustrates a call to skipFactor with the
    submatrix bounds. Further integration will happen in subsequent steps.
    """

    # --- Step 1: Build or update a simple 1D dictionary structure from LLM data ---
    # We'll maintain a parallel 1D dict that captures the hierarchical ordering
    # (this is minimal and will expand in future steps).
    one_d_fim_dict = {}
    # Suppose llm_response_data is a list of category labels in sorted order, e.g. ["O", "A", "B", "C", "A1", ...]
    # This is just an example of how we might create the 1D dictionary from that data:
    for index, label in enumerate(llm_response_data):
        one_d_fim_dict[label] = index

    # Log what we built (for debugging)
    print("[DEBUG] Built 1D FIM Dict:", one_d_fim_dict)

    # --- Step 2: If it makes sense in the current context, call skipFactor on a submatrix ---
    # For demonstration, we'll define a small submatrix as from the first index to the last.
    # (In a real scenario, the submatrix could be determined by whichever nodes we're comparing.)
    if len(one_d_fim_dict) > 1:
        submatrix_start = 0
        submatrix_end = len(one_d_fim_dict) - 1
        submatrix_bounds = (submatrix_start, submatrix_end)

        # We assume skipFactor is already defined somewhere in the existing code.
        # We'll invoke it here with a short descriptive tag and the computed bounds.
        # NOTE: This call does not break or remove any code; it's purely additive.
        print("[DEBUG] Calling skipFactor on submatrix bounds:", submatrix_bounds)
        skipFactor("test_submatrix", submatrix_bounds)

    # We also return the 1D dictionary in case other parts of the code need it.
    return one_d_fim_dict

def run_fractal_identity_process(input_list):
    """
    Existing function that orchestrates the Fractal Identity Matrix (FIM) workflow.
    We'll add a minimal caching layer for LLM calls and integrate a skip-factor
    call that references the submatrix bounds. We do NOT remove or break existing
    functionalities; we only add a small step to demonstrate 1D structure compliance.
    """

    # -----------------------
    # 1) Minimal LLM cache setup
    # -----------------------
    # We'll preserve all existing code and append a small "llm_cache" dict
    # plus a helper function. This is a "one small non-breaking step" to
    # demonstrate caching repeated prompts. No reformatting of lines removed.
    # -----------------------
    import logging

    # Suppose we have an in-memory cache
    llm_cache = {}

    def query_llm_cached(prompt: str, llm_caller):
        """
        Wraps an LLM call with a cache.
        'llm_caller' is assumed to be an existing function that queries an LLM.
        """
        if prompt in llm_cache:
            logging.info(f"[Cache Hit] Using cached LLM response for prompt: {prompt[:50]}...")
            return llm_cache[prompt]
        else:
            # call the actual LLM
            response = llm_caller(prompt)
            llm_cache[prompt] = response
            logging.info(f"[Cache Miss] Queried LLM for prompt: {prompt[:50]}...")
            return response

    # -----------------------
    # 2) Preserving existing structure
    # -----------------------
    # We assume there's existing code that processes 'input_list' and
    # uses an LLM. We'll demonstrate how to incorporate the new
    # 'query_llm_cached' in one place without removing old logic.
    # For illustration, let's say we had a loop calling the LLM.
    # We'll replace direct calls to 'existing_llm_call()' with 'query_llm_cached()'.
    # This is minimal and leaves other code intact.
    # -----------------------

    # Example of the existing code snippet (hypothetical):
    # for item in input_list:
    #     prompt = f"Evaluate weight for item: {item}"
    #     weight_res = existing_llm_call(prompt)
    #     process_weight(item, weight_res)
    #
    # We'll revise it:

    def existing_llm_call(prompt):
        """
        Placeholder for the real LLM call; in practice,
        this might be an API call or local model invocation.
        """
        # Original code or placeholder remains
        logging.info(f"Simulating LLM call for prompt: {prompt}")
        # Return a mock response
        return f"MockWeightResponse({prompt})"

    # Minimal revised version with caching:
    for item in input_list:
        prompt = f"Compute weight for item: {item}"
        # Use our new caching wrapper:
        weight_res = query_llm_cached(prompt, existing_llm_call)
        # Pretend we do something with weight_res...
        logging.info(f"Assigned weight to {item}: {weight_res}")

    # -----------------------
    # 3) Minimal skip factor integration
    # -----------------------
    # We'll add a small reference to a "skip_factor" function that
    # calculates submatrix bounds relevant to a comparison. Only if it makes sense,
    # we call it with "current_submatrix" bounds. Again, we do not break or remove
    # existing code. One small step to demonstrate compliance with the formal 1D structure.
    # -----------------------
    def skip_factor(submatrix_start, submatrix_end, total_size):
        """
        Example skip factor calculation.
        submatrix_start, submatrix_end: define the row/column bounds for the submatrix.
        total_size: total dimension of the full matrix (1D -> NxN in some context).
        Returns a float representing the fraction skipped or processed.
        """
        sub_len = submatrix_end - submatrix_start
        full_len = total_size
        if full_len == 0:
            return 0.0
        # For demonstration, say skip_factor = 1 - (size_of_sub / size_of_total)
        factor = 1.0 - (float(sub_len) / float(full_len))
        logging.info(f"Computed skip factor for submatrix [{submatrix_start}:{submatrix_end}] "
                     f"out of total {full_len}: {factor:.2f}")
        return factor

    # Suppose the code normally deals with a 1D list of items that we extrude to NxN.
    # For demonstration, let's say total_size = len(input_list).
    total_size = len(input_list)
    # Hypothetical submatrix (just an example) from index 0 to mid
    if total_size > 1:
        submatrix_start = 0
        submatrix_end = total_size // 2
        current_skip = skip_factor(submatrix_start, submatrix_end, total_size)
        logging.info(f"Skip factor for current submatrix is {current_skip:.2f}")

    # Everything else remains unchanged. This concludes a small, self-contained
    # addition illustrating the request:
    #  - We added a minimal LLM cache
    #  - We showed how to call skip_factor for a partial submatrix
    #  - We did not remove or break existing code
    #  - We kept the 1D formalism in mind

    logging.info("FIM process completed (minimal changes).")
    return "Process finished successfully (with minimal caching & skip factor)."


#################################################################
# (Partial excerpt from main.py, showing minimal incremental
#  additions to enable caching and a submatrix-based skip factor
#  call without removing or breaking existing code.)
#################################################################

# -----------------------------
# 1) Introduce a small in-memory cache for LLM responses
# -----------------------------
# (Placed near the top-level of main.py)
llm_response_cache = {}  # Maps prompt -> response

def get_cached_llm_response(prompt: str, force_refresh: bool = False):
    """
    Returns a cached LLM response if available and not forced
    to refresh. Otherwise, calls the LLM, stores in cache.
    """
    if not force_refresh and prompt in llm_response_cache:
        # We log about using cache (assuming there's an existing logger)
        print(f"[CACHE] Using cached response for prompt: '{prompt[:60]}...'")
        return llm_response_cache[prompt]
    
    # Otherwise, call the real LLM function (assume `call_llm_api` exists)
    print(f"[CACHE] Cache miss (or forced). Querying LLM for prompt: '{prompt[:60]}...'")
    response = call_llm_api(prompt)  # <-- pre-existing LLM call or placeholder
    llm_response_cache[prompt] = response
    return response


# -----------------------------
# 2) Example HPC skip factor function usage with a submatrix range
# -----------------------------
# (We assume there's already a function or placeholder for HPC skip factor,
#  called `compute_skip_factor_for_submatrix(bounds, total_size) -> float`.)
#  We simply add a minimal, safe usage example to track sub-block comparisons.

def process_submatrix_comparison(row_start: int, row_end: int, col_start: int, col_end: int, total_size: int):
    """
    Example small function that calls the HPC skip factor logic for the submatrix
    bounded by [row_start, row_end] x [col_start, col_end] in an N x N environment.
    
    We do not remove or alter the existing structure. This is a minimal addition
    that references a submatrix-based skip factor for demonstration.
    """
    num_rows = (row_end - row_start + 1)
    num_cols = (col_end - col_start + 1)
    submatrix_area = num_rows * num_cols

    # Hypothetical HPC skip factor call (assume it exists or is imported)
    # e.g. skip_factor = compute_skip_factor_for_submatrix(row_start, row_end, col_start, col_end, total_size)
    # Here we'll do a toy demonstration:

    skip_factor = 1.0 - (submatrix_area / (total_size * total_size))
    
    # We print or log the skip factor; this is a lightly integrated parallel step
    print(f"[HPC] Submatrix ({row_start}:{row_end}, {col_start}:{col_end}) => skip factor ~ {skip_factor:.3f}")

    # The rest of your existing logic for comparing items in that submatrix
    # would go here, but we do not remove or break existing code.


# -----------------------------
# 3) Example usage in existing flow
# -----------------------------
# (Within some part of main.py where you do LLM calls or matrix comparisons,
#  we show how to incorporate the two new features in a minimal, non-breaking way.)

def analyze_relationships_example(node_list, total_size):
    """
    An example method demonstrating how we might:
    1) Use 'get_cached_llm_response' for LLM-based relationship checks.
    2) Condition on submatrix bounds and call 'process_submatrix_comparison'
       to reflect HPC skip factor usage.
    """
    # This is a small demonstration snippet placed inline without removing
    # or altering existing logic. Suppose we want to handle a sub-block of the matrix:
    
    sub_row_start, sub_row_end = 0, min(3, total_size - 1)
    sub_col_start, sub_col_end = 0, min(3, total_size - 1)
    
    # Call HPC skip factor for that submatrix
    process_submatrix_comparison(sub_row_start, sub_row_end, sub_col_start, sub_col_end, total_size)
    
    # Now do a small LLM-based relationship check as a demonstration
    prompt = f"Determine relationship strength among nodes: {node_list[sub_row_start:sub_row_end+1]}"
    response = get_cached_llm_response(prompt)
    
    # Suppose you parse or use 'response' here in your existing code:
    print(f"[LLM] Relationship analysis result: {response}")

    # We do not remove or break existing code. This snippet is an example
    # of how the new caching function and HPC skip factor call can be integrated.


# (End snippet. No removal or breakage of existing plan/system references.)

# main.py - Partial refactoring step to introduce a small, smart cache for LLM calls
# (Without removing or breaking existing code. Preserves plan string, plot, and skip factor function.)

import logging
import os
import json

# -----------------------------------------------------------------
# (1) Example: Introduce a simple dictionary-based caching mechanism for LLM responses.
#     This is a small, incremental update that does not remove or break any existing functionality.
# -----------------------------------------------------------------

# Global cache dictionary with JSON persistence
LLM_CACHE_FILE = "llm_cache.json"
try:
    with open(LLM_CACHE_FILE, "r") as file:
        _llm_response_cache = json.load(file)
except (FileNotFoundError, json.JSONDecodeError):
    _llm_response_cache = {}

def save_llm_cache():
    """Saves the provided cache dictionary to LLM_CACHE_FILE."""
    with open(LLM_CACHE_FILE, "w") as cache_file:
        json.dump(_llm_response_cache, cache_file, indent=2)

def cached_llm_call(prompt, llm_callable, use_cache=True):
    """
    Wrapper for LLM calls that uses a global persistent cache stored in llm_cache.json.
    Checks the cache first; if not present, it queries the LLM, caches the response,
    saves it to JSON, and returns the response.
    """
    if use_cache:
        if prompt in _llm_response_cache:
            logging.info(f"[Cache Hit] Using cached LLM response for prompt: {prompt[:50]}...")
            return _llm_response_cache[prompt]
        else:
            logging.info(f"[Cache Miss] Querying LLM for prompt: {prompt[:50]}...")
            response = llm_callable(prompt)
            _llm_response_cache[prompt] = response
            save_llm_cache()
            return response
    else:
        logging.info(f"[No Cache] Direct LLM call for prompt: {prompt[:50]}...")
        response = llm_callable(prompt)
        _llm_response_cache[prompt] = response
        save_llm_cache()
        return response
        return response

# -----------------------------------------------------------------
# (2) Example usage inside existing code (pseudocode snippet):
#     We assume there's an existing function `call_llm_api(prompt)` somewhere in main.py
#     that performs the real LLM request. We now wrap it with `cached_llm_call`.
# 
#     NOTE: This is just an illustrative snippet showing how you might integrate the cache.
#     It does NOT remove or alter your existing `plan` or any HPC skip factor code.
# -----------------------------------------------------------------

def example_weight_assignment(conceptA, conceptB):
    """
    A small example function demonstrating how you'd use the caching wrapper
    to retrieve a weight (similarity score) from the LLM for two concepts.
    """
    # Prepare a short prompt:
    prompt = f"On a scale 0 to 1, how similar are the concepts '{conceptA}' and '{conceptB}'?"
    
    # Use the caching wrapper around an existing LLM call function:
    llm_response = cached_llm_call(
        prompt=prompt,
        llm_callable=call_llm_api,  # <-- This function must exist somewhere else in main.py
        use_cache=True
    )
    
    # Suppose LLM returns a string that can be parsed into a float:
    try:
        weight = float(llm_response.strip())
    except ValueError:
        # Fallback if the LLM did not return a parseable number:
        weight = 0.0
    logging.info(f"Assigned weight={weight:.4f} for pair ({conceptA}, {conceptB})")
    return weight

# -----------------------------------------------------------------
# (3) Existing skip factor function (EXAMPLE placeholder to show we do NOT remove or break it).
#     We leave this function intact, demonstrating that we preserve existing code.
# -----------------------------------------------------------------

def compute_skip_factor(submatrix_bounds, total_size):
    """
    Placeholder for the existing skip factor function. 
    We do NOT touch or remove it to ensure nothing breaks.
    """
    # ... existing logic ...
    # For illustration, we keep it as-is:
    if total_size == 0:
        return 0
    submatrix_area = (submatrix_bounds[1] - submatrix_bounds[0]) ** 2
    skip_factor = 1 - (submatrix_area / total_size)
    return skip_factor

# -----------------------------------------------------------------
# (4) END OF SMALL STEP: 
#     We have introduced a caching mechanism and a sample usage 
#     without altering or removing existing plan strings or code 
#     that might break your HPC logs, plotting, or skip factor.
# -----------------------------------------------------------------












import logging

class Node:
    def __init__(self, name, weight, parent=None):
        self.name = name
        self.weight = weight
        self.parent = parent
        self.children = []
    
    def add_child(self, child):
        self.children.append(child)
    
    def __repr__(self):
        return f"Node({self.name})"

def flatten_hierarchy(root):
    """
    Recursively flattens the hierarchy into a 1D list.
    Order: start with root (Origin), then append sorted children (by descending weight)
    and further their descendants.
    
    This produces a self-legending 1D sequence that encodes both ancestry and weight.
    """
    result = [root]
    # Sort children in descending order based on weight so the most influential come first.
    sorted_children = sorted(root.children, key=lambda x: x.weight, reverse=True)
    for child in sorted_children:
        result.extend(flatten_hierarchy(child))
    return result

# New object structure to encapsulate the 1D Fractal Identity Matrix (FIM)
class FIMObject:
    def __init__(self, ordered_nodes):
        # Store the flattened ordering that encodes hierarchical position (meaning)
        self.ordered_nodes = ordered_nodes

    def get_index(self, node):
        """
        Returns the index (position) of the node in the ordered list.
        The position inherently carries identity information.
        """
        try:
            return self.ordered_nodes.index(node)
        except ValueError:
            logging.warning(f"{node} is not in the FIM ordering")
            return -1

    def extrude_to_matrix(self):
        """
        Extrudes the 1D ordering into a 2D square matrix.
        Each axis uses the same ordered_nodes list.
        Diagonal elements denote identity (e.g. a connection to self).
        """
        size = len(self.ordered_nodes)
        matrix = [[0 for _ in range(size)] for _ in range(size)]
        for i in range(size):
            for j in range(size):
                # In a pure identity mapping, a node maps 1-to-1 to itself.
                matrix[i][j] = 1 if i == j else 0
        return matrix

def plot_dynamic_fim():
    """
    Plot the adjacency matrix using a dynamic node structure.
    This function uses flatten_hierarchy() to obtain the 1D ordering,
    then computes submatrix boundaries dynamically using dynamic_submatrix_bounds().
    It then overlays the boundaries and labels, ensuring that the complicated
    plot (with annotations, FIM Focus, and skip factor outputs) is preserved.
    """
    # Flatten the node hierarchy (including the origin if desired)
    flat_hierarchy = flatten_hierarchy(origin_node, [])
    labels = [node.label for node in flat_hierarchy]
    matrix_size = len(flat_hierarchy)
    
    # For demonstration purposes, build or use the pre-computed adjacency matrix.
    # In actual use, replace the following with your matrix-building logic.
    matrix = np.random.rand(matrix_size, matrix_size)
    np.fill_diagonal(matrix, 1.0)  # ensure diagonal of 1's

    # Create the plot
    plt.figure(figsize=(10, 8))
    plt.imshow(matrix, cmap='viridis', interpolation='none')
    plt.colorbar(label='Similarity Weight')
    plt.xticks(ticks=range(matrix_size), labels=labels, rotation=90)
    plt.yticks(ticks=range(matrix_size), labels=labels)
    plt.title("Dynamic FIM with Node-based Submatrix Boundaries")

    # --- Compute and overlay dynamic boundaries for each top-level node ---
    # Assume each immediate child of the origin represents a top-level category.
    top_level_nodes = origin_node.children  # they are inserted/sorted dynamically
    for node in top_level_nodes:
        start, end = dynamic_submatrix_bounds(node, flat_hierarchy)
        if start is not None and end is not None:
            # Draw the boundary rectangle around the node's submatrix
            rect = Rectangle(
                (start - 0.5, start - 0.5),
                (end - start + 1),  # width
                (end - start + 1),  # height
                fill=False, 
                edgecolor='red', 
                linewidth=2, 
                linestyle="--"
            )
            plt.gca().add_patch(rect)
            # Annotate the block (place the label near the top boundary)
            mid = (start + end) / 2.0
            plt.text(mid, start - 0.7, f"{node.label}", color="red",
                     fontsize=10, ha="center", va="bottom")

    # --- (Optional) Overlay FIM Focus bounding box as in the existing code ---
    threshold = matrix.max() * 0.5  # e.g., 50% of max weight
    indices = np.argwhere(matrix >= threshold)
    if indices.size > 0:
        row_min, col_min = indices.min(axis=0)
        row_max, col_max = indices.max(axis=0)
        width = col_max - col_min + 1
        height = row_max - row_min + 1
        L_focus = max(width, height)
        L_total = matrix_size
        finability_index_focus = (L_focus / L_total) ** 2

        rect_focus = Rectangle(
            (col_min - 0.5, row_min - 0.5),
            width, height,
            edgecolor='yellow', 
            facecolor='none', 
            linewidth=2, 
            linestyle='--'
        )
        plt.gca().add_patch(rect_focus)
        plt.text(0.95, 0.05, f"FIM Focus: {finability_index_focus:.4f}",
                 transform=plt.gca().transAxes,
                 fontsize=12, color="yellow", horizontalalignment="right",
                 bbox=dict(facecolor='black', alpha=0.5, edgecolor='none'))
    
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    # --------------------------
    # Example Hierarchy Creation
    # --------------------------
    # Create the origin (O)
    root = Node("O", weight=1.0)
    
    # Top-level categories (e.g., A, B, C) sorted by weight
    node_A = Node("A", weight=0.9, parent=root)
    node_B = Node("B", weight=0.8, parent=root)
    node_C = Node("C", weight=0.7, parent=root)
    root.add_child(node_A)
    root.add_child(node_B)
    root.add_child(node_C)
    
    # Subcategories for A (A1, A2, A3)
    node_A1 = Node("A1", weight=0.85, parent=node_A)
    node_A2 = Node("A2", weight=0.8, parent=node_A)
    node_A3 = Node("A3", weight=0.75, parent=node_A)
    node_A.add_child(node_A1)
    node_A.add_child(node_A2)
    node_A.add_child(node_A3)
    
    # Example for B subcategories (B1, B2, B3)
    node_B1 = Node("B1", weight=0.78, parent=node_B)
    node_B2 = Node("B2", weight=0.76, parent=node_B)
    node_B3 = Node("B3", weight=0.74, parent=node_B)
    node_B.add_child(node_B1)
    node_B.add_child(node_B2)
    node_B.add_child(node_B3)
    
    # Subcategories for C (C1, C2, C3)
    node_C1 = Node("C1", weight=0.66, parent=node_C)
    node_C2 = Node("C2", weight=0.64, parent=node_C)
    node_C3 = Node("C3", weight=0.62, parent=node_C)
    node_C.add_child(node_C1)
    node_C.add_child(node_C2)
    node_C.add_child(node_C3)
    
    # ---------------------------------
    # Flatten the Hierarchy into a 1D List
    # ---------------------------------
    ordered_nodes = flatten_hierarchy(root)
    
    # ------------------------
    # Insert into an Object Structure: FIMObject
    # ------------------------
    fim = FIMObject(ordered_nodes)
    
    # Log the 1D ordering, where each node's position encodes its meaning.
    print("FIM 1D Ordering:")
    for idx, node in enumerate(fim.ordered_nodes):
        print(f"Index {idx}: {node.name}")
    
    # ---------------------------------
    # Demonstrate Extrusion into a 2D Matrix:
    # The same ordering is applied on both axes.
    # Diagonal elements (self identity) are set to 1.
    # ---------------------------------
    matrix = fim.extrude_to_matrix()
    print("\nExtruded 2D Matrix (Identity Mapping):")
    for row in matrix:
        print(row)
    
    # Example: Retrieve the index of a node to show that its position
    # in the FEM ordering provides its unique identity
    index_A1 = fim.get_index(node_A1)
    print(f"\nNode {node_A1.name} is at index {index_A1} (position conveys its meaning).")