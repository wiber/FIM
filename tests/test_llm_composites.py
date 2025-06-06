"""
Test file for verifying composite LLM metadata fields constructed
from the FIM problem-space. This test loads a default hierarchy,
populates the root's problem-space metadata, and then uses the LLM
helper functions to generate prompts. It then mocks an LLM call to
simulate the generation of composite metadata (combining the origin
metadata with each parent→child link's data).
"""

import unittest
import json

# Import the FIMHierarchy and helper methods.
# Adjust the import paths as needed for your project.
from LanguageAgentTreeSearch.programming.fim import FIMHierarchy, get_default_hierarchy
from LanguageAgentTreeSearch.programming.llm_helpers import (
    build_link_prompts_for_llm,
    build_combined_links_prompt,
    build_composite_prompts_for_llm,
    attach_llm_composites
)

def mock_llm_function(prompt):
    # Simple mock that returns a fake explanation based on the prompt
    return "Mock Explanation: " + prompt[:50]

class TestLlmComposites(unittest.TestCase):

    def setUp(self):
        # Load a default hierarchy.
        hierarchy_data = get_default_hierarchy()
        self.hierarchy = FIMHierarchy.from_json(hierarchy_data)
        # Set the root's problem-space metadata (to be used in LLM prompts).
        self.hierarchy.root.problem_space = {
            "description": "Test FIM problem space for composite metadata",
            "context": "This context simulates the FIM as the problem space"
        }
        # Ensure ordering and other initializations are updated.
        self.hierarchy.self_heal()
        # Simulate propagation of downward causal reasoning using the mock_llm_function
        self.hierarchy.apply_downward_causal_reasoning(mock_llm_function)

    def test_composite_metadata_fields(self):
        # Build the individual link prompts from the hierarchy.
        llm_prompts = build_link_prompts_for_llm(self.hierarchy)
        self.assertGreater(len(llm_prompts), 0, "No link prompts were generated.")

        # For demonstration, print each composite prompt.
        print("\n--- Generated LLM Link Prompts (Multi-Turn) ---")
        for link_key, prompt_text in llm_prompts:
            print(f"Link key: {link_key}")
            print(prompt_text)
            print("-----")

        # Build combined prompt and test that it includes the problem space text.
        combined_prompt = build_combined_links_prompt(self.hierarchy)
        self.assertIn("Test FIM problem space", combined_prompt)
        print("\n--- Generated Combined LLM Link Prompt ---")
        print(combined_prompt)
        
        # Define a mock LLM function that simulates returning composite metadata.
        def mock_llm_function(prompt):
            # Return a composite explanation string.
            return "Composite Metadata: " + prompt

        # Apply the downward causal reasoning using the mock LLM.
        self.hierarchy.apply_downward_causal_reasoning(mock_llm_function)

        # Verify that each child node (i.e. node with a parent) has a non-empty
        # 'downward_causal_reasoning' field containing the expected composite text.
        composite_results = []
        print("\n--- Composite Metadata Propagated to Child Nodes ---")
        for node in self.hierarchy.linear_order:
            if node.parent is not None:
                composite_results.append(node.downward_causal_reasoning)
                print(f"Node {node.label} composite metadata: {node.downward_causal_reasoning}")
                self.assertIn("Composite Metadata:", node.downward_causal_reasoning)
        
        self.assertGreater(len(composite_results), 0, "No composite metadata found on child nodes.")

    def test_composite_prompts(self):
        composite_data = build_composite_prompts_for_llm(self.hierarchy)
        
        # Ensure the composite is a non-empty dictionary
        self.assertIsInstance(composite_data, dict)
        self.assertGreater(len(composite_data), 0, "Composite object should not be empty.")
        
        # Expected fields for every composite entry
        required_fields = {"origin_metadata", "parent_label", "child_label", "link_weight", "llm_explanation"}
        
        for key, composite in composite_data.items():
            with self.subTest(link_key=key):
                self.assertTrue(required_fields.issubset(composite.keys()),
                                f"Composite entry for {key} is missing required fields.")
                # Optionally print each composite for visual inspection
                print(f"Composite for link {key}:\n{json.dumps(composite, indent=2)}\n")

    def test_attach_llm_composites(self):
        # Load default hierarchy
        hierarchy_data = get_default_hierarchy()
        hierarchy = FIMHierarchy.from_json(hierarchy_data)
        # Set the origin's problem space metadata:
        hierarchy.root.problem_space = {
            "description": "Test problem space for FIM. This includes key factors such as complexity and domain details."
        }
        hierarchy.self_heal()  # Ensure the hierarchy is updated

        # Call the new helper to attach composite LLM prompts to each link.
        attach_llm_composites(hierarchy)

        # Verify that every node that is not the root has an llm_composite attribute.
        composites_found = 0
        for node in hierarchy.linear_order:
            if node.parent is not None:
                self.assertTrue(hasattr(node, "llm_composite"), f"Node {node.node_id} missing llm_composite")
                composites_found += 1
                # Print out the composite for visual inspection
                print(f"\nNode {node.label} composite prompt:\n{node.llm_composite}\n")
        
        # For our default hierarchy, there should be exactly 3 composite prompts (A1, A2, B1)
        self.assertEqual(composites_found, 3, "Expected 3 composite prompts for child links.")

class TestLLMCompositeMetadata(unittest.TestCase):
    def test_composite_metadata_population(self):
        # Use default hierarchy data – this fixture creates a known hierarchy.
        hierarchy_data = get_default_hierarchy()
        hierarchy = FIMHierarchy.from_json(hierarchy_data)
        
        # Ensure the hierarchy is healed (assigns linear ordering, indices, etc.)
        hierarchy.self_heal()
        # Aggregate composite metadata in each node based on the origin and causal reasoning.
        hierarchy.aggregate_composite_metadata()
        
        # Examine every non-root node to check composite metadata is present.
        for node in hierarchy.linear_order:
            if node.parent is not None:
                self.assertTrue(hasattr(node, "composite_metadata"),
                                f"Node {node.label} should have composite_metadata")
                composite = node.composite_metadata
                # Verify presence of expected fields.
                self.assertIn("parent_label", composite)
                self.assertIn("child_label", composite)
                self.assertIn("link_weight", composite)
                self.assertIn("origin_metadata", composite)
                self.assertIn("llm_prompt", composite)
                print(f"Node {node.label} composite metadata:")
                print(composite)

if __name__ == '__main__':
    unittest.main() 