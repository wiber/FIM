import numpy as np

class FractalIdentityMatrix:
    def __init__(self, themes_dict):
        """
        themes_dict: A dictionary where each key is a theme
        and its value is a list of subcategories.
        """
        self.themes_dict = themes_dict
        self.labels = []
        self.matrix = None
        self.build_fim()

    def build_fim(self):
        """
        Constructs the Fractal Identity Matrix, then fills
        the upper-right portion of the matrix with approximately
        15% random weights, creating a sparser matrix.
        """
        # Collect all labels (themes and subcategories)
        for theme, subcategories in self.themes_dict.items():
            self.labels.append(theme)
            self.labels.extend(subcategories)

        size = len(self.labels)
        self.matrix = np.zeros((size, size))

        # Example relationship-building (identity & theme-subcat links)
        np.fill_diagonal(self.matrix, 1)
        index_map = {label: idx for idx, label in enumerate(self.labels)}
        for theme, subcategories in self.themes_dict.items():
            theme_idx = index_map[theme]
            for subcat in subcategories:
                subcat_idx = index_map[subcat]
                # A basic bidirectional weight for theme→subcat
                self.matrix[theme_idx, subcat_idx] = 0.5
                self.matrix[subcat_idx, theme_idx] = 0.5

        # Fill the upper-right region with random values at ~15% sparsity
        for i in range(size):
            for j in range(size):
                if j > i:
                    # Only fill random weight 15% of the time
                    if np.random.random() < 0.15:
                        self.matrix[i, j] = np.random.random()

    def get_matrix(self):
        return self.matrix

    def get_labels(self):
        return self.labels 