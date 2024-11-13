# LanguageAgentTreeSearch/programming/algorithms/theme_analysis.py

from openai import OpenAI

client = OpenAI()
import numpy as np
import random

# Ensure OpenAI API key is set elsewhere in your project setup
# openai.api_key = os.getenv('OPENAI_API_KEY')

def identify_independent_themes(problem_description, num_themes=5):
    """
    Identifies the most independent themes in the problem space using the LLM.
    """
    prompt = f"Identify the {num_themes} most independent themes in the following problem description. Provide them as a numbered list:\n\n{problem_description}"
    response = client.completions.create(engine="text-davinci-003",
    prompt=prompt,
    max_tokens=150,
    n=1,
    temperature=0.5)
    themes_text = response.choices[0].text.strip()
    themes = parse_themes_from_response(themes_text)
    return themes

def parse_themes_from_response(response_text):
    """
    Parses the LLM response to extract a list of themes.
    """
    themes = []
    lines = response_text.split('\n')
    for line in lines:
        if line.strip():
            # Remove numbering if present
            theme = line.lstrip('0123456789.- ').strip()
            themes.append(theme)
    return themes

def rank_themes(themes, problem_description):
    """
    Ranks the themes in order of relevance to the problem space from -1 to 1.
    """
    ranked_themes = []
    for theme in themes:
        prompt = f"On a scale from -1 to 1, how relevant is the theme '{theme}' to the following problem description?\n\n{problem_description}\n\nProvide only the numerical score."
        response = client.completions.create(engine="text-davinci-003",
        prompt=prompt,
        max_tokens=5,
        n=1,
        temperature=0)
        score_str = response.choices[0].text.strip()
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
            response = client.completions.create(engine="text-davinci-003",
            prompt=prompt,
            max_tokens=5,
            n=1,
            temperature=0)
            weight_str = response.choices[0].text.strip()
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