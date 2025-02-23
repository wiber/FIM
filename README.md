# Fractal Identity Matrix (FIM) Proof-of-Concept

This project demonstrates the integration of Fractal Identity Matrix (FIM) principles into a Language Model (LLM) framework. The goal is to optimize problem space subdivision, enhance interpretability, and reduce processing costs by dynamically building and updating a hierarchical structure. In this proof‑of‑concept, nodes in the hierarchy are enriched with causal links, labels, weights, and submatrix bounds through simulated LLM iterations.

## Current State and Features

- **Hierarchy Construction:**  
  The system builds a tree hierarchy from a base graph (for example, an "Origin" node with children "A", "B", "C", and "D", and further sub-nodes like "A1", "A2", etc.).

- **Simulated Updates:**  
  Over a series of iterations:
  - Each node's label is updated based on its immutable label and the current iteration (e.g., `A_simulated_3`).
  - Each node is provided with a `causal_metadata` attribute including a `simulation_iteration` number.

- **Extra Node Injection:**  
  An extra node (named `LLM_3_A3`) is injected into an existing branch (for instance, under node `LLM_3_A`) to simulate the addition of new data. After injection, the system:
  - Re-runs the label update (via `update_labels`).
  - Rebuilds the canonical ordering (ensuring proper indices and invariant prefixes).
  - Updates the simulation in-links (via `update_in_links`) to link parent and child nodes correctly.

- **Self-Heal Mode:**  
  A self-heal option (`--self_heal`) triggers extra repair attempts that enforce submatrix bounds as well as other rule validations to guarantee the hierarchy's integrity.

- **Hierarchy Export:**  
  The final hierarchical snapshot is written to a JSON file located at:
  
  ```
  LanguageAgentTreeSearch/programming/hierarchy_final_trial_1.json
  ```

## Setup and Requirements

- **Python Version:**  
  Requires Python 3.7 or later (Python 3.12 is recommended).

- **Dependencies:**  
  The project uses only standard Python libraries:
  - `json`
  - `logging`
  - `os`
  - `sys`
  - `pprint`

- **Directory Structure:**  
  ```
  LanguageAgentTreeSearch/
    └── programming/
         ├── main.py          # Main script that builds and simulates the FIM hierarchy.
         └── hierarchy_final_trial_1.json   # Output JSON file representing the final hierarchy.
  README.md
  ```

## How to Run

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/your_username/LanguageAgentTreeSearch.git
   cd LanguageAgentTreeSearch/programming
   ```

2. **Activate Your Shell Environment (Bash):**
   Ensure your terminal is using bash. If you use a different shell, switch to bash:
   ```bash
   bash
   ```

3. **Run the FIM Proof-of-Concept:**
   Execute the provided shell script to set up the environment and run the simulation:
   ```bash
   sh run_lats_gpt4.sh
   ```
   Alternatively, you can run the main Python script directly:
   ```bash
   python3 main.py --use_mock --self_heal
   ```
   - The `--use_mock` flag instructs the simulation to use mock data.
   - The `--self_heal` flag triggers additional repair attempts after the extra node injection.

4. **Inspect the Output:**
   After the run, the final hierarchy snapshot is printed to the console and saved as:
   ```
   LanguageAgentTreeSearch/programming/hierarchy_final_trial_1.json
   ```

## Code Details

- **Key Helper Functions:**
  - `update_labels(node, iteration=3)`: Recursively updates each node's label and causal metadata.
  - `update_in_links(node, iteration=3)`: Recursively populates missing in-link details, ensuring proper parent–child causal relationships.
  - `rebuild_canonical_ordering()`: Called on the FIMHierarchy object; this recomputes linear ordering, absolute indices, and invariant prefixes to incorporate changes (such as an injected extra node).

- **Rule Engine and Self-Heal:**  
  A minimal `RuleEngine` is provided to validate the hierarchy and attempt repairs if rule violations occur.

## Future Work

- Enhance rule validation and repair mechanisms.
- Support dynamic updates from real LLM calls rather than simulation.
- Extend visualization and debugging features to aid in analysis.

## License

[MIT License](LICENSE)

---

This README provides the current project state along with all necessary instructions to set up and run the FIM proof‑of‑concept.

    