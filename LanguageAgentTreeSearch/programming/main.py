"""
--------------------------------------------------------------------------------
PLANNING: Constructing the Fully Consolidated FIMPipeline (FIMHierarchy) for 1D Ordering

**Objective:**  
Build a single cohesive object, `FIMHierarchy`, that encapsulates all key outputs from the pipeline. This object includes:
- The final tree structure (the origin and its descendants).
- The randomized graph determining canonical order.
- Aggregated HPC usage and entropy metrics.
- A dictionary mapping node labels to their corresponding `Node` objects.
- A custom linear ordering (`linear_order`) of the nodes.
- Absolute indices (`abs_index`) assigned to each node in the final 1D sequence.
- Submatrix bounds computed for each node.
- **Invariant Prefixes** that are assigned after sorting and are used for addressing and validation.

---

### FINAL 1D ORDERING RULES (Declarative, Step-by-Step)

1. **Origin at Index 0**
   - **Rule:** The very first node in `linear_order` must be the origin node.  
     **Implementation Note:** This node gets the invariant prefix "O" and is identified by the label `"Origin"` (or cleaned form thereof).  
     **Rationale:** It anchors the entire hierarchy, with all subsequent nodes positioned relative to it.

2. **Contiguous Block for Top-Level Categories**
   - **Rule:** Immediately following the origin, all top-level nodes (i.e., the direct children of the origin) must appear as one contiguous block.
   - **Ordering:** These nodes are sorted in **descending order by weight**.  
     **Example:** If the weights indicate that `A`, `B`, and `C` are top-level nodes, the order must be `[Origin, A, B, C,...]`.  
     **Rationale:** This separation distinguishes high-level categories from their subcategories.

3. **Subcategories Arranged After All Top-Level Categories**
   - **Rule:** No subcategory is allowed to appear before the full top-level block has been enumerated.  
     **Rationale:** This rule reinforces the clear, hierarchical separation needed in the 1D ordering.

4. **Subcategories Follow Their Parent Top-Level Order**
   - **Rule:** Once the top-level block is complete, subcategories are listed grouped by their parent. The ordering respects the left-to-right position of the parent as defined in the top-level block.
   - **Ordering:** Within each group, subcategories are sorted in descending order of weight.  
     **Rationale:** This preserves a fractal, parent-first approach throughout the linear order.

5. **Contiguity Within Parent Sub-Blocks**
   - **Rule:** All children of a given parent must form a contiguous sub-block in the final order.  
     **Example:** For a parent `A` with children `A1`, `A2`, and `A3`, these must appear sequentially after `A` with no interleaving from other parent's subcategories.
   - **Rationale:** It distinctly preserves the parent-child relationship as a single uninterrupted unit.

6. **Uniqueness of Labels/Prefixes**
   - **Rule:** Each node must have a unique label or invariant prefix.
   - **Rationale:** This prevents ambiguity in reference and supports reliable hierarchical lookups.

7. **Parent Occurs Before Child**
   - **Rule:** The position of any parent node in the 1D order must always occur before any of its child nodes.
   - **Rationale:** It guarantees a top-down progression in the hierarchy.

8. **Overall Contiguity and No Interleaving Among Groups**
   - **Rule:** The 1D ordering must display a clear separation between the top-level block and each subsequent group of subcategories.
   - **Example:** Valid ordering: `[Origin, A, B, C, A1, A2, B1, B2, C1]`; Invalid ordering: `[Origin, A, B1, B, A1, ...]`.
   - **Rationale:** Ensures that the hierarchy's structure is maintained without mixing nodes from different parent groups.

9. **Descending Weights on Every Level**
   - **Rule:** For any node with children, its children must be arranged in descending order of their respective weights.
   - **Rationale:** This "heavier first" principle supports both effective processing and a consistent address assignment.


PLANNING: SUBMATRIX BOUNDS (Rule 10)

10. Submatrix Bounds:

    a. Direct Children Evaluation:
       - For any node in the hierarchy, if the node has direct children (i.e., immediate children with assigned abs_index values),
         compute the submatrix bounds as:
             • start_index = minimum of the abs_index values among the direct children.
             • end_index   = maximum of the abs_index values among the direct children.
       - These computed bounds must be stored on the node using a setter (set_submatrix_bounds(prefix, start_index, end_index))
         and retrieved via a getter (get_submatrix_bounds(prefix)).
       - After storage, the bounds are checked against the computed values. If any errors exist (i.e., mismatches),
         then the update step is repeated until all nodes' submatrix bounds are correct.

    b. Leaf Nodes:
       - For a node with no direct children (a leaf), the submatrix bounds are inherited from its parent.
       - This means that for a leaf node, you call the parent's getter using the category's invariant prefix to retrieve the 
         bounds, which must include the leaf's own abs_index.
       - The leaf's bounds are then set accordingly, ensuring consistency of the hierarchy.

    c. Validation & Enforcement:
       - A dedicated validation routine traverses the hierarchy and confirms that every node's stored submatrix bounds exactly
         match the expected values based solely on its direct children (or, for leaves, the parent's bounds).
       - If validation errors are detected, an enforcement loop (e.g., enforce_submatrix_bounds_rule) will redo the update
         and validation step repeatedly (up to a maximum number of attempts) until every node is compliant.
         
This rule guarantees that:
    - Each node's submatrix bounds accurately represent the range of the abs_index values of its direct children.
    - Leaf nodes rely on their parent's bounds to determine their placement.
    - All bounds are stored directly on the corresponding node and revalidated iteratively until the hierarchy is internally consistent.

---

### SELF-HEALING AND VALIDATION CHECKS

After constructing the `linear_order`, the following checks—as well as self-healing actions, where applicable—are performed within `FIMHierarchy`:

- **Check that the origin is at index 0.**
- **Verify continuous block formation** for top-level nodes with no subcategory interruptions.
- **Confirm that no subcategory precedes a top-level node.**
- **Ensure parent nodes always precede their children.**
- **Validate unique assignment of labels/invariant prefixes.**
- **Confirm descending weight order at every node level.**
- **Combined Hierarchy Validation:**  
  - **Self-Healing Measure:** The final JSON export merges top-level nodes and subcategories into a single dictionary (via `get_combined_hierarchy_dict()`).  
  - **Check:** The number of top-level nodes from the `linear_order` must match that in the combined hierarchy dictionary.
- **Invariant Prefix Reassignment:**  
  - **Note:** Even though nodes are first sorted in descending weight order, top-level nodes are then explicitly reassigned invariant prefixes in alphabetical order. Validation ensures that these prefixes adhere strictly to `[A, B, C, ...]`, independent of weight order.
- **Data Consolidation:**  
  - All derived data (absolute indices, computed invariant prefixes, combined hierarchy, submatrix bounds, etc.) are attached to the `FIMHierarchy` object. These are made available through methods like `to_dict()` and `to_json()` to support consistent downstream processing and troubleshooting.

By enforcing these nine rules in combination with self-check validations, the FIM pipeline ensures that the final 1D ordering is robust, reproducible, and self-healing. Any deviation detected by the checks triggers logging of explicit error messages, which can then be used to initiate recovery actions or further debugging.

---

### Summary

- **Step 1:** Start with the origin node at index 0.
- **Step 2:** Enumerate top-level nodes in one contiguous, descending-by-weight block immediately after the origin.
- **Step 3:** Append subcategories in the order of their parent's appearance, ensuring sub-block contiguity and descending order by weight within each group.
- **Step 4:** Assign absolute indices and recast invariant prefixes (top-level prefixes are reset alphabetically).
- **Step 5:** Consolidate the unified hierarchy in a single data structure used for JSON export.
- **Step 6:** Run validations and self-healing checks at each step to ensure the structure remains correct.
- **Output:** The `FIMHierarchy` object now contains validated, consolidated information for use across the pipeline, and the export methods (`to_dict()`, `to_json()`) include all computed data along with the full validation results.

This detailed planning ensures that every aspect of the 1D ordering is explicit, repeatable, and verifiable. The robust design supports both the construction and the automatic checking/self-healing of the pipeline's structure.

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
from string import ascii_uppercase

# Ensure logger is defined at the global scope.
logger = logging.getLogger(__name__)

# For completeness in this example, we define a simple Node class here.
class Node:
    def __init__(self, label, weight=1.0, skip_factor=1.0):
        self.label = label
        self.invariant_label = label  # Preserve original immutable label for simulation.
        self.weight = weight
        self.skip_factor = skip_factor
        self.children = []
        self.parent = None
        self.abs_index = None
        self.invariant_prefix = None
        self.submatrix_bounds = {"start_index": None, "end_index": None}  # Reintroduced submatrix bounds.
        # Initialize causal_metadata so that every Node has a default value.
        self.causal_metadata = {}

    def add_child(self, child):
        self.children.append(child)
        child.parent = self

    def set_submatrix_bounds(self, start_index, end_index, prefix=None):
        """Store the submatrix bounds for this node with prefix"""
        self.submatrix_bounds = {
            "start_index": start_index,
            "end_index": end_index,
            "prefix": prefix or self.invariant_prefix
        }

    def get_submatrix_bounds(self):
        """Get the stored submatrix bounds including prefix"""
        return self.submatrix_bounds

    def inspect(self):
        import pprint
        pprint.pprint(self.__dict__)

    def update_weight(self, new_weight):
        """Update the weight of this node and (optionally) trigger a hierarchy rebuild.
        In our design, FIMHierarchy handles the full update once this method is called."""
        self.weight = new_weight
        logging.info("Node %s updated with new weight %s", self.label, new_weight)

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
            child_node.parent = parent_node
            parent_node.add_child(child_node)
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

def save_hierarchy(him, filename):
    with open(filename, 'w') as f:
        # Dump the entire FIMHierarchy object
        json.dump(him.to_dict(), f, indent=4)

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
    
    # Map children to a canonical prefix. We use the order defined by keys in rand_graph["Origin"]
    desired_order = list(rand_graph.get("Origin", {}).keys())
    for i, label in enumerate(desired_order):
        if label in child_bounds:
            prefix = chr(ord('A') + i)
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

        # Initialize state field to consolidate HPC, entropy, weight-change information,
        # and add the new universal "structure_modified" (dirty) flag.
        self.state = {
            "aggregated_hpc": self.aggregated_hpc,
            "total_hpc": sum(self.aggregated_hpc) if self.aggregated_hpc else 0,
            "aggregated_entropy": self.aggregated_entropy,
            "weights_changed": False,  # Already used in current methods.
            "structure_modified": False,  # <-- New dirty state flag.
            "last_revalidation": None  # Timestamp of the last revalidation/update.
        }
        
        # Initialize validation fields.
        self.validation_checks = {}
        self.check_errors = {}

        # 1. Build the final 1D ordering (the linear order reflects top-level categories and subcategories).
        self.linear_order = self.build_final_ordering()

        # 2. Assign absolute indices based on the final ordering.
        self.assign_absolute_indices()

        # 3. Compute invariant prefixes after sorting.
        self.assign_invariant_prefixes()

        # 4. Build a mapping from absolute index to invariant prefix.
        self.label_positions = {node.abs_index: node.invariant_prefix for node in self.linear_order}

        # 5. (Optional) Compute invariant positions from the canonical ordering.
        self.compute_invariant_positions()

        # --- New: Apply the causal metadata update ---
        self.apply_causal_metadata()

        # 6. Run all validations (including causal metadata checks).
        self.run_validations()

        # 7. Collect the outcomes of the validations into a dict.
        self.collect_validation_results()

        # Additional fields.
        self.submatrix_bounds = {}
        self.functional_submatrix_bounds = {}
        self.category_address_map = {}

        # New field for previous linear order
        self.previous_linear_order = [
            getattr(node, 'unique_id', node.label) for node in self.linear_order
        ] if hasattr(self, 'linear_order') else []

        self.rule_engine = RuleEngine()
        self.validate_and_repair()
    
    # -------------------- NEW: UNIVERSAL DIRTY FLAG HANDLERS ---------------------
    def mark_structure_modified(self):
        """
        Mark the hierarchy as modified (dirty). This flag should be set whenever any structural
        changes occur (for example, a node is added, removed, or its weight is updated).
        """
        self.state["structure_modified"] = True
        logging.info("Structure modified flag set to True.")

    def clear_structure_modified(self):
        """
        Clear the structure modified (dirty) flag after a successful revalidation.
        """
        self.state["structure_modified"] = False
        logging.info("Structure modified flag cleared (False).")
    
    # -------------------- UPDATE ORDERING (EXAMPLE USAGE OF DIRTY FLAG) ---------------------
    def update_ordering(self):
        """
        Update linear ordering with rule validation.
        """
        self.previous_linear_order = [
            getattr(node, 'unique_id', node.label) 
            for node in self.linear_order
        ]
        
        # Build initial ordering
        self.linear_order = self.build_final_ordering()
        
        # Mark structure as modified - ordering has changed.
        self.mark_structure_modified()
        
        # Validate and repair conditionally if structure is dirty.
        if self.state["structure_modified"]:
            self.validate_and_repair()
            self.clear_structure_modified()
        
        # Update indices and prefixes
        self.assign_absolute_indices()
        self.assign_invariant_prefixes()
        
        # Compute changes
        self.compute_ordering_diff()

    # ------------------------ UPDATING STATE VIA REVALIDATION --------------------
    def revalidate(self):
        """
        Re-run all validations and update internal validation results.
        Additionally, if the structure was marked as modified (dirty),
        force re-validation and then clear the dirty flag.
        """
        if self.state["structure_modified"]:
            self.run_validations()
            self.collect_validation_results()
            self.update_state()
            logging.info("Revalidation triggered due to structure modification.")
            self.clear_structure_modified()
        else:
            logging.info("No structural changes detected; skipping revalidation.")

    def validate_and_repair(self):
        """Validate and repair hierarchy structure"""
        if not self.rule_engine.repair(self, max_attempts=3):
            logging.warning("Could not repair all rule violations")
            
    def add_custom_rule(self, rule):
        """Add a custom validation rule"""
        self.rule_engine.add_rule(rule)
        
    def update_state(self):
        """
        Update the state field with the latest aggregated HPC and entropy,
        recalculate the total HPC, and record the current timestamp as the last revalidation time.
        """
        import time
        self.state["total_hpc"] = sum(self.aggregated_hpc) if self.aggregated_hpc else 0
        self.state["aggregated_hpc"] = self.aggregated_hpc
        self.state["aggregated_entropy"] = self.aggregated_entropy
        self.state["last_revalidation"] = time.time()

    def mark_weights_changed(self, changed=True):
        """
        Update the state flag to reflect that weights have been modified or new nodes inserted.
        """
        self.state["weights_changed"] = changed

    def build_final_ordering(self):
        """
        Build the final 1D ordering with these steps:
          1. The origin (root) is at index 0.
          2. Top-level nodes (direct children of the origin) are sorted in descending order by weight.
          3. For each top-level node, append its subcategories (also sorted descending by weight).
        """
        order = []
        # Step 1: Add the origin.
        order.append(self.root)
        
        # Step 2: Top-level nodes, sorted by descending weight.
        top_levels = sorted(self.root.children, key=lambda n: n.weight, reverse=True)
        order.extend(top_levels)
        self.top_level_block_end = len(order) - 1

        # Step 3: Append each top-level node's children (subcategories), sorted descending.
        for node in top_levels:
            subcats = sorted(node.children, key=lambda n: n.weight, reverse=True)
            order.extend(subcats)
        return order

    def assign_absolute_indices(self):
        """
        Assign each node an absolute index corresponding to its position in the final ordering.
        """
        for index, node in enumerate(self.linear_order):
            node.abs_index = index

    def assign_invariant_prefixes(self):
        """
        Once sorting is complete, assign invariant prefixes as follows:
          - The root always gets the prefix "O".
          - Top-level nodes (direct children of the origin) are *reassigned* new invariant prefixes in alphabetical order
            based solely on their final ordering position. (For example, regardless of their cleaned unique ID,
            the first top-level node gets "A", the second "B", etc.)
          - For subcategories, compute the invariant prefix as the parent's invariant prefix concatenated with the
            sibling order (1-indexed) based on the parent's children sorted descending by weight.
        """
        # The root.
        self.root.invariant_prefix = "O"
        
        # Top-level nodes: override invariant prefixes by final ordering position.
        top_levels = [node for node in self.linear_order if node.parent == self.root]
        for i, node in enumerate(top_levels):
            node.invariant_prefix = chr(ord('A') + i)
        
        # For subcategories: assign parent's invariant prefix + 1-indexed order among the parent's children.
        for node in self.linear_order:
            if node.parent and node.parent != self.root:
                sorted_children = sorted(node.parent.children, key=lambda n: n.weight, reverse=True)
                child_order = sorted_children.index(node) + 1  # 1-indexed.
                node.invariant_prefix = node.parent.invariant_prefix + str(child_order)

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

    def check_top_level_alphabetical_prefixes(self):
        """
        Validate that the top-level nodes (direct children of the origin) have invariant prefixes assigned
        in alphabetical order based on their final ordering position.
        
        For example, if there are four top-level nodes, their invariant prefixes must be:
              ['A', 'B', 'C', 'D']
        """
        top_levels = [node for node in self.linear_order if node.parent == self.root]
        expected_prefixes = [chr(ord('A') + i) for i in range(len(top_levels))]
        actual_prefixes = [node.invariant_prefix for node in top_levels]
        
        print("Info: Top-level nodes (final ordering) and their assigned alphabetical invariant prefixes:")
        for node in top_levels:
            print(f"  Node {node.label} (Weight: {node.weight:.3f}) -> Invariant Prefix: {node.invariant_prefix}")
        
        if expected_prefixes != actual_prefixes:
            err_msg = (f"Top-level nodes expected alphabetical invariant prefixes {expected_prefixes} "
                       f"but found {actual_prefixes}.")
            self.validation_checks['top_level_alphabetical_prefixes'] = err_msg
            self.check_errors['top_level_alphabetical_prefixes'] = err_msg
        else:
            self.validation_checks['top_level_alphabetical_prefixes'] = "OK"

    def run_validations(self):
        """
        Run existing validations plus causal metadata validation.
        """
        self.check_origin_at_index0()
        self.check_top_level_contiguity()
        self.check_subcategory_blocks_contiguity()
        self.check_parent_before_child()
        self.check_no_duplicates()
        self.check_descending_weights()
        self.check_subcategories_descending_order()
        self.check_subcategory_order_matches_canonical()
        self.check_top_level_alphabetical_prefixes()
        self.check_combined_hierarchy()
        self.check_linear_order_staleness()
        # New: Validate causal metadata.
        causal_errors = self.validate_causal_metadata()
        if causal_errors:
            self.validation_checks['causal_metadata'] = causal_errors
            self.check_errors['causal_metadata'] = causal_errors
        else:
            self.validation_checks['causal_metadata'] = "OK"

    def collect_validation_results(self):
        """
        Write the outcomes of the validation checks to the object as a dict
        so they can be inspected later.
        """
        self.validation_results = {
            "validation_checks": self.validation_checks,
            "validation_errors": self.check_errors
        }

    def print_validation_results(self):
        """
        Print all validation check results stored in the FIMHierarchy, including any errors.
        """
        print("Validation Check Results:")
        for key, result in self.validation_checks.items():
            print(f"  {key}: {result}")
        if self.check_errors:
            print("Validation Errors:")
            for key, err in self.check_errors.items():
                print(f"  {key}: {err}")
        else:
            print("All checks passed successfully.")

    def print_hierarchy_and_validation(self):
        """
        Prints the validation check outputs, then recursively prints the complete FIMHierarchy structure.
        """
        self.print_validation_results()
        print("\nFinal FIMHierarchy Structure:")
        self._recursive_print(self.root)

    def _recursive_print(self, node, indent=0):
        """
        Recursively print a node and its children with a fallback default for invariant_prefix.
        """
        prefix = getattr(node, 'invariant_prefix', 'NA')
        print("  " * indent + f"Node {node.label} (abs_index: {node.abs_index}, invariant_prefix: {node.invariant_prefix}) - Bounds: {node.get_submatrix_bounds()}")
        for child in node.children:
            self._recursive_print(child, indent+1)

    def __str__(self):
        """
        Custom string representation of the FIMHierarchy object, including:
          - The dict of validation results.
          - The recursive hierarchy structure.
        """
        output = []
        output.append("FIMHierarchy Object Representation:")
        output.append("Validation Results Dict: " + str(self.validation_results))
        output.append("\nHierarchy Structure:")
        output.extend(self._recursive_str(self.root))
        return "\n".join(output)

    def _recursive_str(self, node, indent=0):
        """
        Helper method for __str__ to recursively format the hierarchy structure.
        Uses a default for invariant_prefix if missing.
        """
        lines = []
        prefix = getattr(node, 'invariant_prefix', 'NA')
        lines.append("  " * indent + f"Node {node.label} [Prefix: {prefix}] (Index: {node.abs_index}, Weight: {node.weight:.3f})")
        for child in node.children:
            lines.extend(self._recursive_str(child, indent+1))
        return lines

    def _node_to_dict(self, node):
        """
        Convert a Node to a dict suitable for JSON serialization.
        Use 'invariant_prefix' to capture the updated prefix rather than a legacy 'prefix' field.
        """
        return {
            "label": node.label,
            "invariant_prefix": getattr(node, 'invariant_prefix', None),
            "abs_index": node.abs_index,
            "weight": node.weight,
            "skip_factor": getattr(node, 'skip_factor', None),
            "submatrix_bounds": node.submatrix_bounds,
            "children": [self._node_to_dict(child) for child in node.children]
        }

    def get_combined_hierarchy_dict(self):
        """
        Build a combined hierarchy dictionary by using the linear ordering for top-level nodes
        and then including their subtrees (as stored in the original tree). This ensures that the
        top-level categories (typically children of the origin) are not separated from their subcategories.
        """
        top_level_nodes = [node for node in self.linear_order if node.parent == self.root]
        top_level_dicts = [self._node_to_dict(node) for node in top_level_nodes]
        return {
            "origin": self._node_to_dict(self.root),
            "top_levels": top_level_dicts
        }

    def check_combined_hierarchy(self):
        """
        Validate that the combined hierarchy (which merges top-level categories with subcategories)
        includes the correct number of top-level nodes. If there is a mismatch, record an error.
        """
        top_levels_linear = [node for node in self.linear_order if node.parent == self.root]
        combined = self.get_combined_hierarchy_dict().get("top_levels", [])
        if len(top_levels_linear) != len(combined):
            err_msg = f"Combined hierarchy mismatch: expected {len(top_levels_linear)} top-level nodes, found {len(combined)}."
            self.validation_checks["combined_hierarchy"] = err_msg
            self.check_errors["combined_hierarchy"] = err_msg
        else:
            self.validation_checks["combined_hierarchy"] = "OK"

    def check_origin_at_index0(self):
        """
        Rule 1: Validate that the origin node is at index 0.
        """
        if self.linear_order[0] != self.root:
            msg = f"Origin node is not at index 0. Found {self.linear_order[0].label} instead."
            self.validation_checks['origin'] = msg
            self.check_errors['origin'] = msg
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
            self.check_errors['top_level_contiguity'] = msg
        else:
            self.validation_checks['top_level_contiguity'] = "OK"

        # Also check the descending order (Rule 9 applied to the Origin's children).
        top_levels = [node for node in self.linear_order if node.parent == self.root]
        top_weights = [node.weight for node in top_levels]
        sorted_top_weights = sorted(top_weights, reverse=True)
        if top_weights != sorted_top_weights:
            msg = f"Top-level categories are not sorted in descending order: weights found {top_weights}."
            self.validation_checks['top_level_descending'] = msg
            self.check_errors['top_level_descending'] = msg
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
            self.check_errors['subcategory_blocks_contiguity'] = contiguity_errors
        else:
            self.validation_checks['subcategory_blocks_contiguity'] = "OK"

    def check_parent_before_child(self):
        """
        Rule 7: Validate that every parent's absolute index is less than those of its children.
        """
        errors = []
        for node in self.linear_order:
            for child in node.children:
                # If a child doesn't have an assigned abs_index, it means it's not in the linear ordering.
                if child.abs_index is None:
                    errors.append(
                        f"Child {child.label} of parent {node.label} does not have an absolute index assigned (stale linear ordering)."
                    )
                elif node.abs_index is None or node.abs_index >= child.abs_index:
                    errors.append(
                        f"Parent {node.label} at index {node.abs_index} appears after its child {child.label} at index {child.abs_index}."
                    )
        if errors:
            self.validation_checks['parent_before_child'] = errors
            self.check_errors['parent_before_child'] = errors
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
            self.check_errors['duplicates'] = msg
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
            self.check_errors['descending_weights'] = weight_violations
        else:
            self.validation_checks['descending_weights'] = "OK"

    def check_subcategories_descending_order(self):
        """
        New Check:
        For each top-level category (i.e., direct children of the origin), validate that its subcategories
        (direct children of the category) appear in descending order by weight.
        """
        errors = []
        # Only consider top-level categories.
        top_levels = [node for node in self.linear_order if node.parent == self.root]
        for category in top_levels:
            # Get the subcategories as they appear in the final ordering.
            subcats = [child for child in self.linear_order if child.parent == category]
            # Compute the expected order by descending weight.
            expected_order = sorted(subcats, key=lambda n: n.weight, reverse=True)
            if subcats != expected_order:
                errors.append(
                    f"For category {category.label}, subcategories weights: {[child.weight for child in subcats]} do not match expected descending order: {[child.weight for child in expected_order]}."
                )
        if errors:
            self.validation_checks['subcats_descending'] = errors
            self.check_errors['subcats_descending'] = errors
        else:
            self.validation_checks['subcats_descending'] = "OK"

    def check_subcategory_order_matches_canonical(self):
        """
        For each top-level node, validate that its subcategories which are part of the canonical ordering
        have invariant prefixes that match the expected order.
        Extra (noncanonical) children are ignored.
        """
        errors = []
        for node in self.linear_order:
            if node.parent == self.root:
                # Clean parent's label to lookup canonical ordering.
                parent_clean = node.label.replace("LLM_10_", "")
                canonical_dict = self.rand_graph.get(parent_clean, {})
                canonical_order = list(canonical_dict.keys())
                if not canonical_order:
                    continue

                # Get the subcategories from the final ordering.
                subcats = [child for child in self.linear_order if child.parent == node]
                # Filter to only include children that are in the canonical ordering.
                filtered_subcats = [
                    child for child in subcats 
                    if child.label.replace("LLM_10_", "") in canonical_order
                ]
                # Sort the filtered subcategories by descending weight.
                filtered_subcats_sorted = sorted(filtered_subcats, key=lambda n: n.weight, reverse=True)
                # Expected invariant prefixes follow parent's prefix + a sequential number.
                expected_prefixes = [node.invariant_prefix + str(i + 1) for i in range(len(filtered_subcats_sorted))]
                actual_prefixes = [child.invariant_prefix for child in filtered_subcats_sorted]
                if expected_prefixes != actual_prefixes:
                    errors.append(
                        f"For parent {node.label}, expected subcategory invariant prefixes {expected_prefixes} but found {actual_prefixes}."
                    )
        if errors:
            self.validation_checks['subcat_order_canonical'] = errors
            self.check_errors['subcat_order_canonical'] = errors
        else:
            self.validation_checks['subcat_order_canonical'] = "OK"

    def check_linear_order_staleness(self):
        """
        Check if there are any new nodes added that are not present in the final linear order.
        If found, it indicates that the ordering is out-of-date and the weights have changed.
        """
        errors = []
        # Create a set using the node object identity from the existing linear order.
        linear_order_set = set(self.linear_order)
        for node in self.linear_order:
            for child in node.children:
                if child not in linear_order_set:
                    errors.append(
                        f"New child {child.label} (of {node.label}) is not in the linear ordering. "
                        "Re-sorting is required."
                    )
        if errors:
            self.validation_checks["linear_order_staleness"] = errors
            self.check_errors["linear_order_staleness"] = errors
        else:
            self.validation_checks["linear_order_staleness"] = "OK"

    def debug_print_tree(self):
        def _print(node, indent=0):
            print("  " * indent + f"{node.label}: {node.invariant_prefix}")
            for child in node.children:
                _print(child, indent+1)
        _print(self.root)

    # ------------------- NEW HELPER FUNCTIONS FOR BIDIRECTIONAL NAVIGATION -------------------

    def get_node_by_abs_index(self, index):
        """
        Return the node at the given absolute index from the linear order.
        """
        if index < 0 or index >= len(self.linear_order):
            return None
        return self.linear_order[index]

    def get_node_by_label(self, label):
        """
        Return the first node that matches the given label in the linear order.
        """
        for node in self.linear_order:
            if node.label == label:
                return node
        return None

    def get_node_by_prefix(self, prefix):
        """
        Return the first node that matches the given invariant prefix.
        """
        for node in self.linear_order:
            if node.invariant_prefix == prefix:
                return node
        return None

    def get_next_node(self, node):
        """
        Given a node, return the next node in the linear ordering.
        """
        next_index = node.abs_index + 1
        return self.get_node_by_abs_index(next_index)

    def get_previous_node(self, node):
        """
        Given a node, return the previous node in the linear ordering.
        """
        prev_index = node.abs_index - 1
        return self.get_node_by_abs_index(prev_index) if prev_index >= 0 else None

    def get_path_to_origin(self, node):
        """
        Return a list of nodes representing the path from the given node back to the origin.
        """
        path = []
        current = node
        while current is not None:
            path.insert(0, current)
            current = current.parent
        return path

    def get_siblings(self, node):
        """
        Return a list of sibling nodes for the given node.
        (Excludes the node itself.)
        """
        if not node.parent:
            return []
        return [s for s in node.parent.children if s != node]

    def get_causal_metadata_dict(self):
        """
        Build and return a dictionary mapping each node's unique id to its causal metadata.
        The unique id is taken from node.unique_id if set; otherwise, node.label is used as a fallback.
        This ensures the metadata remains attached to the unique node rather than its position.
        """
        metadata_map = {}
        for node in self.linear_order:
            # Use unique_id if it exists; fallback to node.label.
            node_unique_id = getattr(node, 'unique_id', node.label)
            metadata_map[node_unique_id] = node.causal_metadata
        return metadata_map

    def to_dict(self):
        """
        Return a dict representation of the complete FIMHierarchy object.
        This now includes the metadata map showing unique_id: metadata mappings.
        """
        return {
            "root": self._node_to_dict(self.root),
            "rand_graph": self.rand_graph,
            "aggregated_hpc": self.aggregated_hpc,
            "aggregated_entropy": self.aggregated_entropy,
            "state": self.state,
            "validation_results": self.validation_results,
            "label_positions": self.label_positions,
            "linear_order": [getattr(n, 'unique_id', n.label) for n in self.linear_order],
            "previous_linear_order": self.previous_linear_order,
            "ordering_diff": getattr(self, "ordering_diff", None),
            "submatrix_bounds": self.submatrix_bounds,
            "functional_submatrix_bounds": self.functional_submatrix_bounds,
            "causal_metadata_map": self.get_causal_metadata_dict()  # New mapping: unique id -> metadata
        }
    
    def to_json(self, **kwargs):
        """
        Serializes the FIMHierarchy to a JSON-formatted string.
        """
        import json
        return json.dumps(self.to_dict(), **kwargs)

    def print_serialized(self):
        """
        Serializes and prints the entire FIMHierarchy object using JSON.
        This includes the state, validation results, label positions, and the combined hierarchy.
        """
        print(self.to_json(indent=2))

    def get_node_by_invariant_label(self, label):
        """
        Return the first node that matches the given invariant_label in the linear order.
        """
        for node in self.linear_order:
            if node.invariant_label == label:
                return node
        return None

    def compute_ordering_diff(self):
        """
        Compute the difference between the previous and current linear orders.
        Assumes self.previous_linear_order and self.linear_order are lists of unique node ids.
        Stores the mapping in self.ordering_diff, where each key is the node unique id and the value is a dict
        with keys 'old_index' and 'new_index'. Uses node.unique_id if it exists; otherwise, falls back to node.label.
        """
        diff = {}
        # Create a mapping of node id to its index in the previous ordering.
        prev_index_map = {node_id: idx for idx, node_id in enumerate(self.previous_linear_order)}
        
        # For each node in the new linear order, record its new index and any corresponding old index.
        for new_idx, node in enumerate(self.linear_order):
            node_id = getattr(node, 'unique_id', node.label)
            old_idx = prev_index_map.get(node_id)
            diff[node_id] = {"old_index": old_idx, "new_index": new_idx}
        
        self.ordering_diff = diff
        return diff

    def apply_causal_metadata(self):
        """
        Iterate through the linear ordering and update each node's causal metadata.
        For the origin node, simulate its metadata independently.
        For every other node, simulate the parent→child link metadata.
        """
        iteration = len(self.aggregated_hpc)
        for node in self.linear_order:
            if node.parent is None:
                # For the origin node, set its metadata using the origin helper.
                node.causal_metadata = simulate_origin_metadata(node, iteration)
            else:
                # For non-origin nodes, simulate the causal link metadata.
                node.causal_metadata = simulate_llm_causal_reasoning(node.parent, node, iteration)

    def validate_causal_metadata(self):
        """
        Validate that every node (except the origin) has structured causal metadata.
        Checks that the metadata is a dict and that a non-empty 'justification' is present.
        """
        errors = []
        for node in self.linear_order:
            if node.parent is not None:
                meta = node.causal_metadata
                if not isinstance(meta, dict) or not meta.get("justification"):
                    errors.append(f"Node {node.label} (Index {node.abs_index}) is missing structured causal metadata.")
        return errors

    def compute_expected_submatrix_bounds(self, node, category_prefix=None):
        """
        Compute the expected submatrix bounds for a given node following Rule 10.

        For nodes with direct children:
          - Expected start_index = the minimum abs_index among the direct children.
          - Expected end_index   = the maximum abs_index among the direct children.
          
        For leaf nodes (no direct children):
          - Expected bounds are inherited from the parent's submatrix bounds.
          - This is obtained by calling the parent's getter (with its invariant prefix) and
            verifying that the node's own abs_index is within that range.
          - If the parent's bounds are not available or the node's abs_index does not fall
            within them, the node's own abs_index is used for both start and end indices.

        Args:
            node: The node for which to compute the expected bounds.
            category_prefix: Optional prefix for retrieving the parent's bounds via a getter.
                             (Typically, this would be node.parent.invariant_prefix.)
                             
        Returns:
            A dictionary with keys "start_index" and "end_index" representing the expected submatrix bounds.
        """
        # Case 1: Node has direct children.
        if node.children:
            # Filter out any child that does not have an assigned abs_index.
            child_indices = [child.abs_index for child in node.children if child.abs_index is not None]
            if child_indices:
                return {
                    "start_index": min(child_indices),
                    "end_index": max(child_indices)
                }
            else:
                # In the unlikely case that children exist but none have an abs_index,
                # fall back on the node's own abs_index.
                return {"start_index": node.abs_index, "end_index": node.abs_index}
        else:
            # Case 2: Leaf node. Retrieve parent's bounds.
            if node.parent:
                # We assume that parent's invariant_prefix is used as the key.
                parent_bounds = node.parent.get_submatrix_bounds(node.parent.invariant_prefix)
                if (node.abs_index is not None and parent_bounds and
                    parent_bounds.get("start_index") is not None and
                    parent_bounds.get("end_index") is not None and
                    parent_bounds["start_index"] <= node.abs_index <= parent_bounds["end_index"]):
                    return parent_bounds
                else:
                    # If parent's bounds are invalid or the abs_index is out-of-range,
                    # default to using the node's own position.
                    return {"start_index": node.abs_index, "end_index": node.abs_index}
            else:
                # In case of the root having no children (unlikely in proper usage),
                # use its own abs_index.
                return {"start_index": node.abs_index, "end_index": node.abs_index}

    def validate_submatrix_bounds(self):
        """
        Traverse the hierarchy and validate that each node's stored submatrix bounds match
        the expected bounds computed solely from its direct children. For non-leaf nodes, the
        expected bounds are the minimum and maximum abs_index values of its direct children.
        For leaf nodes, the expected bounds are inherited from its parent's category field,
        ensuring that the node's abs_index is included within that range.

        Returns:
            errors (list): A list of error messages for any mismatches found in the hierarchy.
        """
        errors = []

        def _validate(node):
            # Determine expected bounds for nodes with direct children.
            if node.children:
                # Gather abs_index values only of direct children.
                child_indices = [child.abs_index for child in node.children if child.abs_index is not None]
                if child_indices:
                    expected = {"start_index": min(child_indices), "end_index": max(child_indices)}
                else:
                    expected = {"start_index": node.abs_index, "end_index": node.abs_index}
            else:
                # For a leaf node, inherit the parent's bounds.
                if node.parent:
                    # We assume that the parent's invariant_prefix identifies its category.
                    expected = node.parent.get_submatrix_bounds(node.parent.invariant_prefix)
                    # If for some reason this call returns None, default to the node's abs_index.
                    if expected is None:
                        expected = {"start_index": node.abs_index, "end_index": node.abs_index}
                    else:
                        # Validate that the node's abs_index is within the inherited bounds.
                        if not (expected["start_index"] <= node.abs_index <= expected["end_index"]):
                            errors.append(
                                f"Leaf node '{node.label}' (abs_index: {node.abs_index}) is outside its parent's bounds {expected}."
                            )
                else:
                    # If this is the root and it has no children, use its own abs_index.
                    expected = {"start_index": node.abs_index, "end_index": node.abs_index}

            # Retrieve the stored bounds using the node's invariant prefix.
            stored = node.get_submatrix_bounds()
            if stored != expected:
                errors.append(
                    f"Node '{node.label}' (abs_index: {node.abs_index}) has stored bounds {stored} but expected {expected}."
                )
            
            # Recursively validate each child.
            for child in node.children:
                _validate(child)

        _validate(self.root)
        return errors

    def assign_submatrix_bounds_to_nodes(self):
        """
        Recursively assign submatrix bounds to every node in the hierarchy and update
        the invariant prefix based on the node's position.
        
        Invariant prefix assignment:
          - The root (origin) gets "O".
          - Direct children of the origin get letters ("A", "B", "C", etc.).
          - For deeper nodes, the invariant prefix is the parent's invariant prefix concatenated with a sequential number.
        """
        for node in self.linear_order:
            if node.children:
                # Internal node: compute bounds from children and produce no prefix.
                child_indices = [
                    child.abs_index for child in node.children if child.abs_index is not None
                ]
                bounds = {
                    "start_index": min(child_indices) if child_indices else node.abs_index,
                    "end_index": max(child_indices) if child_indices else node.abs_index
                }
            else:
                # Leaf node: simply copy the container's (i.e. parent's) bounds if available,
                # with no prefix assignment.
                if node.parent and node.parent.submatrix_bounds:
                    parent_bounds = node.parent.submatrix_bounds
                    bounds = {
                        "start_index": parent_bounds.get("start_index", node.abs_index),
                        "end_index": parent_bounds.get("end_index", node.abs_index)
                    }
                else:
                    bounds = {"start_index": node.abs_index, "end_index": node.abs_index}
    
            node.submatrix_bounds = bounds
            logging.debug("Assigned bounds for node %s: %s", node.label, node.submatrix_bounds)

    def check_and_update_all_submatrix_bounds(self):
        """
        Traverse the tree and compare each node's stored submatrix bounds with computed bounds.
        Returns a list of discrepancy error messages.
        """
        errors = []
        def _traverse(node):
            stored = node.get_submatrix_bounds()
            if node.children:
                indices = [child.abs_index for child in node.children if child.abs_index is not None]
                if indices:
                    expected = {"start_index": min(indices), "end_index": max(indices)}
                else:
                    expected = {"start_index": node.abs_index, "end_index": node.abs_index}
            else:
                if node.parent:
                    expected = node.parent.get_submatrix_bounds()
                else:
                    expected = {"start_index": node.abs_index, "end_index": node.abs_index}
            if stored != expected:
                errors.append(f"Node '{node.label}' expected {expected}, got {stored}")
            for child in node.children:
                _traverse(child)
        _traverse(self.root)
        return errors

    def enforce_submatrix_bounds_rule(self):
        """
        Self-healing mechanism: repeatedly assign submatrix bounds until no errors remain.
        A safe maximum iteration count is used to prevent infinite loops.
        """
        attempt = 1
        max_iterations = 1000   # Safeguard to avoid infinite looping if errors never resolve.
        while attempt <= max_iterations:
            # --- Added: Re-compute the ordering based on the current (randomized) weights.
            self.linear_order = self.build_final_ordering()
            self.assign_absolute_indices()
            self.assign_invariant_prefixes()
            self.label_positions = {node.abs_index: node.invariant_prefix for node in self.linear_order}
            self.compute_invariant_positions()

            # Now recompute submatrix bounds using the (possibly) updated ordering.
            self.assign_submatrix_bounds_to_nodes()
            errors = self.check_and_update_all_submatrix_bounds()
            if not errors:
                logging.info("Submatrix bounds rule enforced successfully on attempt %d", attempt)
                return
            logging.warning("Attempt %d: Submatrix bounds errors found: %s", attempt, errors)
            attempt += 1
        
        logging.error("Maximum iterations (%d) reached; self-healing failed to remove all submatrix bounds errors.", max_iterations)
        return errors

    def rebuild_canonical_ordering(self):
        """
        Rebuilds the ordering from the current live tree (including injected nodes like "A3").
        This ensures that any extra nodes added after the base graph is created will be
        included (and sorted) in the final hierarchy snapshot.
        """
        self.linear_order = self.build_final_ordering_from_live_tree()
        self.assign_absolute_indices()
        self.assign_invariant_prefixes()
        self.label_positions = {node.abs_index: node.invariant_prefix for node in self.linear_order}

    def build_final_ordering_from_live_tree(self):
        """
        Build a final ordering by traversing the current live tree (depth‑first search).
        This method sorts children in descending order by weight (adjust as needed).
        """
        ordering = []
        def traverse(node):
            ordering.append(node)
            for child in sorted(node.children, key=lambda n: n.weight, reverse=True):
                traverse(child)
        traverse(self.root)
        return ordering

    def trigger_hierarchy_update(self):
        """Rebuilds hierarchy after weight changes."""
        logging.info("Triggering full hierarchy update due to weight change.")
        self.linear_order = self.build_final_ordering()
        self.assign_absolute_indices()
        self.assign_invariant_prefixes()
        # Assuming assign_submatrix_bounds_to_nodes exists; otherwise, use the appropriate method.
        self.assign_submatrix_bounds_to_nodes()
        self.propagate_causal_metadata()

    def update_weight(self, identifier, new_weight):
        """
        Updates the weight of a node and triggers a full hierarchy update.
        The identifier can be:
          - An absolute index (int)
          - An invariant prefix (str)
          - A node label (str)
        """
        node = None
        if isinstance(identifier, int):  # Absolute index
            node = self.get_node_by_abs_index(identifier)
        elif isinstance(identifier, str):
            node = self.get_node_by_prefix(identifier) or self.get_node_by_label(identifier)

        if node:
            node.update_weight(new_weight)
            self.trigger_hierarchy_update()
            # Optionally mark via our "dirty flag" as well:
            self.mark_structure_modified()
        else:
            raise ValueError(f"Node {identifier} not found.")

    def propagate_causal_metadata(self):
        """
        Updates causal metadata after reordering. Ensures parent-child relationships
        remain intact with the latest weights.
        """
        for node in self.linear_order:
            if node.parent:
                node.causal_metadata["parent_causal_weight"] = node.parent.weight
                total = sum(child.weight for child in node.parent.children)
                node.causal_metadata["relative_weight"] = node.weight / total if total != 0 else 0
                logging.info("Propagated causal metadata for node %s", node.label)

def simulate_origin_metadata(node, iteration):
    """
    Simulate causal metadata for the origin node.
    """
    return {
        "justification": f"Simulated origin metadata for node {node.label} at iteration {iteration}",
        "payload": {
            "origin_name": node.label,
            "origin_invariant_prefix": node.invariant_prefix,
            "origin_abs_index": node.abs_index,
            "origin_weight": node.weight,
        }
    }

def simulate_llm_causal_reasoning(parent, child, iteration):
    """
    Simulate causal reasoning metadata for a non-origin node based on its parent.
    """
    return {
        "justification": f"Simulated causal reasoning between {parent.label} and {child.label} at iteration {iteration}",
        "payload": {
            "parent_name": parent.label,
         "parent_invariant_prefix": parent.invariant_prefix,
         "parent_abs_index": parent.abs_index,
         "parent_weight": parent.weight,
            "child_name": child.label,
         "child_invariant_prefix": child.invariant_prefix,
         "child_abs_index": child.abs_index,
            "child_weight": child.weight,
        }
    }

# --------------------------------------------------------------------
# Minimal implementation of RuleEngine to support FIMHierarchy.
# This class provides stubs for add_default_rules() and repair().
# You can later add more robust rule validation and repair mechanisms.
# --------------------------------------------------------------------
class RuleEngine:
    """
    Minimal implementation of RuleEngine for validating and repairing the hierarchy.
    """
    def __init__(self):
        self.rules = []
        self.add_default_rules()

    def add_default_rules(self):
        # Add default rules if available.
        # For now, no default rules are set.
        pass

    def add_rule(self, rule):
        """Add a custom validation rule."""
        self.rules.append(rule)

    def repair(self, hierarchy, max_attempts=3):
        """
        A minimal repair method.
        Rebuilds the canonical ordering from the live tree and checks that the extra node is present.
        """
        logging.info("Running minimal repair process in RuleEngine.")

        def find_node_by_label(node, label):
            if node.label == label:
                return node
            for child in node.children:
                result = find_node_by_label(child, label)
                if result is not None:
                    return result
            return None
          
        success = False
        for attempt in range(1, max_attempts + 1):
            node_A = find_node_by_label(hierarchy.root, "LLM_3_A")
            if not node_A:
                logging.error("Node LLM_3_A not found in hierarchy!")
                return False
  
            logging.info("Rebuilding canonical ordering (from live tree) and reassigning indices/prefixes (attempt %d)...", attempt)
            # Rebuild ordering from live tree (which now includes the extra node, if attached)
            hierarchy.linear_order = hierarchy.build_final_ordering_from_live_tree()
            hierarchy.assign_absolute_indices()
            hierarchy.assign_invariant_prefixes()
            hierarchy.label_positions = {node.abs_index: node.invariant_prefix for node in hierarchy.linear_order}

            # Check that the extra node (labeled with "A3") is present among node_A's children.
            if any("A3" in child.label for child in node_A.children):
                logging.info("Extra node found in LLM_3_A children. Repair successful on attempt %d.", attempt)
                success = True
                break
        if not success:
            logging.error("Maximum attempts (%d) reached; self-healing failed.", max_attempts)
            return False
        return True

# Global helper defintion for searching a node by label
def find_node_by_label(node, label):
    if node.label == label:
        return node
    for child in node.children:
        result = find_node_by_label(child, label)
        if result is not None:
            return result
    return None

# Global helper function to update labels based on simulation rules.
def update_labels(node, iteration=3):
    """
    Recursively update every node's label and causal metadata.
    This simulation function updates the label by appending a suffix based on the iteration,
    and adds a 'simulation_iteration' field into the node's causal_metadata.
    """
    node.label = f"{node.invariant_label}_simulated_{iteration}"
    node.causal_metadata["simulation_iteration"] = iteration
    for child in node.children:
        update_labels(child, iteration)

# Global helper function to update in-links (simulate causal reasoning)
def update_in_links(node, iteration=3):
    """
    Recursively update each node's causal metadata with simulation link data if missing.
    This ensures that each node (especially new ones) has a proper in link connecting it to its parent.
    """
    if node.parent and 'justification' not in node.causal_metadata:
        node.causal_metadata["justification"] = f"Simulated causal reasoning between {node.parent.label} and {node.label} at iteration {iteration}"
        node.causal_metadata["payload"] = {
            "parent_name": node.parent.label,
            "parent_invariant_prefix": node.parent.invariant_prefix,
            "parent_abs_index": node.parent.abs_index,
            "parent_weight": node.parent.weight,
            "child_name": node.label,
            "child_invariant_prefix": node.invariant_prefix,
            "child_abs_index": node.abs_index,
            "child_weight": node.weight
        }
    for child in node.children:
        update_in_links(child, iteration)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    
    # Updated base graph that includes 4 top-level categories for the Origin node.
    base_graph = {
        "Origin": {"A": 1.0, "B": 1.0, "C": 1.0, "D": 1.0},
        "A": {"A1": 1.0, "A2": 1.0},
        "B": {"B1": 1.0, "B2": 1.0},
        "C": {"C1": 1.0, "C2": 1.0},
        "D": {"D1": 1.0, "D2": 1.0}
    }
    root_label = "Origin"
    
    # Use the full base graph in our process_llm_iterations function
    root, aggregated_hpc, aggregated_entropy, final_rand_graph = process_llm_iterations(
        base_graph, root_label, iterations=3, dimension=1
    )
    
    # At this point, verify that the built tree has the correct structure:
    # The Origin node should have 4 children (A, B, C, D) directly attached.
    if len(root.children) < 4:
        logging.error("The Origin node does not have all expected direct children (expected 4).")
    else:
        logging.info(f"Origin has {len(root.children)} direct children as expected.")
    
    # Build the FIMHierarchy object from the fully updated tree.
    fim = FIMHierarchy(root, final_rand_graph, aggregated_hpc, aggregated_entropy)
    
    # Enforce submatrix bounds (and any additional repairs) on the FIMHierarchy.
    fim.enforce_submatrix_bounds_rule()
    
    # Now, log the final, fully updated hierarchy.
    def print_tree(node, indent=0):
        print("  " * indent + f"Node: {node.label} (abs_index: {node.abs_index}, invariant_prefix: {node.invariant_prefix}) - Bounds: {node.get_submatrix_bounds()}")
        for child in node.children:
            print_tree(child, indent + 1)
    
    print("\nFinal Hierarchy with Submatrix Bounds:")
    print_tree(fim.root)

    # Define the correct output path for the final hierarchy JSON.
    json_output_path = "LanguageAgentTreeSearch/programming/hierarchy_final_trial_1.json"
 
    # SIMULATION: Inject an extra node into node A's subcategories
    node_A = find_node_by_label(fim.root, "LLM_3_A")
    extra_node = Node("LLM_3_A3", weight=0.5)  # Example weight from cat context
    extra_node.parent = node_A
    node_A.add_child(extra_node)
    logging.info("Injected extra node 'LLM_3_A3' into node 'LLM_3_A' to simulate an additional node.")
    logging.info("After injection, Node LLM_3_A children: %s", [child.label for child in node_A.children])

    # Re-run simulation updates so that the newly injected extra node receives simulation metadata.
    update_labels(fim.root)

    # Since a new node has been added, re-run the canonical ordering rebuild (updating indices/invariant prefixes)
    fim.rebuild_canonical_ordering()

    # Update the in link details for nodes that are missing connection information.
    update_in_links(fim.root)

    # If self healing inputs are provided, trigger an additional repair attempt.
    import sys
    if "--self_heal" in sys.argv:
         logging.info("Self healing input detected; triggering additional repair attempt.")
         fim.enforce_submatrix_bounds_rule()
         node_A_after = find_node_by_label(fim.root, "LLM_3_A")
         if node_A_after:
              logging.info("After self healing, Node LLM_3_A children: %s", [child.label for child in node_A_after.children])
         print("\nHierarchy after additional self healing attempt:")
         print_tree(fim.root)
         # Write the updated (canonical) hierarchy to JSON.
         import os
         os.makedirs(os.path.dirname(json_output_path), exist_ok=True)
         with open(json_output_path, "w") as json_file:
              json.dump(fim.to_dict(), json_file, indent=4)
         logging.info(f"Final Hierarchy after self healing written to {json_output_path}")

    # If self healing is requested, apply it so that the final state is up-to-date.
    if "--self_heal" in sys.argv:
         logging.info("Self healing input detected; triggering additional repair attempt.")
         fim.enforce_submatrix_bounds_rule()

    # Before capturing the final state, force a rebuild from the live tree.
    fim.rebuild_canonical_ordering()

    # Capture and log the final snapshot, then write it to the output file.
    final_snapshot = fim.to_dict()
    import pprint
    print("\nFinal Hierarchy Snapshot:")
    pprint.pprint(final_snapshot)
    import os
    os.makedirs(os.path.dirname(json_output_path), exist_ok=True)
    with open(json_output_path, "w") as json_file:
         json.dump(final_snapshot, json_file, indent=4)
    logging.info(f"Final Hierarchy written to {json_output_path}")