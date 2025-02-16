"""
--------------------------------------------------------------------------------
PLANNING: Transitioning main.py to a More Dynamic, Functional FIM Design 
with LLM Call Strategy & HPC Cost Logging
--------------------------------------------------------------------------------
```
--------------------------------------------------------------------------------
PLANNING: Transitioning main.py to a More Dynamic, Functional FIM Design 
with LLM Call Strategy, HPC Cost Logging, and Skip Formula Integration
--------------------------------------------------------------------------------

Below is the revised plan for incrementally refactoring this file (main.py) 
toward a dynamic, functionally-driven Fractal Identity Matrix (FIM) 
architecture—explicitly incorporating HPC interpretability, cost tracking, 
and the skip formula:

            Skip Factor = ( c / t )^n

where 
• c = number of relevant categories (or blocks) we actually process,  
• t = total categories/blocks overall, and  
• n = number of dimensions or expansions in the problem space.  

We retain the existing matrix/plot logic while ensuring HPC cost logging 
and the skip formula appear consistently in the code. The primary goals are 
to:

1) Eliminate hard-coded submatrix offsets.  
2) Move to a Node-based, hierarchical design.  
3) Dynamically compute submatrix bounds and apply skip-factor analysis.  
4) Maintain the HPC log of LLM calls.  
5) Reflect how HPC interpretability benefits from focusing on smaller submatrices 
   (thus saving compute time) per the skip formula.  

Below are the key steps and how each integrates HPC interpretability, 
the skip factor formula, LLM calls, and dynamic node-based design.  

--------------------------------------------------------------------------------
1. **Remove Static Submatrix Dictionaries & Hard-coded Bounds**  
--------------------------------------------------------------------------------
   - Eliminate all fixed offset indices or dictionaries describing submatrix 
     boundaries (e.g., `{"A": (6,8), "B": (9,11), ...}`).
   - Replace them with a function (e.g., `get_submatrix_bounds(node)`) that 
     computes each node’s sub-block using node.weight or sums of child weights.
   - The skip formula will be applied to each sub-block boundary so we can 
     track HPC cost. For instance, if a submatrix is only c out of t possible 
     blocks in an n-dimensional sense, skip factor = (c/t)^n.  

--------------------------------------------------------------------------------
2. **Adopt a Hierarchical Node Structure**  
--------------------------------------------------------------------------------
   - Each category or subcategory is a `Node` object with:
       • `name` or `label` (string).  
       • `weight` (float).  
       • `parent` pointer (for top-level nodes, it’s `None`).  
       • a `children` list, sorted descending by weight.  
   - During insertion or updates, recalculate HPC usage to reflect how 
     focusing on certain nodes can skip others. If we only “visit” c 
     out of t total children, HPC skip factor = (c/t)^n.  
   - Eliminate the need for a separate static dictionary to define 
     parent→child blocks.  

--------------------------------------------------------------------------------
3. **Weight-Driven Sorted Insertions**  
--------------------------------------------------------------------------------
   - Whenever we add or update a category or subcategory, we derive 
     a similarity or relevance weight from an LLM prompt (tracked in HPC logs).  
   - Insert the new Node into its parent's `children` array in descending 
     order by weight.  
   - If a node’s weight changes, re-sort it among its siblings.  
   - This ensures the adjacency matrix can be built in a “naturally” sorted 
     manner. HPC interpretability is enhanced because we see the heaviest 
     influences first, consistent with the skip formula (we might skip 
     lower-weight blocks).  

--------------------------------------------------------------------------------
4. **LLM Calls & HPC Logging**  
--------------------------------------------------------------------------------
   - Preserve existing prompt-based calls (e.g., `assign_similarity_weights`), 
     but ensure each triggers HPC usage increments:
       • “Immediate” memory usage for simpler calls.  
       • “Working” usage for subcategory expansions or heavier calls.  
       • “Long-Term” usage for large batch interactions.  
   - Each call increments a global counter (`llm_call_counter`) for clarity, 
     and logs HPC usage in a dictionary (e.g., `HPC_USAGE`).  
   - After each step, we can compute how the skip factor might reduce HPC 
     usage if we only call the LLM on relevant sub-blocks. For instance, 
     if c = 5 sub-blocks used vs. t = 10 possible, skip = (5/10)^1 = 0.5, 
     meaning 50% HPC skip.  

--------------------------------------------------------------------------------
5. **Flattening & Matrix Building**  
--------------------------------------------------------------------------------
   - Provide a function `flatten_hierarchy(root_node, result=[])` that 
     yields a 1D list of nodes in sorted order (heaviest children first).  
   - Build or update the NxN adjacency matrix from this flattened list.  
     Row/column i in the matrix corresponds to `flat_list[i]`. The diagonal 
     can remain 1.0 if we want an identity mapping or can remain 0 if 
     no self-link is required.  
   - For HPC interpretability, each row or sub-block can be 
     “skipped” if the weight is below a threshold—tying directly to 
     `(c/t)^n` to measure how many blocks we can skip.  

--------------------------------------------------------------------------------
6. **Enhanced Plotting with HPC Skip Factor**  
--------------------------------------------------------------------------------
   - Keep the existing matrix plotting but direct sub-block boundaries 
     to `get_submatrix_bounds(node, flat_list)`.  
   - Use color-coded rectangles for top-level categories and subcategories.  
   - Print HPC skip factor for each sub-block, e.g. “Sub-block (A) skip factor = (2/5)^1 = 0.4.”  
   - Continue to show bounding boxes and compute the “Finability Index,” 
     `(L_focus / L_total)^2`, for the bounding region.  

--------------------------------------------------------------------------------
7. **Incremental Implementation**  
--------------------------------------------------------------------------------
   **Order of changes** (each step validated with HPC logs and skip factor prints):
   1. Introduce the `Node` class plus a global `origin_node` or `root`.  
   2. Convert existing static categories into Node objects under `origin_node`.  
   3. Implement `add_category(parent, child_label, child_weight)` to do 
      weight-sorted insertion. Recompute HPC usage.  
   4. Build adjacency matrix from `flatten_hierarchy(root_node)`.  
   5. Replace all submatrix bounding logic with `get_submatrix_bounds(node)`.  
   6. Incorporate skip-factor prints. For instance, if we skip a submatrix 
      of size c vs. total t, HPC usage is multiplied by (c/t)^n.  

--------------------------------------------------------------------------------
8. **Testing & Verification**  
--------------------------------------------------------------------------------
   - After each step, confirm the dynamic insertion yields correct 
     adjacency shape.  
   - Check HPC logs to ensure each LLM call increments usage. Confirm 
     skip factor calculations: if we only retrieve c out of t sub-blocks, 
     HPC cost is proportionally lower.  
   - Verify the final plot has color-coded blocks and bounding lines 
     matching the Node-based structure. Check the Finability Index 
     `(L_focus / L_total)^2` and skip factor `(c/t)^n` match your 
     HPC interpretability requirements.  

By following these steps methodically—and ensuring HPC cost, interpretability, 
and skip-factor logic is integrated at every stage—we transition `main.py` 
into a more robust, transparent FIM. We will be able to:

• Add or remove categories dynamically (by LLM weighting),  
• Track HPC usage with skip factor optimizations,  
• Plot sub-blocks with bounding lines & HPC skip factor annotations,  
• Maintain all prior matrix visuals and LLM interactions, but with 
  deeper hierarchical meaning and HPC interpretability at each step.

```


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
import matplotlib.font_manager as fm
import math


import os
import json

LLM_CACHE_FILE = "llm_cache.json"
try:
    with open(LLM_CACHE_FILE, "r") as file:
        llm_response_cache = json.load(file)
except (FileNotFoundError, json.JSONDecodeError):
    llm_response_cache = {}

def save_llm_cache(llm_cache, filename="llm_cache.json"):
    """Write the LLM cache (dictionary) to a JSON file."""
    try:
        with open(filename, "w") as f:
            json.dump(llm_cache, f, indent=4)
        logging.info(f"LLM cache saved to {filename}.")
    except Exception as e:
        logging.error(f"Error writing llm_cache to {filename}: {e}")

def load_llm_cache(filename="llm_cache.json"):
    """Read the LLM cache from a JSON file. If not available, return an empty dict."""
    try:
        with open(filename, "r") as f:
            cache = json.load(f)
        logging.info(f"LLM cache loaded from {filename}.")
        return cache
    except Exception as e:
        logging.warning(f"Could not read {filename}, starting with an empty cache.")
        return {}

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

def sortKeysByWeight(d):
    """
    Returns the keys of dictionary 'd', sorted in descending order by their values.
    If a value is None, it is treated as negative infinity.
    """
    return sorted(d.keys(), key=lambda k: d[k] if d[k] is not None else float('-inf'), reverse=True)

def linearizeOneD(graph, root):
    # graph[node] -> { child: weight, ... }
    # root is "Origin" in your example

    # 1) Initialize final ordering with the root:
    order = [root]

    # 2) Sort the root's children by their weight, then append them:
    rootChildren = sortKeysByWeight(graph[root])  # e.g. ["A","B","C"]
    for child in rootChildren:
        order.append(child)

    # 3) Now walk through 'order' from index 1 onward:
    #    For each node, append its children (sorted).
    i = 1
    while i < len(order):
        currentNode = order[i]
        # If currentNode has children in graph, sort & append them:
        if currentNode in graph:
            kids = sortKeysByWeight(graph[currentNode])  # e.g. ["A1","A2","A3"]
            for k in kids:
                # Optionally avoid duplicates:
                if k not in order:
                    order.append(k)
        i += 1

    return order

def add_new_category(matrix, labels, new_label, weight=1.0):
    # expand the matrix, fill in new rows/columns, update labels, log HPC usage etc.
    return updated_matrix, updated_labels

def randomize_graph_weights(graph):
    """
    Randomizes all the weights in the graph.
    Modifies the graph in place.
    """
    for parent, children in graph.items():
        for child in children:
            children[child] = random.uniform(0, 1)
    return graph

# --- Define the Hierarchy and Node classes ---
class Node:
    def __init__(self, label, children_weights=None):
        self.label = label                      # Full descriptive label
        self.prefix = None                      # Dynamically computed hierarchical identifier
        self.index = None                       # Position in the 1D ordering
        self.metadata = {}                      # Extra info (e.g., HPC/LLM metadata/prompts)
        self.children = children_weights if children_weights is not None else {}
        self.parent = None                      # Parent pointer (set during BFS)

class Hierarchy:
    def __init__(self, graph, origin):
        """
        :param graph: dict mapping each node -> {child: weight, ...}
        :param origin: string (e.g. "Origin")
        """
        self.graph = graph
        self.origin = origin
        self.ordered_nodes = []       # List of Node objects in final 1D order
        self.llm_cache = {}           # For storing LLM prompts and responses (as metadata)
        self.hpc_log = []             # Log HPC/LLM cost data
    
    def linearize_one_d(self):
        """
        Creates a 1D ordering using the children link weights stored in each Node.
        1) Builds Node objects from the graph.
        2) Uses a BFS starting from the origin, sorting each node's children by weight.
        3) Returns the final list of labels.
        """
        # Build the set of all labels (parents and children)
        all_labels = set()
        for parent, children in self.graph.items():
            all_labels.add(parent)
            for child in children.keys():
                all_labels.add(child)
                
        # Create Node objects for every label.
        nodes_dict = {}
        for label in all_labels:
            if label in self.graph:
                node = Node(label, self.graph[label])
            else:
                node = Node(label)
            nodes_dict[label] = node

        # BFS starting from the origin
        order = []
        queue = [nodes_dict[self.origin]]
        while queue:
            current = queue.pop(0)
            order.append(current.label)
            if current.children:
                # Log original children weights (unsorted)
                original_order = list(current.children.items())
                logging.info(f"Before sort at node '{current.label}': {original_order}")
                
                # Sort children by weight (descending)
                sorted_children_labels = sorted(
                    current.children.keys(),
                    key=lambda child: current.children[child] if current.children[child] is not None else float('-inf'),
                    reverse=True
                )
                sorted_order = [(child, current.children[child]) for child in sorted_children_labels]
                logging.info(f"After sort at node '{current.label}': {sorted_order}")
                
                for child_label in sorted_children_labels:
                    child_node = nodes_dict[child_label]
                    if child_node.parent is None:
                        child_node.parent = current
                    # Avoid duplicates in the ordering.
                    if child_label not in order:
                        queue.append(child_node)
                        
        # Convert the ordering into Node objects and assign indices.
        self.ordered_nodes = []
        for idx, label in enumerate(order):
            node = nodes_dict[label]
            node.index = idx
            self.ordered_nodes.append(node)
            
        return order

    def print_ordering(self):
        logging.info("Final ordered nodes:")
        for node in self.ordered_nodes:
            logging.info(f"Index {node.index}: {node.label} (Prefix: {node.prefix})")

def assign_prefixes(hierarchy):
    """
    Dynamically assigns prefixes based on a node's rank among its siblings.
    - The origin receives the fixed prefix "O".
    - Direct children of the origin receive letters (A, B, ...).
    - All others receive the parent's prefix concatenated with their sibling rank (1-indexed).
    """
    # Set origin prefix
    for node in hierarchy.ordered_nodes:
        if node.label == hierarchy.origin:
            node.prefix = "O"
            break

    # Set prefixes for nodes with a parent.
    for node in hierarchy.ordered_nodes:
        if node.parent is not None:
            parent = node.parent
            sorted_children = sorted(
                parent.children.items(),
                key=lambda x: x[1] if x[1] is not None else float('-inf'),
                reverse=True
            )
            sibling_labels = [child_label for child_label, _ in sorted_children]
            rank = sibling_labels.index(node.label)
            if parent.label == hierarchy.origin:
                node.prefix = chr(65 + rank)  # 0 -> 'A', 1 -> 'B', etc.
            else:
                node.prefix = parent.prefix + str(rank + 1)

def randomize_graph_weights(graph):
    """
    Returns a new graph with the same structure as 'graph' but randomizes the weights.
    """
    new_graph = {}
    for parent, children in graph.items():
        new_graph[parent] = {}
        for child in children:
            new_graph[parent][child] = random.uniform(0, 1)
    return new_graph

def compute_entropy(hierarchy):
    """
    Compute an average Shannon entropy over the nodes that have children.
    """
    total_entropy = 0.0
    count = 0
    for node in hierarchy.ordered_nodes:
        if node.children:
            weights = list(node.children.values())
            total_weight = sum(weights)
            if total_weight <= 0:
                continue
            normalized = [w / total_weight for w in weights]
            entropy = -sum(p * math.log2(p) for p in normalized if p > 0)
            total_entropy += entropy
            count += 1
    if count > 0:
        return total_entropy / count
    return 0

def simulate_hpc_cost(prompts_present=False):
    """
    Simulate an HPC cost calculation.
    If FIM prompts metadata is present, add an extra cost component.
    """
    cost = random.uniform(0.1, 5.0)
    if prompts_present:
        cost += 1.0  # additional cost for even more complex prompt processing
    return cost

def simulate_llm_call(old_label, iteration):
    """
    Simulate an LLM call that "swaps out" a node's name.
    """
    return f"LLM_{iteration}_{old_label}"

def update_fim_prompts(hierarchy, llm_cache, cache_file="llm_cache.json"):
    """
    Define and store the set of prompts framing the FIM problem space.
    These prompts detail:
      1. Origin & Problem Space (Prompt One)
      2. Identification of Top-Level Categories (Prompt Two)
      3. Subcategories per Top-Level Category (Prompt Three)
      4. Key Cross-Interactions (Prompt Four)
      
    The prompts are saved into llm_cache and attached to the origin node's metadata.
    They are also written to a JSON file.
    """
    fim_prompts = {
        "prompt_1": (
            "SYSTEM MESSAGE (optional): You are assisting in constructing a Fractal Identity Matrix (FIM) for causal analysis.\n"
            "USER PROMPT:\n"
            "Below is the overall FIM problem-space definition:\n"
            "- The FIM concept: 'Fractal Identity Matrix for HPC interpretability'\n"
            "- Domain: HPC cost efficiency, energy usage, interpretability\n\n"
            "Please summarize and clarify the problem space. Provide a concise bullet list or a short JSON structure including:\n"
            "1. A summary in 1-2 paragraphs\n"
            "2. Core objectives or success criteria\n"
            "3. A short set of keywords that define the context\n"
            "Return the result in JSON or a similarly parseable format."
        ),
        "prompt_2": (
            "USER PROMPT:\n"
            "Using the problem-space summary from Prompt One (and its metadata), identify the major top-level causal factors (4–6) that most strongly "
            "influence or define the origin. Return them as a JSON array of objects, each with:\n"
            " - 'name': string\n"
            " - 'why_important': short explanation\n"
            " - 'approx_weight': a guess on the impact (0.0 - 1.0)"
        ),
        "prompt_3": (
            "USER PROMPT:\n"
            "For each top-level category provided in Prompt Two, provide 3–5 subcategories in the context of both the category and the overall origin. "
            "For each subcategory, return a JSON object with:\n"
            " - 'sub_name'\n"
            " - 'why_important': explanation referencing both the parent's category and the origin\n"
            " - 'causal_importance_to_parent': a float (0–1) describing the importance of the link from parent to subcategory\n"
            "Return the result grouped by parent category in JSON format."
        ),
        "prompt_4": (
            "USER PROMPT:\n"
            "Given the entire hierarchy (origin, categories, subcategories) so far, identify the 10–15 most crucial cross-interactions that impact HPC "
            "interpretability. For each interaction, return a JSON object with the following keys:\n"
            " - 'nodeA'\n"
            " - 'nodeB'\n"
            " - 'causal_importance': float (0.0–1.0)\n"
            " - 'brief_rationale': a short explanation of how this link fits into the overall causality\n"
            "Return the output as a JSON array sorted in descending order of 'causal_importance'."
        )
    }
    # Save prompts into the LLM cache
    llm_cache["fim_prompts"] = fim_prompts

    # Attach the prompts to the origin node's metadata.
    for node in hierarchy.ordered_nodes:
        if node.prefix == "O":  # the origin node
            node.metadata["fim_prompts"] = fim_prompts.copy()
            break

    # Save updated LLM cache to JSON file.
    save_llm_cache(llm_cache, filename=cache_file)

def parse_args():
    parser = argparse.ArgumentParser(
        description="Run the Hierarchy FIM pipeline with LLM caching and HPC logging."
    )
    parser.add_argument("--use_mock", action="store_true", help="Use mock LLM responses.")
    # Additional arguments as needed.
    parser.add_argument("--run_name", type=str, default="test_run", help="Run name for the execution.")
    parser.add_argument("--root_dir", type=str, default="root", help="Root directory.")
    parser.add_argument("--dataset_path", type=str, default="./benchmarks/humaneval-py.jsonl", help="Path to dataset.")
    parser.add_argument("--strategy", type=str, default="mcts", help="Strategy to use.")
    parser.add_argument("--language", type=str, default="py", help="Programming language.")
    parser.add_argument("--model", type=str, default="gpt-03-mini-high", help="Model to use.")
    parser.add_argument("--max_iters", type=int, default=10, help="Maximum iterations.")
    parser.add_argument("--expansion_factor", type=int, default=2, help="Expansion factor.")
    parser.add_argument("--number_of_tests", type=int, default=2, help="Number of tests.")
    parser.add_argument("--verbose", action="store_true", help="Verbose mode.")
    parser.add_argument("--num_agents", type=int, default=5, help="Number of agents.")
    parser.add_argument("--output_path", type=str, default="./output.json", help="Output path.")
    return parser.parse_args()

# --- Main pipeline ---
def main():
    args = parse_args()
    logging.basicConfig(level=logging.INFO)

    # Log the detected flag and arguments.
    logging.info(f"USE_MOCK flag detected: {args.use_mock}")
    logging.info(f"Parsed command-line arguments: {args}")
    
    # Define the original graph structure with 4 top categories.
    original_graph = {
        "Origin": {"A": 0.9, "B": 0.8, "C": 0.7, "D": 0.65},
        "A": {"A1": 0.85, "A2": 0.8, "A3": 0.75},
        "B": {"B1": 0.78, "B2": 0.76, "B3": 0.74},
        "C": {"C1": 0.66, "C2": 0.64, "C3": 0.62},
        "D": {"D1": 0.70, "D2": 0.68, "D3": 0.67}
    }
    origin = "Origin"

    # --- First loop: Three iterations using randomized weights ---
    counter = 0
    while counter < 3:
        logging.info(f"\n=== Iteration {counter + 1} (Randomized Ordering) ===")
        # Randomize weights each iteration.
        randomized_graph = randomize_graph_weights(original_graph)
        hierarchy = Hierarchy(randomized_graph, origin)
        hierarchy.linearize_one_d()  # Logs before/after sorting at each node.
        assign_prefixes(hierarchy)
        hierarchy.print_ordering()
        counter += 1

    # --- Second loop: Higher iteration count for actual LLM/JSON/HPC processing ---
    llm_iterations = 10  # Example iteration count for detailed processing.
    aggregated_hpc = []
    aggregated_entropy = []
    # We'll use a global llm_cache (simulate using a local dict for now)
    llm_cache = {}
    counter2 = 0
    while counter2 < llm_iterations:
        logging.info(f"\n=== LLM Iteration {counter2 + 1} ===")
        # Randomize weights.
        randomized_graph = randomize_graph_weights(original_graph)
        hierarchy = Hierarchy(randomized_graph, origin)
        hierarchy.linearize_one_d()
        assign_prefixes(hierarchy)
        # Update the FIM prompts metadata and store them in llm_cache / origin node.
        update_fim_prompts(hierarchy, llm_cache)
        
        # Simulate swapping out node names via LLM calls.
        for node in hierarchy.ordered_nodes:
            new_label = simulate_llm_call(node.label, counter2 + 1)
            logging.info(f"Swapping node name from '{node.label}' to '{new_label}'")
            node.label = new_label

        # Check if origin has FIM prompts metadata.
        origin_has_prompts = any(node.metadata.get("fim_prompts") for node in hierarchy.ordered_nodes if node.prefix == "O")
        # Simulate HPC call (including extra cost if prompts are present).
        hpc_cost = simulate_hpc_cost(prompts_present=origin_has_prompts)
        aggregated_hpc.append(hpc_cost)
        logging.info(f"Simulated HPC cost for iteration {counter2 + 1}: {hpc_cost:.3f}")

        # Compute entropy for the current hierarchy.
        entropy_value = compute_entropy(hierarchy)
        aggregated_entropy.append(entropy_value)
        logging.info(f"Computed structure entropy for iteration {counter2 + 1}: {entropy_value:.3f}")

        # Print current ordering with dynamic prefixes.
        hierarchy.print_ordering()
        counter2 += 1

    # End of LLM iterations: Report aggregated HPC and entropy results.
    avg_hpc = sum(aggregated_hpc) / len(aggregated_hpc) if aggregated_hpc else 0
    avg_entropy = sum(aggregated_entropy) / len(aggregated_entropy) if aggregated_entropy else 0
    logging.info("\n=== Aggregated Results ===")
    logging.info(f"Average HPC cost over {llm_iterations} iterations: {avg_hpc:.3f}")
    logging.info(f"Average structure entropy over {llm_iterations} iterations: {avg_entropy:.3f}")

if __name__ == "__main__":
    main()