#!/bin/bash
reset
set -e  # Exit immediately if a command fails

# Reset logs to ensure only one run's output is present
rm -f test_output.log main_output.log all_executed_files.log

# Activate virtual environment
source venv/bin/activate

# Ensure PYTHONPATH is correctly set to the repository root (adjust as needed)
export PYTHONPATH=$(pwd)/../..

# Print environment for debugging
echo "📌 PYTHONPATH: $PYTHONPATH"
echo "📌 Running tests..."

# Run tests (set UNIT_TEST_FAIL_MODE so that extra tests run)
UNIT_TEST_FAIL_MODE=1 python -m unittest discover -s tests -p "test_*.py" -v 2>&1 | tee test_output.log

# Run the main program, passing through any CLI arguments
echo "🚀 Running main.py with passed flags: $@"
python main.py "$@" 2>&1 | tee main_output.log

### --- NEW: Copy and Print Relevant Files ---
echo "📌 Copying all relevant executed files to memory..."

# Define the list of files to copy (include the .sh, main.py, and test files)
FILES=(
  "run_lats_gpt4.sh"
  "main.py"
  "tests/test_fim_hierarchy.py"
  "tests/test_fim_validation.py"
  "tests/test_rules.py"
  "tests/*"
)

# Clear (or create) the output log file first
> all_executed_files.log

# Loop through each file and append its contents to the output file
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
