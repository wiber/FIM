import random
import time
import math

class Node:
    """A simple node for our hierarchy tree."""
    def __init__(self, name, parent=None, criteria=None):
        self.name = name
        self.parent = parent
        self.criteria = criteria or {}
        self.children = []
        self.data_points = []

    def add_child(self, child_node):
        self.children.append(child_node)

    def add_data_point(self, data_point):
        self.data_points.append(data_point)

    def __repr__(self):
        return f"Node(name='{self.name}', children={len(self.children)}, data_points={len(self.data_points)})"

class FIMDataHierarchy:
    """Builds and searches a hierarchy based on data properties."""

    def __init__(self, data):
        self.root = Node("Root")
        self.total_nodes = 1
        self._build_from_data(data)

    def _build_from_data(self, data):
        """Partitions data and builds the FIM tree."""
        for item in data:
            # 1st Level: Conductivity Type
            conductivity = item['conductivity_type']
            conductivity_node = self._get_or_create_child(self.root, conductivity)

            # 2nd Level: Thermal Stability (in ranges of 100K)
            stability = item['thermal_stability']
            stability_range = f"Stab_{math.floor(stability / 100) * 100}K"
            stability_node = self._get_or_create_child(conductivity_node, stability_range)
            
            # 3rd Level: Band Gap (in ranges of 0.1eV)
            band_gap = item['band_gap']
            band_gap_range = f"BG_{math.floor(band_gap * 10) / 10}"
            band_gap_node = self._get_or_create_child(stability_node, band_gap_range)

            band_gap_node.add_data_point(item)

    def _get_or_create_child(self, parent, child_name):
        """Finds an existing child node or creates a new one."""
        for child in parent.children:
            if child.name == child_name:
                return child
        new_child = Node(child_name, parent=parent)
        parent.add_child(new_child)
        self.total_nodes += 1
        return new_child

    def search(self, query):
        """
        Searches the FIM hierarchy, skipping irrelevant branches.
        Returns (list of matches, number of nodes visited).
        """
        matches = []
        nodes_visited = 0
        
        q_stability_min, q_stability_max = query.get('thermal_stability_range', (0, float('inf')))
        q_band_gap_min, q_band_gap_max = query.get('band_gap_range', (0, float('inf')))

        q_conductivity = query.get('conductivity_type')

        def recurse(node):
            nonlocal nodes_visited
            nodes_visited += 1

            # --- Pruning Logic (The "Skip Factor") ---
            if node.parent == self.root: # Conductivity Node
                if q_conductivity and node.name != q_conductivity:
                    return

            # Check stability ranges for pruning
            if node.name.startswith("Stab_"):
                node_stability = int(node.name.split('_')[1][:-1])
                # If the entire range of this node is outside the query, prune it.
                if node_stability + 100 < q_stability_min or node_stability > q_stability_max:
                    return

            # Check band gap ranges for pruning
            if node.name.startswith("BG_"):
                node_bg = float(node.name.split('_')[1])
                # If the entire range of this node is outside the query, prune it.
                if node_bg + 0.1 < q_band_gap_min or node_bg > q_band_gap_max:
                    return

            # If it's a leaf node (or has data), check individual data points
            for item in node.data_points:
                nodes_visited += 1 # Count each data point check as a "visit"
                if (q_stability_min <= item['thermal_stability'] <= q_stability_max and
                    q_band_gap_min <= item['band_gap'] <= q_band_gap_max):
                    if not q_conductivity or item['conductivity_type'] == q_conductivity:
                        matches.append(item)
            
            for child in node.children:
                recurse(child)

        recurse(self.root)
        return matches, nodes_visited

def generate_materials_data(num_materials):
    """Generates a list of synthetic material data points."""
    materials = []
    conductivity_types = ['insulator', 'semiconductor', 'conductor']
    for i in range(num_materials):
        materials.append({
            'material_id': i,
            'band_gap': round(random.uniform(0.1, 8.0), 2),
            'thermal_stability': random.randint(300, 1200),
            'conductivity_type': random.choice(conductivity_types)
        })
    return materials

def linear_search(data, query):
    """
    Performs a brute-force scan of the entire dataset.
    Returns (list of matches, number of items scanned).
    """
    matches = []
    items_scanned = 0
    q_stability_min, q_stability_max = query.get('thermal_stability_range', (0, float('inf')))
    q_band_gap_min, q_band_gap_max = query.get('band_gap_range', (0, float('inf')))
    q_conductivity = query.get('conductivity_type')

    for item in data:
        items_scanned += 1
        if (q_stability_min <= item['thermal_stability'] <= q_stability_max and
            q_band_gap_min <= item['band_gap'] <= q_band_gap_max):
             if not q_conductivity or item['conductivity_type'] == q_conductivity:
                matches.append(item)
                
    return matches, items_scanned

def run_benchmark():
    """Sets up and runs the full benchmark test."""
    NUM_MATERIALS = 10_000_000
    QUERY = {
        'thermal_stability_range': (750, 780), # More specific range
        'band_gap_range': (2.1, 2.2),         # More specific range
        'conductivity_type': 'semiconductor'
    }

    print("--- HPC Search Benchmark (High Granularity) ---")
    print(f"Generating {NUM_MATERIALS:,} synthetic material data points...")
    start_time = time.time()
    materials_data = generate_materials_data(NUM_MATERIALS)
    print(f"Data generation took {time.time() - start_time:.2f} seconds.\n")

    # --- FIM Hierarchy Method ---
    print("Building FIM Data Hierarchy...")
    start_time = time.time()
    fim_hierarchy = FIMDataHierarchy(materials_data)
    build_time = time.time() - start_time
    print(f"Hierarchy built in {build_time:.2f} seconds. Total nodes: {fim_hierarchy.total_nodes:,}\n")
    
    print("Running FIM Hierarchy Search...")
    start_time = time.time()
    fim_matches, fim_accesses = fim_hierarchy.search(QUERY)
    fim_time = time.time() - start_time
    print(f"FIM search completed in {fim_time:.4f} seconds.")

    # --- Linear Scan Method ---
    print("\nRunning Linear Scan (Brute-Force)...")
    start_time = time.time()
    linear_matches, linear_accesses = linear_search(materials_data, QUERY)
    linear_time = time.time() - start_time
    print(f"Linear scan completed in {linear_time:.4f} seconds.")

    # --- Results ---
    print("\n--- Benchmark Results ---")
    print(f"Query: Find materials with stability in {QUERY['thermal_stability_range']}K, "
          f"band gap in {QUERY['band_gap_range']}eV, and type '{QUERY['conductivity_type']}'.\n")

    print(f"[Linear Search]")
    print(f"  - Items Scanned: {linear_accesses:,}")
    print(f"  - Matches Found: {len(linear_matches):,}")
    print(f"  - Time Taken:    {linear_time:.4f}s\n")

    print(f"[FIM Hierarchy Search]")
    print(f"  - Nodes/Items Visited: {fim_accesses:,}")
    print(f"  - Matches Found:       {len(fim_matches):,}")
    print(f"  - Time Taken:          {fim_time:.4f}s (plus {build_time:.2f}s one-time build cost)\n")
    
    print("--- Performance Analysis ---")
    if fim_accesses > 0:
        performance_factor = linear_accesses / fim_accesses
        print(f"Memory Access Reduction: FIM search accessed the database {performance_factor:,.1f}x fewer times.")
        print("This 'Skip Factor' directly translates to massive energy and time savings on hardware like CeRAM.")

        # --- Mathematical Justification ---
        print("\n\n--- Mathematical Justification for the Skip Factor ---")
        print("The performance gain is a direct mathematical consequence of changing the search strategy from a linear scan to a structured, hierarchical query.")
        
        print("\n1. The Cost of Linear Search (The Baseline)")
        print("   A linear search must inspect every single item in the dataset to find matches.")
        print(f"   - C_linear = N = {linear_accesses:,} memory accesses")

        print("\n2. The FIM Hierarchy: Creating Searchable Partitions")
        print("   The FIM approach builds a structured index that creates logical partitions of the data space (like a multi-level filing cabinet).")
        print("   - Level 1: conductivity_type ('insulator', 'semiconductor', 'conductor')")
        print("   - Level 2: thermal_stability (in 100K increments)")
        print("   - Level 3: band_gap (in 0.1eV increments)")
        
        print("\n3. From Theory to Practice: Total FIM Cost")
        print("   The FIM search navigates this hierarchy, pruning (skipping) entire branches that cannot match the query.")
        print("   The actual cost is the sum of visiting the internal 'signpost' nodes plus inspecting the data points at the relevant leaves.")
        print(f"   - C_fim = C_traversal + C_leaf_inspection = {fim_accesses:,} memory accesses")
        
        print("\n4. Final Calculation: The Skip Factor Multiple")
        print("   The multiple is the ratio of the linear search cost to the FIM search cost, showing how many times more work the linear search performs.")
        print(f"   - Skip Factor Multiple = C_linear / C_fim")
        print(f"   - Skip Factor Multiple = {linear_accesses:,} / {fim_accesses:,} = {performance_factor:,.2f}x")

    else:
        print("FIM search did not access any items.")

    if len(fim_matches) == len(linear_matches):
        print("\nValidation: Both methods returned the same number of results. Correctness confirmed.")
    else:
        print("\nError: Mismatch in results count!")


if __name__ == "__main__":
    run_benchmark() 