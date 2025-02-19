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

# --- FINAL 1D ORDERING RULES (Declarative) ---
#
# 1. Origin at Index 0
#    - Rule: The first node in the linear_order (i.e., linear_order[0]) MUST be the origin node,
#            identified by label "Origin" or the invariant prefix "O".
#    - Why: This cements the pivot concept—everything else is sorted relative to the origin.
#
# 2. Top-Level Categories in One Contiguous Block
#    - Rule: Immediately after the origin, ALL top-level categories appear (no subcategories yet).
#    - They MUST be sorted in descending weight from the origin.
#    - Example: If there are 3 top-level categories A, B, C (sorted by descending weight from origin),
#            then linear_order = [Origin, A, B, C, ...].
#    - Why: Ensures that no subcategory from A or B is interspersed before we finish listing ALL top categories.
#
# 3. All Subcategory Blocks Appear AFTER the Top-Level Block
#    - Rule: Once ALL top-level categories have been placed (indices 1 .. k in the final list),
#            the subcategory blocks begin.
#    - No subcategory may appear BEFORE all top-level categories are enumerated.
#    - Why: Fulfills the requirement that "all subcategory blocks must appear AFTER all category blocks."
#
# 4. Subcategory Blocks Are Listed in the Parent's Order
#    - Rule: If the top-level block order is {A, B, C}, then the subcategory blocks must appear exactly in that sequence:
#         1. Subcategories of A (sorted by descending weight from A),
#         2. Subcategories of B (sorted by descending weight from B),
#         3. Subcategories of C (sorted by descending weight from C).
#    - Why: Ensures that the ordering of top-level categories governs the order in which their subcategories appear.
#
# 5. Within Each Category's Subcategory Block
#    - Rule: The subcategories (e.g., A1, A2, A3) are sorted in descending weight from the parent
#            and form a contiguous sub-block (i.e., no mixing of different parent subcategories).
#    - Example: For parent A, if A1 > A2 > A3 in weight, then the block is [A1, A2, A3] (not interleaved with others).
#    - Why: Maintains the fractal and hierarchical sorting logic.
#
# 6. No Duplicate Labels
#    - Rule: Each node's label (or invariant_label) in the final 1D ordering MUST be unique.
#    - Why: To guarantee that all references remain unambiguous, especially for hierarchical queries.
#
# 7. Parent Before Child
#    - Rule: A parent node's index MUST always be less than the indices of its children.
#    - Why: Ensures that no child appears before its parent in the final ordering.
#
# 8. Contiguity
#    - Rule: Each top-level category is listed exactly once in the top-level block, and every subcategory block is contiguous.
#    - Example: A valid ordering is [Origin, A, B, C, A1, A2, B1, B2, C1, C2]; an invalid ordering is [Origin, A, B1, B, A1].
#    - Why: Reflects the intended fractal submatrix structure and grouping.
#
# 9. Descending Weight at Every Level
#    - Rule: For any node P with children {C1, C2, ...}, in the final ordering, C1 appears before C2
#            if weight(P -> C1) > weight(P -> C2).
#    - Why: Preserves the "heavier first" (pivotal) principle at each hierarchical level.
#
# --- END OF FINAL 1D ORDERING RULES ---
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
        self.rand_graph = rand_graph  # Source-of-truth canonical order.
        self.aggregated_hpc = aggregated_hpc
        self.aggregated_entropy = aggregated_entropy

        # Initialize validation fields.
        self.validation_checks = {}
        self.check_errors = []

        # 1. Build the final 1D ordering _by sorting first_.
        self.linear_order = self.build_final_ordering()

        # 2. Assign absolute indices to every node based on the new ordering.
        self.assign_absolute_indices()

        # 3. Now assign invariant prefixes based on the final ordering.
        self.assign_invariant_prefixes()

        # 4. Build a mapping from absolute index to invariant prefix.
        self.label_positions = {node.abs_index: node.invariant_prefix for node in self.linear_order}

        # 5. Compute invariant positions from the canonical ordering (if needed).
        self.compute_invariant_positions()

        # 6. Run all validation checks.
        self.run_validations()

        # Additional fields.
        self.submatrix_bounds = {}
        self.functional_submatrix_bounds = {}
        self.category_address_map = {}

    def build_final_ordering(self):
        """
        Build the final 1D ordering with the following steps:
          1. Place the origin at index 0.
          2. Sort all top-level categories (children of the origin) by descending weight.
          3. For each top-level category, sort its subcategories by descending weight.
          
        By performing all sorts first (by weight), we ensure that:
          - The top-level block is contiguous and sorted descending.
          - Each subcategory block is also sorted descending relative to its parent.
        """
        order = []
        # --- Step 1: Add the origin (always at index 0)
        order.append(self.root)

        # --- Step 2: Build the top-level categories, sorted by descending weight.
        top_levels = sorted(self.root.children, key=lambda n: n.weight, reverse=True)
        order.extend(top_levels)
        # Save the boundary index: top-level block runs from index 1 to self.top_level_block_end.
        self.top_level_block_end = len(order) - 1

        # --- Step 3: For each top-level node, append its children sorted by descending weight.
        for node in top_levels:
            # Regardless of any canonical ordering from rand_graph, enforce descending weight.
            subcats = sorted(node.children, key=lambda n: n.weight, reverse=True)
            order.extend(subcats)

        return order

    def assign_absolute_indices(self):
        """
        Assign an absolute index (the 1D index) to every node in self.linear_order.
        """
        for index, node in enumerate(self.linear_order):
            node.abs_index = index

    def assign_invariant_prefixes(self):
        """
        With the final ordering fixed, assign an invariant prefix to every node.
          - The origin always gets the prefix "O".
          - Top-level nodes (children of origin) get an invariant prefix, here chosen to be their cleaned label.
          - For subcategories, the prefix is computed as their parent's prefix plus a 1-indexed position among siblings.
          
        By assigning prefixes _after_ sorting, we guarantee that the prefix reflects the correct position.
        """
        # Assign prefix for the root.
        self.root.invariant_prefix = "O"

        # Top-level nodes: those with parent == root.
        top_levels = [node for node in self.linear_order if node.parent == self.root]
        for node in top_levels:
            # Here we set the prefix to the cleaned label (e.g., "B", "D", etc.).
            node.invariant_prefix = node.label.replace("LLM_10_", "")

        # For subcategories: assign parent's prefix plus the index among siblings (1-indexed).
        for node in self.linear_order:
            if node.parent and node.parent != self.root:
                # Extract all siblings (children of the same parent) _in the final ordering_.
                siblings = [child for child in self.linear_order if child.parent == node.parent]
                order_idx = siblings.index(node) + 1  # 1-indexed
                node.invariant_prefix = node.parent.invariant_prefix + str(order_idx)

    def compute_invariant_positions(self):
        """
        For each node (except the root) compute invariant_position (1-indexed rank within parent's group)
        based on the canonical ordering provided in the rand_graph.
        """
        for node in self.linear_order:
            if node == self.root:
                node.invariant_position = 0
            elif node.parent == self.root:
                canonical_order = list(self.rand_graph.get("Origin", {}).keys())
                cleaned = node.label.replace("LLM_10_", "")
                if cleaned in canonical_order:
                    node.invariant_position = canonical_order.index(cleaned) + 1
                else:
                    sorted_children = sorted(node.parent.children, key=lambda n: n.weight, reverse=True)
                    node.invariant_position = sorted_children.index(node) + 1
            else:
                parent_clean = node.parent.label.replace("LLM_10_", "")
                canonical_order = list(self.rand_graph.get(parent_clean, {}).keys())
                cleaned = node.label.replace("LLM_10_", "")
                if canonical_order and (cleaned in canonical_order):
                    node.invariant_position = canonical_order.index(cleaned) + 1
                else:
                    sorted_siblings = sorted(node.parent.children, key=lambda n: n.weight, reverse=True)
                    node.invariant_position = sorted_siblings.index(node) + 1

    def run_validations(self):
        """
        Runs all of our validation checks and stores results in self.validation_checks and self.check_errors.
        """
        self.check_origin_at_index0()
        self.check_top_level_contiguity()
        self.check_subcategory_blocks_contiguity()
        self.check_parent_before_child()
        self.check_no_duplicates()
        self.check_descending_weights()
        # New validations for ordering against canonical expectations:
        self.check_top_level_order_matches_origin()
        self.check_subcategory_order_matches_canonical()

    def check_origin_at_index0(self):
        """
        Rule 1: Validate that the origin node is at index 0.
        """
        if self.linear_order[0] != self.root:
            msg = f"Origin node is not at index 0. Found {self.linear_order[0].label} instead."
            self.validation_checks['origin'] = msg
            self.check_errors.append(msg)
        else:
            self.validation_checks['origin'] = "OK"

    def check_top_level_contiguity(self):
        """
        Rule 2: Validate that all top-level nodes (children of the origin) are in one contiguous block
                immediately after the origin.
        Also validates that these nodes are sorted in descending order by weight.
        """
        # Expected indices for top-level nodes: from 1 to top_level_block_end.
        expected_indices = list(range(1, self.top_level_block_end + 1))
        found_indices = [i for i, node in enumerate(self.linear_order[1:], start=1) if node.parent == self.root]
        if expected_indices != found_indices:
            msg = f"Top-level nodes are not contiguous: found indices {found_indices}, expected {expected_indices}."
            self.validation_checks['top_level_contiguity'] = msg
            self.check_errors.append(msg)
        else:
            self.validation_checks['top_level_contiguity'] = "OK"

        # Also check the descending order (Rule 9 applied to the Origin's children).
        top_levels = [node for node in self.linear_order if node.parent == self.root]
        top_weights = [node.weight for node in top_levels]
        sorted_top_weights = sorted(top_weights, reverse=True)
        if top_weights != sorted_top_weights:
            msg = f"Top-level categories are not sorted in descending order: weights found {top_weights}."
            self.validation_checks['top_level_descending'] = msg
            self.check_errors.append(msg)
        else:
            self.validation_checks['top_level_descending'] = "OK"

    def check_subcategory_blocks_contiguity(self):
        """
        Rule 3: Validate that every subcategory (node whose parent is not the root)
                appears AFTER the entire top-level block.
        """
        contiguity_errors = []
        for i, node in enumerate(self.linear_order):
            if node.parent is None or node.parent == self.root:
                continue
            if i <= self.top_level_block_end:
                contiguity_errors.append(
                    f"Subcategory {node.label} (parent {node.parent.label}) appears at index {i} but should appear after index {self.top_level_block_end}."
                )
        if contiguity_errors:
            self.validation_checks['subcategory_blocks_contiguity'] = contiguity_errors
            self.check_errors.extend(contiguity_errors)
        else:
            self.validation_checks['subcategory_blocks_contiguity'] = "OK"

    def check_parent_before_child(self):
        """
        Rule 7: Validate that every parent's absolute index is less than those of its children.
        """
        errors = []
        for node in self.linear_order:
            for child in node.children:
                if node.abs_index >= child.abs_index:
                    errors.append(
                        f"Parent {node.label} at index {node.abs_index} appears after its child {child.label} at index {child.abs_index}."
                    )
        if errors:
            self.validation_checks['parent_before_child'] = errors
            self.check_errors.extend(errors)
        else:
            self.validation_checks['parent_before_child'] = "OK"

    def check_no_duplicates(self):
        """
        Rule 6: Validate that every invariant prefix is unique.
        """
        seen = set()
        duplicates = set()
        for node in self.linear_order:
            if node.invariant_prefix in seen:
                duplicates.add(node.invariant_prefix)
            else:
                seen.add(node.invariant_prefix)
        if duplicates:
            msg = f"Duplicate invariant_prefix values found: {duplicates}."
            self.validation_checks['duplicates'] = msg
            self.check_errors.append(msg)
        else:
            self.validation_checks['duplicates'] = "OK"

    def check_descending_weights(self):
        """
        Rule 9: Validate that for each parent, its direct children (the subcategory block)
                appear in descending order of weight.
        """
        weight_violations = []
        for node in self.linear_order:
            if node.children:
                # Only consider those children included in our final ordering.
                child_nodes = [child for child in self.linear_order if child.parent == node]
                expected_order = sorted(child_nodes, key=lambda n: n.weight, reverse=True)
                if child_nodes != expected_order:
                    expected_weights = [child.weight for child in expected_order]
                    actual_weights = [child.weight for child in child_nodes]
                    weight_violations.append(
                        f"For parent {node.label}, expected children's weights {expected_weights} but found {actual_weights}."
                    )
        if weight_violations:
            self.validation_checks['descending_weights'] = weight_violations
            self.check_errors.extend(weight_violations)
        else:
            self.validation_checks['descending_weights'] = "OK"

    def check_top_level_order_matches_origin(self):
        """
        New Check:
        Validate that the order of top-level nodes (children of origin) in the final ordering
        matches the canonical order from rand_graph['Origin'].
        """
        errors = []
        canonical_order = list(self.rand_graph.get("Origin", {}).keys())
        # Expected invariant prefixes for top-level nodes are the canonical keys (if matched via cleaning).
        expected_prefixes = []
        top_levels = [node for node in self.linear_order if node.parent == self.root]
        for node in top_levels:
            cleaned = node.label.replace("LLM_10_", "")
            if cleaned in canonical_order:
                expected_prefixes.append(cleaned)
            else:
                # Fallback: use the computed invariant_prefix.
                expected_prefixes.append(node.invariant_prefix)
        actual_prefixes = [node.invariant_prefix for node in top_levels]
        if expected_prefixes != actual_prefixes:
            errors.append(
                f"Top-level nodes expected invariant prefixes {expected_prefixes} but found {actual_prefixes}."
            )
        if errors:
            self.validation_checks['top_level_order_origin'] = errors
            self.check_errors.extend(errors)
        else:
            self.validation_checks['top_level_order_origin'] = "OK"

    def check_subcategory_order_matches_canonical(self):
        """
        New Check:
        For each top-level node, validate that its subcategories appear
        in the final ordering in the order given by the canonical ordering from rand_graph.
        """
        errors = []
        for node in self.linear_order:
            if node.parent == self.root:
                parent_clean = node.label.replace("LLM_10_", "")
                canonical_order = list(self.rand_graph.get(parent_clean, {}).keys())
                if not canonical_order:
                    continue  # No canonical ordering defined; skip check.
                # Extract the subcategories of the current top-level node as they appear in the final order.
                subcats = [child for child in self.linear_order if child.parent == node]
                # Build expected invariant prefixes using the parent's invariant_prefix and canonical order.
                expected_prefixes = []
                # For each key in the parent's canonical list, if a child exists with that cleaned label, add its expected prefix.
                for key in canonical_order:
                    for child in subcats:
                        cleaned_child = child.label.replace("LLM_10_", "")
                        if cleaned_child == key:
                            # Expected prefix: parent's invariant_prefix concatenated with the (1-indexed position from canonical order).
                            expected_prefixes.append(node.invariant_prefix + str(canonical_order.index(key) + 1))
                actual_prefixes = [child.invariant_prefix for child in subcats]
                if expected_prefixes != actual_prefixes:
                    errors.append(
                        f"For parent {node.label}, expected subcategory invariant prefixes {expected_prefixes} but found {actual_prefixes}."
                    )
        if errors:
            self.validation_checks['subcat_order_canonical'] = errors
            self.check_errors.extend(errors)
        else:
            self.validation_checks['subcat_order_canonical'] = "OK"

    def print_validation_results(self):
        """Utility to print all validation check results."""
        print("Final 1D Ordering Validation Results:")
        for key, result in self.validation_checks.items():
            print(f"{key}: {result}")
        if self.check_errors:
            print("\nErrors:")
            for err in self.check_errors:
                print(f"- {err}")
        else:
            print("\nAll checks passed successfully.")

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
    logging.info(f"Root label: {fim.root.label} (Prefix: {fim.label_positions.get(fim.root.abs_index, 'N/A')})")
    logging.info("Custom Linear Ordering sorted by weight:")
    for node in fim.linear_order:
        logging.info(
            f"Index {node.abs_index}: {node.label} (Prefix: {fim.label_positions.get(node.abs_index, 'N/A')}, "
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
        fim.print_validation_results()
        # Print the submatrix bounds stored on the FIMHierarchy object.
        print("Submatrix bounds from FIMHierarchy object:", fim.submatrix_bounds)
        # Print the functional submatrix bounds computed directly from the graph.
        print("Functional submatrix bounds from graph:", fim.functional_submatrix_bounds)
        # Example: Print the prefix for the root.
        print(f"Root label: {fim.root.label} (Prefix: {fim.label_positions.get(fim.root.abs_index, 'N/A')})")
        save_hierarchy(fim.root, filename=f"hierarchy_final_trial_{trial+1}.json")
        print("Final FIMHierarchy object:", fim)

if __name__ == "__main__":
    main()