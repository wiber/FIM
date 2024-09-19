import numpy as np
from fim import CentralFIM, FIM
from agent import Agent
import logging
import math

class Node:
    def __init__(self, state, parent=None, value=0):
        self.state = state
        self.parent = parent
        self.children = []
        self.visits = 0
        self.value = value
        self.agent_id = None  # To track which agent created this node

class CentralFIM:
    def __init__(self, num_categories, num_agents):
        self.matrix = [[0 for _ in range(num_categories)] for _ in range(num_categories)]
        self.num_agents = num_agents

    def update(self, agent_id, category_id, value):
        self.matrix[category_id][category_id] = value

    def get_state(self, agent_id):
        return self.matrix

class MAFIM:
    def __init__(self, num_agents, num_categories, model):
        self.agents = [Agent(i, model, self) for i in range(num_agents)]
        self.fim = FIM(num_agents, num_categories)
        self.num_categories = num_categories
        self.model = model
        self.original_prompt = None  # Add this line

    def initialize_agents(self):
        # Initialize with one agent
        self.agents = [Agent(0, self.model, self)]

    def run_mcts(self, prompt, max_iterations):
        self.original_prompt = prompt  # Add this line
        root = Node(prompt)
        for i in range(max_iterations):
            node = self.select(root)
            if not self.is_terminal(node):
                node = self.expand(node)
            reward = self.simulate(node)
            self.backpropagate(node, reward)
        return self.best_solution(root)

    def select(self, node):
        while not self.is_terminal(node):
            if not node.children:
                return node
            node = self.best_uct(node)
        return node

    def best_uct(self, node):
        return max(node.children, key=lambda c: c.value / c.visits + math.sqrt(2 * math.log(node.visits) / c.visits) if c.visits > 0 else float('inf'))

    def is_terminal(self, node):
        return node.visits > 5

    def expand(self, node):
        fim_state = self.fim.get_state(0)
        chosen_agent = self.choose_agent(node.state, 'generate')
        new_state = chosen_agent.generate_solution(self.original_prompt, node.state, fim_state)
        
        evaluating_agent = self.choose_agent(new_state, 'evaluate')
        score = evaluating_agent.evaluate_solution(new_state)
        
        self.share_agent_findings(chosen_agent.agent_id, new_state, score)
        
        child = Node(new_state, parent=node)
        child.agent_id = chosen_agent.agent_id
        child.value = score
        node.children.append(child)
        return child

    def choose_agent(self, current_state, task):
        fim_state = self.fim.get_state(0)
        relevant_category = self.determine_relevant_category(task, current_state)
        best_agent = max(self.agents, key=lambda a: fim_state[a.agent_id][relevant_category])
        return best_agent

    def determine_relevant_category(self, task, current_state):
        # Implement logic to map tasks to FIM categories
        # This could be based on the nature of the task and the current state of the solution
        # For example:
        if task == 'generate':
            return self.find_least_developed_category(current_state)
        elif task == 'optimize':
            return self.find_most_complex_category(current_state)
        elif task == 'test':
            return self.find_most_critical_category(current_state)
        else:
            return 0  # Default to the first category if task is unknown

    def find_least_developed_category(self, current_state):
        # Implement logic to find the least developed part of the solution
        # This could be based on code complexity, completeness, etc.
        return 0  # Placeholder

    def find_most_complex_category(self, current_state):
        # Implement logic to find the most complex part of the solution
        # This could be based on cyclomatic complexity, number of functions, etc.
        return 0  # Placeholder

    def find_most_critical_category(self, current_state):
        # Implement logic to find the most critical part of the solution
        # This could be based on error rates, importance of functionality, etc.
        return 0  # Placeholder

    def share_agent_findings(self, agent_id, findings, score=None):
        # Agent shares its findings with others
        self.shared_memory[agent_id] = findings
        logging.info(f"Agent {agent_id} shared: {findings[:50]}...")
        
        # Other agents process the shared information
        for agent in self.agents:
            if agent.agent_id != agent_id:
                agent.process_shared_info(agent_id, findings)

    def simulate(self, node):
        evaluating_agent = self.choose_agent(node.state, 'evaluate')
        score = evaluating_agent.evaluate_solution(node.state)  # We're not passing tests here
        return score

    def backpropagate(self, node, reward):
        while node:
            node.visits += 1
            node.value += reward
            self.update_fim(node, reward)
            node = node.parent

    def best_solution(self, node):
        best_child = max(node.children, key=lambda c: c.value / c.visits)
        return best_child.state

    def should_spawn_agent(self):
        # More sophisticated logic based on problem complexity
        complexity = self.assess_problem_complexity()
        return len(self.agents) < self.max_agents and complexity > len(self.agents) * 0.2

    def assess_problem_complexity(self):
        # Implement logic to assess problem complexity
        # For now, use a simple heuristic based on prompt length
        return min(1.0, len(self.original_prompt) / 1000)

    def spawn_agent(self):
        new_agent_id = len(self.agents)
        new_agent = Agent(new_agent_id, self.model, self)
        self.agents.append(new_agent)
        logging.info(f"Spawned new agent with ID {new_agent_id}")

    def update_fim(self, node, reward):
        if node.agent_id is not None:
            category = self.determine_relevant_category(node.state)
            self.fim.update(node.agent_id, category, reward)
            logging.info(f"Updated FIM for agent {node.agent_id}, category {category}, reward {reward}")

def run_multi_agent_mcts(dataset, model, language, max_iters, num_agents, num_categories):
    try:
        mafim = MAFIM(num_agents, num_categories, model)
        
        results = []
        for i, item in enumerate(dataset):
            logging.info(f"Processing item {i+1}/{len(dataset)}")
            try:
                prompt = item['prompt']
                logging.info(f"Processing prompt: {prompt[:50]}...")  # Log the start of the prompt
                solution = mafim.run_mcts(prompt, max_iters)
                logging.info(f"Solution generated: {solution[:50]}...")
                results.append({
                    'prompt': prompt,
                    'solution': solution,
                    'evaluation': "MCTS simulation completed"
                })
            except Exception as e:
                logging.error(f"Error processing item {i+1}: {str(e)}", exc_info=True)
                results.append({
                    'prompt': prompt,
                    'solution': f"Error: {str(e)}",
                    'evaluation': "Error during MCTS simulation"
                })

        return results
    except Exception as e:
        logging.error(f"Error in run_multi_agent_mcts: {str(e)}", exc_info=True)
        raise
