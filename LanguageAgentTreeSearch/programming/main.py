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

def rank_themes(themes, problem_description):
    """
    Ranks the themes in order of relevance to the problem space from -1 to 1.
    """
    ranked_themes = []
    for theme in themes:
        prompt = (
            f"On a scale from -1 to 1, how relevant is the theme '{theme}' "
            f"to the following problem description?\n\n{problem_description}\n\n"
            f"Provide only the numerical score."
        )
        try:
            response = client.chat.completions.create(model="gpt-4",  # or "gpt-3.5-turbo"
            messages=[
                {"role": "system", "content": "You are an expert at ranking themes."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=5,
            n=1,
            temperature=0)
            score_str = response.choices[0].message.content.strip()
            score = float(score_str)
        except (ValueError, Exception) as e:
            print(f"Error ranking theme '{theme}': {e}")
            score = 0.0  # Default score if parsing fails
        ranked_themes.append((theme, score))
    # Sort themes based on the score in descending order
    ranked_themes.sort(key=lambda x: x[1], reverse=True)
    return ranked_themes

def print_ranked_themes(ranked_themes):
    """
    Prints the ranked themes and their relevance scores.
    """
    print("\nRanked Themes:")
    for idx, (theme, score) in enumerate(ranked_themes, start=1):
        print(f"{idx}. Theme: '{theme}' with relevance score: {score}")

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'message': record.getMessage(),
        }
        return json.dumps(log_entry)

def setup_logging(output_file):
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler with JSON formatting
    file_handler = logging.FileHandler(output_file, mode='w')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = JSONFormatter()
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    return logger

# Use this logger instead of print statements
logger = setup_logging('output.json')

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run_name", type=str, help="The name of the run")
    parser.add_argument("--root_dir", type=str,
                        help="The root logging directory", default="root")
    parser.add_argument("--dataset_path", type=str,
                        help="The path to the benchmark dataset", default="root")
    parser.add_argument("--strategy", type=str,
                        help="Strategy: `simple`, `reflexion`")
    parser.add_argument("--language", type=str, help="Strategy: `py` or `rs`")
    parser.add_argument(
        "--model", type=str, help="OpenAI models only for now. For best results, use GPT-4")
    parser.add_argument("--pass_at_k", type=int,
                        help="Pass@k metric", default=1)
    parser.add_argument("--max_iters", type=int,
                        help="The maximum number of self-improvement iterations", default=10)
    parser.add_argument("--expansion_factor", type=int,
                        help="The expansion factor for the reflexion UCS and A* strategy", default=3)
    parser.add_argument("--number_of_tests", type=int,
                        help="The maximum number of internal tests for each question", default=6)
    parser.add_argument("--is_leetcode", action='store_true',
                        help="To run the leetcode benchmark")  # Temporary

    parser.add_argument("--verbose", action='store_true',
                        help="To print live logs")
    # TODO: implement this
    # parser.add_argument("--is_resume", action='store_true', help="To resume run")
    # parser.add_argument("--resume_dir", type=str, help="If resume, the logging directory", default="")
    parser.add_argument("--output_path", type=str, required=True)  # Add this line
    parser.add_argument('--num_agents', type=int, default=1, help='Number of agents to use')
    parser.add_argument('--num_categories', type=int, default=10, help='Number of categories for FIM')
    args = parser.parse_args()
    return args


def strategy_factory(strategy: str):
    def kwargs_wrapper_gen(func, delete_keys=[]):
        def kwargs_wrapper(**kwargs):
            for key in delete_keys:
                del kwargs[key]
            return func(**kwargs)
        return kwargs_wrapper

    if strategy == "simple":
        return kwargs_wrapper_gen(run_simple, delete_keys=["expansion_factor", "max_iters"])
    elif strategy == "reflexion":
        return kwargs_wrapper_gen(run_reflexion, delete_keys=["expansion_factor"])
    elif strategy == "mcts":
        return kwargs_wrapper_gen(run_mcts, delete_keys=["expansion_factor"])
    elif strategy == "dfs":
        return kwargs_wrapper_gen(run_dfs, delete_keys=["expansion_factor"])
    elif strategy == "immediate-reflexion":
        return kwargs_wrapper_gen(run_immediate_reflexion, delete_keys=["expansion_factor"])
    elif strategy == "immediate-refinement":
        return kwargs_wrapper_gen(run_immediate_refinement, delete_keys=["expansion_factor"])
    elif strategy == "test-acc":
        return kwargs_wrapper_gen(run_test_acc, delete_keys=["expansion_factor", "max_iters"])
    else:
        raise ValueError(f"Strategy `{strategy}` is not supported")


def load_dataset(dataset_path):
    with open(dataset_path, 'r') as f:
        return [json.loads(line) for line in f]


def save_results(results, output_path):
    with open(output_path, 'w') as f:
        for result in results:
            json.dump(result, f)
            f.write('\n')


def main(args):
    if not openai.api_key:
        print("Error: OPENAI_API_KEY is not set.")
        return

    # Load dataset
    dataset = load_dataset(args.dataset_path)
    logger.info(f"Dataset loaded with {len(dataset)} items")

    # Extract problem descriptions
    problem_descriptions = "\n".join([
        item.get('prompt', '') for item in dataset if 'prompt' in item
    ])

    if not problem_descriptions.strip():
        print("No problem descriptions found in the dataset.")
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