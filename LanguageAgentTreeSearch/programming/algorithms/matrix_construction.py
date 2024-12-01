import numpy as np

def build_theme_matrix(themes):
    """
    Builds a symmetric matrix representing themes and their relationships.

    Parameters:
    - themes (list): Nested list of themes and subthemes.

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
    matrix = np.zeros((n, n))

    # Populate the matrix based on parent-child relationships
    index_map = {theme: idx for idx, theme in enumerate(theme_list)}
    for parent, child in parent_child_pairs:
        i = index_map[parent]
        j = index_map[child]
        matrix[i, j] = 1  # or assign a weight based on your criteria
        matrix[j, i] = 1  # Ensure symmetry

    return matrix, theme_list 