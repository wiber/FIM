#!/bin/bash
reset
set -e  # Exit immediately if a command fails

# Process CLI arguments to optionally skip tests.
RUN_TESTS=1
args=("$@")
filtered_args=()
for arg in "${args[@]}"; do
    if [ "$arg" == "--no-tests" ] || [ "$arg" == "--prod" ]; then
        RUN_TESTS=0
    else
        filtered_args+=("$arg")
    fi
done

# Reset logs to ensure only one run's output is present
rm -f test_output.log main_output.log all_executed_files.log full_terminal_output.log

# Activate virtual environment
source venv/bin/activate

# Ensure PYTHONPATH is correctly set to the repository root.
export PYTHONPATH=$(pwd)/../..

# Print environment for debugging
echo "📌 PYTHONPATH: $PYTHONPATH"

# Redirect entire terminal output (stdout and stderr) to a log file.
exec &> >(tee full_terminal_output.log)

# Run tests only if not in production mode.
if [ "$RUN_TESTS" -eq 1 ]; then
    echo "📌 Running tests..."
    UNIT_TEST_FAIL_MODE=1 python -m unittest discover -s tests -p "test_*.py" -v | tee test_output.log
else
    echo "📌 Skipping tests as requested (--no-tests/--prod flag provided)."
fi

# Run the main program, passing along all remaining CLI arguments.
echo "🚀 Running main.py with passed flags: ${filtered_args[@]}"
python main.py "${filtered_args[@]}" 2>&1 | tee main_output.log

### --- Copy Full Terminal Output and Relevant Files ---
echo "📌 Copying full terminal output and code files to all_executed_files.log..."

# Define the list of files to copy
FILES=(
  "run_lats_gpt4.sh"
  "main.py"
  "tests/test_fim_hierarchy.py"
  "tests/test_fim_validation.py"
  "tests/test_rules.py"
  "full_terminal_output.log"
)

# Clear (or create) the output log file first
> all_executed_files.log

# Loop through each file and append its contents to the output file
for FILE in "${FILES[@]}"; do
    if [[ -f "$FILE" ]]; then
        echo -e "\n--- File: $FILE ---\n" >> all_executed_files.log
        cat "$FILE" >> all_executed_files.log
    else
        echo "⚠️  Skipped missing file: $FILE" >> all_executed_files.log
    fi
done

echo "✅ Copied content saved to all_executed_files.log"
echo "✅ Script execution complete."
