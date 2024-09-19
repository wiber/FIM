import argparse
from main import main

def test_fim_integration():
    args = argparse.Namespace(
        run_name="test_fim",
        root_dir="root",
        dataset_path="./benchmarks/humaneval-py.jsonl",
        strategy="mcts",
        language="py",
        model="gpt-4",
        max_iters=2,
        expansion_factor=2,
        number_of_tests=2,
        verbose=True,
        is_leetcode=False,
        output_path="./output.json"
    )
    main(args)

if __name__ == "__main__":
    test_fim_integration()