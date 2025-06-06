"""
Test file for computing and validating skip factors on a custom tree.

The skip factor for a node is computed as:
    skip_factor = (number of children with weight >= threshold / total number of children)^dimension

For a leaf node, skip_factor is set to 1.0.
This test creates a custom tree where some children are below threshold.
It then verifies skip factors for both dimension 1 (1D) and dimension 2 (2D).
"""

import unittest
from LanguageAgentTreeSearch.programming.main import Node, compute_and_update_skip_factors

class TestSkipFactors(unittest.TestCase):
    def setUp(self):
        # Build a custom tree manually.
        #
        #            Origin (weight=1.0)
        #           /       |        \
        #          A        B         C
        #         (1.0)    (1.0)     (1.0)
        #        /     \    /    \       (no children)
        #      A1      A2  B1    B2
        #    (0.4)   (0.8) (0.6) (0.5)
        #
        # Here, threshold = 0.5. Thus:
        #   - For node A: total=2; A1 (0.4) < 0.5 and A2 (0.8) >= 0.5, so processed=1. => SK1 = 0.5, SK2 = (0.5^2)=0.25.
        #   - For node B: both B1 (0.6) and B2 (0.5) are >= 0.5 => processed=2; SK=1.0.
        #   - For node C: no children so SK=1.0.
        
        self.origin = Node("Origin", weight=1.0)
        self.origin.children = []
        
        # Top-level nodes
        self.A = Node("A", weight=1.0)
        self.B = Node("B", weight=1.0)
        self.C = Node("C", weight=1.0)
        for child in [self.A, self.B, self.C]:
            child.parent = self.origin
        self.origin.children.extend([self.A, self.B, self.C])
        
        # Children for A: A1 and A2
        self.A1 = Node("A1", weight=0.4)
        self.A2 = Node("A2", weight=0.8)
        self.A1.parent = self.A
        self.A2.parent = self.A
        self.A.children.extend([self.A1, self.A2])
        
        # Children for B: B1 and B2
        self.B1 = Node("B1", weight=0.6)
        self.B2 = Node("B2", weight=0.5)
        self.B1.parent = self.B
        self.B2.parent = self.B
        self.B.children.extend([self.B1, self.B2])
        # C remains a leaf (no children)
    
    def test_skip_factor_1d(self):
        # Compute skip factors using dimension=1
        compute_and_update_skip_factors(self.origin, threshold=0.5, dimension=1)
        
        # For origin: 3 children (all have weight 1.0 >= threshold): skip_factor should be (3/3)^1 = 1.0.
        self.assertEqual(self.origin.skip_factor, 1.0)
        # For node A: 2 children; one qualifies (A2) => skip_factor = (1/2)^1 = 0.5.
        self.assertAlmostEqual(self.A.skip_factor, 0.5)
        # For node B: 2 children; both qualify => skip_factor = (2/2)^1 = 1.0.
        self.assertEqual(self.B.skip_factor, 1.0)
        # For node C (leaf): skip_factor should be 1.0.
        self.assertEqual(self.C.skip_factor, 1.0)
        # For leaf children, skip_factor equals 1.0.
        self.assertEqual(self.A1.skip_factor, 1.0)
        self.assertEqual(self.A2.skip_factor, 1.0)
        self.assertEqual(self.B1.skip_factor, 1.0)
        self.assertEqual(self.B2.skip_factor, 1.0)
        
        # Printing the computed results for debugging/log purposes.
        print("\n[SkipFactors Test] Dimension 1 Results:")
        print("Origin skip_factor:", self.origin.skip_factor)
        print("A skip_factor:", self.A.skip_factor)
        print("B skip_factor:", self.B.skip_factor)
        print("C skip_factor:", self.C.skip_factor)
        print("A1 skip_factor:", self.A1.skip_factor)
        print("A2 skip_factor:", self.A2.skip_factor)
        print("B1 skip_factor:", self.B1.skip_factor)
        print("B2 skip_factor:", self.B2.skip_factor)
    
    def test_skip_factor_2d(self):
        # Compute skip factors using dimension=2 this time
        compute_and_update_skip_factors(self.origin, threshold=0.5, dimension=2)
        
        # For node A: skip_factor = (1/2)^2 = 0.25.
        self.assertAlmostEqual(self.A.skip_factor, 0.25)
        # Other nodes (origin, B, C) remain the same as before.
        self.assertEqual(self.origin.skip_factor, 1.0)
        self.assertEqual(self.B.skip_factor, 1.0)
        self.assertEqual(self.C.skip_factor, 1.0)
        self.assertEqual(self.A1.skip_factor, 1.0)
        self.assertEqual(self.A2.skip_factor, 1.0)
        self.assertEqual(self.B1.skip_factor, 1.0)
        self.assertEqual(self.B2.skip_factor, 1.0)
        
        # Print the key result for node A in 2D for debugging.
        print("\n[SkipFactors Test] Dimension 2 Results:")
        print("A skip_factor:", self.A.skip_factor, "(expected 0.25)")

if __name__ == '__main__':
    unittest.main() 