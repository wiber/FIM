import os
import sys
import unittest
import json
import logging
from copy import deepcopy
from LanguageAgentTreeSearch.programming.main import (
    FIMHierarchy,
    build_tree_from_graph,
    compare_states,
    propagate_causal_effects,
    propagate_cumulative_causality,
    propagate_causal_influence,
    simulate_llm_update,
    Node
)

FAIL_MODE = os.environ.get("UNIT_TEST_FAIL_MODE", "0") == "1"

# Remove custom flags so they don't interfere with unittest's argument parsing.
custom_flags = ["--run_rand_test"]
sys.argv = [arg for arg in sys.argv if arg not in custom_flags]

class TestFIMHierarchy(unittest.TestCase):

    def setUp(self):
        # Create a basic test graph representing a simple hierarchical structure.
        self.base_graph = {
            "Origin": {"A": 0.8, "B": 0.7, "C": 0.6, "D": 0.5},
            "A": {"A1": 0.9, "A2": 0.85},
            "B": {"B1": 0.75, "B2": 0.65},
            "C": {"C1": 0.55, "C2": 0.45},
            "D": {"D1": 0.35, "D2": 0.25}
        }
        self.root_label = "Origin"
        # Build tree from graph.
        self.root = build_tree_from_graph(self.base_graph, self.root_label)
        # Disable logging for clarity of test output.
        logging.disable(logging.CRITICAL)
        self.aggregated_hpc = [1.0, 1.0, 1.0]
        self.aggregated_entropy = [0.5, 0.5, 0.5]
        # Create the FIMHierarchy object.
        self.fh = FIMHierarchy(self.root, self.base_graph, self.aggregated_hpc, self.aggregated_entropy)
        self.fh.trigger_hierarchy_update()

        # If UNIT_TEST_FAIL_MODE is enabled, purposefully break ordering by swapping abs_index
        if FAIL_MODE and len(self.fh.linear_order) >= 2:
            self.fh.linear_order[0].abs_index, self.fh.linear_order[1].abs_index = \
                self.fh.linear_order[1].abs_index, self.fh.linear_order[0].abs_index

    def tearDown(self):
        logging.disable(logging.NOTSET)

    def test_ordering_validation(self):
        """Test that parent's absolute index is strictly less than child's after update."""
        for node in self.fh.linear_order:
            if node.parent and node.abs_index is not None and node.parent.abs_index is not None:
                self.assertLess(
                    node.parent.abs_index,
                    node.abs_index,
                    f"Parent {node.parent.label} (index {node.parent.abs_index}) should be less than child {node.label} (index {node.abs_index})."
                )
        # Report any failed nodes; the list should be empty.
        failed = self.fh.report_failed_nodes()
        self.assertEqual(len(failed), 0, f"Ordering validation failed for nodes: {failed}")

    def test_causal_propagation(self):
        """Test that causal effects and cumulative causality propagate down the tree."""
        propagate_causal_effects(self.fh.root)
        propagate_cumulative_causality(self.fh.root)
        # The root's cumulative chain should be empty.
        self.assertEqual(self.fh.root.cumulative_causality, [])
        # Every child should have inherited some causal chain.
        for child in self.fh.root.children:
            self.assertGreater(
                len(child.cumulative_causality), 0,
                f"Child {child.label} did not inherit a cumulative causality chain."
            )

    def test_json_export(self):
        """Test that the full JSON export and prompt-ready JSON contain the expected fields."""
        full_json = self.fh.to_full_json()
        self.assertIn("node_id", full_json)
        # Verify that the prompt-ready JSON is a list.
        prompt_json = self.fh.to_prompt_json()
        self.assertIsInstance(prompt_json, list, "Prompt-ready JSON should be a list.")

    def test_self_heal_structure(self):
        """
        Break the ordering by swapping absolute indices of two nodes,
        then invoke self-healing and verify that ordering issues are resolved.
        """
        if len(self.fh.linear_order) >= 2:
            self.fh.linear_order[0].abs_index, self.fh.linear_order[1].abs_index = (
                self.fh.linear_order[1].abs_index, self.fh.linear_order[0].abs_index
            )
        self.fh.self_heal_structure()
        for node in self.fh.linear_order:
            if node.parent and node.abs_index is not None and node.parent.abs_index is not None:
                self.assertLess(
                    node.parent.abs_index,
                    node.abs_index,
                    f"After healing, parent {node.parent.label} (index {node.parent.abs_index}) should be less than child {node.label} (index {node.abs_index})."
                )
        failed = self.fh.report_failed_nodes()
        self.assertEqual(len(failed), 0, f"Self-healing did not resolve ordering issues: {failed}")

    def test_llm_update_failure(self):
        """
        Test that requesting a field update on a nonexistent node (here 'non_existent_node')
        triggers a ValueError.
        """
        with self.assertRaises(ValueError):
            self.fh.set_node_field("non_existent_node", "weight", 0.85)

    def test_llm_update_success(self):
        """
        Test that an LLM suggestion to update a node's weight for an existing node is applied properly.
        """
        # Pick an existing node from the linear order.
        existing_node_id = self.fh.linear_order[1].node_id
        suggestion = {"node_id": existing_node_id, "field": "weight", "new_value": 0.77}
        try:
            self.fh.apply_llm_suggestions([suggestion])
        except Exception as e:
            self.fail(f"LLM update failed with exception: {e}")
        # Verify the weight update was applied.
        updated_weight = self.fh.get_node_field(existing_node_id, "weight")
        self.assertAlmostEqual(updated_weight, 0.77, places=4,
                               msg="Node weight was not updated correctly via LLM suggestion.")

    def test_weight_inheritance(self):
        """
        Test that when adding a new child to a parent with a non-default weight,
        the child's weight is reassigned to 90% of the parent's weight.
        """
        parent = Node("TestParent", weight=0.8)
        child = Node("TestChild")  # Default weight is 1.0.
        parent.add_child(child)
        self.assertAlmostEqual(
            child.weight, 0.8 * 0.9, places=4,
            msg="Child weight did not inherit correctly from parent's weight."
        )

    def test_compare_states(self):
        """
        Test the compare_states() function by capturing a state,
        modifying a node weight, and verifying that the diff reflects the change.
        """
        # Capture baseline state.
        baseline = self.fh.to_full_json()
        baseline_state = {}
        def flatten(node):
            baseline_state[node["node_id"]] = {
                "weight": node["weight"],
                "parent": node.get("parent_id")
            }
            for child in node.get("children", []):
                flatten(child)
        flatten(baseline)
        # Modify a node's weight.
        if len(self.fh.linear_order) > 1:
            target_node = self.fh.linear_order[1]
            old_weight = target_node.weight
            target_node.weight = old_weight * 1.1
        # Capture new state.
        new_state_json = self.fh.to_full_json()
        new_state = {}
        def flatten_new(node):
            new_state[node["node_id"]] = {
                "weight": node["weight"],
                "parent": node.get("parent_id")
            }
            for child in node.get("children", []):
                flatten_new(child)
        flatten_new(new_state_json)
        diff = compare_states(baseline_state, new_state)
        self.assertTrue(len(diff) > 0, "compare_states did not detect modifications in the state.")

    def test_equal_weights_sorting(self):
        """
        Test that when children have equal weight, the ordering is determined by alphabetical order.
        """
        # Build a custom graph with three children having equal weight.
        graph_equal = {
            "Origin": {"X": 0.7, "Y": 0.7, "Z": 0.7},
            "X": {},
            "Y": {},
            "Z": {}
        }
        root_equal = build_tree_from_graph(graph_equal, "Origin")
        fh_equal = FIMHierarchy(root_equal, graph_equal, [1.0, 1.0, 1.0], [0.5, 0.5, 0.5])
        fh_equal.trigger_hierarchy_update()

        # Expect children to be sorted alphabetically: ['X', 'Y', 'Z'] (if default insertion order isn't already alphabetical)
        children_labels = [child.label for child in fh_equal.root.children]
        sorted_labels = sorted(children_labels)
        self.assertEqual(children_labels, sorted_labels,
            "Equal weight children are not sorted alphabetically as a tiebreaker.")

    def test_randomisation_preserves_structure(self):
        """Test that randomisation yields a new ordering and preserves legal structure."""
        # Save the current ordering (by node_id).
        original_order = [node.node_id for node in self.fh.linear_order]
        
        import random
        # Randomly alter each node's weight.
        for node in self.fh.linear_order:
            node.weight *= random.uniform(0.5, 1.5)

        # Re-run the ordering update process.
        self.fh.trigger_hierarchy_update()

        # Capture the new ordering of node_ids.
        new_order = [node.node_id for node in self.fh.linear_order]
        self.assertNotEqual(
            original_order, new_order,
            "Randomisation did not change the ordering."
        )

        # Check that every child in the ordering still comes after its parent.
        for node in self.fh.linear_order:
            if node.parent and node.abs_index is not None and node.parent.abs_index is not None:
                self.assertLess(
                    node.parent.abs_index, node.abs_index,
                    f"After randomisation, parent {node.parent.label} (index {node.parent.abs_index}) " 
                    f"is not less than child {node.label} (index {node.abs_index})."
                )

if __name__ == "__main__":
    unittest.main() 