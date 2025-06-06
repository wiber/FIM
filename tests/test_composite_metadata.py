import json
import unittest

# Import the helper to create a default hierarchy and the FIMHierarchy class.
# (Assumes get_default_hierarchy and FIMHierarchy are exposed via main.py.)
from LanguageAgentTreeSearch.programming.main import get_default_hierarchy, FIMHierarchy
from LanguageAgentTreeSearch.programming.llm_helpers import (
    build_link_prompts_for_llm,
    build_combined_links_prompt
)

class TestCompositeMetadata(unittest.TestCase):
    def test_propagated_composite_metadata_and_prompts(self):
        # Create the default hierarchy structure.
        hierarchy_data = get_default_hierarchy()
        hierarchy = FIMHierarchy.from_json(hierarchy_data)
        hierarchy.self_heal()

        # Propagate composite (combined) causal metadata down from the root.
        hierarchy.propagate_combined_metadata(hierarchy.root)

        print("\n--- Propagated Composite Metadata for Each Node ---")
        for node in hierarchy.linear_order:
            # Ensure each node has the combined metadata attached.
            self.assertIsNotNone(node.causal_inference_links, f"Node {node.label} is missing composite metadata")
            # For nodes with a parent, verify that parent's label is recorded.
            if node.parent:
                self.assertEqual(
                    node.causal_inference_links.get("parent_label"),
                    node.parent.label,
                    f"Node {node.label} composite metadata does not match parent's label"
                )
            # For demonstration, print the composite metadata.
            print(f"Node {node.label} composite metadata:")
            print(json.dumps(node.causal_inference_links, indent=2))

        # Build LLM link prompts (multi-turn approach) to verify that the prompts include the origin problem space.
        llm_prompts = build_link_prompts_for_llm(hierarchy)
        print("\n--- Generated LLM Link Prompts (Multi-Turn) ---")
        for link_key, prompt_text in llm_prompts:
            print(f"\nLink key: {link_key}")
            print(prompt_text)
            # Check that the prompt includes at least the origin problem space marker.
            self.assertIn("ORIGIN PROBLEM-SPACE", prompt_text)

        # Also build a combined single prompt and print it.
        combined_prompt = build_combined_links_prompt(hierarchy)
        print("\n--- Generated Combined LLM Link Prompt ---")
        print(combined_prompt)
        self.assertIn("ORIGIN PROBLEM-SPACE", combined_prompt)

if __name__ == '__main__':
    unittest.main() 