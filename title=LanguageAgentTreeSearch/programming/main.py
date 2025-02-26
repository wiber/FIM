#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main file for running the FIMHierarchy pipeline.
"""

import json
import random
import argparse
import logging

# --- NEW: Move the build_tree_from_json function to the top of the file ---
def build_tree_from_json(graph_data, origin_label):
    """
    Build a tree from the JSON graph data using the canonical Node class.
    This function is now defined above the FIMHierarchy class.
    """
    def _build_subtree(label, parent=None):
        node = Node(label)
        node.parent = parent
        if parent:
            parent.children.append(node)
        if label in graph_data:
            for child_label, child_weight in graph_data[label].items():
                child_node = _build_subtree(child_label, node)
                child_node.weight = child_weight
        return node
    return _build_subtree(origin_label)

# ---- Existing Node class should be imported or defined here. ----
# For instance:
# from LanguageAgentTreeSearch.programming.node import Node
# (For now, assume Node is defined somewhere in the project)

###########################################################
#      BIG OBJECT: FIMHierarchy CLASS DEFINITION          #
###########################################################

class FIMHierarchy:
    """
    Aggregates all key fields into one object:
      - root: the final tree's root (Node)
      - rand_graph: the randomized graph used in tree-building and ordering
      - aggregated_hpc: list of HPC cost values from iterations
      - entropy: list of entropy values from iterations
      - node_dict: dictionary mapping labels to Node objects
      - linear_order: list of Node objects in custom linear sort order
      - prefixes: a dictionary mapping each node's abs_index to its computed prefix
    """
    def __init__(self, root, graph_data, aggregated_hpc=None, aggregated_entropy=None):
        self.root = root
        self.graph = graph_data  # Save graph_data for later reference.
        self.rand_graph = graph_data.copy() if hasattr(graph_data, 'copy') else graph_data
        self.aggregated_hpc = aggregated_hpc if aggregated_hpc is not None else []
        self.entropy = aggregated_entropy if aggregated_entropy is not None else []
        self.linear_order = []
        self.hpc_usage = []  # Default to an empty list
        total_hpc = sum(x for x in self.hpc_usage if x is not None) if self.hpc_usage else 0
        # ... other initialization code ...

    # NEW: Self-healing routine to enforce ordering and metadata rules.
    def self_heal(self):
        """
        Self-healing routine for FIMHierarchy.
        Enforces the 1D ordering, updates invariant prefixes,
        propagates causal metadata, and calculates submatrix bounds.
        """
        # Step 1: Build strict 1D ordering (origin, top-level, and subcategories)
        self.linear_order = self.build_strict_ordering()
        # Step 2: Reassign invariant prefixes: Origin, A, B, ... for top-level; parent's prefix + counter for subcategories.
        self.assign_invariant_prefixes()
        # Step 3: Propagate cumulative causality from the root downwards.
        FIMHierarchy.propagate_cumulative_causality(self.root)
        # Step 4: Calculate submatrix bounds for each node.
        self.calculate_submatrix_bounds()

    @staticmethod
    def propagate_cumulative_causality(node):
        """
        Recursively propagate cumulative causality.
        For each child, its 'cumulative_causality' becomes the parent's chain plus the parent's label.
        """
        if not hasattr(node, "cumulative_causality"):
            node.cumulative_causality = []
        for child in node.children:
            child.cumulative_causality = node.cumulative_causality[:] + [node.label]
            FIMHierarchy.propagate_cumulative_causality(child)

    def build_strict_ordering(self):
        """
        Create a 1D ordering of nodes following these rules:
         - Origin (root) is first.
         - Direct children of the origin (top-level nodes) appear as a contiguous block sorted in descending weight.
         - Each top-level node is followed by its subcategories sorted in descending weight.
        This is a placeholder for a full implementation.
        """
        ordering = []
        # Ensure the origin (root) is first.
        ordering.append(self.root)
        # Assume self.root.children holds top-level categories.
        top_levels = sorted(self.root.children, key=lambda n: n.weight, reverse=True)
        ordering.extend(top_levels)
        # Append each top-level node's subcategories.
        for node in top_levels:
            subcategories = sorted(node.children, key=lambda n: n.weight, reverse=True)
            ordering.extend(subcategories)
        return ordering

    def assign_invariant_prefixes(self):
        """
        Reassign invariant prefixes:
         - The origin gets 'O'
         - Top-level nodes get 'A', 'B', 'C', ... in the order of appearance.
         - Subcategories receive their parent's prefix suffixed with an incrementing number (e.g., A1, A2).
        """
        if not self.linear_order:
            return

        self.linear_order[0].invariant_prefix = "O"  # Assign prefix for the origin.
        top_count = len(self.root.children)
        parent_prefix_map = {}
        for i, node in enumerate(self.linear_order[1:top_count+1], start=0):
            prefix = chr(ord('A') + i)
            node.invariant_prefix = prefix
            parent_prefix_map[node] = prefix

        subcat_counters = {}
        for node in self.linear_order[top_count+1:]:
            parent = node.parent
            parent_prefix = parent_prefix_map.get(parent, "X")
            count = subcat_counters.get(parent_prefix, 0) + 1
            subcat_counters[parent_prefix] = count
            node.invariant_prefix = f"{parent_prefix}{count}"

    def calculate_submatrix_bounds(self):
        """
        Calculate submatrix bounds for each node.
         - For a node with children, compute the min and max 'abs_index' from direct children.
         - For a leaf node, inherit bounds from the parent.
        """
        def calc_bounds(node):
            if node.children:
                indices = [child.abs_index for child in node.children if child.abs_index is not None]
                node.submatrix_bounds = (min(indices), max(indices)) if indices else None
                for child in node.children:
                    calc_bounds(child)
            else:
                node.submatrix_bounds = node.parent.submatrix_bounds if node.parent and hasattr(node.parent, 'submatrix_bounds') else None
        calc_bounds(self.root)

    @staticmethod
    def propagate_causal_effects(node):
        """
        Recursively propagate direct causal effects.
        For now, assign a stub causal_inference dictionary to each node.
        """
        node.causal_inference = {
            "cause_effect_relation": {
                "cause": node.label,
                "effect": "Stub",
                "influence_strength": 1.0
            }
        }
        for child in node.children:
            FIMHierarchy.propagate_causal_effects(child)

    @classmethod
    def from_json(cls, json_data):
        """
        Build a FIMHierarchy instance from JSON.
        """
        root = build_tree_from_json(json_data, "Origin")
        return cls(root, json_data)

# NEW: Update the parse_arguments function to accept additional flags.
def parse_arguments():
    parser = argparse.ArgumentParser(description="Run FIMHierarchy pipeline")
    parser.add_argument('--use_mock', action='store_true', help="Use mock data source")
    parser.add_argument('--run-tests', action='store_true', help="Flag to run tests mode")
    parser.add_argument('--input-json', type=str, required=True, help="Path to JSON input seed for the hierarchy")
    parser.add_argument('--self-heal', action='store_true', help="Trigger the self-healing routine on initialization")
    parser.add_argument('--print-hierarchy', action='store_true', help="Print the final hierarchy to terminal")
    return parser.parse_args()

# Updated main() function to load the external JSON and create the hierarchy.
def main():
    args = parse_arguments()
    with open(args.input_json, "r") as f:
        hierarchy_data = json.load(f)
    
    # Create the FIMHierarchy instance using our from_json class method.
    hierarchy = FIMHierarchy.from_json(hierarchy_data)

    if args.self_heal:
        hierarchy.self_heal()

    if args.print_hierarchy:
        print("Final Hierarchy Linear Order:")
        for node in hierarchy.linear_order:
            print(f"Node: {node.label}, Prefix: {node.invariant_prefix}, Bounds: {node.submatrix_bounds}")

    # Example: write updated hierarchy to file.
    with open("hierarchy_updated.json", "w") as out_file:
        json.dump(hierarchy.to_dict(), out_file, indent=4)

# -------------------------------------------------------------------
# Main entry point.
# -------------------------------------------------------------------
if __name__ == "__main__":
    main()

# At the end of the file, expose key functions for easier imports.
simulate_llm_update = lambda hierarchy: hierarchy  # Stub: returns hierarchy unmodified.
propagate_causal_effects = FIMHierarchy.propagate_causal_effects
propagate_cumulative_causality = FIMHierarchy.propagate_cumulative_causality

# NEW: Helper function for comparing states.
def compare_states(state1, state2):
    differences = {}
    for key in state1:
        if state1[key] != state2.get(key):
            differences[key] = (state1[key], state2.get(key))
    return differences 