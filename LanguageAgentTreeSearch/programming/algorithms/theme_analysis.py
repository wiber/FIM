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

def identify_independent_themes(problem_description, num_themes=5, depth=0, max_depth=2, prompt_prefix=None):
    """
    Identifies the most independent themes in the problem space using the LLM.
    Now includes an optional 'prompt_prefix' for added context or constraints.
    """
    if prompt_prefix is None:
        prompt_prefix = ""

    prompt = (
        f"{prompt_prefix}\n\n"
        f"Identify the {num_themes} most independent themes in the following problem description. "
        f"Provide them as a numbered list:\n\n{problem_description}"
    )
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an assistant that identifies themes."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=150,
            temperature=0.7,
        )
        themes = parse_themes_from_response(response['choices'][0]['message']['content'])
        return themes
    except Exception as e:
        print(f"Error identifying themes: {e}")
        return []

def generate_subcategories(theme, num_subcategories=5, focus_on_fim=False):
    """
    Generates subcategories for a given theme using the LLM.
    If 'focus_on_fim' is True, the prompt asks for fractal-friendly subdivisions.
    """
    if focus_on_fim:
        prefix = (
            f"You are building a fractal structure of knowledge. "
            f"Each subcategory must be uniquely distinct yet collectively exhaustive "
            f"for the theme '{theme}'. "
        )
    else:
        prefix = ""

    prompt = (
        f"{prefix}For the theme '{theme}', identify {num_subcategories} subcategories. "
        f"Provide them as a numbered list:"
    )

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
    Very simplistic parser that expects lines like:
    1) ThemeOne
    2) ThemeTwo
    ...
    Return them as a list of strings.
    """
    lines = response_text.strip().split("\n")
    themes = []
    for line in lines:
        # Example: "1) Something"
        # Or just "Something"
        line = line.strip()
        if line.startswith(("-", "*", "•", "1)", "2)", "3)")):
            # remove leading markers
            line = line[line.find(")") + 1:].strip()
        if line:
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

def estimate_hpc_cost(total_subblocks, accessed_subblocks):
    """
    Returns (cost, skip_factor) based on how many sub-blocks are accessed vs total.
    cost = fraction_of_blocks_accessed, skip_factor = 1 - cost.
    """
    if total_subblocks == 0:
        return 0.0, 1.0
    cost = accessed_subblocks / total_subblocks
    skip_factor = 1.0 - cost
    return cost, skip_factor

def print_matrix_with_labels(matrix, labels):
    """
    Simple textual printout of the matrix with row/column labels.
    """
    if len(labels) != matrix.shape[0]:
        print("Label count does not match matrix dimension.")
        return

    print("Matrix (upper row is labels):")
    print("       ", "  ".join(lbl[:6] for lbl in labels))
    for i, row in enumerate(matrix):
        row_str = "  ".join(f"{val:.2f}" for val in row)
        print(f"{labels[i][:6]}  {row_str}")

# Example usage:
timestamp = generate_timestamp()