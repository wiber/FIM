#!/bin/bash
reset
set -e  # Exit immediately if a command fails

# Process CLI arguments and look for a flag to skip tests.
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

# Ensure PYTHONPATH is correctly set to the repository root (adjust as needed)
export PYTHONPATH=$(pwd)/../..

# Print environment for debugging
echo "📌 PYTHONPATH: $PYTHONPATH"

# Redirect entire terminal output (stdout and stderr) to a log file.
exec &> >(tee full_terminal_output.log)

# Run tests if enabled.
if [ "$RUN_TESTS" -eq 1 ]; then
    echo "📌 Running tests..."
    UNIT_TEST_FAIL_MODE=1 python -m unittest discover -s tests -p "test_*.py" -v 2>&1 | tee test_output.log
else
    echo "📌 Skipping tests as requested via --no-tests/--prod flag."
fi

# Run the main program, passing along all remaining CLI arguments.
echo "🚀 Running main.py with passed flags: ${filtered_args[@]}"
python main.py "${filtered_args[@]}" 2>&1 | tee main_output.log

### --- NEW: Copy Terminal Output and Relevant Files ---
echo "📌 Copying terminal output and code files to all_executed_files.log..."

# Append full terminal output to all_executed_files.log
{
  echo -e "\n--- Terminal Output ---\n"
  cat full_terminal_output.log
} >> all_executed_files.log

# Define the list of files to copy (the .sh, main.py, and test files)
FILES=(
  "run_lats_gpt4.sh"
  "main.py"
  "tests/test_fim_hierarchy.py"
  "tests/test_fim_validation.py"
  "tests/test_rules.py"
  "tests/"
)

# Clear (or create) the output log file first (already done above) and then loop through each file.
for FILE in "${FILES[@]}"; do
    if [[ -f "$FILE" ]]; then
        echo "🔍 Copying: $FILE"
        echo -e "\n--- File: $FILE ---\n" >> all_executed_files.log
        cat "$FILE" >> all_executed_files.log
        echo "" >> all_executed_files.log
    else
        echo "⚠️  Skipped missing file: $FILE"
    fi
done

echo "✅ Copied content saved to all_executed_files.log"
echo "✅ Script execution complete."
