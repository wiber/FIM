import unittest
from LanguageAgentTreeSearch.programming.main import (
    FIMHierarchy,
    build_tree_from_graph,
    break_rule_origin_not_at_zero,
    break_rule_duplicate_prefixes,
    break_rule_unsorted_children_weights,
    break_rule_submatrix_bounds,
    break_rule_causal_metadata,
)

class TestAllRules(unittest.TestCase):
    def setUp(self):
        # Define a basic graph that follows the rules.
        self.graph = {
            "Origin": {"A": 1.0, "B": 1.0, "C": 1.0},
            "A": {"A1": 1.0, "A2": 1.0},
            "B": {"B1": 1.0, "B2": 1.0},
            "C": {"C1": 1.0, "C2": 1.0}
        }
        # Build the tree from the graph.
        root = build_tree_from_graph(self.graph, "Origin")
        # Create the hierarchy; assuming FIMHierarchy constructor takes root and graph.
        self.fh = FIMHierarchy(root, self.graph)
        # Let the validations run so we start in a clean state.
        self.fh.run_validations()

    def test_origin_rule(self):
        # Rule 1: The Origin node must be at index 0.
        self.assertEqual(self.fh.linear_order[0].label, "Origin", "Origin must be at index 0.")

    def test_top_level_contiguity(self):
        # Rule 2: Top-level nodes (direct children of Origin) must be contiguous.
        top_levels = [node for node in self.fh.linear_order if node.parent == self.fh.root]
        indices = [self.fh.linear_order.index(node) for node in top_levels]
        self.assertEqual(
            max(indices) - min(indices) + 1, 
            len(indices),
            "Top-level nodes should be contiguous."
        )

    def test_descending_weights(self):
        # Rule 9: Within each parent's children, the weights must be sorted in descending order.
        for node in self.fh.linear_order:
            if node.children:
                child_weights = [child.weight for child in node.children]
                self.assertEqual(
                    child_weights, sorted(child_weights, reverse=True),
                    f"Children of node {node.label} must be sorted in descending order."
                )

    def test_parent_child_order(self):
        # Rule 7: Parent node must always appear before its children.
        for node in self.fh.linear_order:
            if node.parent:
                parent_index = self.fh.linear_order.index(node.parent)
                child_index = self.fh.linear_order.index(node)
                self.assertLess(
                    parent_index, child_index,
                    f"Parent {node.parent.label} should appear before child {node.label}."
                )

    def test_invariant_prefix_uniqueness(self):
        # Rule 6: Sibling invariant prefixes should be unique.
        for node in self.fh.linear_order:
            if node.parent == self.fh.root:
                siblings = node.parent.children
                prefixes = [child.invariant_prefix for child in siblings]
                self.assertEqual(
                    len(prefixes), len(set(prefixes)),
                    f"Sibling nodes under {node.parent.label} must have unique invariant prefixes."
                )

    def test_submatrix_bounds(self):
        # Rule 10: Submatrix bounds must properly reflect the min and max abs_index values of children.
        for node in self.fh.linear_order:
            if node.children:
                bounds = node.get_submatrix_bounds()
                indices = [child.abs_index for child in node.children]
                min_index = min(indices)
                max_index = max(indices)
                self.assertEqual(
                    bounds["start_index"], min_index,
                    f"Start index for node {node.label} should be {min_index}."
                )
                self.assertEqual(
                    bounds["end_index"], max_index,
                    f"End index for node {node.label} should be {max_index}."
                )

    def test_causal_metadata(self):
        # Rule 8: Non-root nodes must have valid causal metadata.
        for node in self.fh.linear_order:
            if node.parent:
                self.assertIn(
                    "cause_effect_relation", node.causal_inference,
                    f"Node {node.label} must include a cause_effect_relation in its causal_inference."
                )

    def test_self_heal_idempotence(self):
        # Verify that running self-healing multiple times yields the same final state.
        baseline_order = [node.node_id for node in self.fh.linear_order]
        self.fh.self_heal_structure()
        self.fh.self_heal_structure()
        healed_order = [node.node_id for node in self.fh.linear_order]
        self.assertEqual(
            baseline_order, healed_order,
            "Self-healing is not idempotent; repeated runs must yield the same ordering."
        )

if __name__ == '__main__':
    unittest.main() 