import unittest
import logging
from LanguageAgentTreeSearch.programming.main import (
    FIMHierarchy,
    build_tree_from_graph,
    break_rule_descending_weights,
    break_rule_submatrix_bounds,
    propagate_causal_effects,
    propagate_cumulative_causality,
    Node,
    run_simple_validations
)

# Disable logging for clarity in test output.
logging.disable(logging.CRITICAL)

class TestFIMValidation(unittest.TestCase):
    def setUp(self):
        # Build a simple graph for testing the Origin index rule.
        self.graph = {
            "Origin": {"A": 0.9, "B": 0.8},
            "A": {"A1": 0.85},
            "B": {"B1": 0.75}
        }
        self.root = build_tree_from_graph(self.graph, "Origin")
        logging.disable(logging.CRITICAL)
        # Create the FIMHierarchy. Aggregated dummy values provided.
        self.fh = FIMHierarchy(self.root, self.graph, [1.0, 1.0], [0.5, 0.5])
        self.fh.trigger_hierarchy_update()

        # For testing, define a simple validation function that sets check_errors.
        def run_simple_validations(fh):
             errors = {}
             if fh.root.abs_index != 0:
                 errors["origin"] = "Origin is not at index 0"
             fh.check_errors = errors
        self.fh.check_errors = {}
        self.fh.run_validations = lambda: run_simple_validations(self.fh)

    def tearDown(self):
        logging.disable(logging.NOTSET)

    # ------------------ Rule 1: Origin at Index 0 --------------------
    def test_origin_valid(self):
        self.fh.run_validations()
        self.assertEqual(
            self.fh.linear_order[0].invariant_prefix,
            "O",
            "Origin node is not at index 0 in valid configuration."
        )

    def test_origin_broken(self):
        # Swap the origin with the second node to break the rule.
        self.fh.linear_order[0], self.fh.linear_order[1] = \
            self.fh.linear_order[1], self.fh.linear_order[0]
        self.fh.run_validations()
        self.assertIn(
            "origin", self.fh.check_errors,
            "Failed to detect origin violation when non-origin appears first."
        )

    def test_origin_repaired(self):
        # Break the rule.
        self.fh.linear_order[0], self.fh.linear_order[1] = \
            self.fh.linear_order[1], self.fh.linear_order[0]
        # Repair the hierarchy.
        self.fh.self_heal_structure()
        self.fh.run_validations()
        self.assertEqual(
            self.fh.linear_order[0].invariant_prefix,
            "O",
            "Self-healing did not reassign Origin to index 0."
        )

    def test_origin_rule(self):
        # Initially validate that the origin is at index 0.
        self.fh.run_validations()
        self.assertIsNone(self.fh.check_errors.get("origin"), "Origin should be at index 0.")
        
        # Break the rule: force the origin not to be at index 0.
        break_rule_origin_not_at_zero(self.fh)
        self.fh.run_validations()
        self.assertIn("origin", self.fh.check_errors, "Violation of the origin rule was not detected.")
        
        # Self-heal and then validate again.
        self.fh.self_heal_structure()
        self.fh.run_validations()
        self.assertIsNone(self.fh.check_errors.get("origin"), "Self-healing did not restore the origin's position.")

    # ------------------ Rule 2: Contiguous Top-Level Nodes --------------------
    def test_top_level_contiguous_valid(self):
        top_levels = [node for node in self.fh.linear_order if node.parent == self.fh.root]
        indexes = [self.fh.linear_order.index(node) for node in top_levels]
        self.assertEqual(
            list(range(min(indexes), max(indexes) + 1)),
            indexes,
            "Top-level nodes are not in one contiguous block."
        )

    def test_top_level_contiguous_broken(self):
        top_levels = [node for node in self.fh.linear_order if node.parent == self.fh.root]
        # If the first top-level node has children, insert one child in between top-level nodes.
        if top_levels and top_levels[0].children:
            misplaced = top_levels[0].children[0]
            insert_index = self.fh.linear_order.index(top_levels[1])
            self.fh.linear_order.insert(insert_index, misplaced)
        self.fh.run_validations()
        self.assertIn(
            "top_level", self.fh.check_errors,
            "Failed to detect non-contiguous top-level block."
        )

    def test_top_level_contiguous_repaired(self):
        top_levels = [node for node in self.fh.linear_order if node.parent == self.fh.root]
        if top_levels and top_levels[0].children:
            misplaced = top_levels[0].children[0]
            insert_index = self.fh.linear_order.index(top_levels[1])
            self.fh.linear_order.insert(insert_index, misplaced)
        self.fh.self_heal_structure()
        self.fh.run_validations()
        top_levels_after = [node for node in self.fh.linear_order if node.parent == self.fh.root]
        indexes_after = [self.fh.linear_order.index(node) for node in top_levels_after]
        self.assertEqual(
            list(range(min(indexes_after), max(indexes_after) + 1)),
            indexes_after,
            "Self-healing did not restore contiguous top-level nodes."
        )

    # ------------------ Rule 3: Parent Before Child Ordering --------------------
    def test_parent_before_child_ordering(self):
        for node in self.fh.linear_order:
            if node.parent and node.abs_index is not None and node.parent.abs_index is not None:
                self.assertLess(node.parent.abs_index, node.abs_index,
                                f"Parent ({node.parent.label}) should come before {node.label}.")

    def test_parent_before_child_repair(self):
        # Deliberately break ordering: set a child's abs_index lower than parent's.
        if len(self.fh.linear_order) > 1:
            self.fh.linear_order[1].abs_index = self.fh.linear_order[0].abs_index - 1
        # Run self-healing.
        self.fh.self_heal_structure()
        # Check parent's index is lower than child's.
        for node in self.fh.linear_order:
            if node.parent and node.abs_index is not None and node.parent.abs_index is not None:
                self.assertLess(node.parent.abs_index, node.abs_index,
                                f"After healing, parent {node.parent.label} should come before {node.label}.")

    # ------------------ Rule 4: Descending Weights for Children --------------------
    def test_descending_weights_valid(self):
        for node in self.fh.linear_order:
            if node.children:
                child_weights = [child.weight for child in node.children]
                self.assertEqual(child_weights, sorted(child_weights, reverse=True),
                                 f"Children of {node.label} should be sorted in descending order by weight.")

    def test_descending_weights_broken_and_fixed(self):
        # Check initial state: parent's weight should be >= child's.
        self.fh.run_validations()
        for node in self.fh.linear_order:
            if node.parent:
                self.assertLessEqual(node.weight, node.parent.weight)
        # Break the descending weight assumption.
        self.break_descending_weights()
        self.fh.run_validations()
        weight_errors = [err for err in self.fh.check_errors if "weight" in err]
        self.assertTrue(weight_errors, "Descending weight violation detected.")
        # Run self-healing.
        self.fh.self_heal_structure()
        self.fh.run_validations()
        weight_errors = [err for err in self.fh.check_errors if "weight" in err]
        self.assertFalse(weight_errors, "Self-healing fixed the descending weights.")

    # ------------------ Rule 5: Valid Submatrix Bounds --------------------
    def test_submatrix_bounds_valid(self):
        for node in self.fh.linear_order:
            bounds = node.get_submatrix_bounds()
            self.assertIsNotNone(bounds["start_index"], f"Node {node.label} must have a valid start_index.")
            self.assertIsNotNone(bounds["end_index"], f"Node {node.label} must have a valid end_index.")

    def test_submatrix_bounds_broken_and_fixed(self):
        # Validate initial state.
        self.fh.run_validations()
        for node in self.fh.linear_order:
            bounds = node.get_submatrix_bounds()
            self.assertIsNotNone(bounds["start_index"], f"{node.label} start_index is set.")
            self.assertIsNotNone(bounds["end_index"], f"{node.label} end_index is set.")
        # Break: clear submatrix bounds.
        self.break_submatrix_bounds()
        self.fh.run_validations()
        violation_count = sum(
            1 for node in self.fh.linear_order
            if node.get_submatrix_bounds()["start_index"] is None or node.get_submatrix_bounds()["end_index"] is None
        )
        self.assertGreater(violation_count, 0, "Submatrix bounds violation detected.")
        # Run self-healing and revalidate.
        self.fh.self_heal_structure()
        self.fh.run_validations()
        for node in self.fh.linear_order:
            bounds = node.get_submatrix_bounds()
            self.assertIsNotNone(bounds["start_index"], f"After healing: {node.label} start_index restored.")
            self.assertIsNotNone(bounds["end_index"], f"After healing: {node.label} end_index restored.")

    # ------------------ Rule 6: Valid Causal Metadata --------------------
    def test_causal_metadata_valid(self):
        propagate_causal_effects(self.fh.root)
        for node in self.fh.linear_order:
            # For non-root nodes, verify that causal_inference has keys.
            if node != self.fh.root and hasattr(node, "causal_inference"):
                ci = node.causal_inference
                self.assertIn("cause_effect_relation", ci, f"Node {node.label} must include cause_effect_relation.")
                self.assertIn("influence_strength", ci["cause_effect_relation"],
                              f"Node {node.label} must define influence_strength.")

    # (LLM summarisation tests might be added later to check that a human‑readable summary is generated.)
    
    # --- Helper methods to break specific rules ---
    
    def break_descending_weights(self):
        # For one child, increase its weight above its parent.
        for node in self.fh.linear_order:
            if node.parent:
                node.weight = node.parent.weight * 1.1
                return

    def break_submatrix_bounds(self):
        # Clear submatrix bounds for all nodes.
        for node in self.fh.linear_order:
            node.set_submatrix_bounds(None, None)

if __name__ == "__main__":
    unittest.main() 