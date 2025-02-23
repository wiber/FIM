import unittest
import json
import logging

# Adjust this import if your module structure is different.
from LanguageAgentTreeSearch.programming.main import (
    FIMHierarchy,
    build_tree_from_graph,
    propagate_causal_effects,
    propagate_cumulative_causality,
    simulate_llm_update,
    compare_states
)

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

    def test_self_heal_structure(self):
        """
        Test that if we break ordering artificially, self-healing fixes it.
        For example, we swap the absolute indices of two nodes.
        """
        if len(self.fh.linear_order) >= 2:
            # Swap abs_index of the first two nodes.
            self.fh.linear_order[0].abs_index, self.fh.linear_order[1].abs_index = (
                self.fh.linear_order[1].abs_index, self.fh.linear_order[0].abs_index
            )
        # Run self-healing.
        self.fh.self_heal_structure()
        # Check again that every child has a higher abs_index than its parent.
        for node in self.fh.linear_order:
            if node.parent and node.abs_index is not None and node.parent.abs_index is not None:
                self.assertLess(node.parent.abs_index, node.abs_index,
                                f"After healing: Parent {node.parent.label} abs_index not less than child {node.label}'s abs_index.")
        failed = self.fh.report_failed_nodes()
        self.assertEqual(len(failed), 0, f"Self-healing failed with errors: {failed}")

    def test_llm_update_application_failure(self):
        """
        Intentionally apply an LLM update suggestion for a nonexistent node.
        It should raise a ValueError.
        """
        # For now, simulate a suggestion that targets a node id that does not exist.
        with self.assertRaises(ValueError):
            self.fh.set_node_field("B_simulated_3", "weight", 0.85)

    def test_llm_update_application_success(self):
        """
        Now simulate an LLM update on an existing node.
        We use a known node_id from the current hierarchy.
        """
        # Pick an existing node id.
        existing_node_id = self.fh.linear_order[1].node_id
        suggestion = {"node_id": existing_node_id, "field": "weight", "new_value": 0.77}
        # This should succeed without raising an error.
        try:
            self.fh.apply_llm_suggestions([suggestion])
        except Exception as e:
            self.fail(f"LLM update for an existing node failed: {e}")
        # Verify the update.
        updated_weight = self.fh.get_node_field(existing_node_id, "weight")
        self.assertAlmostEqual(updated_weight, 0.77, places=4, msg="Node weight was not updated correctly via LLM suggestion.")

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

if __name__ == "__main__":
    unittest.main() 