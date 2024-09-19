import logging

class Agent:
    def __init__(self, agent_id, model, mafim):
        self.agent_id = agent_id
        self.model = model
        self.mafim = mafim
        self.knowledge_base = {}  # Agent's personal knowledge base

    def generate_solution(self, original_prompt, current_state, fim_state):
        context = f"""
Original Prompt:
{original_prompt}

Current State:
{current_state}

FIM State:
{fim_state}

Shared Knowledge:
{self.knowledge_base}

Generate a solution based on the above information:
"""
        solution = self.model.generate(context)
        return solution

    def perform_subtask(self, subtask, state):
        # Implement logic to perform a specific subtask
        # This could involve generating code, optimizing existing code, or running tests
        return state

    def identify_subtasks(self, state):
        # Implement logic to identify potential subtasks based on the current state
        # This could involve analyzing the code structure, identifying optimization opportunities, etc.
        return []  # Placeholder

    def evaluate_solution(self, solution, tests=None):
        # If tests are not provided, we'll use a generic evaluation
        if tests is None:
            context = f"""
Solution:
{solution}

Evaluate the above solution on a scale of 0 to 1, where 0 is completely incorrect and 1 is perfect.
Only return the numeric score.
"""
        else:
            context = f"""
Solution:
{solution}

Tests:
{tests}

Evaluate the above solution based on the given tests on a scale of 0 to 1, where 0 is completely incorrect and 1 is perfect.
Only return the numeric score.
"""
        evaluation = self.model.generate(context)
        try:
            score = float(evaluation)
            return max(0, min(score, 1))  # Ensure score is between 0 and 1
        except ValueError:
            logging.error(f"Agent {self.agent_id} failed to generate a valid score")
            return 0  # Default to 0 if we can't parse the score

import logging

class Agent:
    def __init__(self, agent_id, model, mafim):
        self.agent_id = agent_id
        self.model = model
        self.mafim = mafim
        self.knowledge_base = {}  # Agent's personal knowledge base

    def generate_solution(self, original_prompt, current_state, fim_state):
        # Use the LLM to generate a solution based on the prompt, state, and shared knowledge
        context = f"Original prompt: {original_prompt}\nCurrent state: {current_state}\nFIM state: {fim_state}\n"
        context += f"Shared knowledge: {self.knowledge_base}"
        solution = self.model.generate(context)
        return solution

    def process_shared_info(self, source_agent_id, info):
        # Process and integrate shared information from other agents
        self.knowledge_base[source_agent_id] = info
        logging.info(f"Agent {self.agent_id} processed info from Agent {source_agent_id}")

    def evaluate_solution(self, solution, tests=None):
        # If tests are not provided, we'll use a generic evaluation
        if tests is None:
            context = f"""
Solution:
{solution}

Evaluate the above solution on a scale of 0 to 1, where 0 is completely incorrect and 1 is perfect.
Only return the numeric score.
"""
        else:
            context = f"""
Solution:
{solution}

Tests:
{tests}

Evaluate the above solution based on the given tests on a scale of 0 to 1, where 0 is completely incorrect and 1 is perfect.
Only return the numeric score.
"""
        evaluation = self.model.generate(context)
        try:
            score = float(evaluation)
            return max(0, min(score, 1))  # Ensure score is between 0 and 1
        except ValueError:
            logging.error(f"Agent {self.agent_id} failed to generate a valid score")
            return 0  # Default to 0 if we can't parse the score
