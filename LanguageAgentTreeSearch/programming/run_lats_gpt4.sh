#!/bin/bash

# Echo the API key (be careful not to share this output)
echo "OPENAI_API_KEY: ${OPENAI_API_KEY:0:5}...${OPENAI_API_KEY: -5}"

#!/bin/bash
# Run the Python script
python main.py \
  --run_name "test_run" \
  --root_dir "root" \
  --dataset_path "./benchmarks/humaneval-py.jsonl" \
  --strategy "mcts" \
  --language "py" \
  --model "gpt-4" \
  --max_iters 10 \
  --expansion_factor 2 \
  --number_of_tests 2 \
  --verbose \
  --num_agents 5 \
  --output_path "./output.json"