import os
import time
import datetime
import numpy as np
import matplotlib.pyplot as plt

from dotenv import load_dotenv
from algorithms.theme_analysis import identify_independent_themes, generate_subcategories
from algorithms.fim import FractalIdentityMatrix
import logging
import openai

# Load environment variables from .env file
load_dotenv()

# Set the OpenAI API key
openai.api_key = os.getenv('OPENAI_API_KEY')

def openai_completion_with_retry(prompt, model="gpt-4", max_tokens=150, temperature=0.7):
    retry_count = 0
    max_retries = 5
    backoff_factor = 2
    while True:
        try:
            response = openai.ChatCompletion.create(model=model,
            messages=[
                {"role": "system", "content": "You are an assistant that identifies themes."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=temperature)
            return response
        except openai.error.RateLimitError as e:
            retry_count += 1
            if retry_count > max_retries:
                print(f"Maximum retries exceeded. {e}")
                return None
            sleep_time = backoff_factor ** retry_count
            print(f"Rate limit error: {e}. Retrying in {sleep_time} seconds...")
            time.sleep(sleep_time)
        except openai.error.OpenAIError as e:
            retry_count += 1
            if retry_count > max_retries:
                print(f"OpenAI API error: {e}")
                return None
            sleep_time = backoff_factor ** retry_count
            print(f"OpenAI API error: {e}. Retrying in {sleep_time} seconds...")
            time.sleep(sleep_time)
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None

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

def identify_independent_themes(problem_description, num_themes=5):
    prompt = f"Identify the {num_themes} most independent themes in the following problem description. Provide them as a numbered list:\n\n{problem_description}"
    response = openai_completion_with_retry(prompt, model="gpt-4")
    if response:
        # Extract the content from the first choice
        response_text = response['choices'][0]['message']['content']
        themes = parse_themes_from_response(response_text)
        return themes
    else:
        print("Failed to identify themes.")
        return []

def generate_subcategories(theme, num_subcategories=5):
    prompt = f"For the theme '{theme}', identify {num_subcategories} subcategories. Provide them as a numbered list:"
    response = openai_completion_with_retry(prompt, model="gpt-4")
    if response:
        response_text = response['choices'][0]['message']['content']
        subcategories = parse_themes_from_response(response_text)
        return subcategories
    else:
        print(f"Failed to generate subcategories for theme: {theme}")
        return []

def visualize_matrix(matrix, labels):
    plt.figure(figsize=(10, 10))
    plt.imshow(matrix, cmap='viridis', interpolation='nearest')
    plt.colorbar()
    plt.xticks(ticks=range(len(labels)), labels=labels, rotation='vertical')
    plt.yticks(ticks=range(len(labels)), labels=labels)
    plt.tight_layout()
    plt.show()

def generate_timestamp():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def main(args):
    if not openai.api_key:
        print("Error: OPENAI_API_KEY is not set.")
        return

    # Example problem description; replace with actual input as needed
    problem_description = """
    We are developing a platform to help individuals and AIs overcome information overload by organizing and prioritizing personal and professional goals using innovative AI algorithms. The origin node is interpretability - think of it as the map that lets you save on your electricity bill because you can understand where what your are looking for is located, which tradeoffs are being made so you can make informed decisions about them etc. Just as humans can reason about a map and we'd expect you to find what you are looking for more efficiently we also expect that watching your eyes glide across the map tells us about how you think about the process. In short you get efficiency from the map and intepretability as a byproduct.
    """

    # Step 1: Identify independent themes
    themes = identify_independent_themes(problem_description, num_themes=5)
    if not themes:
        print("No themes identified.")
        return

    print("Identified Themes:")
    for theme in themes:
        print(f"- {theme}")

    # Step 2: Generate subcategories for each theme
    themes_dict = {}
    for theme in themes:
        subcategories = generate_subcategories(theme, num_subcategories=5)
        if not subcategories:
            logging.warning(f"No subcategories identified for theme '{theme}'.")
            continue
        themes_dict[theme] = subcategories
        logging.info(f"\nSubcategories for '{theme}':")
        for subcat in subcategories:
            logging.info(f"  - {subcat}")

    if not themes_dict:
        print("No subcategories generated. Exiting.")
        return

    # Step 3: Build the Fractal Identity Matrix
    fim = FractalIdentityMatrix(themes_dict)
    matrix = fim.get_matrix()
    labels = fim.get_labels()

    # Step 4: Visualize the Matrix
    visualize_matrix(matrix, labels)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run the Language Agent Tree Search with FIM.")

    parser.add_argument("--run_name", type=str, required=True, help="Name of the run")
    parser.add_argument("--root_dir", type=str, required=True, help="Root directory")
    parser.add_argument("--dataset_path", type=str, required=True, help="Path to the dataset")
    parser.add_argument("--strategy", type=str, default="mcts", help="Strategy to use")
    parser.add_argument("--language", type=str, default="py", help="Programming language")
    parser.add_argument("--model", type=str, default="gpt-4", help="Model to use")
    parser.add_argument("--max_iters", type=int, default=10, help="Maximum iterations")
    parser.add_argument("--expansion_factor", type=int, default=2, help="Expansion factor")
    parser.add_argument("--number_of_tests", type=int, default=2, help="Number of tests")
    parser.add_argument("--verbose", action='store_true', help="Enable verbose output")
    parser.add_argument("--num_agents", type=int, default=1, help="Number of agents to use")
    parser.add_argument("--num_categories", type=int, default=10, help="Number of categories for FIM")
    parser.add_argument("--output_path", type=str, required=True, help="Path for the output")

    args = parser.parse_args()
    main(args)