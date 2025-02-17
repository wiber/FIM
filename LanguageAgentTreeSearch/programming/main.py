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

def compute_prefixes_from_parents(linear_order):
    """
    Compute a dictionary mapping each node's abs_index to its prefix.
    The rules are:
      - The root (first element in linear_order) gets prefix "root".
      - For all other nodes:
          * If a node's parent is the root, then in the order of appearance (sorted by abs_index)
            the first such node gets prefix "A", the second "B", etc.
          * For deeper levels, a node's prefix is its parent's prefix followed by a number
            (starting at 1) denoting its order among that parent's children (sorted by abs_index).
    This ensures that the node at abs_index 1 will always have prefix "A" regardless
    of which node ended up there.
    """
    prefixes = {}
    if not linear_order:
        return prefixes

    # Root:
    root = linear_order[0]
    prefixes[root.abs_index] = "root"

    # Build mapping for direct children of root.
    root_children = [node for node in linear_order if node.parent == root]
    # Sort by abs_index so that the one with lowest index gets "A".
    root_children.sort(key=lambda n: n.abs_index)
    for i, child in enumerate(root_children):
        letter = chr(ord('A') + i)
        prefixes[child.abs_index] = letter
        assign_children_prefix(child, letter, prefixes, linear_order)
    return prefixes

def assign_children_prefix(parent, parent_prefix, prefixes, linear_order):
    """
    For a given parent node (which is not root), assign a prefix to each of its children,
    appending a numeric indicator (starting at 1) to the parent's prefix.
    The children are ordered by their abs_index.
    """
    children = [node for node in linear_order if node.parent == parent]
    children.sort(key=lambda n: n.abs_index)
    for i, child in enumerate(children):
        new_prefix = f"{parent_prefix}{i+1}"
        prefixes[child.abs_index] = new_prefix
        assign_children_prefix(child, new_prefix, prefixes, linear_order)

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
        # Compute prefixes based solely on parent's pointers and abs_index ordering.
        self.prefixes = compute_prefixes_from_parents(self.linear_order)

###########################################################
#         FUNCTIONAL STYLE HELPER FUNCTIONS               #
###########################################################

def create_fim_hierarchy(graph, root_label, iterations, dimension):
    """
    Create and return a FIMHierarchy object by processing the LLM/HPC iterations.
    This is our functional "pipeline" entry point.
    """
    final_root, aggregated_hpc, aggregated_entropy, final_rand_graph = process_llm_iterations(
        graph, root_label, iterations=iterations, dimension=dimension)
    return FIMHierarchy(final_root, final_rand_graph, aggregated_hpc, aggregated_entropy)

def log_fim_hierarchy(fim):
    """
    Log all key fields from the FIMHierarchy.
    Returns the same fim object (for further functional chaining if needed).
    """
    logging.info("=== FIM Hierarchy Data ===")
    logging.info(f"Root label: {fim.root.label} (Prefix: {fim.prefixes[fim.root.abs_index]})")
    logging.info("Custom Linear Ordering sorted by weight:")
    for node in fim.linear_order:
        logging.info(
            f"Index {node.abs_index}: {node.label} (Prefix: {fim.prefixes[node.abs_index]}, "
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
    logging.info(f"Arguments: {args}")

    # Define the original static graph with category D included.
    graph = {
        "Origin": {"A": 0.9, "B": 0.7, "C": 0.6, "D": 0.65},
        "A": {"A1": 0.85, "A2": 0.8, "A3": 0.75},
        "B": {"B1": 0.78, "B2": 0.76, "B3": 0.74},
        "C": {"C1": 0.66, "C2": 0.64, "C3": 0.62},
        "D": {"D1": 0.60, "D2": 0.55, "D3": 0.50}
    }
    root_label = "Origin"

    # Process each complete run (trial) as a fully functional pipeline.
    for trial in range(args.runs):
        logging.info(f"\n===== Trial {trial+1} =====")
        fim = create_fim_hierarchy(graph, root_label, iterations=args.iterations, dimension=args.dimension)
        fim = log_fim_hierarchy(fim)
        save_hierarchy(fim.root, filename=f"hierarchy_final_trial_{trial+1}.json")

if __name__ == "__main__":
    main()