import json
import pytest
import uuid
import logging

# Adjust the import statement as needed to get at your module's objects.
# For example, if your main file is LanguageAgentTreeSearch/programming/main.py:
from LanguageAgentTreeSearch.programming.main import (
    Node,
    FIMHierarchy,
    build_tree_from_graph,
    build_node_dict,
    propagate_causal_effects,
    propagate_cumulative_causality
)

# Setup logging for the tests.
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def test_orphan_node_detection():
    """
    Create a small tree and manually detach a node so that it becomes orphaned.
    Verify that report_failed_nodes() flags the orphan.
    """
    base_graph = {
        "Origin": {"A": 1.0},
        "A": {"A1": 1.0}
    }
    root = build_tree_from_graph(base_graph, "Origin")
    # Attach invariant_prefix for consistency (normally set during updates)
    root.invariant_prefix = "O"
    # Build a mapping from invariant label to node.
    nodes = build_node_dict(root)
    orphan_node = nodes["A1"]
    # Force an orphan: detach its parent.
    orphan_node.parent = None
    
    # For FIMHierarchy, we need to set a dummy linear order.
    linear_order = [root, orphan_node]
    aggregated_hpc = [1.0]
    aggregated_entropy = [0.5]
    fim = FIMHierarchy(root, {}, aggregated_hpc, aggregated_entropy)
    fim.linear_order = linear_order

    failed = fim.report_failed_nodes()
    # We expect an error on "A1"
    assert any("A1" in label for label, _ in failed), "Orphan node A1 was not detected."

def test_sorting_violation_fix():
    """
    Create a small tree with a sorting violation by manually assigning abs_index values that are out-of-order.
    Then call self_heal_structure() and verify that the ordering violation is cleared.
    """
    base_graph = {
        "Origin": {"A": 1.0},
        "A": {"A1": 1.0}
    }
    root = build_tree_from_graph(base_graph, "Origin")
    # Set invariant_prefixes for proper identification.
    root.invariant_prefix = "O"
    nodes = build_node_dict(root)
    node_A = nodes["A"]
    node_A.invariant_prefix = "A"
    node_A1 = nodes["A1"]
    node_A1.invariant_prefix = "A1"
    
    # Simulate incorrect ordering: assign bad abs_index values.
    root.abs_index = 0
    node_A.abs_index = 3
    node_A1.abs_index = 2  # Violation: node_A (parent) has index 3 but child A1 has index 2.

    aggregated_hpc = [1.0]
    aggregated_entropy = [0.5]
    fim = FIMHierarchy(root, {}, aggregated_hpc, aggregated_entropy)
    # Overwrite the linear order for our test.
    fim.linear_order = [root, node_A, node_A1]

    failed_before = fim.report_failed_nodes()
    assert any("A1" in label for label, _ in failed_before), "Sorting violation was not detected before healing."

    # Now trigger self-healing
    fim.self_heal_structure()
    failed_after = fim.report_failed_nodes()
    assert not any("A1" in label for label, _ in failed_after), "Sorting violation persists after self-healing."

def test_weight_inheritance_on_add_child():
    """
    Verify that when a child is added with default weight (1.0) to a parent with non-default weight,
    the child's weight gets updated to 90% of the parent's weight.
    """
    # Create a parent and a new child
    parent = Node("Parent", weight=0.8)
    parent.invariant_prefix = "P"
    child = Node("Child", weight=1.0)
    child.invariant_prefix = "C"

    # Before adding, child's weight is default.
    assert child.weight == 1.0
    parent.add_child(child)
    # After adding, expect child's weight to be 0.8 * 0.9 = 0.72.
    assert abs(child.weight - 0.72) < 1e-4, "Child's weight was not inherited correctly from parent."

def test_causal_propagation_and_cumulative_causality():
    """
    Construct a two-level tree, propagate causal metadata, then propagate cumulative causality,
    and check that the child nodes have a non-empty cumulative causality chain.
    """
    base_graph = {
        "Origin": {"A": 1.0},
        "A": {"A1": 1.0}
    }
    root = build_tree_from_graph(base_graph, "Origin")
    # Set invariant_prefixes
    root.invariant_prefix = "O"
    nodes = build_node_dict(root)
    nodes["A"].invariant_prefix = "A"
    nodes["A1"].invariant_prefix = "A1"
    
    aggregated_hpc = [1.0]
    aggregated_entropy = [0.5]
    fim = FIMHierarchy(root, {}, aggregated_hpc, aggregated_entropy)
    
    # Propagate direct causal effects.
    propagate_causal_effects(fim.root)
    # Check that both nodes have a causal_inference field.
    assert hasattr(fim.root, "causal_inference"), "Root node has no causal_inference."
    assert hasattr(nodes["A"], "causal_inference"), "Node A has no causal_inference."
    
    # Now propagate cumulative causality.
    propagate_cumulative_causality(fim.root)
    # The cumulative causal chain on A1 should be non-empty.
    assert hasattr(nodes["A1"], "cumulative_causality"), "Node A1 lacks cumulative causality."
    assert len(nodes["A1"].cumulative_causality) > 0, "Cumulative causality chain on A1 is empty."

# Optionally, add more tests here focused on other rules and aspects,
# such as full JSON export and self-healing after an LLM update.

if __name__ == "__main__":
    pytest.main() 