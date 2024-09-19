import networkx as nx
import numpy as np
import csv
import os
from anthropic import Anthropic

def create_ai_workflow_graph():
    G = nx.Graph()
    G.add_edges_from([
        ('DataPreprocessor', 'FeatureExtractor'),
        ('FeatureExtractor', 'ModelTrainer'),
        ('ModelTrainer', 'ModelEvaluator'),
        ('ModelEvaluator', 'Deployer'),
        ('Deployer', 'MonitoringTool')
    ])
    return G

def graph_to_adjacency_matrix(G):
    return nx.adjacency_matrix(G).toarray()

def graph_to_incidence_matrix(G):
    return nx.incidence_matrix(G).toarray()

def save_matrix_to_csv(matrix, row_labels, col_labels, filename):
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([''] + list(col_labels))
        for label, row in zip(row_labels, matrix):
            writer.writerow([label] + list(row.astype(int)))

def read_matrix_from_csv(filename):
    with open(filename, 'r') as f:
        reader = csv.reader(f)
        headers = next(reader)[1:]  # Skip the empty first cell
        matrix = []
        row_labels = []
        for row in reader:
            row_labels.append(row[0])
            matrix.append([int(cell) for cell in row[1:]])
    return np.array(matrix), row_labels, headers

# Create the AI workflow graph
G = create_ai_workflow_graph()

# Get adjacency matrix
adj_matrix = graph_to_adjacency_matrix(G)

# Get incidence matrix
inc_matrix = graph_to_incidence_matrix(G)

# Save adjacency matrix to CSV file
save_matrix_to_csv(adj_matrix, G.nodes(), G.nodes(), "adjacency_matrix.csv")

# For incidence matrix, we need to create edge labels
edge_labels = [f"{u[:2]}{v[:2]}" for u, v in G.edges()]
save_matrix_to_csv(inc_matrix, G.nodes(), edge_labels, "incidence_matrix.csv")

print("Matrices have been saved to 'adjacency_matrix.csv' and 'incidence_matrix.csv'")

# Read matrices from CSV files
adj_matrix, adj_row_labels, adj_col_labels = read_matrix_from_csv("adjacency_matrix.csv")
inc_matrix, inc_row_labels, inc_col_labels = read_matrix_from_csv("incidence_matrix.csv")

# Initialize Anthropic client
client = Anthropic(
    api_key=os.environ.get("ANTHROPIC_API_KEY"),
)

# Function to ask questions about the matrices
def ask_about_matrices(question):
    prompt = f"""
    You are an AI expert specializing in graph theory and matrix analysis. Your task is to analyze the given adjacency and incidence matrices of an AI workflow graph and answer questions about them.

    Adjacency Matrix:
    {adj_matrix}
    Row/Column Labels: {adj_row_labels}

    Incidence Matrix:
    {inc_matrix}
    Row Labels: {inc_row_labels}
    Column Labels: {inc_col_labels}

    Question: {question}

    Provide a clear, concise, and accurate answer based on the information in the matrices. Focus on the specific relationship or property asked about in the question. Limit your response to 2-3 sentences.
    """
    message = client.messages.create(
        max_tokens=300,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model="claude-3-opus-20240229",
    )
    return message.content

# Example usage
question = "What does the adjacency matrix tell us about the relationship between DataPreprocessor and FeatureExtractor?"
answer = ask_about_matrices(question)
print(f"Q: {question}")
print(f"A: {answer}")

# You can ask more questions here