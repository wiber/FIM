#!/usr/bin/env python3
"""
Test to ensure that the LLM integration properly updates composite metadata and node weights.
"""

import json
import unittest
from LanguageAgentTreeSearch.programming.fim import FIMHierarchy
from LanguageAgentTreeSearch.programming.main import get_default_hierarchy
from programming.llm_helpers import actual_llm_function


def dummy_llm_function(prompt):
    """
    Dummy LLM function that returns a JSON response with a suggested weight.
    For this test, if the prompt contains the letter 'A', we return a suggested weight of 0.95;
    otherwise, return 0.85.
    """
    if "A" in prompt:
        return json.dumps({"suggested_weight": 0.95})
    else:
        return json.dumps({"suggested_weight": 0.85})


class TestLLMIntegration(unittest.TestCase):
    def setUp(self):
        # Create a default hierarchy object (FIMHierarchy)
        # get_default_hierarchy() is assumed to return an instance of FIMHierarchy with a root node.
        self.hierarchy = get_default_hierarchy()
        # Propagate composite metadata starting from the root.
        self.hierarchy.propagate_combined_metadata(self.hierarchy.root)

    def test_apply_llm_updates_weights(self):
        # Apply our dummy LLM function to update composite metadata.
        self.hierarchy.apply_llm_to_composite_metadata(dummy_llm_function)

        # Check every node (except the Origin) to see if weights were updated to the expected value.
        # Here we assume that if a node's prompt includes "A", its weight should become 0.95, otherwise 0.85.
        for node in self.hierarchy.linear_order:
            if node.parent is None:
                continue  # Skip the root node.
            prompt = node.causal_inference.get("prompt", "")
            expected_weight = 0.95 if "A" in prompt else 0.85
            self.assertEqual(
                node.weight,
                expected_weight,
                f"Node '{node.label}' weight expected to be {expected_weight} but was {node.weight}.",
            )

    def test_llm_response_stored(self):
        # Apply the dummy LLM function.
        self.hierarchy.apply_llm_to_composite_metadata(dummy_llm_function)
        # Ensure that each non-root node has the LLM response stored in its composite metadata.
        for node in self.hierarchy.linear_order:
            if node.parent:
                ci = node.causal_inference
                self.assertIn(
                    "llm_response",
                    ci,
                    f"Node '{node.label}' does not have 'llm_response' stored in composite metadata.",
                )
                # Optionally, verify the format of the stored response:
                try:
                    json.loads(ci["llm_response"])
                except Exception as e:
                    self.fail(
                        f"Node '{node.label}' 'llm_response' is not valid JSON: {ci['llm_response']}"
                    )


if __name__ == "__main__":
    unittest.main()