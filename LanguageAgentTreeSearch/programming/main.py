"""
--------------------------------------------------------------------------------
PLANNING: FIM pipeline moving to a fully consolidated big object in functional
style. The FIMHierarchy object aggregates:
  - The final tree (the root Node)
  - The final randomized graph (with weights)
  - Aggregated HPC usage and structure entropy (across iterations)
  - The node dictionary (mapping labels to Node objects)
  - A custom linear ordering (sorted by randomized weights)
  - Absolute positions and submatrix bounds (computed from direct children)
  - Prefixes computed separately (using the parent links and linear order)
--------------------------------------------------------------------------------
"""

import os
import json
import random
import logging
import argparse
import math
import numpy as np
import pprint

# For completeness in this example, we define a simple Node class here.
class Node:
    def __init__(self, label, weight=1.0):
        self.label = label                      # Label updated by simulated LLM calls
        self.invariant_label = label            # Original ID (can be removed later)
        self.weight = weight                    # Weight is set from the randomized graph
        self.skip_factor = 1.0                  # Computed later based on children
        self.children = []                      # List of Node objects
        self.abs_index = None                   # Absolute position in the linear order
        self.submatrix_bounds = None            # Bounds computed from direct children
        self.parent = None                      # Parent pointer (added)

    def add_child(self, child):
        self.children.append(child)
        child.parent = self  # Set the child's parent pointer

    def inspect(self):
        pprint.pprint(self.__dict__)

###########################################################
#      TREE/GRAPH BUILDING AND HELPER FUNCTIONS           #
###########################################################

def build_tree_from_graph(graph, root_label):
    """
    Build a Node-based tree from a dictionary-based graph.
    For each relationship, the node.weight field is updated from the
    randomized graph. Also, when adding children, we set the parent pointer.
    """
    nodes = {}
    labels = set()
    # Gather all labels from keys and children.
    for parent, children in graph.items():
        labels.add(parent)
        for child in children:
            labels.add(child)
    for label in labels:
        nodes[label] = Node(label, weight=1.0)
    for parent, children in graph.items():
        parent_node = nodes[parent]
        for child, weight in children.items():
            child_node = nodes[child]
            child_node.weight = weight
            parent_node.add_child(child_node)  # This also sets child_node.parent
    if root_label not in nodes:
        raise ValueError(f"Root label '{root_label}' not found in the provided graph.")
    return nodes[root_label]

def build_node_dict(root):
    """
    Build a dictionary mapping labels to node objects by traversing the tree.
    """
    node_dict = {}
    def traverse(node):
        if node.invariant_label in node_dict:
            logging.warning(f"Duplicate label encountered: {node.invariant_label}")
        node_dict[node.invariant_label] = node
        for child in node.children:
            traverse(child)
    traverse(root)
    return node_dict

def sort_keys_by_weight(child_dict):
    """
    Given a dictionary mapping child labels to weights,
    returns a list of keys sorted by descending weight.
    """
    return sorted(child_dict.keys(), key=lambda k: child_dict[k], reverse=True)

def linearize_one_d(graph, root_label, node_dict):
    """
    Build a custom linear ordering as follows:
      1. Start with the root.
      2. Append the root's direct children (sorted by weight from the randomized graph).
      3. Then, iterate over the growing order; for each node that has children,
         append its sorted children (those not already in the order).
    Returns the list of Node objects in the final order.
    """
    order = []
    try:
        root = node_dict[root_label]
    except KeyError:
        raise ValueError(f"Root label '{root_label}' not found in node dictionary.")
    order.append(root)
    if root_label in graph:
        children_sorted = sort_keys_by_weight(graph[root_label])
        for child in children_sorted:
            if child in node_dict:
                order.append(node_dict[child])
            else:
                logging.error(f"Child '{child}' from graph[{root_label}] not found in node_dict.")
    i = 1
    while i < len(order):
        current_node = order[i]
        if current_node.invariant_label in graph:
            children_sorted = sort_keys_by_weight(graph[current_node.invariant_label])
            for child in children_sorted:
                if child in node_dict and node_dict[child] not in order:
                    order.append(node_dict[child])
                elif child not in node_dict:
                    logging.error(f"Child '{child}' from graph[{current_node.invariant_label}] not found in node_dict.")
        i += 1
    return order

def assign_linear_bounds(linear_order, graph):
    """
    Given the linear order (from linearize_one_d), assign:
      - Each node an absolute position (node.abs_index).
      - For nodes with children (keys in the graph) compute submatrix bounds as
        (min(index among direct children), max(index among direct children)).
      - For nodes with no direct children, bounds equal the node's index.
    """
    for idx, node in enumerate(linear_order):
        node.abs_index = idx
    for node in linear_order:
        if node.invariant_label in graph:
            child_indices = []
            for child in graph[node.invariant_label]:
                for ordered_node in linear_order:
                    if ordered_node.invariant_label == child:
                        child_indices.append(ordered_node.abs_index)
                        break
            if child_indices:
                node.submatrix_bounds = (min(child_indices), max(child_indices))
            else:
                node.submatrix_bounds = (node.abs_index, node.abs_index)
        else:
            node.submatrix_bounds = (node.abs_index, node.abs_index)

def compute_and_update_skip_factors(node, threshold=0.5, dimension=1):
    """
    Recursively update the skip factor for a node.
    Calculated as (c/t)**dimension, where c is the count of children with weight >= threshold
    and t is the total count of children.
    """
    total = len(node.children)
    if total == 0:
        node.skip_factor = 1.0
    else:
        processed = sum(1 for child in node.children if child.weight >= threshold)
        node.skip_factor = (processed / total) ** dimension
    for child in node.children:
        compute_and_update_skip_factors(child, threshold, dimension)

def simulate_llm_call(old_label, iteration):
    """
    Simulate an LLM call that renames a node.
    """
    return f"LLM_{iteration}_{old_label}"

def process_llm_iterations(graph, root_label, iterations=3, dimension=1):
    """
    Runs simulated LLM/HPC iterations:
      - Randomizes graph weights.
      - Rebuilds the tree from the randomized graph.
      - Updates skip factors.
      - Simulates LLM renaming of each node.
    Returns a 4-tuple:
      (final tree root, aggregated HPC values, aggregated entropy values, final randomized graph).
    """
    aggregated_hpc = []
    aggregated_entropy = []
    root = None
    final_rand_graph = None
    for i in range(iterations):
        logging.info(f"\n=== Iteration {i+1} ===")
        randomized_graph = {k: {ck: random.uniform(0, 1) for ck in v} for k, v in graph.items()}
        final_rand_graph = randomized_graph
        logging.info(f"Randomized weights for iteration {i+1}: {randomized_graph}")
        root = build_tree_from_graph(randomized_graph, root_label)
        compute_and_update_skip_factors(root, dimension=dimension)
        def update_labels(node):
            node.label = simulate_llm_call(node.invariant_label, i+1)
            for child in node.children:
                update_labels(child)
        update_labels(root)
        aggregated_hpc.append(random.uniform(0.1, 5.0))
        aggregated_entropy.append(random.uniform(0, 1))
    return root, aggregated_hpc, aggregated_entropy, final_rand_graph

def save_hierarchy(root_node, filename="final_hierarchy.json"):
    """
    Save the node-based hierarchy to a JSON file.
    """
    def node_to_dict(node):
        return {
            "prefix": None,  # Prefixes are now stored separately in the FIMHierarchy object.
            "label": node.label,
            "abs_index": node.abs_index,
            "weight": node.weight,
            "skip_factor": node.skip_factor,
            "submatrix_bounds": node.submatrix_bounds,
            "children": [node_to_dict(child) for child in node.children]
        }
    with open(filename, "w") as f:
        json.dump(node_to_dict(root_node), f, indent=4)
    logging.info(f"Hierarchy saved to {filename}")

###########################################################
#  NEW: COMPUTE PREFIXES FROM PARENT LINKS AND ABS_INDEX   #
###########################################################

def compute_submatrix_bounds_including_origin(root, rand_graph):
    """
    Compute submatrix bounds including the origin (O) and its direct children.

    For the origin, use root.submatrix_bounds (expected to be, for example, (1,4)).
    Then for each top-level category (child of root) in the canonical order from rand_graph["Origin"],
    assign a block whose width is determined by the number of its direct children (or 1 if none).
    
    Returns:
      A dictionary mapping category addresses to their submatrix bounds.
      For example: {"O": (1,4), "A": (5,8), "B": (9,11), ...}
    """
    bounds = {}
    # Add the origin node's submatrix bounds under the key "O"
    origin_prefix = "O"
    bounds[origin_prefix] = root.submatrix_bounds  # Expected to be, e.g., (1,4)
    
    # The first available index comes right after the origin's block.
    current_offset = root.submatrix_bounds[1] + 1
    
    # Use the canonical order from rand_graph["Origin"].
    desired_order = list(rand_graph["Origin"].keys())
    
    # For each top-level category in that order, assign a sequential block.
    for i, label in enumerate(desired_order):
        # Locate the node among root.children by its unique label.
        node = next((child for child in root.children if child.label == label), None)
        if node:
            # Determine width: number of children or default 1.
            width = len(node.children) if node.children else 1
            # Assign a letter prefix ("A", "B", etc.).
            prefix = chr(ord('A') + i)
            bounds[prefix] = (current_offset, current_offset + width - 1)
            current_offset += width
    return bounds

def compute_prefixes_from_parents(linear_order, rand_graph):
    """
    Compute a dictionary mapping each node's abs_index to its prefix.

    For the origin and its direct children, use the canonical order defined in rand_graph["Origin"].
    """
    prefixes = {}
    if not linear_order:
        return prefixes
    root = linear_order[0]
    prefixes[root.abs_index] = "root"
    assign_top_level_prefixes_from_rand_graph(root, prefixes, rand_graph)
    return prefixes

def assign_top_level_prefixes_from_rand_graph(root, prefixes, rand_graph):
    """
    Assign prefixes to the direct children of the origin node using the canonical
    order specified in rand_graph["Origin"]. If the rand graph order is A, B, C, D,
    then the children are assigned prefixes "A", "B", "C", "D" in that same order.
    
    Args:
      root: The origin Node whose children are the top-level categories.
      prefixes: A dictionary mapping node.abs_index to its computed prefix.
      rand_graph: The original rand_graph dict, which contains an "Origin" key whose
                  keys are in the canonical order.
    """
    # Use the desired order directly as provided by the rand graph.
    desired_order = list(rand_graph["Origin"].keys())
    # Build a mapping from each top-level node's unique label to the node.
    node_mapping = {child.label: child for child in root.children}
    for i, label in enumerate(desired_order):
        node = node_mapping.get(label)
        if node:
            prefix = chr(ord('A') + i)
            prefixes[node.abs_index] = prefix

def get_canonical_tree(graph, provided_root_label):
    """
    Returns a tree built from the canonical origin.
    
    If the provided root label is not found in the graph,
    this helper falls back to the canonical key "Origin".

    Args:
      graph: The rand_graph dictionary.
      provided_root_label: The root label coming from the current state.

    Returns:
      The tree built from the canonical origin key.
    """
    if provided_root_label not in graph:
        logging.warning(
            f"Provided root label '{provided_root_label}' not found in graph. Falling back to 'Origin'."
        )
        canonical_root = "Origin"
    else:
        canonical_root = provided_root_label
    return build_tree_from_graph(graph, canonical_root)

def compute_submatrix_bounds_for_children(node, start_index):
    """
    Compute dynamic submatrix bounds for the children of a given node,
    starting from start_index.
    
    In a real pipeline, you might adjust each child's block width based on
    a real measure (e.g., descendant counts, HPC usage, node complexity, etc.).
    For demonstration, we compute a "block width" as follows:
    
        block_width = (len(child.label) % 4) + 1
    
    Returns:
      A tuple (child_bounds, next_index) where child_bounds is a dictionary that maps
      each child's invariant_label to its computed submatrix bounds, and next_index is the
      next available index after processing all children.
    """
    child_bounds = {}
    current_index = start_index
    for child in node.children:
        block_width = (len(child.label) % 4) + 1  # Placeholder for dynamic width computation.
        child_bounds[child.invariant_label] = (current_index, current_index + block_width - 1)
        current_index += block_width
    return child_bounds, current_index

def compute_submatrix_bounds_from_rand_graph(root, rand_graph):
    """
    Compute submatrix bounds based on the canonical tree and dynamic computation for children.
    
    For the origin (assumed to be 'O'), we use its assigned submatrix_bounds.
    Then, using the helper compute_submatrix_bounds_for_children, we compute bounds
    dynamically for the children. We use the order defined by the canonical rand_graph ("Origin")
    for mapping children to prefix letters.
    
    Returns:
       A dictionary mapping canonical prefixes ('O', 'A', 'B', ...) to the computed submatrix bounds.
    """
    bounds = {}
    # For the origin, the prefix is 'O'
    bounds['O'] = root.submatrix_bounds
    start_index = root.submatrix_bounds[1] + 1
    child_bounds, _ = compute_submatrix_bounds_for_children(root, start_index)
    
    # Map children to a canonical prefix. We use the order defined by the keys in rand_graph["Origin"]
    desired_order = list(rand_graph.get("Origin", {}).keys())
    for i, label in enumerate(desired_order):
        if label in child_bounds:
            prefix = chr(ord('A') + i)  # 'A', 'B', 'C', etc.
            bounds[prefix] = child_bounds[label]
    return bounds

def build_category_address_map_from_rand_graph(root, prefixes, submatrix_bounds, rand_graph):
    """
    Build a dictionary mapping from category addresses (prefixes) to their
    submatrix bounds using the order defined in rand_graph["Origin"].

    Returns:
      A dictionary such as:
      {"O": (1,4), "A": (5,8), "B": (9,11), ...}
      
    Correction:
      Instead of looking up the bounds with node.label, we now use the computed prefix.
    """
    address_map = {}
    # Include the origin:
    origin_prefix = prefixes.get(root.abs_index, "O")
    address_map[origin_prefix] = root.submatrix_bounds

    desired_order = list(rand_graph["Origin"].keys())
    node_mapping = {child.label: child for child in root.children}
    for i, label in enumerate(desired_order):
        node = node_mapping.get(label)
        if node:
            # Lookup the prefix from the mapping (or default to chr(ord('A')+i)).
            prefix = prefixes.get(node.abs_index, chr(ord('A') + i))
            # Previously, we mistakenly used node.label; now, use the prefix.
            bounds = submatrix_bounds.get(prefix)
            address_map[prefix] = bounds
    return address_map

###########################################################
#      NEW: BUILDING THE BIG OBJECT (FIMHierarchy)        #
###########################################################

class FIMHierarchy:
    """
    Aggregates all key fields into one object:
      - root: the final tree's root (Node)
      - rand_graph: the randomized graph used in tree-building and ordering
      - aggregated_hpc: list of HPC cost values from iterations
      - aggregated_entropy: list of entropy values from iterations
      - node_dict: dictionary mapping labels to Node objects
      - linear_order: list of Node objects in custom linear sort order
      - prefixes: a dictionary mapping each node's abs_index to its computed prefix
    """
    def __init__(self, root, rand_graph, aggregated_hpc, aggregated_entropy):
        self.root = root
        self.rand_graph = rand_graph
        self.aggregated_hpc = aggregated_hpc
        self.aggregated_entropy = aggregated_entropy
        
        self.node_dict = build_node_dict(self.root)
        self.linear_order = linearize_one_d(self.rand_graph, self.root.invariant_label, self.node_dict)
        assign_linear_bounds(self.linear_order, self.rand_graph)
        
        # Build canonical tree to ensure we consistently use the canonical key.
        canonical_tree = get_canonical_tree(self.rand_graph, self.root.label)
        canonical_node_dict = build_node_dict(canonical_tree)
        canonical_linear_order = linearize_one_d(self.rand_graph, canonical_tree.label, canonical_node_dict)
        assign_linear_bounds(canonical_linear_order, self.rand_graph)
        self.submatrix_bounds = compute_submatrix_bounds_from_rand_graph(canonical_tree, self.rand_graph)
        
        # Save functional submatrix bounds from the graph.
        self.functional_submatrix_bounds = FIMHierarchy.get_submatrix_bounds_from_graph(self.rand_graph, self.root.label)
        
        self.prefixes = compute_prefixes_from_parents(self.linear_order, self.rand_graph)
        
        self.category_address_map = build_category_address_map_from_rand_graph(
            self.root, self.prefixes, self.submatrix_bounds, self.rand_graph
        )
    
        # --- Debug output (for verification) ---
        logging.info("FIMHierarchy constructed:")
        logging.info("Submatrix Bounds: %s", self.submatrix_bounds)
        logging.info("Functional Submatrix Bounds: %s", self.functional_submatrix_bounds)
        logging.info("Category Address Map: %s", self.category_address_map)
    
    @staticmethod
    def get_submatrix_bounds_from_graph(graph, root_label):
        canonical_tree = get_canonical_tree(graph, root_label)
        node_dict = build_node_dict(canonical_tree)
        linear_order = linearize_one_d(graph, canonical_tree.label, node_dict)
        assign_linear_bounds(linear_order, graph)
        return compute_submatrix_bounds_from_rand_graph(canonical_tree, graph)
    
    def __repr__(self):
        return (
            f"FIMHierarchy(root_label={self.root.label}, num_nodes={len(self.linear_order)},\n"
            f"aggregated_hpc={self.aggregated_hpc}, aggregated_entropy={self.aggregated_entropy},\n"
            f"submatrix_bounds={self.submatrix_bounds},\n"
            f"functional_submatrix_bounds={self.functional_submatrix_bounds},\n"
            f"category_address_map={self.category_address_map})"
        )
    
    def inspect(self):
        import pprint
        print("\n=== FIMHierarchy Inspection ===")
        pprint.pprint(self.__dict__)

###########################################################
#         FUNCTIONAL STYLE HELPER FUNCTIONS               #
###########################################################

def debug_print(obj, label=""):
    """
    Helper to print an object with a label for easier debugging.
    """
    print(f"\n=== {label} ===")
    print(obj)

def create_fim_hierarchy(graph, root_label, iterations, dimension):
    """
    Create and return a FIMHierarchy object by processing the iterations.
    At key steps, we print out the objects so that you see what is being
    passed between functions.
    """
    # process_llm_iterations returns a tuple:
    # (root, aggregated_hpc, aggregated_entropy, final_rand_graph)
    root, aggregated_hpc, aggregated_entropy, final_rand_graph = process_llm_iterations(
        graph, root_label, iterations=iterations, dimension=dimension
    )
    debug_print(root, "After process_llm_iterations - Root")
    debug_print(aggregated_hpc, "After process_llm_iterations - Aggregated HPC")
    debug_print(aggregated_entropy, "After process_llm_iterations - Aggregated Entropy")
    debug_print(final_rand_graph, "After process_llm_iterations - Final Rand Graph")
    
    fim = FIMHierarchy(root, final_rand_graph, aggregated_hpc, aggregated_entropy)
    debug_print(fim, "After FIMHierarchy Initialization")
    return fim

def log_fim_hierarchy(fim):
    """
    Log all key fields from the FIMHierarchy.
    Returns the same fim object (for further functional chaining if needed).
    """
    logging.info("=== FIM Hierarchy Data ===")
    logging.info(f"Root label: {fim.root.label} (Prefix: {fim.prefixes.get(fim.root.abs_index, 'N/A')})")
    logging.info("Custom Linear Ordering sorted by weight:")
    for node in fim.linear_order:
        logging.info(
            f"Index {node.abs_index}: {node.label} (Prefix: {fim.prefixes.get(node.abs_index, 'N/A')}, "
            f"Weight: {node.weight:.3f}, Skip: {node.skip_factor:.3f}, "
            f"Submatrix bounds: {node.submatrix_bounds})"
        )
    logging.info("Aggregated HPC usage: " + ", ".join(f"{cost:.3f}" for cost in fim.aggregated_hpc))
    logging.info("Aggregated entropy: " + ", ".join(f"{ent:.3f}" for ent in fim.aggregated_entropy))
    return fim

###########################################################
#                    MAIN PIPELINE                      #
###########################################################

def parse_args():
    parser = argparse.ArgumentParser(
        description="FIM pipeline integrated with skip factor and HPC logging."
    )
    parser.add_argument("--iterations", type=int, default=10, help="Number of LLM/HPC iterations")
    parser.add_argument("--dimension", type=int, default=1, help="Dimension used in skip factor computation")
    parser.add_argument("--runs", type=int, default=1, help="Number of complete pipeline runs for verification")
    parser.add_argument("--use_mock", action="store_true", help="Use mock LLM responses")
    args, unknown = parser.parse_known_args()
    return args

def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    args = parse_args()
    
    if args.use_mock:
        print("Mock flag passed: Using mock LLM responses.")
        
    logging.info(f"Arguments: {args}")

    graph = {
        "Origin": {"A": 0.9, "B": 0.7, "C": 0.6, "D": 0.65},
        "A": {"A1": 0.85, "A2": 0.8, "A3": 0.75, "New_2526": 0.7013515327158085},
        "B": {"B1": 0.78, "B2": 0.76, "B3": 0.74},
        "C": {"C1": 0.66, "C2": 0.64, "C3": 0.62},
        "D": {"D1": 0.6, "D2": 0.55, "D3": 0.5}
    }
    root_label = "Origin"

    for trial in range(args.runs):
        logging.info(f"===== Trial {trial+1} =====")
        fim = create_fim_hierarchy(graph, root_label, iterations=args.iterations, dimension=args.dimension)
        fim = log_fim_hierarchy(fim)
        fim.inspect()
        # Print the submatrix bounds stored on the FIMHierarchy object.
        print("Submatrix bounds from FIMHierarchy object:", fim.submatrix_bounds)
        # Print the functional submatrix bounds computed directly from the graph.
        print("Functional submatrix bounds from graph:", fim.functional_submatrix_bounds)
        # Example: Print the prefix for the root.
        print(f"Root label: {fim.root.label} (Prefix: {fim.prefixes.get(fim.root.abs_index, 'N/A')})")
        save_hierarchy(fim.root, filename=f"hierarchy_final_trial_{trial+1}.json")
        print("Final FIMHierarchy object:", fim)

if __name__ == "__main__":
    main()