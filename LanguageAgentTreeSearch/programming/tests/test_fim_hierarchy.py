import unittest
import json
import logging

# These import lines must NOT be indented.
from LanguageAgentTreeSearch.programming.main import (
    FIMHierarchy,
    build_tree_from_graph,
    propagate_causal_effects,
    propagate_cumulative_causality,
    simulate_llm_update,
    compare_states,
    break_rule_descending_weights,
    break_rule_submatrix_bounds
)

# Helper functions to force rule violations.
def break_rule_origin_not_at_zero(fh):
    # Force a violation by swapping the root ("Origin") with the first non-root node.
    if len(fh.linear_order) > 1:
        fh.linear_order[0], fh.linear_order[1] = fh.linear_order[1], fh.linear_order[0]

def break_rule_top_level_contiguity(fh):
    # Force a violation by taking one top-level node and inserting it in between other nodes.
    top_level = [node for node in fh.linear_order if node.parent == fh.root]
    if len(top_level) >= 2:
        idx = fh.linear_order.index(top_level[1])
        # Find a non‑top‑level node to swap with.
        for i, node in enumerate(fh.linear_order):
            if node.parent != fh.root:
                fh.linear_order[idx], fh.linear_order[i] = fh.linear_order[i], fh.linear_order[idx]
                break

def break_rule_parent_child_interleaving(fh):
    # Force a violation by swapping a child to appear before its parent.
    for node in fh.linear_order:
        if node.parent:
            parent_idx = fh.linear_order.index(node.parent)
            child_idx = fh.linear_order.index(node)
            if child_idx > parent_idx:
                # Swap positions so that child comes first.
                fh.linear_order[parent_idx], fh.linear_order[child_idx] = fh.linear_order[child_idx], fh.linear_order[parent_idx]
                break

def break_rule_duplicate_prefixes(fh):
    # Force duplicate invariant prefixes by setting two top-level nodes to the same prefix.
    # Here we collect all top-level nodes (children of the root).
    top_level_nodes = [node for node in fh.linear_order if node.parent == fh.root]
    if len(top_level_nodes) >= 2:
        top_level_nodes[0].invariant_prefix = "DUP"
        top_level_nodes[1].invariant_prefix = "DUP"

def break_rule_unsorted_children_weights(fh):
    # Force violation: for one parent, sort its children in ascending order instead of descending.
    for node in fh.linear_order:
        if node.children:
            node.children.sort(key=lambda child: child.weight)
            break

def break_rule_causal_metadata(fh):
    # Force violation: corrupt the causal_inference for one non-root node.
    for node in fh.linear_order:
        if node.parent:
            node.causal_inference = {"corrupted": True}
            break

class TestFIMHierarchy(unittest.TestCase):

    def setUp(self):
        # Setup a basic graph and build the tree.
        self.base_graph = {
            "Origin": {"A": 1.0, "B": 1.0, "C": 1.0, "D": 1.0},
            "A": {"A1": 1.0, "A2": 1.0},
            "B": {"B1": 1.0, "B2": 1.0},
            "C": {"C1": 1.0, "C2": 1.0},
            "D": {"D1": 1.0, "D2": 1.0}
        }
        self.root_label = "Origin"
        self.root = build_tree_from_graph(self.base_graph, self.root_label)
        
        # Disable logging for clarity in test output.
        logging.disable(logging.CRITICAL)
        
        self.aggregated_hpc = [1.0, 1.0, 1.0]
        self.aggregated_entropy = [0.5, 0.5, 0.5]
        
        # Create the hierarchy object.
        self.fh = FIMHierarchy(self.root, self.base_graph, self.aggregated_hpc, self.aggregated_entropy)
        # Run initial update.
        self.fh.trigger_hierarchy_update()
        # Force self-healing before proceeding
        self.fh.self_heal_structure()
        # Now the hierarchy should be in a "healthy" state.
    
    def tearDown(self):
        logging.disable(logging.NOTSET)
    
    def test_ordering_validation(self):
        """Test that ordering validations (parent abs_index < child abs_index) pass after update."""
        # Re-trigger update to simulate a fresh state.
        self.fh.trigger_hierarchy_update()
        for node in self.fh.linear_order:
            if node.parent and node.abs_index is not None and node.parent.abs_index is not None:
                self.assertLess(node.parent.abs_index, node.abs_index,
                                f"Parent {node.parent.label} abs_index should be less than child {node.label}'s abs_index.")
        # Ensure report_failed_nodes() returns an empty list.
        failed = self.fh.report_failed_nodes()
        self.assertEqual(len(failed), 0, f"Unexpected failed ordering checks: {failed}")

    def test_causal_propagation(self):
        """Test that causal effects and cumulative causality are propagated."""
        propagate_causal_effects(self.fh.root)
        propagate_cumulative_causality(self.fh.root)
        # Root should have an empty cumulative chain.
        self.assertEqual(self.fh.root.cumulative_causality, [])
        # Children should inherit parent's causal chain.
        for child in self.fh.root.children:
            self.assertGreater(len(child.cumulative_causality), 0,
                               f"Child {child.label} should have a non-empty cumulative causality chain.")

    def test_json_export(self):
        """Test that the full JSON export includes necessary fields."""
        full_json = self.fh.to_full_json()
        # Check that keys like 'node_id', 'label', and 'children' exist.
        self.assertIn("node_id", full_json)
        self.assertIn("label", full_json)
        self.assertIn("children", full_json)
        # Also, test the prompt-ready JSON.
        prompt_json = self.fh.to_prompt_json()
        self.assertIsInstance(prompt_json, list, "Prompt-ready JSON should be a list.")

    def test_state_comparison(self):
        """Test that compare_states detects a change in a node's state."""
        # Get the baseline state.
        prev_state = self.fh.get_flat_state()
        # Modify a node's weight deliberately.
        node_to_modify = self.fh.linear_order[1]
        old_weight = node_to_modify.weight
        node_to_modify.update_weight(old_weight * 0.95)
        # Get the new state and compare.
        current_state = self.fh.get_flat_state()
        differences = compare_states(prev_state, current_state)
        self.assertIn(node_to_modify.node_id, differences,
                      "State change was not detected in comparison.")
    
    def test_bounds_integrity(self):
        """Ensure that all nodes have valid submatrix bounds (start_index and end_index)."""
        for node in self.fh.linear_order:
            bounds = node.get_submatrix_bounds()
            self.assertIsNotNone(bounds["start_index"], f"Start index is None for node {node.label}")
            self.assertIsNotNone(bounds["end_index"], f"End index is None for node {node.label}")

    def test_minimum_children_per_level(self):
        """
        Ensure that every non-leaf node in the final ordering has at least 2 children.
        """
        # Assuming self.fh is set up in setUp() to be a FIMHierarchy built from sample_hierarchy.json:
        for node in self.fh.linear_order:
            if node.children:  # Only check non-leaf nodes.
                self.assertGreaterEqual(len(node.children), 2,
                    f"Node {node.label} must have at least 2 children. Found {len(node.children)}.")

    def test_self_healing_propagates_causality(self):
        """Test that self-healing propagates cumulative causality to all nodes."""
        # Trigger self-healing.
        self.fh.self_heal_structure()
        # Check that each node has a cumulative_causality attribute defined (it may be empty for the root).
        for node in self.fh.linear_order:
            self.assertIsNotNone(getattr(node, "cumulative_causality", None),
                                 f"Node {node.label} is missing cumulative causal chain.")

class TestFIMValidationRules(unittest.TestCase):
    def setUp(self):
        # Use a simple graph for a small hierarchy.
        self.graph = {
            "Origin": {"A": 0.9, "B": 0.8, "C": 0.7},
            "A": {"A1": 0.85},
            "B": {"B1": 0.75},
            "C": {"C1": 0.65}
        }
        self.root = build_tree_from_graph(self.graph, "Origin")
        logging.disable(logging.CRITICAL)
        self.aggregated_hpc = [1.0, 1.0]
        self.aggregated_entropy = [0.5, 0.5]
        self.fh = FIMHierarchy(self.root, self.graph, self.aggregated_hpc, self.aggregated_entropy)
        self.fh.trigger_hierarchy_update()

    def tearDown(self):
        logging.disable(logging.NOTSET)

    def test_origin_index_rule(self):
        # Valid: Root must be at index 0.
        self.assertEqual(self.fh.linear_order[0].label, "Origin",
                         "Valid state: 'Origin' should be at index 0.")
        # Break the rule.
        break_rule_origin_not_at_zero(self.fh)
        self.assertNotEqual(self.fh.linear_order[0].label, "Origin",
                            "Rule break: 'Origin' is not at index 0.")
        # Self-healing should restore the rule.
        self.fh.self_heal_structure()
        self.assertEqual(self.fh.linear_order[0].label, "Origin",
                         "Self-healing failed to place 'Origin' at index 0.")

    def test_top_level_contiguity_rule(self):
        # Valid: Top-level nodes (children of Origin) should be contiguous.
        top_level = [node for node in self.fh.linear_order if node.parent == self.fh.root]
        indices = [self.fh.linear_order.index(node) for node in top_level]
        self.assertEqual(max(indices) - min(indices) + 1, len(top_level),
                         "Valid state: Top-level nodes must be contiguous.")
        # Break the rule.
        break_rule_top_level_contiguity(self.fh)
        top_level = [node for node in self.fh.linear_order if node.parent == self.fh.root]
        indices = [self.fh.linear_order.index(node) for node in top_level]
        self.assertNotEqual(max(indices) - min(indices) + 1, len(top_level),
                            "Rule break: Top-level contiguity violation not detected.")
        self.fh.self_heal_structure()
        top_level = [node for node in self.fh.linear_order if node.parent == self.fh.root]
        indices = [self.fh.linear_order.index(node) for node in top_level]
        self.assertEqual(max(indices) - min(indices) + 1, len(top_level),
                         "Self-healing did not restore top-level contiguity.")

    def test_parent_child_order_rule(self):
        # Valid: Parent must appear before its child.
        for node in self.fh.linear_order:
            if node.parent:
                self.assertLess(self.fh.linear_order.index(node.parent),
                                self.fh.linear_order.index(node),
                                f"In valid state: Parent {node.parent.label} should come before child {node.label}.")
        # Break the rule.
        break_rule_parent_child_interleaving(self.fh)
        violation = any(
            self.fh.linear_order.index(node.parent) >= self.fh.linear_order.index(node)
            for node in self.fh.linear_order if node.parent
        )
        self.assertTrue(violation, "Rule break: Parent-child ordering violation not simulated.")
        self.fh.self_heal_structure()
        for node in self.fh.linear_order:
            if node.parent:
                self.assertLess(self.fh.linear_order.index(node.parent),
                                self.fh.linear_order.index(node),
                                f"After healing: Parent {node.parent.label} should come before child {node.label}.")

    def test_contiguous_parent_child_blocks(self):
        # Valid: Children for a given parent should be contiguous.
        for node in self.fh.linear_order:
            if node.children:
                child_indices = [self.fh.linear_order.index(child) for child in node.children]
                self.assertEqual(max(child_indices) - min(child_indices) + 1, len(child_indices),
                                 f"Valid state: Children of {node.label} must be contiguous.")
        # Break the rule by interleaving one child outside its parent's block.
        if self.fh.root.children:
            parent = self.fh.root.children[0]
            if parent.children:
                moved_child = parent.children.pop(0)
                self.fh.linear_order.insert(1, moved_child)
        violation = False
        for node in self.fh.linear_order:
            if node.parent:
                siblings = node.parent.children
                child_indices = [self.fh.linear_order.index(child) for child in siblings]
                if max(child_indices) - min(child_indices) + 1 != len(siblings):
                    violation = True
                    break
        self.assertTrue(violation, "Rule break: Failed to simulate non-contiguous parent-child block.")
        self.fh.self_heal_structure()
        for node in self.fh.linear_order:
            if node.parent:
                siblings = node.parent.children
                child_indices = [self.fh.linear_order.index(child) for child in siblings]
                self.assertEqual(max(child_indices) - min(child_indices) + 1, len(siblings),
                                 f"After healing: Children of {node.parent.label} are not contiguous.")

    def test_duplicate_prefix_rule(self):
        # Valid: Sibling invariant prefixes should be unique.
        prefixes = [node.invariant_prefix for node in self.fh.linear_order if node.parent == self.fh.root]
        self.assertEqual(len(prefixes), len(set(prefixes)),
                         "Valid state: No duplicate invariant prefixes expected among top-level nodes.")
        # Break the rule.
        break_rule_duplicate_prefixes(self.fh)
        prefixes = [node.invariant_prefix for node in self.fh.linear_order if node.parent == self.fh.root]
        self.assertNotEqual(len(prefixes), len(set(prefixes)),
                            "Rule break: Duplicate invariant prefixes not detected.")
        self.fh.self_heal_structure()
        prefixes = [node.invariant_prefix for node in self.fh.linear_order if node.parent == self.fh.root]
        self.assertEqual(len(prefixes), len(set(prefixes)),
                         "Self-healing did not resolve duplicate invariant prefixes.")

    def test_descending_weights_rule(self):
        # Valid: For every parent, children should be ordered in descending weight.
        for node in self.fh.linear_order:
            if node.children:
                weights = [child.weight for child in node.children]
                self.assertEqual(weights, sorted(weights, reverse=True),
                                 f"Valid state: Children of {node.label} must be sorted in descending order.")
        # Break the rule.
        break_rule_unsorted_children_weights(self.fh)
        violation_found = False
        for node in self.fh.linear_order:
            if node.children:
                weights = [child.weight for child in node.children]
                if weights != sorted(weights, reverse=True):
                    violation_found = True
                    break
        self.assertTrue(violation_found, "Rule break: Descending weights rule violation not simulated.")
        self.fh.self_heal_structure()
        for node in self.fh.linear_order:
            if node.children:
                weights = [child.weight for child in node.children]
                self.assertEqual(weights, sorted(weights, reverse=True),
                                 f"After healing: Children of {node.label} are not sorted in descending order.")

    def test_submatrix_bounds_rule(self):
        # Valid: Each node must have non-None submatrix bounds.
        for node in self.fh.linear_order:
            bounds = node.get_submatrix_bounds()
            self.assertIsNotNone(bounds["start_index"], f"Valid state: {node.label} must have a start_index.")
            self.assertIsNotNone(bounds["end_index"], f"Valid state: {node.label} must have an end_index.")
        # Break the rule.
        break_rule_submatrix_bounds(self.fh)
        violation_count = 0
        for node in self.fh.linear_order:
            bounds = node.get_submatrix_bounds()
            if bounds["start_index"] is None or bounds["end_index"] is None:
                violation_count += 1
        self.assertGreater(violation_count, 0, "Rule break: Submatrix bounds violation not detected.")
        self.fh.self_heal_structure()
        for node in self.fh.linear_order:
            bounds = node.get_submatrix_bounds()
            self.assertIsNotNone(bounds["start_index"], f"After healing: {node.label} must have a start_index.")
            self.assertIsNotNone(bounds["end_index"], f"After healing: {node.label} must have an end_index.")

    def test_causal_metadata_rule(self):
        # Valid: Non-root nodes must have valid causal_inference details.
        for node in self.fh.linear_order:
            if node.parent:
                self.assertIn("cause_effect_relation", node.causal_inference,
                              f"Valid state: {node.label} should have causal_inference details.")
        # Break the rule.
        break_rule_causal_metadata(self.fh)
        violation_found = any("corrupted" in node.causal_inference for node in self.fh.linear_order if node.parent)
        self.assertTrue(violation_found, "Rule break: Failed to simulate corrupted causal metadata.")
        self.fh.self_heal_structure()
        for node in self.fh.linear_order:
            if node.parent:
                self.assertIn("cause_effect_relation", node.causal_inference,
                              f"After healing: {node.label} is missing causal_inference details.")
    
    def test_self_heal_idempotence(self):
        # Capture the initial linear order.
        baseline_order = [node.node_id for node in self.fh.linear_order]
        self.fh.self_heal_structure()
        # Re-run self-healing and verify that nothing changes.
        self.fh.self_heal_structure()
        healed_order = [node.node_id for node in self.fh.linear_order]
        self.assertEqual(baseline_order, healed_order,
                         "Self-healing is not idempotent; repeated runs must yield the same state.")

if __name__ == "__main__":
    unittest.main() 