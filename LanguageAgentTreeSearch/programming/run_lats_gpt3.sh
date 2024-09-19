python main.py \
  --run_name "test_gpt3" \
  --root_dir "root" \
  --dataset_path ./benchmarks/humaneval-py.jsonl \
  --strategy "mcts" \
  --language "py" \
  --model "gpt-3.5-turbo" \
  --pass_at_k "1" \
  --max_iters "4" \
  --expansion_factor "3" \
  --number_of_tests "4" \
  --verbose