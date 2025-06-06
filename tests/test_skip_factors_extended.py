import unittest
import json
import os
from LanguageAgentTreeSearch.programming.main import (
    FIMHierarchy,
    compute_and_update_skip_factors,
    randomize_tree_weights
)

class TestSkipFactorsExtended(unittest.TestCase):
    def setUp(self):
        # Load the sample hierarchy JSON
        json_path = os.path.join(os.path.dirname(__file__), "..", "sample_hierarchy.json")
        with open(json_path, "r") as f:
            self.hierarchy_data = json.load(f)
        
        # Build the hierarchy from the JSON seed.
        # Using the provided from_json method ensures a valid structure with at least 3 categories
        self.fh = FIMHierarchy.from_json(self.hierarchy_data)
        # Trigger an initial update to build ordering.
        self.fh.trigger_hierarchy_update()
        
        # For this test, we modify one child's weight to be below the threshold.
        # For example, in category A, set "A3" to 0.4 so that for node A:
        # total children = 3, processed children (with weight >= 0.5) = 2.
        for node in self.fh.linear_order:
            if node.label == "A":  # find top-level node A
                for child in node.children:
                    if child.label == "A3":
                        child.update_weight(0.4)  # below default threshold of 0.5
        # Now, update skip factors after modifying weights.
    
    def test_skip_factors_1d(self):
        """Compute and print skip factors for 1D ordering (dimension=1)."""
        # Compute skip factors for all nodes with threshold 0.5 and dimension=1.
        compute_and_update_skip_factors(self.fh.root, threshold=0.5, dimension=1)
        
        # For demonstration, print out the skip factor for each top-level category.
        print("\n--- Skip Factors (1D, dimension=1) ---")
        for node in self.fh.linear_order:
            if node.parent == self.fh.root:  # top-level category
                total = len(node.children)
                processed = sum(1 for child in node.children if child.weight >= 0.5)
                expected = (processed / total) if total > 0 else 1.0
                print(f"Category '{node.label}': {processed} of {total} children >= 0.5 -> Skip Factor = {node.skip_factor} (Expected ~{expected:.2f})")
                # Assert that the computed skip factor is as expected.
                self.assertAlmostEqual(node.skip_factor, expected, places=2)
    
    def test_skip_factors_2d(self):
        """Compute and print skip factors for 2D ordering (dimension=2)."""
        # Compute skip factors for all nodes with threshold 0.5 and dimension=2.
        compute_and_update_skip_factors(self.fh.root, threshold=0.5, dimension=2)
        
        # For demonstration, print out the skip factor for each top-level category.
        print("\n--- Skip Factors (2D, dimension=2) ---")
        for node in self.fh.linear_order:
            if node.parent == self.fh.root:  # top-level category
                total = len(node.children)
                processed = sum(1 for child in node.children if child.weight >= 0.5)
                expected = (processed / total) ** 2 if total > 0 else 1.0
                print(f"Category '{node.label}': {processed} of {total} children >= 0.5 -> Skip Factor = {node.skip_factor} (Expected ~{expected:.2f})")
                self.assertAlmostEqual(node.skip_factor, expected, places=2)

if __name__ == '__main__':
    unittest.main() 