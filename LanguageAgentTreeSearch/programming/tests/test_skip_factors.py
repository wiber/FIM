import unittest
from LanguageAgentTreeSearch.programming.main import (
    Node,
    compute_and_update_skip_factors,
    build_tree_from_json,
    randomize_tree_weights,
    FIMHierarchy
)
import json

class TestSkipFactors(unittest.TestCase):
    def setUp(self):
        # For testing, we construct a small tree using a simple JSON structure.
        # The tree structure here follows the sample hierarchy pattern.
        self.json_data = {
            "Origin": {"A": 1.0, "B": 1.0},
            "A": {"A1": 0.8, "A2": 0.75},
            "B": {"B1": 0.85, "B2": 0.8, "B3": 0.78}
        }
        # Build the tree from JSON; the function assigns each node basic weights.
        self.root = build_tree_from_json(self.json_data, "Origin")
        # Note: do not call any self-healing routine here causing the tree reconstruction.
        # We want to work with the in-memory tree and then explicitly compute skip factors.
    
    def test_skip_factors_1d(self):
        """
        Test the computation of skip factors in 1D (dimension = 1).
        For each node with children, the expected skip factor is:
            (number of children with weight >= threshold / total number of children) ** 1.
        Also, print out the computed values with explanations.
        """
        threshold = 0.5  # With our sample, all child weights exceed 0.5.
        dimension = 1
        # Compute skip factors for the entire tree recursively.
        compute_and_update_skip_factors(self.root, threshold=threshold, dimension=dimension)
        
        # For the root:
        if self.root.children:
            total = len(self.root.children)
            processed = sum(1 for child in self.root.children if child.weight >= threshold)
            expected = (processed / total) ** dimension
            self.assertAlmostEqual(self.root.skip_factor, expected, places=5,
                                   msg="skip_factor for root does not match expected value")
            print("\n1D Skip Factors:")
            print(f"Root Node: {self.root.label} -> Children: {total}, Processed: {processed}, "
                  f"Computed skip_factor: {self.root.skip_factor} (Expected: {expected})")
        
        # For each direct child of the root:
        for child in self.root.children:
            if child.children:
                total = len(child.children)
                processed = sum(1 for grandchild in child.children if grandchild.weight >= threshold)
                expected = (processed / total) ** dimension if total > 0 else 1.0
            else:
                expected = 1.0
            self.assertAlmostEqual(child.skip_factor, expected, places=5,
                                   msg=f"skip_factor for {child.label} does not match expected value")
            print(f"Node: {child.label} -> Children: {len(child.children) if child.children else 0}, "
                  f"Computed skip_factor: {child.skip_factor} (Expected: {expected})")
    
    def test_skip_factors_2d(self):
        """
        Test the computation of skip factors in 2D (dimension = 2).
        For each node with children, the expected skip factor is:
            (number of children with weight >= threshold / total number of children) ** 2.
        The test prints the calculated values with an explanation.
        """
        threshold = 0.5  # All children exceed this threshold in our sample data.
        dimension = 2
        compute_and_update_skip_factors(self.root, threshold=threshold, dimension=dimension)
        
        if self.root.children:
            total = len(self.root.children)
            processed = sum(1 for child in self.root.children if child.weight >= threshold)
            expected = (processed / total) ** dimension
            self.assertAlmostEqual(self.root.skip_factor, expected, places=5,
                                   msg="skip_factor for root does not match expected value for dimension 2")
            print("\n2D Skip Factors:")
            print(f"Root Node: {self.root.label} -> Children: {total}, Processed: {processed}, "
                  f"Computed skip_factor: {self.root.skip_factor} (Expected: {expected})")
        
        for child in self.root.children:
            if child.children:
                total = len(child.children)
                processed = sum(1 for grandchild in child.children if grandchild.weight >= threshold)
                expected = (processed / total) ** dimension if total > 0 else 1.0
            else:
                expected = 1.0
            self.assertAlmostEqual(child.skip_factor, expected, places=5,
                                   msg=f"skip_factor for {child.label} does not match expected value for dimension 2")
            print(f"Node: {child.label} -> Children: {len(child.children) if child.children else 0}, "
                  f"Computed skip_factor: {child.skip_factor} (Expected: {expected})")

class TestSkipFactorsExtended(unittest.TestCase):
    def setUp(self):
        # Use a sample structure with at least 3 top-level nodes and 3 sub-nodes each.
        self.sample_graph = {
            "Origin": {"A": 1.0, "B": 1.0, "C": 1.0},
            "A": {"A1": 0.8, "A2": 0.75, "A3": 0.7},
            "B": {"B1": 0.85, "B2": 0.8, "B3": 0.78},
            "C": {"C1": 0.9, "C2": 0.85, "C3": 0.8}
        }
        # Build the tree from the sample graph
        self.root = build_tree_from_json(self.sample_graph, "Origin")
        # Create the FIMHierarchy instance from the in-memory tree and graph data.
        self.fh = FIMHierarchy(self.root, self.sample_graph)
        # Run initial self-healing (this sets ordering, indices, prefixes, etc.)
        self.fh.trigger_hierarchy_update()

    def test_skip_factors_extended_1d_and_2d(self):
        # Find the top-level node "A"
        nodeA = None
        for child in self.fh.root.children:
            if child.invariant_label == "A":
                nodeA = child
                break
        self.assertIsNotNone(nodeA, "Category A must be found among the top-level nodes.")
        
        # In node A, modify the weight of child "A2" to force a non-trivial skip factor.
        nodeA_child = None
        for child in nodeA.children:
            if child.invariant_label == "A2":
                nodeA_child = child
                break
        self.assertIsNotNone(nodeA_child, "Child A2 should exist under Category A.")
        
        # Update A2's weight to below the threshold (e.g., 0.4)
        nodeA_child.update_weight(0.4)
        
        # Recompute skip factors for dimension 1.
        compute_and_update_skip_factors(self.fh.root, threshold=0.5, dimension=1)
        
        # For node A: total children = 3, processed children should now be 2 (A1 and A3 meet threshold)
        expected_skip_factor_1d = 2 / 3
        self.assertAlmostEqual(
            nodeA.skip_factor, expected_skip_factor_1d, places=2,
            msg=f"Expected skip factor for node A (1D) should be {expected_skip_factor_1d}, got {nodeA.skip_factor}"
        )
        
        # For all other top-level nodes (B and C) with all children above threshold, skip factor should be 1.0.
        for category in self.fh.root.children:
            if category.invariant_label != "A":
                self.assertEqual(
                    category.skip_factor, 1.0,
                    f"Expected skip factor for node {category.invariant_label} to be 1.0, got {category.skip_factor}"
                )
        
        # Now recompute skip factors for dimension 2.
        compute_and_update_skip_factors(self.fh.root, threshold=0.5, dimension=2)
        expected_skip_factor_2d = (2 / 3) ** 2
        self.assertAlmostEqual(
            nodeA.skip_factor, expected_skip_factor_2d, places=2,
            msg=f"Expected skip factor for node A (2D) should be {expected_skip_factor_2d}, got {nodeA.skip_factor}"
        )
        
        # Print calculated skip factors for debugging/verification.
        print("\n--- Skip Factors Report ---")
        for category in self.fh.root.children:
            print(f"Node {category.invariant_label}: skip_factor = {category.skip_factor}")
        print(f"Node A skip_factor (dimension 2) = {nodeA.skip_factor}")

if __name__ == '__main__':
    unittest.main() 