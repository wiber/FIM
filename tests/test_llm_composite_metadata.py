import unittest
import logging
from LanguageAgentTreeSearch.programming.fim import FIMHierarchy, get_default_hierarchy
from LanguageAgentTreeSearch.programming.llm_helpers import build_link_prompts_for_llm, build_combined_links_prompt

class TestLLMCompositeMetadata(unittest.TestCase):
    def setUp(self):
        # Use the default hierarchy if available; otherwise create a minimal one.
        try:
            self.hierarchy_data = get_default_hierarchy()
        except Exception:
            # Minimal test hierarchy structure with one root and two levels
            self.hierarchy_data = {
                "root": {
                    "label": "Origin",
                    "children": [
                        {
                            "label": "A", 
                            "weight": 1.0, 
                            "children": [
                                {"label": "A1", "weight": 0.8, "children": []},
                                {"label": "A2", "weight": 0.9, "children": []}
                            ]
                        },
                        {
                            "label": "B", 
                            "weight": 1.0, 
                            "children": [
                                {"label": "B1", "weight": 0.85, "children": []}
                            ]
                        }
                    ]
                }
            }
        # Create the FIMHierarchy from JSON seed.
        self.hierarchy = FIMHierarchy.from_json(self.hierarchy_data)
        self.hierarchy.self_heal()
        # Propagate composite causal metadata from the root downwards.
        self.hierarchy.propagate_combined_metadata(self.hierarchy.root)
    
    def test_composite_metadata_propagation(self):
        """
        Test that composite metadata (stored in causal_inference_links) is added to each node.
        - For the root (Origin) this should be empty.
        - For every child node, there should be causal inference information.
        """
        for node in self.hierarchy.linear_order:
            self.assertTrue(hasattr(node, "causal_inference_links"),
                            f"Node '{node.label}' missing 'causal_inference_links' attribute")
            if node.parent:
                self.assertNotEqual(node.causal_inference_links, {},
                                    f"Node '{node.label}' should have non-empty causal inference metadata")
            else:
                self.assertEqual(node.causal_inference_links, {},
                                 "Root node should have an empty 'causal_inference_links' attribute")
    
    def test_llm_prompts_generation(self):
        """
        Use the multi-turn helper to generate prompts for each parent-child link,
        verifying that the prompts include the origin's problem space, and the parent's and child's labels.
        """
        prompts = build_link_prompts_for_llm(self.hierarchy)
        # Expect one prompt per non-root node.
        expected_prompts_count = len([node for node in self.hierarchy.linear_order if node.parent])
        self.assertEqual(len(prompts), expected_prompts_count)
        
        for (link_key, prompt_text) in prompts:
            # Check that the origin's problem space is referenced.
            self.assertIn("ORIGIN PROBLEM-SPACE:", prompt_text)
            # Retrieve nodes using the helper _find_node_by_id (assumed available in FIMHierarchy)
            parent_node = self.hierarchy._find_node_by_id(link_key[0])
            child_node = self.hierarchy._find_node_by_id(link_key[1])
            self.assertIsNotNone(parent_node, f"Parent node for key {link_key[0]} not found.")
            self.assertIsNotNone(child_node, f"Child node for key {link_key[1]} not found.")
            # Verify that parent's and child's labels appear in the prompt.
            self.assertIn(parent_node.label, prompt_text)
            self.assertIn(child_node.label, prompt_text)
    
    def test_combined_llm_prompt_generation(self):
        """
        Use the combined prompt helper to generate a single prompt that lists all parent->child links.
        """
        combined_prompt = build_combined_links_prompt(self.hierarchy)
        self.assertIn("ORIGIN PROBLEM-SPACE:", combined_prompt)
        # Check that every link is mentioned.
        for node in self.hierarchy.linear_order:
            if node.parent:
                self.assertIn(f"Parent={node.parent.label}", combined_prompt)
                self.assertIn(f"Child={node.label}", combined_prompt)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    unittest.main() 