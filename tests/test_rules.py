import unittest
import json
import logging
from LanguageAgentTreeSearch.programming.main import (
    FIMHierarchy,
    build_tree_from_graph,
    compare_states,
    propagate_causal_influence,
    Node
)

class TestRules(unittest.TestCase):
    def setUp(self):
        # Create a simple graph with a few nodes.
        self.graph = {
            "Origin": {"A": 0.9, "B": 0.8},
            "A": {"A1": 0.85},
            "B": {"B1": 0.75}
        }
        self.root = build_tree_from_graph(self.graph, "Origin")
        logging.disable(logging.CRITICAL)
        # For simplicity, aggregated values are set to a dummy list.
        self.fh = FIMHierarchy(self.root, self.graph, [1.0], [0.5])
        self.fh.trigger_hierarchy_update()

    def tearDown(self):
        logging.disable(logging.NOTSET)

    def test_compare_states(self):
        """
        Capture the state of the hierarchy before and after changing a node's weight.
        Compare the flattened states to detect differences.
        """
        baseline_json = self.fh.to_full_json()
        baseline_state = {}
        def flatten(node):
            baseline_state[node["node_id"]] = {
                "weight": node["weight"],
                "parent": node.get("parent_id")
            }
            for child in node.get("children", []):
                flatten(child)
        flatten(baseline_json)

        # Modify a node's weight artificially.
        if len(self.fh.linear_order) > 1:
            self.fh.linear_order[1].weight *= 1.1

        new_json = self.fh.to_full_json()
        new_state = {}
        def flatten_new(node):
            new_state[node["node_id"]] = {
                "weight": node["weight"],
                "parent": node.get("parent_id")
            }
            for child in node.get("children", []):
                flatten_new(child)
        flatten_new(new_json)

        diff = compare_states(baseline_state, new_state)
        self.assertTrue(
            len(diff) > 0,
            "compare_states did not detect modifications when expected."
        )

    def test_lookup_by_label(self):
        """
        Test that given a label, we can (by traversing the tree)
        find the corresponding node. If FIMHierarchy implements a direct method
        (e.g. get_node_by_label), this test should be adjusted accordingly.
        """
        def lookup_by_label(node, target_label):
            if node.label == target_label:
                return node
            for child in node.children:
                result = lookup_by_label(child, target_label)
                if result:
                    return result
            return None

        node_found = lookup_by_label(self.fh.root, "A1")
        self.assertIsNotNone(node_found, "Lookup by label failed to find node A1")
        self.assertEqual(node_found.label, "A1",
                         "Lookup by label did not return the correct node.")

    def test_lookup_by_abs_index(self):
        """
        Test that the linear ordering of nodes allows us to locate nodes by their absolute index.
        Assuming every node has a valid abs_index, build a mapping and verify consistency.
        """
        index_map = {node.abs_index: node for node in self.fh.linear_order if node.abs_index is not None}
        for node in self.fh.linear_order:
            if node.abs_index is not None:
                self.assertEqual(
                    index_map[node.abs_index],
                    node,
                    f"Lookup by abs_index does not return the correct node for {node.label}."
                )

    def test_causal_influence_propagation(self):
        """
        Test that the propagation of causal influence sets the right 'causal_source' flag.
        This test simulates a scenario where parent's influence is inherited.
        """
        # Propagate influence down the tree.
        propagate_causal_influence(self.fh.root)
        # For each non-root node, check that its causal source is 'inherited'
        for node in self.fh.linear_order:
            if node.parent:
                self.assertEqual(node.causal_metadata.get("causal_source"),
                                 "inherited",
                                 f"Causal source for {node.label} is not marked as inherited.")

if __name__ == "__main__":
    unittest.main() 