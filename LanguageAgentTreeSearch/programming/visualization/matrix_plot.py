import seaborn as sns
import matplotlib.pyplot as plt
from scipy.cluster.hierarchy import linkage, dendrogram

def plot_theme_matrix(matrix, theme_list):
    """
    Plots the theme relationship matrix with hierarchical clustering.

    Parameters:
    - matrix (np.ndarray): The theme relationship matrix.
    - theme_list (list): List of theme names.
    """
    # Perform hierarchical clustering
    linkage_matrix = linkage(matrix, method='average')
    
    # Create dendrogram and reorder the matrix
    dendro = dendrogram(linkage_matrix, labels=theme_list, no_plot=True)
    idx = dendro['leaves']
    matrix = matrix[np.ix_(idx, idx)]
    reordered_labels = [theme_list[i] for i in idx]
    
    # Plot the heatmap
    plt.figure(figsize=(10, 8))
    sns.heatmap(matrix, xticklabels=reordered_labels, yticklabels=reordered_labels, cmap='viridis')
    plt.xticks(rotation=90)
    plt.title("Recursive Theme Relationships")
    plt.tight_layout()
    plt.show() 