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
