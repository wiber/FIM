"""
LLM Helpers for the Fractal Identity Map (FIM) project.

This module provides:
  - actual_llm_function: A function that simulates an LLM response.
  - build_link_prompts_for_llm: Build multi-turn prompts from the hierarchy.
  - build_combined_links_prompt: Build a combined prompt for LLM evaluation.
"""

import json
import re
import random

def actual_llm_function(prompt: str) -> str:
    """
    Simulated actual LLM function.
    
    This stub function returns a JSON string simulating an LLM response.
    It includes a randomly suggested weight along with an explanation.
    """
    # Simulate a weight suggestion between 0.7 and 1.0.
    suggested_weight = round(random.uniform(0.7, 1.0), 2)
    explanation = (
        "Simulated response: Based on the causal reasoning provided, "
        f"the system suggests a new weight of {suggested_weight}."
    )
    response = {
        "suggested_weight": suggested_weight,
        "explanation": explanation
    }
    return json.dumps(response)

def build_link_prompts_for_llm(hierarchy):
    """
    Build an iterable of individual LLM prompts for each causal link in the hierarchy.
    
    Each element is a tuple (link_key, prompt) where link_key is a unique identifier
    (e.g., parent's label + '->' + child's label).
    """
    prompts = []
    for node in hierarchy.linear_order:
        if not node.parent:
            continue
        # Obtain composite metadata; try both attribute names.
        ci = getattr(node, "causal_inference", None)
        if ci is None:
            ci = getattr(node, "causal_inference_links", None)
        if ci is None:
            continue
        prompt = ci.get("prompt")
        if prompt:
            link_key = f"{node.parent.label}->{node.label}"
            prompts.append((link_key, prompt))
    return prompts

def build_combined_links_prompt(hierarchy):
    """
    Build a single prompt by combining all individual link prompts,
    useful for multi-turn LLM interactions.
    
    Returns a string that concatenates individual prompts with clear delimiters.
    """
    prompts = build_link_prompts_for_llm(hierarchy)
    combined_prompt = "Combined LLM Link Prompt:\n"
    for link_key, prompt in prompts:
        combined_prompt += f"--- Link: {link_key} ---\n{prompt}\n\n"
    return combined_prompt

def build_composite_prompts_for_llm(hierarchy):
    """
    Build a composite dictionary for each parent->child link that includes:
      - The origin metadata (as a JSON string)
      - The parent's label
      - The child's label
      - The link weight
      - The downward causal reasoning explanation (if available)
      
    Returns a dictionary keyed by (parent_id, child_id).
    """
    # Get the origin metadata (from the "problem_space" attribute of the root node)
    origin_data = getattr(hierarchy.root, "problem_space", {})
    origin_json = json.dumps(origin_data, indent=2) if isinstance(origin_data, dict) else str(origin_data)
    
    composites = {}
    for node in hierarchy.linear_order:
        if node.parent:
            key = (node.parent.node_id, node.node_id)
            composites[key] = {
                "origin_metadata": origin_json,
                "parent_label": node.parent.label,
                "child_label": node.label,
                "link_weight": node.weight,
                "llm_explanation": getattr(node, "downward_causal_reasoning", "No explanation")
            }
    return composites

def attach_llm_composites(hierarchy):
    """
    For each parent->child link in the hierarchy, build the composite LLM prompt
    (using the origin's problem-space metadata and link details) and attach it to the child node.
    """
    prompts = build_link_prompts_for_llm(hierarchy)
    for (link_key, prompt_text) in prompts:
        child_node = hierarchy._find_node_by_id(link_key[1])
        if child_node:
            child_node.llm_composite = prompt_text

if __name__ == "__main__":
    # Quick test of the function.
    test_prompt = (
        "Given the problem space and causal link, explain how the Origin defines the causal identity..."
    )
    print("Simulated LLM response:", actual_llm_function(test_prompt))

"""
Dummy implementation of LLM helper functions.
Replace this with actual API calls when ready.
"""

def actual_llm_function(prompt):
    # Simulate LLM processing by printing the prompt
    print("LLM Prompt Received:", prompt)
    # Return a dummy dictionary that updates composite metadata
    return {
        "llm_response": "Dummy response based on prompt",
        "analysis": "Dummy analysis"
    } 