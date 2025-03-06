# fim.py

import numpy as np
import logging

class CentralFIM:
    def __init__(self, num_categories, num_agents):
        self.matrix = np.zeros((num_categories, num_categories))
        self.agent_vectors = np.zeros((num_agents, num_categories))

    def update(self, agent_id, category_id, value):
        self.agent_vectors[agent_id, category_id] = value
        self.matrix[category_id] = np.mean(self.agent_vectors[:, category_id])

    def get_state(self, category_id):
        return self.matrix[category_id]

    def evaluate_state(self, state, agent_id):
        return np.dot(state, self.agent_vectors[agent_id])
    
    def backpropagate(self, node, reward):
        while node:
            node.visits += 1
            node.value += reward
            # Update FIM based on this path's performance
            self.update_fim(node, reward)
            node = node.parent

    def update_fim(self, node, reward):
        if node.agent_id is not None:
            category = self.determine_relevant_category(node.state)
            self.fim.update(node.agent_id, category, reward)


class FIM:
    def __init__(self, num_agents, num_categories):
        self.matrix = [[0.1 for _ in range(num_categories)] for _ in range(num_agents)]

    def update(self, agent_id, category, reward):
        self.matrix[agent_id][category] += reward
        # Normalize the row
        row_sum = sum(self.matrix[agent_id])
        self.matrix[agent_id] = [val / row_sum for val in self.matrix[agent_id]]

    def get_state(self, level=0):
        return self.matrix


class Node:
    def __init__(self, state, parent=None, value=0):
        self.state = state
        self.parent = parent
        self.children = []
        self.visits = 0
        self.value = value
        self.agent_id = None  # Add this to track which agent created this node


class FIMHierarchy:
    # ... existing methods ...

    def _find_node_by_id(self, node_id):
        """
        Helper method to locate a node in the linear_order by its node_id.
        """
        for node in self.linear_order:
            if node.node_id == node_id:
                return node
        return None

    def apply_downward_causal_reasoning(self, llm_function):
        """
        For every parent → child link in the hierarchy,
        use the helper to build a prompt that combines:
          - The origin node's problem-space metadata,
          - The parent category's label,
          - The child node's label,
          - The link weight.
 
        Then, call the provided llm_function (which may be a mock for testing)
        on each prompt and store the response on the child node.
        """
        from llm_helpers import build_link_prompts_for_llm
        link_prompts = build_link_prompts_for_llm(self)
        for (link_key, prompt_text) in link_prompts:
            llm_response = llm_function(prompt_text)
            # link_key is a tuple (parent_id, child_id)
            child_node = self._find_node_by_id(link_key[1])
            if child_node is not None:
                child_node.downward_causal_reasoning = llm_response
                
        # Optionally, return a mapping of link_key -> response
        return {lk: self._find_node_by_id(lk[1]).downward_causal_reasoning for lk, _ in link_prompts}

    def build_link_prompts_for_llm(self):
        """
        Construct a list of (link_key, prompt_text) tuples for every parent→child link.
        Each prompt includes the origin's problem-space metadata, parent's label, child's label, and the link weight.
        """
        import json
        origin_data = getattr(self.root, "problem_space", {})
        origin_json = json.dumps(origin_data, indent=2) if isinstance(origin_data, dict) else str(origin_data)

        prompts = []
        for node in self.linear_order:
            if node.parent is None:
                continue

            parent_label = node.parent.label
            child_label = node.label
            link_weight = node.weight

            prompt_text = (
                f"ORIGIN PROBLEM-SPACE:\n{origin_json}\n\n"
                f"We have a parent category \"{parent_label}\" linking to a child \"{child_label}\" "
                f"with a link weight of {link_weight}.\n\n"
                "QUESTION:\n"
                f"How does the origin's problem space define or explain this link from parent to child with weight={link_weight}?"
            )

            key = (node.parent.node_id, node.node_id)
            prompts.append((key, prompt_text))
        return prompts

    def build_combined_links_prompt(self):
        """
        Construct a single, combined prompt that includes all parent→child links.
        """
        import json
        origin_data = getattr(self.root, "problem_space", {})
        origin_json = json.dumps(origin_data, indent=2) if isinstance(origin_data, dict) else str(origin_data)

        lines = []
        lines.append("ORIGIN PROBLEM-SPACE:")
        lines.append(origin_json)
        lines.append("\nWe have the following parent->child links:")

        for node in self.linear_order:
            if node.parent:
                lines.append(f"- Parent={node.parent.label}, Child={node.label}, Weight={node.weight}")

        lines.append("\nQUESTION:\nFor each parent->child link above, how does the origin's problem space define or explain it?")
        return "\n".join(lines)

    def apply_downward_causal_reasoning(self, llm_function):
        """
        For each parent→child link in the hierarchy, call the llm_function with a generated prompt.
        Attach the LLM response to the child node's downward_causal_reasoning attribute.
        """
        prompts = self.build_link_prompts_for_llm()
        for link_key, prompt_text in prompts:
            response = llm_function(prompt_text)
            node = self._find_node_by_id(link_key[1])
            if node:
                node.downward_causal_reasoning = response

    def propagate_combined_metadata(self, node, origin_metadata=None):
        """
        Recursively propagates composite causal metadata for LLM integration.
        The composite metadata now includes:
          - The origin's problem-space metadata (seeded with defaults if missing).
          - A structured link object containing:
                • The parent's label,
                • The child's label,
                • The influence strength (child.weight),
          - A prompt string that clearly asks:
                "Based on the origin definition, how does the category [parent] define its causal relationship to [child] given an influence strength of [weight]?"
        For the root node, causal_inference is set to an empty dict.
        """
        if origin_metadata is None:
            origin_metadata = getattr(self.root, "problem_space", {})
            if not origin_metadata:
                # Expanded origin metadata with an explicit process definition.
                origin_metadata = {
                    "description": "Funded Information Model (FIM) problem space for optimizing hierarchical decision making.",
                    "objectives": [
                        "Optimize HPC cost",
                        "Maintain hierarchical clarity",
                        "Ensure accurate causal propagation",
                        "Establish transparent cause–effect relationships"
                    ],
                    "constraints": [
                        "Limited computational resources",
                        "Real-time performance requirements"
                    ],
                    "cost_model": {
                        "per_inference": 0.01,
                        "daily_budget": 1000
                    },
                    "metrics": [
                        "skip_factor",
                        "ordering_validation",
                        "submatrix_bounds"
                    ],
                    "process_definition": "The FIM process integrates hierarchical causal reasoning with LLM-based explanation. "
                                          "It organizes categories and subcategories to reduce redundant inferences while ensuring that each causal link "
                                          "is transparent and traceable.",
                    "process_role": "Origin defines the overall problem space and provides context for establishing the causal influence "
                                    "between parent categories and their subcategories."
                }
                self.root.problem_space = origin_metadata
        if node.parent is None:
            # For the root node, no causal metadata is needed.
            node.causal_inference = {}
        for child in node.children:
            # For debugging: log the parent's and child's actual values.
            print(f"DEBUG: Propagating metadata -- Parent label: '{node.label}', Child label: '{child.label}', Weight: {child.weight}")

            # Build an enhanced prompt using actual node values and origin metadata.
            prompt_text = (
                f"Given the problem space defined by:\n"
                f"  Description: {origin_metadata.get('description', 'No description provided')}\n"
                f"  Objectives: {origin_metadata.get('objectives', 'N/A')}\n"
                f"  Constraints: {origin_metadata.get('constraints', 'N/A')}\n"
                f"  Cost Model: {origin_metadata.get('cost_model', 'N/A')}\n"
                f"  Metrics: {origin_metadata.get('metrics', 'N/A')}\n\n"
                f"Please explain how the category '{node.label}' causally influences its subcategory '{child.label}' "
                f"with an influence strength of {child.weight}."
            )

            # Assign the composite causal metadata to the child using the proper values.
            child.causal_inference = {
                "cause_effect_relation": {
                    "cause": node.label,
                    "effect": child.label,
                    "influence_strength": child.weight
                },
                "process_metadata": origin_metadata,
                "prompt": prompt_text
            }
            self.propagate_combined_metadata(child, origin_metadata)

    def apply_llm_to_composite_metadata(self, llm_function):
        """
        For every non-root node with composite metadata, call the llm_function using its prompt
        and store the LLM response in the composite metadata under 'llm_response'.
        """
        for node in self.linear_order:
            if not node.parent:
                continue
            # Try to fetch from the updated attribute; fall back if necessary.
            ci = getattr(node, "causal_inference", None)
            if ci is None:
                ci = getattr(node, "causal_inference_links", None)
            if ci is None:
                continue
            prompt = ci.get("prompt")
            if prompt:
                llm_response = llm_function(prompt)
                ci["llm_response"] = llm_response
