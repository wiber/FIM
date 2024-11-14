import hashlib
import json
import os
import numpy as np
import openai
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import networkx as nx
import logging
import time

cache_dir = 'cache/'

def get_cache_filename(prompt):
    md5_hash = hashlib.md5(prompt.encode()).hexdigest()
    return os.path.join(cache_dir, f"{md5_hash}.json")

def cached_llm_call(prompt):
    os.makedirs(cache_dir, exist_ok=True)
    cache_file = get_cache_filename(prompt)
    if os.path.isfile(cache_file):
        with open(cache_file, 'r') as f:
            response = json.load(f)
    else:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        with open(cache_file, 'w') as f:
            json.dump(response, f)
    return response 

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(message)s')

def swap_rows_columns(matrix, i, j):
    matrix[[i, j], :] = matrix[[j, i], :]
    matrix[:, [i, j]] = matrix[:, [j, i]]
    return matrix

def recursive_sort_submatrix(matrix, start_idx, n, depth, max_depth):
    if depth > max_depth or start_idx >= n - 1:
        return matrix

    logging.info(f"Recursion Depth {depth}: Sorting submatrix starting at index {start_idx}")
    unsorted_indices = list(range(start_idx + 1, n))
    unsorted_indices.sort(key=lambda x: matrix[start_idx][x], reverse=True)

    for idx in unsorted_indices:
        if matrix[start_idx][idx] > 0:
            logging.info(f"Recursion Depth {depth}: Swapping index {start_idx + 1} with {idx}")
            matrix = swap_rows_columns(matrix, start_idx + 1, idx)
            matrix = recursive_sort_submatrix(matrix, start_idx + 1, n, depth + 1, max_depth)
        else:
            logging.info(f"Recursion Depth {depth}: No significant connection for index {idx}")
            break

    return matrix

def symmetrical_matrix_transformation(matrix, origin_index, depth=0, max_depth=2):
    n = len(matrix)
    if depth > max_depth:
        return matrix

    logging.info(f"Recursion Depth {depth}: Moving origin index {origin_index} to (0,0)")
    matrix = swap_rows_columns(matrix, 0, origin_index)

    sorted_indices = [0]
    unsorted_indices = list(range(1, n))

    while unsorted_indices:
        last_sorted = sorted_indices[-1]
        unsorted_indices.sort(key=lambda x: matrix[last_sorted][x], reverse=True)

        next_index = unsorted_indices.pop(0)
        logging.info(f"Recursion Depth {depth}: Swapping index {len(sorted_indices)} with {next_index}")
        matrix = swap_rows_columns(matrix, len(sorted_indices), next_index)
        sorted_indices.append(next_index)

        matrix = recursive_sort_submatrix(matrix, len(sorted_indices) - 1, n, depth + 1, max_depth)

    return matrix

def parse_themes_from_response(response_text):
    themes = []
    lines = response_text.split('\n')
    for line in lines:
        if line.strip():
            parts = line.split('. ', 1)
            if len(parts) == 2:
                themes.append(parts[1].strip())
    return themes

def identify_independent_themes(problem_description, num_themes=5, depth=0, max_depth=2):
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
        
        all_themes = []
        for theme in themes:
            subthemes = identify_independent_themes(theme, num_themes=num_themes, depth=depth+1, max_depth=max_depth)
            all_themes.append({
                'theme': theme,
                'subthemes': subthemes
            })
        return all_themes
    except Exception as e:
        logging.error(f"Error identifying themes: {e}")
        return []

def build_theme_matrix(themes):
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
    matrix = np.zeros((n, n))

    index_map = {theme: idx for idx, theme in enumerate(theme_list)}
    for parent, child in parent_child_pairs:
        i = index_map[parent]
        j = index_map[child]
        matrix[i, j] = 1  # Assign weight as needed
        matrix[j, i] = 1  # Ensure symmetry

    return matrix, theme_list

def calculate_metrics(matrix, threshold=0.5):
    metrics = {}
    
    # Signal-to-Noise Ratio (SNR)
    signal = np.sum(matrix[matrix >= threshold])
    noise = np.sum(matrix[matrix < threshold])
    metrics['SNR'] = signal / (noise + 1e-9)
    
    # Entropy
    total = np.sum(matrix)
    probabilities = matrix / (total + 1e-9)
    probabilities = probabilities[matrix > 0]
    entropy = -np.sum(probabilities * np.log(probabilities + 1e-9))
    metrics['Entropy'] = entropy
    
    # Clustering Coefficient
    G = nx.from_numpy_array(matrix >= threshold)
    clustering = nx.average_clustering(G)
    metrics['Clustering Coefficient'] = clustering
    
    # Degree Centrality
    centrality = nx.degree_centrality(G)
    metrics['Degree Centrality'] = centrality
    
    return metrics

def plot_recursive_matrix(matrix, theme_list, max_depth=2):
    plt.figure(figsize=(12, 10))
    sns.heatmap(matrix, xticklabels=theme_list, yticklabels=theme_list, cmap='viridis', annot=True, fmt=".2f")
    
    boundaries = identify_submatrix_boundaries(matrix, theme_list, max_depth)
    for boundary in boundaries:
        start, end = boundary
        plt.gca().add_patch(Rectangle((start, start), end - start, end - start, fill=False, edgecolor='red', lw=2))

    plt.title("Recursive Theme Relationship Matrix")
    plt.xlabel("Themes")
    plt.ylabel("Themes")
    plt.xticks(rotation=90)
    plt.yticks(rotation=0)
    plt.tight_layout()
    plt.show()

def identify_submatrix_boundaries(matrix, theme_list, max_depth):
    boundaries = []
    n = len(matrix)
    current = 0
    for depth in range(max_depth):
        connections = np.sum(matrix[current:n, current:n], axis=0)
        if len(connections) == 0:
            break
        next_boundary = current + len(connections)
        boundaries.append((current, next_boundary))
        current = next_boundary
        if current >= n:
            break
    return boundaries

def plot_metrics_over_steps(metrics_history):
    steps = range(1, len(metrics_history) + 1)
    snr = [metrics['SNR'] for metrics in metrics_history]
    entropy = [metrics['Entropy'] for metrics in metrics_history]
    clustering = [metrics['Clustering Coefficient'] for metrics in metrics_history]
    
    plt.figure(figsize=(12, 8))
    plt.plot(steps, snr, label='SNR', marker='o')
    plt.plot(steps, entropy, label='Entropy', marker='s')
    plt.plot(steps, clustering, label='Clustering Coefficient', marker='^')
    
    plt.xlabel('Recursion Steps', fontsize=14)
    plt.ylabel('Metric Values', fontsize=14)
    plt.title('Metrics Over Recursion Steps', fontsize=16)
    plt.legend(fontsize=12)
    plt.grid(True)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    # Define your problem description
    problem_description = """
    Your comprehensive problem description goes here. It should be detailed enough for the LLM to extract meaningful themes and subthemes.
    """

    # Identify themes using LLM
    themes = identify_independent_themes(problem_description, num_themes=5, depth=0, max_depth=2)
    logging.info("Identified Themes and Subthemes:")
    for theme in themes:
        logging.info(theme)

    # Build the relationship matrix
    matrix, theme_list = build_theme_matrix(themes)
    logging.info("Initial Theme Relationship Matrix:")
    print(matrix)

    # Transform the matrix with recursive symmetrical sorting
    transformed_matrix = symmetrical_matrix_transformation(matrix, origin_index=0, depth=0, max_depth=2)
    logging.info("Transformed Matrix:")
    print(transformed_matrix)

    # Plot the recursive matrix
    plot_recursive_matrix(transformed_matrix, theme_list, max_depth=2)

    # Calculate metrics
    metrics = calculate_metrics(transformed_matrix, threshold=0.5)
    logging.info("Calculated Metrics:")
    for key, value in metrics.items():
        if isinstance(value, dict):
            logging.info(f"{key}:")
            for sub_key, sub_val in value.items():
                logging.info(f"  {sub_key}: {sub_val:.2f}")
        else:
            logging.info(f"{key}: {value:.2f}")

    # Collect metrics over recursion steps
    metrics_history = []
    for depth in range(1, 3):
        transformed = symmetrical_matrix_transformation(matrix, origin_index=0, depth=0, max_depth=depth)
        current_metrics = calculate_metrics(transformed, threshold=0.5)
        metrics_history.append(current_metrics)
    
    # Plot metrics over steps
    plot_metrics_over_steps(metrics_history)