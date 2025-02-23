#!/bin/bash

# Activate the virtual environment
source venv/bin/activate

# Echo the API key (be careful not to share this output)
echo "OPENAI_API_KEY: ${OPENAI_API_KEY:0:5}...${OPENAI_API_KEY: -5}"

#
if [[ "$@" == *"--unit_tests"* ]]; then
  # Change to the repository root (parent of LanguageAgentTreeSearch).
  cd ../..
  export PYTHONPATH=$(pwd)
  python -m unittest tests.test_fim_hierarchy
  exit 0
fi

# If the flag "--run_tests" is provided, run all tests via discovery.
if [[ "$@" == *"--run_tests"* ]]; then
  cd "$(dirname "$0")/.."
  export PYTHONPATH=$(pwd)
  # Use module discovery; the tests folder is now importable.
  python -m unittest discover -s tests -p "test_*.py"
  exit 0
fi

## Check if we need to run a specific unit test file (using --unit_test_file or --single_test)
if [[ "$@" == *"--unit_test"* ]]; then
  # Change directory to the repository root.
  cd "$(dirname "$0")/../../"
  export PYTHONPATH=$(pwd)
  python -m unittest tests.test_fim_hierarchy
  exit 0
fi

# New flag --run_unittests that uses discovery to run all tests in the tests/ folder.
if [[ "$@" == *"--run_unittests"* ]]; then
  cd "$(dirname "$0")/../.."
  export PYTHONPATH=$(pwd)
  python -m unittest discover -s tests -p "test_*.py"
  exit 0
fi

# New flag to run a single test file for FIMHierarchy.
if [[ "$@" == *"--run_single_test"* ]]; then
  cd "$(dirname "$0")/../.."
  export PYTHONPATH=$(pwd)
  python -m unittest tests/test_fim_hierarchy.py
  exit 0
fi

# Check for mock flag
if [[ "$1" == "--mock" ]]; then
  USE_MOCK="--use_mock"
fi

# If no test flags provided, run the main program.
python main.py "$@" \
  --run_name "test_run" \
  --root_dir "root" \
  --dataset_path "./benchmarks/humaneval-py.jsonl" \
  --strategy "mcts" \
  --language "py" \
  --model "gpt-03-mini-high" \
  --max_iters 10 \
  --expansion_factor 2 \
  --number_of_tests 2 \
  --verbose \
  --num_agents 5 \
  --output_path "./output.json" \
  $USE_MOCK
