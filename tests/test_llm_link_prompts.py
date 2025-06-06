import json
import unittest
from LanguageAgentTreeSearch.programming.llm_helpers import build_link_prompts_for_llm, build_combined_links_prompt
from fim import FIMHierarchy, Node  # Adjust the import if FIMHierarchy is in a different module
from LanguageAgentTreeSearch.programming.fim import get_default_hierarchy

# For testing purposes we define minimal dummy classes for Node and FIMHierarchy.
# In your codebase you would normally import these from your FIM module.
class Node:
    def __init__(self, node_id, label, weight, parent=None):
        self.node_id = node_id
        self.label = label
        self.weight = weight
        self.parent = parent
        self.children = []
        self.downward_causal_reasoning = None

class FIMHierarchy:
    def __init__(self, root, linear_order):
        self.root = root
        self.linear_order = linear_order

# Helper function to build prompts for LLM based on the hierarchy.
def build_link_prompts_for_llm(hierarchy):
    """
    Construct a list of prompts that ask the LLM how the origin's problem space defines
    each link (from parent to child) by including the origin metadata, parent label,
    child label, and link weight.
    Returns a list of (link_key, prompt_text) tuples.
    """
    origin_data = getattr(hierarchy.root, "problem_space", {})
    origin_json = json.dumps(origin_data, indent=2) if isinstance(origin_data, dict) else str(origin_data)
    
    prompts = []
    for node in hierarchy.linear_order:
        # Skip the root since it has no parent.
        if node.parent is None:
            continue

        parent_label = node.parent.label
        child_label = node.label
        link_weight = node.weight

        prompt_text = f"""
ORIGIN PROBLEM-SPACE:
{origin_json}

We have a parent category "{parent_label}" linking to a child "{child_label}"
with a link weight of {link_weight}.

QUESTION:
How does the origin's problem space define or explain
this link from parent to child with weight={link_weight}?
        """.strip()

        # Use a unique key based on parent's and child's IDs.
        key = (node.parent.node_id, node.node_id)
        prompts.append((key, prompt_text))
        
    return prompts

class TestLLMLinkPrompts(unittest.TestCase):
    def setUp(self):
        """
        Create a minimal FIMHierarchy with three nodes:
           - Origin (with problem_space metadata)
           - Parent 'A' (child of Origin)
           - Child 'A1' (child of 'A')
        """
        from LanguageAgentTreeSearch.programming.fim import FIMHierarchy, Node
        # Create the origin and set its problem_space details.
        origin = Node(node_id="origin", label="Origin", invariant_prefix="O", abs_index=0, weight=1.0)
        origin.problem_space = {"description": "Test Problem Space for FIM"}

        # Create a parent node 'A'
        parent = Node(node_id="A", label="A", invariant_prefix="A", abs_index=1, weight=1.0)
        parent.parent = origin

        # Create a child node 'A1'
        child = Node(node_id="A1", label="A1", invariant_prefix="A1", abs_index=2, weight=0.8)
        child.parent = parent

        # Set up children pointers
        origin.children = [parent]
        parent.children = [child]

        # Build the hierarchy and linear order
        hierarchy = FIMHierarchy()
        hierarchy.root = origin
        hierarchy.linear_order = [origin, parent, child]
        self.hierarchy = hierarchy

    def test_build_link_prompts_for_llm(self):
        """
        Test that the multi-turn helper function builds one prompt per parent→child link,
        embedding the origin problem space, parent's label, child's label, and link weight.
        """
        from LanguageAgentTreeSearch.programming.llm_helpers import build_link_prompts_for_llm
        prompts = build_link_prompts_for_llm(self.hierarchy)
        # Expect 2 prompts: one for parent 'A' (child of Origin) and one for child 'A1' (child of A)
        self.assertEqual(len(prompts), 2, "Expected 2 link prompts but got a different count")

        for (link_key, prompt_text) in prompts:
            # Check for header and key fields in each prompt.
            self.assertIn("ORIGIN PROBLEM-SPACE:", prompt_text)
            parent_id, child_id = link_key
            parent_node = next(n for n in self.hierarchy.linear_order if n.node_id == parent_id)
            child_node = next(n for n in self.hierarchy.linear_order if n.node_id == child_id)
            self.assertIn(parent_node.label, prompt_text, "Parent label missing in prompt")
            self.assertIn(child_node.label, prompt_text, "Child label missing in prompt")
            self.assertIn(str(child_node.weight), prompt_text, "Link weight missing in prompt")

    def test_build_combined_links_prompt(self):
        """
        Test that the combined helper produces a single prompt containing all required link data.
        """
        from LanguageAgentTreeSearch.programming.llm_helpers import build_combined_links_prompt
        combined_prompt = build_combined_links_prompt(self.hierarchy)
        # Verify the origin problem space is present.
        self.assertIn("Test Problem Space for FIM", combined_prompt, "Origin problem space metadata missing")

        # Verify that both links appear:
        self.assertIn("Parent=Origin, Child=A", combined_prompt, "Link from Origin to A missing")
        self.assertIn("Parent=A, Child=A1", combined_prompt, "Link from A to A1 missing")

    def test_apply_downward_causal_reasoning(self):
        # Create a mock LLM that returns a fixed explanation based on the prompt
        def mock_llm(prompt):
            return "Mock explanation: " + prompt[:30]  # include the first 30 chars for identification
        
        hierarchy = create_dummy_hierarchy()
        hierarchy.apply_downward_causal_reasoning(mock_llm)
        # Every node with a parent should now have a downward_causal_reasoning attribute
        for node in hierarchy.linear_order:
            if node.parent:
                self.assertTrue(hasattr(node, "downward_causal_reasoning"))
                self.assertIn("Mock explanation", node.downward_causal_reasoning)

class TestLLMLinkPromptsComposite(unittest.TestCase):
    def setUp(self):
        # Build a minimal hierarchy:
        #  1. Origin node with problem_space metadata.
        #  2. Two top-level nodes: A and B (parent = Origin)
        #  3. One sub-node under A: A1 (parent = A)
        self.root = DummyNode("root", "Origin", 1.0)
        self.root.problem_space = {
            "problem": "Test business problem",
            "details": "The origin defines the overall business challenge."
        }
        
        node_a = DummyNode("a", "A", 0.9, parent=self.root)
        node_b = DummyNode("b", "B", 0.8, parent=self.root)
        node_a1 = DummyNode("a1", "A1", 0.8, parent=node_a)
        
        # Define the linear order: root then A, B, then A1.
        self.hierarchy = DummyHierarchy(self.root, [self.root, node_a, node_b, node_a1])
    
    def test_build_link_prompts_for_llm(self):
        """
        Test that for each parent->child link the helper constructs a prompt 
        which includes the origin metadata, parent's label, child's label and link weight.
        """
        prompts = build_link_prompts_for_llm(self.hierarchy)
        # We expect three prompts: Origin->A, Origin->B, and A->A1.
        self.assertEqual(len(prompts), 3)
        
        # Verify the prompt for the first link (Origin -> A)
        key, prompt_text = prompts[0]
        # Check that the prompt contains the origin problem-space data.
        expected_origin_str = json.dumps(self.root.problem_space, indent=2)
        self.assertIn("ORIGIN PROBLEM-SPACE:", prompt_text)
        self.assertIn(expected_origin_str, prompt_text)
        # Check that parent's and child labels and the weight appear.
        self.assertIn('parent category "Origin"', prompt_text)
        self.assertIn('linking to a child "A"', prompt_text)
        self.assertIn("link weight of 0.9", prompt_text)
    
    def test_build_combined_links_prompt(self):
        """
        Test that the combined prompt includes the origin metadata and a bullet list
        of all parent->child links with the correct fields.
        """
        combined_prompt = build_combined_links_prompt(self.hierarchy)
        # Check that it starts with origin metadata.
        self.assertIn("ORIGIN PROBLEM-SPACE:", combined_prompt)
        expected_origin_str = json.dumps(self.root.problem_space, indent=2)
        self.assertIn(expected_origin_str, combined_prompt)
        
        # The combined prompt should list each link in a bullet format.
        # Expected links: Origin->A, Origin->B, and A->A1.
        self.assertIn("- Parent=Origin, Child=A, Weight=0.9", combined_prompt)
        self.assertIn("- Parent=Origin, Child=B, Weight=0.8", combined_prompt)
        self.assertIn("- Parent=A, Child=A1, Weight=0.8", combined_prompt)
        
        # Check that a question header is added at the end.
        self.assertIn("QUESTION:", combined_prompt)

def test_composite_llm_prompts_contains_problem_space():
    """
    Test that the dynamically built link prompts include the origin's problem space 
    metadata along with each link's parent label, child label, and weight.
    """
    # Create a dummy hierarchy from the default data.
    hierarchy = FIMHierarchy.from_json(get_default_hierarchy())
    # Set the root's problem space metadata (FIM is understood as the problem space)
    hierarchy.root.problem_space = {"problem": "FIM as the problem space", "importance": "High"}

    # Build link prompts (each prompt is a tuple (link_key, prompt_text)).
    prompts = build_link_prompts_for_llm(hierarchy)

    # Loop over every generated prompt and verify the composite prompts
    for key, prompt_text in prompts:
        # Check that the origin problem space metadata is included.
        assert "FIM as the problem space" in prompt_text, f"Prompt does not include problem space metadata: {prompt_text}"

        # Retrieve the parent and child nodes using their IDs (link key: (parent_id, child_id))
        parent_node = next((n for n in hierarchy.linear_order if n.node_id == key[0]), None)
        child_node = next((n for n in hierarchy.linear_order if n.node_id == key[1]), None)
        assert parent_node is not None, f"Parent node not found for key: {key}"
        assert child_node is not None, f"Child node not found for key: {key}"

        # Verify that the parent's label, child's label, and weight appear in the prompt text.
        assert parent_node.label in prompt_text, f"Prompt missing parent's label: {prompt_text}"
        assert child_node.label in prompt_text, f"Prompt missing child's label: {prompt_text}"
        weight_str = str(child_node.weight)
        assert weight_str in prompt_text, f"Prompt missing weight: {prompt_text}"

if __name__ == "__main__":
    unittest.main() 