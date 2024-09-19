import os
import argparse
import json
from immediate_refinement import run_immediate_refinement
from immediate_reflexion import run_immediate_reflexion

from simple import run_simple
from reflexion import run_reflexion
from test_acc import run_test_acc
from utils import read_jsonl, read_jsonl_gz
from mcts import MAFIM, run_multi_agent_mcts  # Adjust the import path if necessary
from dfs import run_dfs
from fim import CentralFIM

from generators.model import model_factory  # Adjust this import based on your actual implementation

import logging
import json
from datetime import datetime

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
    logger.info(f"Number of agents specified: {args.num_agents}")
    logger.debug(f"Initializing MAFIM with {args.num_agents} agents")
    
    try:
        model = model_factory(args.model)
        print(f"Model created successfully: {type(model)}")
    except Exception as e:
        print(f"Error creating model: {str(e)}")
        return

    dataset = load_dataset(args.dataset_path)
    results = run_multi_agent_mcts(
        dataset=dataset,
        model=model,
        language=args.language,
        max_iters=args.max_iters,
        num_agents=args.num_agents,
        num_categories=args.num_categories
    )
    save_results(results, args.output_path)

    print(f"Processed {len(results)} items.")
    for i, item in enumerate(results[:5]):
        print(f"Item {i}:")
        print(f"  Prompt: {item['prompt'][:50]}...")
        print(f"  Solution: {item['solution'][:50]}...")
        print()

    import matplotlib.pyplot as plt

    def analyze_results(mafim, solutions):
        # Plot FIM evolution
        fim_states = mafim.fim.get_state()
        plt.figure(figsize=(10, 6))
        for agent in range(len(fim_states)):
            plt.plot(fim_states[agent], label=f'Agent {agent}')
        plt.title('FIM Evolution')
        plt.xlabel('Category')
        plt.ylabel('Performance')
        plt.legend()
        plt.savefig('fim_evolution.png')

        # Analyze solution quality over time
        solution_qualities = [sol['score'] for sol in solutions]
        plt.figure(figsize=(10, 6))
        plt.plot(solution_qualities)
        plt.title('Solution Quality Over Time')
        plt.xlabel('Problem')
        plt.ylabel('Solution Score')
        plt.savefig('solution_quality.png')

    analyze_results(mafim, results)

if __name__ == "__main__":
    import argparse
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
    main(args)
