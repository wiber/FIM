"""
Node class for the Fractal Identity Map (FIM) hierarchy.

This module defines the basic Node structure used for building the tree.
"""

class Node:
    def __init__(self, label, weight=1.0, children=None, parent=None):
        """
        Initialize a Node with a label, weight, a list of children, and an optional parent.
        Also attaches defaults for problem_space, causal_inference, and abs_index.
        """
        self.label = label
        self.weight = weight
        self.children = children if children is not None else []
        self.parent = parent
        self.problem_space = None
        self.causal_inference = {}  # to store composite metadata (e.g., prompt, LLM responses)
        self.abs_index = None  # to be assigned later in ordering

    def __repr__(self):
        return f"Node(label={self.label}, weight={self.weight})" 