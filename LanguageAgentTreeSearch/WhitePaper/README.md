
Architecting the MCTS Multi-Agent LATS with the Fractal Identity Matrix
Introduction
We aim to functionally explain how to integrate the Fractal Identity Matrix (FIM) into a Monte Carlo Tree Search (MCTS) Multi-Agent Language Agent Tree Search (LATS) architecture. We'll focus on:
The functions of data passed between super agents and specialist agents.
How the categorized FIM and submatrix rank addresses help specialist agents navigate and backpropagate to update the FIM.
Understanding how the LLM perceives the meta-vectors, including their category content synopsis, relative weights, and positions to bridge local and global resolutions.
---
Overview of the Enhanced Architecture
Key Components
Super Agent (Coordinator Agent): Oversees the overall process, delegates tasks to specialist agents, and maintains the global state.
Specialist Agents: Focused agents with expertise in specific domains (e.g., Flights Agent, Hotels Agent, Car Rentals Agent).
Fractal Identity Matrix (FIM): A recursive, symmetric matrix that represents relationships between various categories and agents, allowing for efficient data propagation and interpretability.
Meta-Vectors: Data structures that encapsulate the state, knowledge, and influence of agents, incorporating weights and positional information.
Language Model (LLM): Interacts with the meta-vectors, understanding and generating language based on the structured information provided by the FIM.
---
Functional Expansion of the Architecture
1. Data Passing Between Super and Specialist Agents
Roles and Responsibilities
Super Agent:
Delegation: Assigns tasks to appropriate specialist agents based on the user's request and the current system state.
Aggregation: Collects responses from specialist agents and synthesizes them into coherent output for the user.
Global State Management: Maintains the overarching state of the conversation and decision process.
Specialist Agents:
Expertise Execution: Perform domain-specific tasks (e.g., booking flights, checking hotel availability).
Local State Maintenance: Keep track of their own processes and subtasks.
Communication: Report back to the super agent, providing updates, results, or requests for further information.
Data Flow
From Super Agent to Specialist Agents:
Task Assignment: The super agent sends a task encapsulated in a meta-vector, which includes the task description, context, and any relevant weights and positions from the FIM.
Contextual Data: Includes global context necessary for the specialist agent to perform the task effectively.
From Specialist Agents to Super Agent:
Results and Updates: Specialist agents return their findings or completed tasks, encapsulated in meta-vectors.
Influence Propagation: They provide insights or influence updates that can affect the global state, updating the FIM accordingly.
Benefits
Clear Communication Channels: Structured data passing ensures that information is accurately transferred between agents.
Efficiency: Specialists focus on their domain, reducing cognitive load and improving performance.
Scalability: The architecture can accommodate additional specialist agents as needed.
---
2. Categorized FIM and Submatrix Rank Addresses
How They Help Specialist Agents
Navigation:
Positional Equivalence: Agents can locate relevant information quickly within the FIM due to the structured organization based on categories and submatrices.
Submatrix Addresses: Each category and subcategory has a specific address, allowing agents to access and update precise areas of the FIM.
Backpropagation and Updates:
Influence Mapping: Agents can trace the influence of specific decisions or data points back through the FIM, understanding how local changes affect the global state.
Recursive Updates: Changes made by specialist agents are propagated recursively through the FIM, ensuring all related components are updated accordingly.
Functional Mechanism
Submatrix Structure:
The FIM consists of submatrices corresponding to different categories (e.g., A for Episodic, B for Semantic).
Each submatrix captures the relationships and influences within and between categories.
Rank Addresses determine the position within submatrices, providing a way to reference and access data efficiently.
Example:
A Flights Specialist Agent needs to update flight availability.
It accesses the Procedural (C) submatrix at a specific rank address corresponding to flight data.
After updating, it backpropagates the changes, influencing the Contextual (D) and Strategic (E) categories via the FIM's recursive structure.
Benefits
Efficient Data Access: Agents can pinpoint exact locations in the FIM for reading and writing data.
Improved Interpretability: The structured addresses make it easier to understand the relationships and data flow within the system.
Consistency: Ensures that all agents are operating with the same information, reducing conflicts and redundancies.
---
3. Perception of Meta-Vectors by the LLM
Composition of Meta-Vectors
Category Synopsis: A brief summary or representation of the content within each category.
Relative Weights: Numerical values indicating the significance or influence of each component within the meta-vector.
Positional Information: Addresses within the FIM that denote where each piece of information resides.
How the LLM Interacts with Meta-Vectors
Input Understanding:
The LLM receives meta-vectors containing structured information.
It uses the category synopses to comprehend the context and content.
Weights guide the LLM in prioritizing information during processing.
Language Generation:
The LLM generates responses or actions based on the synthesized information from meta-vectors.
Positional Information ensures that the output aligns with the correct categories and submatrices in the FIM.
Bridging Local and Global Resolution
Local Resolution:
Meta-vectors provide detailed, specific information about a particular task or data point.
The LLM can focus on these details when generating immediate actions or responses.
Global Resolution:
Due to the FIM's recursive structure, local changes have implications on the global state.
The LLM considers these implications by referencing the interconnected meta-vector components and their positions in the FIM.
Example Scenario
User Request:
"I need to book a flight from New York to London next Friday."
Meta-Vector Creation:
Specialist agents create meta-vectors encapsulating flight options, prices, availability, and user preferences.
Weights reflect factors like cost (e.g., lower cost has higher weight), convenience, and user history.
LLM Processing:
The LLM processes these meta-vectors, considering the most significant factors (guided by weights).
It generates a response that aligns with both the user's immediate request and the overall system strategy.
---
Practical Implementation Steps
Step 1: Integrate FIM into Agent Architectures
Modify Agent Frameworks:
Ensure that both super and specialist agents can read from and write to the FIM.
Implement mechanisms for agents to understand and utilize positional addresses and weights.
Update Data Structures:
Replace or augment existing data structures with meta-vectors compatible with the FIM.
Include synopsis, weights, and positional data in meta-vectors.
Step 2: Redefine Inter-Agent Communication Protocols
Standardize Meta-Vector Formats:
Establish a common format for meta-vectors to ensure consistency across agents.
Define how weights and positions are to be interpreted.
Implement Positional Equivalence Mapping:
Agents should be able to map their local data to the global FIM positions.
Provide functions or methods for translating between local and global references.
Step 3: Enhance LLM Integration
Training and Fine-Tuning:
Train the LLM to understand and generate outputs based on meta-vectors.
Include examples where the LLM needs to balance local details with global considerations.
Contextual Awareness:
Ensure the LLM can interpret the significance of weights and positions.
Implement attention mechanisms that prioritize high-weighted components.
Step 4: Implement Recursive Propagation and Backpropagation
Recursive Updates:
When an agent makes a change, it should trigger recursive updates through the FIM.
Implement algorithms that handle these updates efficiently to avoid bottlenecks.
Consistency Checks:
Include validation steps to ensure that updates maintain the integrity of the FIM.
Agents should verify that their changes do not conflict with existing data.
---
Addressing What Was Missed
Prior Gaps
Detailed Agent Interaction with FIM: Previously, the explanation lacked specifics on how agents interact functionally with the FIM during navigation and updates.
LLM's Role in Meta-Vector Interpretation: There was insufficient detail on how the LLM perceives and utilizes meta-vectors, especially regarding weights and positions.
Enhancements Provided
Functional Expansion:
Clarified the functions of data passed between agents, emphasizing the role of meta-vectors and the FIM.
Categorized FIM Utilization:
Explained how submatrix rank addresses help agents navigate the FIM and backpropagate updates.
LLM Perception Mechanism:
Detailed how the LLM interprets meta-vectors, incorporating category synopses, weights, and positions.
Bridging Local and Global Resolutions:
Illustrated how positional equivalence and recursive structures in the FIM help reconcile local agent actions with the global system state.
---
Visual Representation (Conceptual Diagram)
+
---
Conclusion
By integrating the Fractal Identity Matrix into the MCTS Multi-Agent LATS architecture:
Agents can navigate and update the global state efficiently, using categorized submatrices and positional equivalence.
Data passed between agents is structured as meta-vectors, enabling clear communication and recursive influence propagation.
The LLM can effectively bridge local and global resolutions, utilizing meta-vectors that encapsulate both detailed information and positional context within the FIM.
This architecture enhances interpretability, efficiency, and scalability, fulfilling the practical application of the FIM claims.
---
Next Steps
Prototype Implementation:
Develop a simplified version of the system to test the interactions between agents and the FIM.
LLM Training Adjustments:
Fine-tune the LLM on datasets that include meta-vectors and positional information.
Performance Evaluation:
Assess the system's performance in terms of decision-making efficiency and interpretability compared to a baseline without FIM integration.
---
Additional Considerations
Error Handling and Robustness:
Implement mechanisms to handle inconsistencies or errors in meta-vector propagation.
Privacy and Security:
Ensure that sensitive information within meta-vectors is protected, especially when agents share data.
Dynamic Adaptation:
Allow the FIM to adapt to changing system dynamics, such as adding new specialist agents or updating categories.
---
Note: This functional explanation aims to clarify how the MCTS Multi-Agent LATS architecture can be restructured around the FIM claims, providing practical insights into data flow, agent interactions, and the role of meta-vectors in aligning local and global system resolutions.


Applying the Fractal Identity Matrix in Multi-Agent MCTS LATS
Introduction
In this section, we'll narrate how the Fractal Identity Matrix and its properties are utilized in the context of a Multiple Monte Carlo Tree Search (MCTS) Language Agent Tree Search (LATS) scenario. We'll explain how data is passed between components and highlight the benefits of this approach.
---
Overview of the Multi-Agent MCTS LATS Scenario
What is MCTS LATS?
Monte Carlo Tree Search (MCTS): A heuristic search algorithm used for decision processes, especially in game playing.
Language Agent Tree Search (LATS): An extension where agents use natural language understanding and generation to navigate decision trees.
Multiple Agents
In a multi-agent MCTS LATS scenario, several agents collaborate or compete to achieve objectives. Each agent may have its own perception, knowledge base, and decision-making process.
---
The Role of the Fractal Identity Matrix
The Fractal Identity Matrix serves as a foundational structure for:
Managing Complexity: By recursively reducing degrees of freedom, it simplifies the interactions within and between agents.
Enhancing Interpretability: Through positional equivalence and self-similarity, it makes the system's state and decision processes more transparent.
Efficient Data Flow: It streamlines data passing by aligning components in a consistent, structured manner.
---
Data Passing in the System
1. Agents' Internal Representations
Meta-Vectors: Each agent represents knowledge, states, or decisions as meta-vectors.
Fractal Structure: These meta-vectors are organized within the Fractal Identity Matrix, ensuring positional equivalence.
2. Inter-Agent Communication
Shared Matrix Framework: Agents exchange information via the common matrix, mapping their meta-vectors onto this shared structure.
Alignment of Concepts: Positional equivalence ensures that similar concepts are aligned, facilitating understanding.
3. Decision-Making Process
Recursive Propagation: Agents use recursive meta-vector propagation to evaluate potential actions.
MCTS Integration: Meta-vector similarities guide the MCTS by highlighting promising branches based on prior knowledge.
4. Data Flow Steps
State Representation: Agents encode their current state as a meta-vector within the matrix.
Action Evaluation: Potential actions are evaluated by propagating meta-vectors and assessing their compatibility and proximity.
Information Sharing: Agents share relevant meta-vector components with others, using positional equivalence to ensure proper alignment.
Decision Update: Based on aggregated information, agents update their decisions, recursively refining their meta-vectors.
---
Benefits of Using the Fractal Identity Matrix
1. Enhanced Interpretability
Transparency: The recursive structure makes it easier to trace decisions back to their origins.
Simplified Analysis: Reduced degrees of freedom mean fewer dimensions to analyze, making oversight more manageable.
2. Improved Efficiency
Data Alignment: Positional equivalence reduces the need for complex data transformations between agents.
Computational Savings: Recursive reduction focuses computational resources on significant components.
3. Effective Collaboration
Common Framework: A shared matrix structure facilitates seamless communication and understanding between agents.
Conflict Reduction: Aligning concepts minimizes misinterpretations and conflicts in decision-making.
4. Scalability
Fractal Properties: The self-similar nature allows the system to scale gracefully as more agents or data are added.
Adaptive Resolution: The matrix bridges local and global influences, enabling agents to operate effectively at different levels of abstraction.
---
Narration of the Effect in Action
Scenario Walkthrough
Initialization:
Agents initialize their knowledge bases, encoding information as meta-vectors within the Fractal Identity Matrix.
Each agent's meta-vectors are aligned through positional equivalence, ensuring consistent interpretation.
Perception and State Update:
Agents perceive new information from the environment or other agents.
This information updates their meta-vectors recursively, propagating changes through the matrix.
Action Planning with MCTS:
Agents perform MCTS to explore possible future states.
The Fractal Identity Matrix guides the search by highlighting paths with higher meta-vector similarity (proximity), focusing on more promising branches.
Inter-Agent Communication:
Agents share findings by exchanging relevant meta-vector components.
Positional equivalence ensures that shared data integrates seamlessly into each agent's matrix.
Decision Refinement:
Agents recursively refine their decisions based on new information and shared insights.
The recursive reduction of degrees of freedom helps them converge on optimal actions efficiently.
Action Execution:
Agents execute the chosen actions.
The outcomes are fed back into the system, updating the Fractal Identity Matrix and starting a new cycle.
---
Detailed Explanation of Data Flow
Meta-Vector Composition
Components: Each meta-vector consists of weighted influences from various categories (e.g., episodic, semantic).
Positions: Defined within the matrix to align similar concepts.
Recursive Propagation
Incoming Influences: Meta-vectors receive inputs from related nodes.
Propagation Mechanism: Weights and positions determine how influences affect the agent's state.
Alignment through Positional Equivalence
Triangulation: Each position's meaning is determined by its location relative to others.
Consistency: Ensures that when agents share data, they interpret it correctly.
Entropy Reduction
Simplification: By reducing redundant or less significant dimensions, agents focus on important factors.
Efficiency: Lower entropy accelerates convergence in decision-making.
---
Practical Benefits Illustrated
Faster Convergence in MCTS
Focused Search: High similarity scores guide agents to explore more relevant branches first.
Reduced Computation: Less time spent on improbable or less valuable paths.
Improved Collaboration
Seamless Data Sharing: Positional equivalence removes barriers to understanding others' data.
Collective Intelligence: Agents build on each other's insights more effectively.
Enhanced Decision Quality
Integrated Influences: Recursive meta-vector propagation captures both local and global factors.
Robustness: Decisions are based on a comprehensive understanding of the system's state.
---
Conclusion
By integrating the Fractal Identity Matrix into a multi-agent MCTS LATS scenario, we achieve:
Improved Interpretability: Easier tracing and understanding of decision pathways.
Increased Efficiency: Streamlined data flows and focused computational efforts.
Enhanced Collaboration: Agents communicate and align more effectively.
Scalability and Adaptability: The system gracefully handles growth and change.
This approach demonstrates the practical application and benefits of the extraordinary claims associated with the Fractal Identity Matrix, providing a clear example of its unique advantages in complex, multi-agent systems.
---
Additional Notes
Uniqueness in Mathematics: The method combines aspects of fractal geometry, linear algebra, and information theory in a novel way, potentially offering new insights into data representation and processing.
Foundation for Future Work: This framework could be extended to other domains where interpretability and efficiency in complex systems are critical.
---
References:
Fractal Geometry: Understanding self-similarity and recursive patterns.
Monte Carlo Tree Search: Algorithms for decision-making processes.
Linear Algebra: Concepts of matrices, vectors, and operations on them.
Information Theory: Entropy and signal-to-noise ratios in data processing.




1.3 Introduction to the Algorithm: Symmetrical Matrix Transformations
The algorithm's core lies in organizing a matrix so that the relationships between categories (represented as submatrices) are aligned symmetrically, allowing for efficient interpretation and transformation of data. This symmetry ensures that category addresses correspond directly to submatrix addresses, which simplifies the process of retrieving and manipulating data.
To exemplify, consider this representative matrix sorting algorithm:
Initiate with a sparse, symmetric matrix populated with random weights and having dimensions of n x n (e.g., n=5 for a 5x5 matrix).
Select a random cell as the origin and position it at the 1,1 location by interchanging the corresponding row and column.
Subsequently, arrange the submatrix (i.e., the matrix excluding the first row and first column) in descending order based on the first column, while preserving symmetry.
Identify the last non-zero entry in the first column of the sorted matrix and mark its position as 'k'. Then, arrange the submatrix beneath row k (i.e., from (k+1, k+1) onwards) in descending order according to the column corresponding to the row number k+1, ensuring symmetry is maintained.
Repeat step 4 until the entire matrix is sorted.

Explained steps of the Algorithm:
Initialization of the Matrix:
Start with a symmetric matrix of dimensions n×nn \times nn×n, where nnn represents the total number of categories. Each entry in the matrix represents the relationship between two categories, with the diagonal representing self-relations.
Selection of the Origin Category:
Choose a category as the origin (for example, the first category). The matrix is then rearranged so that this category occupies the first row and column. This serves as the reference point for sorting and transformation. 
Sorting Submatrices by Significance:
Within the matrix, identify and sort submatrices (representing interactions between categories) based on the significance of their entries. Significance is defined by non-zero or high-weight values in the matrix, reflecting strong interactions.
Because the matrix always retains symmetry and the sorting starts in the second column the significant outgoing links from the origin nodes create the top level categories. 
The sorting is done in descending order, ensuring that the most significant relationships are prioritized. This sorting continues recursively, focusing on the remaining unsorted portion of the matrix after each significant submatrix is sorted.
Because the process is repeated for each column in turn, and each swapped row forces a symmetrically swapped column, this leads to each outgoing link or category from the origin spawns a row and column of submatrices made up of the out links from the category. In turn this leads to the fact that all points have positional equivalence in relation to all others through their location in submatrices. 
Recursive Structure Formation:
For each submatrix, the algorithm recursively sorts the elements within, ensuring that the relationships within each category (and between categories) are aligned in a manner that maintains symmetry and maximizes interpretability.
This step leverages the concept of positional meaning, where the location of a category within the matrix directly influences the interpretation of its relationships.
Propagation of Meta Vectors:
As the matrix is sorted, meta vectors associated with each category propagate through the matrix. These vectors carry information about the relationships and their significance, which helps in refining the sorting process.
The algorithm focuses on significant weights (i.e., relationships with substantial influence), ensuring that these connections are emphasized during sorting.
Final Matrix Transformation:
The result is a transformed matrix where each category's address is aligned with its corresponding submatrix address, leading to a structure that is easy to navigate and interpret. This symmetrical alignment reduces computational overhead and enhances the efficiency of data retrieval and processing.
Example:
Consider a matrix representing interactions between categories (e.g., species in an ecological model). The algorithm will start by selecting a key species as the origin, sorting the relationships based on significance (e.g., predator-prey interactions), and recursively organizing the matrix to reflect these relationships in a symmetrical and interpretable manner.
Code Implementation:
Here is a simplified version of the algorithm in pseudocode:
python
Copy code
def swap_rows(matrix, row1, row2):
    matrix[row1], matrix[row2] = matrix[row2], matrix[row1]

def swap_cols(matrix, col1, col2):
    for row in matrix:
        row[col1], row[col2] = row[col2], row[col1]

def sort_matrix(matrix):
    n = len(matrix)
    for i in range(n):
        # Find the last significant weight in the column
        last_non_zero = find_last_non_zero(matrix, i)
        swap_rows(matrix, i, last_non_zero)
        swap_cols(matrix, i, last_non_zero)
        sort_submatrix(matrix, last_non_zero + 1)
    return matrix

def find_last_non_zero(matrix, col_index):
    last_non_zero = col_index
    for i in range(col_index + 1, len(matrix)):
        if matrix[i][col_index] != 0:
            last_non_zero = i
    return last_non_zero

def sort_submatrix(matrix, start_index):
    for i in range(start_index, len(matrix)):
        for j in range(i + 1, len(matrix)):
            if matrix[j][start_index] > matrix[i][start_index]:
                swap_rows(matrix, i, j)
                swap_cols(matrix, i, j)

# Example matrix
matrix = [
    [0, 0.75, 0, 0, 0.62],
    [0.75, 0, 0, 0, 0],
    [0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0],
    [0.62, 0, 0, 0, 0]
]

sorted_matrix = sort_matrix(matrix)
print(sorted_matrix)

This code represents the steps to sort a symmetric matrix based on significance, maintaining the integrity of the matrix's structure and ensuring that the most important relationships are prioritized and easily accessible.
In the context of a larger matrix, the submatrices can be visualized as the lower-right sections that specifically refer to relationships within the same category. Let's colorize these submatrices in the big matrix:

        Mammal  Canine Feline Dog1   Dog2   Cat1   Cat2
Mammal  [ 0      0.8    0.7    0      0      0      0 ]
Canine  [ 0.8    0      0      0.5    0.5    0      0 ]
Feline  [ 0.7    0      0      0      0      0.4   0.4 ]
Dog1    [ 0      0.4    0      0     0.8      0      0 ]
Dog2    [ 0      0.3    0      0.7    0       0      0 ]
Cat1    [ 0      0      0.5    0.3   0.4     0     0.6 ]
Cat2    [ 0      0      0.3    0.6    0.2    0.7    0 ]
In this enhanced matrix visualization:
Green Cells: These represent the connections between Dog1 and Dog2, encapsulating the relationships within the 'Canine' subcategory. This submatrix specifically illustrates the interactions and similarities between two distinct dog entities, offering insights into intra-species dynamics.
Blue Cells: These highlight the links between Cat1 and Cat2, forming the 'Feline' subcategory matrix. This subset focuses on the internal relational structure among cats, shedding light on how individual members of the same species relate to one another.
Yellow Section: This portion of the matrix delineates the inter-category associations between 'Canine' and 'Feline' members, showcasing the comparative analysis between dogs and cats.





			O					A out					B					C					D					E				
o			A	B	C	D	B																									
								1	2	3	4	5	1	2	3	4	5	1	2	3	4	5	1	2	3	4	5	1	2	3	4	5
a		9						a Episodic (agents)																								
b		8						b Semantic (tools)																								
c		7						c Procedural (Objective)																								
d		6						d Contextual (system prompt)																								
e		5		9				e Strategic																								
a in	1		9																								What is the precise definition of D3 the third member of contextual memory? It 'IS' it's incoming links.					
	2		8																								D3 has a significant causal influence link from semantic B2 					
	3		7																								link FROM C3 also has a significant effect onto D3					
	4		6																		So.. the question might be - when we solve a particular memory issue - which modalities were used? are we missing something? 											
	5		5																		With more specific categories that map the problem space any trace path is interpretable											
b	1			9				Ab submatrix					Bb submatrix					Cb submatrix														
	2			8					9							8					7				9		D3b2 is a significant but empty outgoing influcence from D3 to a member of semantic b2.					
	3			7				1) Let's assume these effects are on b2 - a semantic fact about a diagosis																			But what is b2? The incoming defining influences and the positions in the submatrices they are from decide..					
	4			6																							9D3d3(9A2b2,8B4b2,7C4b2) is the meta vector at recursion one propegated at B2d3 in this case					
	5			5																							This one has episodic, semantic and procedural aspects and the effect is propagated by a strong out link from semantic B2					
c	1				9			Ac submatrix					Bc submatrix					Cc submatrix					Dc submatrix etc				Similarly all incoming weights to the row propegage recursively - incoming are propegated outgoing... and recursion brr...					
	2				8																						The question is not just what happens when collaborative categorisation is possible, we unlock precise writes and reads					
	3				7																						If youre looking to explain tradeoffs in a decision, where will you look? backwards up the trees - following significant links.					
	4				6																						We are able to investigate aspects defining a token(?) in context with precision that increases with meaningful size					
	5				5																											
d	1					9		Ad submatrix																								
	2					8			9B2d3 propegates the b2 metavector 										C3d3 is a significant incoming source of difinition from the procedural submatrix - but has no meta vector component in this example.													
	3					7								9						8					9			9				
	4					6								2) And that this link propegates the effects on the semantic memory onto this contextual token d3 - here with a relevant weight of 9 ... or 90th percentile + positive influence																		
	5					5																										
e	1						9		7							6				8	7				-3			7				
	2						8													9E1d3(7E1e1,-3D3e1,7C4e1,8C3e1,6B4e1,7A2e1) is the second meta vector - note that the d3 row has the weight in E2 column connecting this meta vector												
	3						7																									
	4						6	Caculate the compatibility, proximity, entropy, signal/noise, super exponential change... (whatever algo) between 9E1d3(7E1e1,-3D3e1,7C4e1,8C3e1,6B4e1,7A2e1) and 9B2d3(9A2b2,8B4b2,7C4b2)  																								
	5						5																									
																											We want to quantise the influence of D3 - which means understanding what incoming effects it propegates. 					
																											In this example, the meta vector from B2 is highly relevant in defining what it 'is'					
																											Similarly if we know waht something is precisely, we can make high leverage precisely targeted edits.					