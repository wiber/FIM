import unittest
from LanguageAgentTreeSearch.programming.main import Node, compute_and_update_skip_factors

class TestSkipFactors(unittest.TestCase):
    def setUp(self):
        # Create a simple tree manually:
        #   Root ("Origin") with three children:
        #     - Child1 with weight=1.0 (≥ threshold)
        #     - Child2 with weight=0.4 (< threshold)
        #     - Child3 with weight=0.7 (≥ threshold)
        self.root = Node("Origin", weight=1.0)
        self.child1 = Node("Child1", weight=1.0)
        self.child2 = Node("Child2", weight=0.4)
        self.child3 = Node("Child3", weight=0.7)
        
        # Set up parent-child relations
        self.root.children = [self.child1, self.child2, self.child3]
        self.child1.parent = self.root
        self.child2.parent = self.root
        self.child3.parent = self.root

    def test_skip_factor_1d(self):
        """Test that skip factors are computed correctly in 1D (dimension=1)."""
        threshold = 0.5
        compute_and_update_skip_factors(self.root, threshold=threshold, dimension=1)
        
        # For self.root: of its 3 children, only child1 and child3 have weight >= 0.5 (2 out of 3)
        expected_skip_factor = (2 / 3) ** 1  # Should be approximately 0.6667
        self.assertAlmostEqual(self.root.skip_factor, expected_skip_factor, places=3,
                               msg="For dimension=1, expected skip factor ≈ (2/3)^1 for the root node")
        
        # Leaf nodes (without children) get a default skip factor of 1.0.
        self.assertEqual(self.child1.skip_factor, 1.0)
        self.assertEqual(self.child2.skip_factor, 1.0)
        self.assertEqual(self.child3.skip_factor, 1.0)

    def test_skip_factor_2d(self):
        """Test that skip factors are computed correctly in 2D (dimension=2)."""
        threshold = 0.5
        compute_and_update_skip_factors(self.root, threshold=threshold, dimension=2)
        
        # For self.root: skip factor should be (2/3)^2 ≈ 0.4444
        expected_skip_factor = (2 / 3) ** 2
        self.assertAlmostEqual(self.root.skip_factor, expected_skip_factor, places=3,
                               msg="For dimension=2, expected skip factor ≈ (2/3)^2 for the root node")
        
        # Leaf nodes remain unchanged.
        self.assertEqual(self.child1.skip_factor, 1.0)
        self.assertEqual(self.child2.skip_factor, 1.0)
        self.assertEqual(self.child3.skip_factor, 1.0)

if __name__ == '__main__':
    unittest.main() 