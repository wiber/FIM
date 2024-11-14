import numpy as np

class FractalIdentityMatrix:
    def __init__(self, themes_dict):
        """
        themes_dict: A dictionary where each key is a theme and its value is a list of subcategories.
        """
        self.themes_dict = themes_dict
        self.labels = []
        self.matrix = None
        self.build_fim()

    def build_fim(self):
        """
        Constructs the Fractal Identity Matrix.
        """
        # Collect all labels (themes and subcategories)
        for theme, subcategories in self.themes_dict.items():
            self.labels.append(theme)
            self.labels.extend(subcategories)

        size = len(self.labels)
        self.matrix = np.zeros((size, size))

        # Build relationships in the matrix
        index_map = {label: idx for idx, label in enumerate(self.labels)}

        # Set identity for each element
        np.fill_diagonal(self.matrix, 1)

        # Connect themes to their subcategories
        for theme, subcategories in self.themes_dict.items():
            theme_idx = index_map[theme]
            for subcat in subcategories:
                subcat_idx = index_map[subcat]
                # Set bidirectional relationship
                self.matrix[theme_idx, subcat_idx] = 0.5
                self.matrix[subcat_idx, theme_idx] = 0.5

        # Optionally, connect subcategories within the same theme
        for subcategories in self.themes_dict.values():
            for i in range(len(subcategories)):
                for j in range(i + 1, len(subcategories)):
                    idx_i = index_map[subcategories[i]]
                    idx_j = index_map[subcategories[j]]
                    self.matrix[idx_i, idx_j] = 0.3  # Adjust weight as needed
                    self.matrix[idx_j, idx_i] = 0.3

    def get_matrix(self):
        return self.matrix

    def get_labels(self):
        return self.labels 