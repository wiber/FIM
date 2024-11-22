# LanguageAgentTreeSearch/programming/algorithms/theme_analysis.py
import openai
import os

import time
import datetime
import logging

import numpy as np
import random

# Ensure OpenAI API key is set elsewhere in your project setup
# openai.api_key = os.getenv('OPENAI_API_KEY')

def identify_independent_themes(problem_description, num_themes=5, depth=0, max_depth=2):
    """
    Recursively identifies the most independent themes in the problem space using the LLM.

    Parameters:
    - problem_description (str): The text describing the problem.
    - num_themes (int): Number of themes to identify at each level.
    - depth (int): Current recursion depth.
    - max_depth (int): Maximum depth of recursion.

    Returns:
    - list: A list of themes and their subthemes.
    """
    if depth > max_depth:
        return []

    prompt = f"Identify the {num_themes} most independent themes in the following description. Provide them as a numbered list:\n\n{problem_description}"
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an assistant that identifies themes."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=0.7,
        )
        themes = parse_themes_from_response(response['choices'][0]['message']['content'])
        
        # Recursively identify subthemes for each theme
        all_themes = []
        for theme in themes:
            subthemes = identify_independent_themes(theme, num_themes=num_themes, depth=depth+1, max_depth=max_depth)
            all_themes.append({
                'theme': theme,
                'subthemes': subthemes
            })
        return all_themes
    except Exception as e:
        print(f"Error identifying themes: {e}")
        return []

def generate_subcategories(theme, num_subcategories=5):
    """
    Generates subcategories for a given theme using the LLM.
    """
    prompt = f"For the theme '{theme}', identify {num_subcategories} subcategories. Provide them as a numbered list:"
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an assistant that identifies subcategories."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=0.7,
        )
        subcategories = parse_themes_from_response(response['choices'][0]['message']['content'])
        return subcategories
    except Exception as e:
        print(f"Error generating subcategories for '{theme}': {e}")
        return []

def parse_themes_from_response(response_text):
    """
    Parses the themes from the response text into a list.
    """
    themes = []
    for line in response_text.strip().split('\n'):
        if line.strip():
            # Remove numbering if present
            line = line.strip()
            if '.' in line:
                line = line.split('.', 1)[1].strip()
            themes.append(line)
    return themes

def rank_themes(themes, problem_description):
    """
    Ranks the themes in order of relevance to the problem space from -1 to 1.
    """
    ranked_themes = []
    for theme in themes:
        prompt = f"On a scale from -1 to 1, how relevant is the theme '{theme}' to the following problem description?\n\n{problem_description}\n\nProvide only the numerical score."
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an assistant that evaluates theme relevance."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=5,
            temperature=0,
        )
        score_str = response['choices'][0]['message']['content'].strip()
        try:
            score = float(score_str)
        except ValueError:
            score = 0.0  # Default score if parsing fails
        ranked_themes.append((theme, score))
    ranked_themes.sort(key=lambda x: x[1], reverse=True)
    return ranked_themes

def initialize_symmetric_matrix(themes):
    """
    Initializes a symmetric matrix with weights representing the relationships between themes.
    """
    n = len(themes)
    matrix = np.zeros((n, n))
    for i in range(n):
        for j in range(i+1, n):
            prompt = f"On a scale from 0 to 1, how strongly is the theme '{themes[i]}' related to the theme '{themes[j]}'? Provide only the numerical score."
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an assistant that evaluates theme relationships."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=5,
                temperature=0,
            )
            weight_str = response['choices'][0]['message']['content'].strip()
            try:
                weight = float(weight_str)
            except ValueError:
                weight = 0.0
            matrix[i, j] = weight
            matrix[j, i] = weight  # Ensure symmetry
    return matrix

def select_origin(matrix, themes):
    """
    Selects a random cell as the origin and positions it at (0, 0).
    """
    n = len(themes)
    origin_index = random.randint(0, n - 1)
    # Swap rows and columns in the matrix
    matrix[[0, origin_index]] = matrix[[origin_index, 0]]
    matrix[:, [0, origin_index]] = matrix[:, [origin_index, 0]]
    # Swap themes
    themes[0], themes[origin_index] = themes[origin_index], themes[0]
    return matrix, themes

def sort_submatrix(matrix, themes, start_index=0):
    """
    Recursively sorts the submatrix based on the specified algorithm.
    """
    n = len(themes)
    if start_index >= n - 1:
        return matrix, themes

    # Extract the submatrix from start_index
    submatrix = matrix[start_index:, start_index:]
    first_col = submatrix[1:, 0]

    # Get indices to sort based on the first column (descending order)
    sort_indices = np.argsort(-first_col) + start_index + 1

    # Perform swaps based on sorted indices
    for i in range(len(sort_indices)):
        idx = sort_indices[i]
        position = start_index + i + 1
        if idx != position:
            # Swap rows
            matrix[[position, idx]] = matrix[[idx, position]]
            # Swap columns
            matrix[:, [position, idx]] = matrix[:, [idx, position]]
            # Swap themes
            themes[position], themes[idx] = themes[idx], themes[position]
            # Update sort_indices to reflect swaps
            swap_idx = np.where(sort_indices == position)[0][0]
            sort_indices[swap_idx] = idx

    # Identify the last non-zero entry in the first column
    non_zero_entries = np.nonzero(first_col)[0]
    if len(non_zero_entries) == 0:
        k = start_index
    else:
        k = start_index + non_zero_entries[-1] + 1

    # Recursively sort the next submatrix
    return sort_submatrix(matrix, themes, start_index=k+1)

def generate_timestamp():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

# Example usage:
timestamp = generate_timestamp()

def rank_theme_interactions(theme, subtheme, cutoff_ratio=0.2, num_interactions=None):
    """
    Uses the LLM to rank the top significant directional interactions for a given theme or subtheme based on a cutoff ratio.

    Parameters:
    - theme (str): The main theme.
    - subtheme (str or None): The subtheme, if any.
    - cutoff_ratio (float): The ratio to determine the top interactions (e.g., 0.2 for top 20%).
    - num_interactions (int or None): Number of top interactions to identify. If None, determined by cutoff_ratio.

    Returns:
    - dict: A dictionary of ranked interactions with their weights.
    """
    if num_interactions is None:
        # Determine based on domain knowledge or dynamically
        num_interactions = 5  
    
    if subtheme:
        prompt = (f"For the themes '{theme}' and its subtheme '{subtheme}', identify the top {cutoff_ratio * 100}% most significant **directional** interactions "
                  "from **columns** to **rows** between different tokens or concepts across **all subcategories** related to these themes. "
                  "Ensure that interactions between different subcategories are included. Provide them in a numbered list with associated weights on a scale from 0 to 1.\n\n"
                  "Format:\n"
                  "1. Interaction Description (Column -> Row) - Weight: X.XX\n"
                  "2. ...")
    else:
        prompt = (f"For the theme '{theme}', identify the top {cutoff_ratio * 100}% most significant **directional** interactions "
                  "from **columns** to **rows** between different tokens or concepts across **all subcategories** related to this theme. "
                  "Ensure that interactions between different subcategories are included. Provide them in a numbered list with associated weights on a scale from 0 to 1.\n\n"
                  "Format:\n"
                  "1. Interaction Description (Column -> Row) - Weight: X.XX\n"
                  "2. ...")
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an assistant that identifies and ranks significant **directional** interactions between themes and subthemes."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=600,
            temperature=0.7,
        )
        interactions = parse_ranked_interactions(response['choices'][0]['message']['content'])
        return interactions
    except Exception as e:
        logging.error(f"Error ranking interactions between '{theme}' and '{subtheme}': {e}")
        return {}

def identify_and_rank_interactions(themes, cutoff_ratio=0.2):
    """
    Identifies and ranks the top significant interactions between themes using the LLM based on a cutoff ratio.

    Parameters:
    - themes (list): List of identified themes and subthemes.
    - cutoff_ratio (float): Ratio to determine the top interactions (e.g., 0.2 for top 20%).

    Returns:
    - dict: A dictionary mapping theme pairs to their ranked weights.
    """
    ranked_interactions = {}
    
    for theme in themes:
        if 'subthemes' in theme and theme['subthemes']:
            # Focus on subthemes for ranking interactions
            for subtheme in theme['subthemes']:
                # Dynamically determine the number of interactions based on the cutoff ratio
                total_possible_interactions = 10  # Example: Define based on domain knowledge or dynamically
                num_interactions = max(1, int(total_possible_interactions * cutoff_ratio))
                ranked_interactions.update(rank_theme_interactions(theme['theme'], subtheme['theme'], cutoff_ratio, num_interactions))
        else:
            # Rank interactions for main themes without subthemes
            total_possible_interactions = 10  # Example: Define based on domain knowledge or dynamically
            num_interactions = max(1, int(total_possible_interactions * cutoff_ratio))
            ranked_interactions.update(rank_theme_interactions(theme['theme'], None, cutoff_ratio, num_interactions))
    
    return ranked_interactions

def build_theme_matrix(themes, ranked_interactions):
    """
    Builds a directed matrix representing themes and their ranked relationships.

    Parameters:
    - themes (list): Nested list of themes and subthemes.
    - ranked_interactions (dict): Ranked interactions with weights.

    Returns:
    - matrix (np.ndarray): The constructed theme relationship matrix.
    - theme_list (list): Flattened list of themes in order.
    """
    theme_list = []
    parent_child_pairs = []

    def extract_themes(theme_dict, parent=None):
        theme = theme_dict['theme']
        theme_list.append(theme)
        if parent is not None:
            parent_child_pairs.append((parent, theme))
        for subtheme in theme_dict.get('subthemes', []):
            extract_themes(subtheme, parent=theme)

    for theme_dict in themes:
        extract_themes(theme_dict)

    n = len(theme_list)
    matrix = np.zeros((n, n))  # Directed matrix

    # Populate the matrix based on parent-child relationships
    index_map = {theme: idx for idx, theme in enumerate(theme_list)}
    for parent, child in parent_child_pairs:
        i = index_map[parent]
        j = index_map[child]
        weight = ranked_interactions.get(f"{parent} -> {child}", 1)  # Default weight if not ranked
        matrix[i, j] = weight  # Directed: from parent to child

    # Incorporate other ranked interactions
    for interaction, weight in ranked_interactions.items():
        if "->" in interaction:
            parts = interaction.split("->")
            if len(parts) == 2:
                source, target = parts[0].strip(), parts[1].strip()
                if source in index_map and target in index_map:
                    i, j = index_map[source], index_map[target]
                    matrix[i, j] = weight  # Directed

    return matrix, theme_list

def visualize_network_with_influence(self, title="Network with Influence Propagation"):
    """
    Visualizes the network graph after influence propagation, with node sizes and edge transparency based on influence.

    Parameters:
    - title (str): Title of the graph.

    Returns:
    - None
    """
    G = self._create_networkx_graph(self.matrix)
    pos = nx.spring_layout(G, seed=42)  # For consistent layout

    weights = [G[u][v]['weight'] for u, v in G.edges()]
    nx.draw_networkx_nodes(G, pos, node_color=[G.nodes[n]['color'] for n in G.nodes()], node_size=500)
    nx.draw_networkx_edges(G, pos, arrowstyle='->', arrowsize=10, width=[w * 2 for w in weights], alpha=0.7)
    nx.draw_networkx_labels(G, pos, font_size=10, font_family="sans-serif")

    plt.title(title)
    plt.axis('off')
    plt.show()

def _create_networkx_graph(self, matrix):
    """
    Creates a directed NetworkX graph from the matrix and node colors.

    Parameters:
    - matrix (np.ndarray): The relationship matrix.

    Returns:
    - G (networkx.DiGraph): Directed graph representing the matrix.
    """
    G = nx.DiGraph()
    for i in range(self.n):
        G.add_node(self.labels[i], color=self.node_colors.get(self.labels[i], 'blue'))
    for i in range(self.n):
        for j in range(self.n):
            if matrix[i][j] > self.threshold:
                G.add_edge(self.labels[i], self.labels[j], weight=matrix[i][j])
    return G

def visualize_colored_matrix(self, matrix, theme_list, title="Fractal Identity Matrix with Categories"):
    """
    Visualizes the matrix as a heatmap, including inter-category connections and using meta-vector information for color assignment.

    Parameters:
    - matrix (np.ndarray): The transformed theme relationship matrix.
    - theme_list (list): List of theme names corresponding to matrix indices.
    - title (str): Title of the heatmap.

    Returns:
    - None
    """
    plt.figure(figsize=(12, 10))
    ax = sns.heatmap(matrix, xticklabels=theme_list, yticklabels=theme_list, cmap='viridis', annot=True, fmt=".2f", linewidths=.5)
    plt.title(title)
    plt.xlabel("Themes")
    plt.ylabel("Themes")
    plt.xticks(rotation=90)
    plt.yticks(rotation=0)

    # Highlight submatrices if needed
    boundaries = self.identify_submatrix_boundaries(matrix, max_depth=2)
    for boundary in boundaries:
        start, end = boundary
        rect = Rectangle((start, start), end - start, end - start, fill=False, edgecolor='red', lw=2)
        ax.add_patch(rect)

    # Adjust layout to accommodate labels
    try:
        plt.tight_layout()
    except UserWarning as e:
        logging.warning(f"Tight layout not applied: {e}")
    plt.show()