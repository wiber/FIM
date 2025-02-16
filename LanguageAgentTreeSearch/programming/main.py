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
        self.metadata = {}                      # Extra info (e.g., HPC/LLM data)
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
        self.llm_cache = {}           # For JSON caching (if needed)
        self.hpc_log = []             # Log HPC/LLM cost data

    def linearize_one_d(self):
        """
        Creates a 1D ordering using the children link weights stored in each Node.
        This method:
          1) Builds Node objects from the graph.
          2) Uses a breadth-first search (BFS) starting from the origin,
             sorting each node's children by weight.
          3) Returns the final list of labels.
        """
        # Build a set of all labels (parents and children)
        all_labels = set()
        for parent, children in self.graph.items():
            all_labels.add(parent)
            for child in children.keys():
                all_labels.add(child)
                
        # Create Node objects for each label.
        nodes_dict = {}
        for label in all_labels:
            if label in self.graph:
                node = Node(label, self.graph[label])
            else:
                node = Node(label)
            nodes_dict[label] = node

        # Perform a BFS starting from the origin, sorting children by stored weights.
        order = []
        queue = [nodes_dict[self.origin]]
        while queue:
            current = queue.pop(0)
            order.append(current.label)
            if current.children:
                # Log the original children order before sorting.
                original_order = list(current.children.items())
                logging.info(f"Before sort at node '{current.label}': {original_order}")
                
                # Sort children in descending order.
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
                    # Avoid duplicates in the order.
                    if child_label not in order:
                        queue.append(child_node)
                        
        # Convert labels into the ordered Node objects and assign indices.
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
    Dynamically assign prefixes based on each node's rank among its siblings.
    - The origin gets prefix "O".
    - For direct children of origin, use letters (A, B, ...).
    - For all others, use parent's prefix concatenated with the sibling rank (1-indexed).
    """
    # Assign origin prefix.
    for node in hierarchy.ordered_nodes:
        if node.label == hierarchy.origin:
            node.prefix = "O"
            break

    # Assign prefixes for nodes with a parent.
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
                node.prefix = chr(65 + rank)  # 0 -> A, 1 -> B, etc.
            else:
                node.prefix = parent.prefix + str(rank + 1)

def randomize_graph_weights(graph):
    """
    Returns a new graph with the same structure as 'graph' but with random weights.
    """
    new_graph = {}
    for parent, children in graph.items():
        new_graph[parent] = {}
        for child in children:
            new_graph[parent][child] = random.uniform(0, 1)
    return new_graph

def compute_entropy(hierarchy):
    """
    Compute an entropy measure over the structure.
    For each node with children, compute the Shannon entropy of the normalized weights, then average.
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

def simulate_hpc_cost():
    """
    Simulate an HPC cost calculation (for demonstration purposes).
    """
    return random.uniform(0.1, 5.0)

def simulate_llm_call(old_label, iteration):
    """
    Simulate an LLM call that "swaps out" a node's name.
    """
    return f"LLM_{iteration}_{old_label}"

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
        hierarchy.linearize_one_d()  # This logs before/after sort in each node.
        assign_prefixes(hierarchy)
        hierarchy.print_ordering()
        counter += 1

    # --- Second loop: Higher iteration count for actual calls (LLM, JSON, HPC logging, entropy) ---
    llm_iterations = 10  # Example higher iteration count.
    aggregated_hpc = []
    aggregated_entropy = []
    counter2 = 0
    while counter2 < llm_iterations:
        logging.info(f"\n=== LLM Iteration {counter2 + 1} ===")
        # Randomize weights.
        randomized_graph = randomize_graph_weights(original_graph)
        hierarchy = Hierarchy(randomized_graph, origin)
        hierarchy.linearize_one_d()
        assign_prefixes(hierarchy)
        
        # Simulate swapping out node names via LLM calls.
        for node in hierarchy.ordered_nodes:
            # Update node label with a simulated LLM call.
            new_label = simulate_llm_call(node.label, counter2 + 1)
            logging.info(f"Swapping node name from '{node.label}' to '{new_label}'")
            node.label = new_label

        # Simulate an HPC call and store its cost.
        hpc_cost = simulate_hpc_cost()
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