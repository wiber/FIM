import numpy as np
import openai

class FractalIdentityMatrix:
    """
    FractalIdentityMatrix can be built either:
      1) From a user-given themes_dict (a Python dictionary of { top_theme: [sub_themes] }).
      2) From an LLM call that generates these themes dynamically based on a prompt.

    This class then constructs a matrix with:
      - Diagonal = 1 to indicate "identity"
      - Off-diagonal weights for theme ↔ sub-theme links
      - Random weights (with chosen sparsity) in the upper-right portion
    """

    def __init__(self, themes_dict=None, openai_api_key=None, prompt_text=None, model="gpt-4", sparsity=0.15):
        """
        :param themes_dict: dictionary of top-level themes to list of subcategories
        :param openai_api_key: OpenAI API key if you want to dynamically generate the dictionary from an LLM
        :param prompt_text: a string prompt that seeds the LLM to generate categories/subcategories
        :param model: model name for the OpenAI API
        :param sparsity: fraction of random weights above the diagonal
        """
        self.labels = []
        self.matrix = None
        self.themes_dict = themes_dict
        self.openai_api_key = openai_api_key
        self.prompt_text = prompt_text
        self.model = model
        self.sparsity = sparsity

        # If no themes_dict is provided, but we have an OpenAI key and a prompt,
        # we can try generating the dictionary from GPT:
        if self.themes_dict is None and self.openai_api_key and self.prompt_text:
            self.themes_dict = self._generate_themes_from_llm()

        if self.themes_dict is None:
            # Fallback to a default static dictionary with 5 top-level categories
            self.themes_dict = self._get_default_goto_market_dict()

        self.build_fim()

    def _generate_themes_from_llm(self):
        """
        Calls the OpenAI API to generate a dictionary of top-level themes and subcategories
        based on a user-provided prompt. The prompt should describe the "going from zero to one"
        go-to-market scenario or any other scenario you'd like subdivided.
        """
        openai.api_key = self.openai_api_key

        # A chat-based call to OpenAI to parse or create a suitable dictionary
        # For example, you might prompt the model to list 5 major categories with 2–5 subcategories each
        # We'll attempt to parse a JSON structure from the response
        response = openai.ChatCompletion.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an AI that generates hierarchical categories."},
                {
                    "role": "user",
                    "content": (
                        f"Please read the following scenario:\n\n{self.prompt_text}\n\n"
                        "Now, create a dictionary-like JSON that has exactly 5 top-level themes, "
                        "each theme having 3-5 subcategories for a go-to-market plan. "
                        "Return only valid JSON. Example:\n\n"
                        "{\n"
                        "  \"Theme1\": [\"Sub1\", \"Sub2\", ...],\n"
                        "  \"Theme2\": [...],\n"
                        "  ...\n"
                        "}"
                    ),
                },
            ],
            temperature=0.3,
        )

        raw_content = response["choices"][0]["message"]["content"]

        try:
            # Attempt to parse the JSON output:
            themes = eval(raw_content)
            # It's safer to use json.loads, but some LLM responses might need eval if quotes are mismatched.
            # If using json.loads, do: import json; themes = json.loads(raw_content)
        except:
            themes = {
                "Market Positioning": ["Unique Value Prop", "Pricing Strategy", "Brand Strategy"],
                "Sales Strategy": ["Lead Generation", "Conversion Tactics", "Key Accounts"],
                "Partnerships": ["Strategic Alliances", "Vendor Partnerships", "Creative Collaborations"],
                "Regulatory & Governance": ["Compliance Standards", "Legal Review", "Risk Assessment"],
                "Financial Model": ["Revenue Streams", "Cost Structure", "Capital Expenditure"]
            }

        return themes

    def _get_default_goto_market_dict(self):
        """
        Returns a static dictionary that outlines 5 top-level categories with subcategories
        for a typical 'go-to-market' scenario. This is used if the user didn't provide a dictionary
        or an LLM-ready prompt.
        """
        return {
            "Market Positioning": [
                "Unique Value Prop",
                "Pricing Strategy",
                "Brand Strategy",
                "Segment Prioritization"
            ],
            "Sales Strategy": [
                "Lead Generation",
                "Lead Nurturing",
                "Conversion Tactics"
            ],
            "Partnerships": [
                "Strategic Alliances",
                "Vendor Partnerships",
                "Creative Collaborations"
            ],
            "Regulatory & Governance": [
                "Compliance Standards",
                "Legal Review",
                "Risk Assessment"
            ],
            "Financial Model": [
                "Revenue Streams",
                "Capital Expenditure",
                "Operational Expenditure"
            ]
        }

    def build_fim(self):
        """
        Constructs the Fractal Identity Matrix using self.themes_dict,
        then fills the upper-right portion of the matrix with random values
        at ~self.sparsity fraction to keep it somewhat sparse.
        """
        # Collect all labels (themes and subcategories)
        self.labels.clear()
        for theme, subcategories in self.themes_dict.items():
            self.labels.append(theme)
            self.labels.extend(subcategories)

        size = len(self.labels)
        self.matrix = np.zeros((size, size))

        # Identity on the diagonal
        np.fill_diagonal(self.matrix, 1)

        # Assign weights for theme <-> subcategory
        index_map = {label: idx for idx, label in enumerate(self.labels)}
        for theme, subcategories in self.themes_dict.items():
            theme_idx = index_map[theme]
            for subcat in subcategories:
                subcat_idx = index_map[subcat]
                self.matrix[theme_idx, subcat_idx] = 0.5
                self.matrix[subcat_idx, theme_idx] = 0.5

        # Fill upper-right region with random values at 'self.sparsity' fraction
        for i in range(size):
            for j in range(i+1, size):
                if np.random.random() < self.sparsity:
                    self.matrix[i, j] = np.random.random()
                # optionally, keep the lower-left mirrored if you want symmetric:
                # self.matrix[j, i] = self.matrix[i, j]

    def get_matrix(self):
        """
        :return: The numpy matrix representing the fractal identity structure
        """
        return self.matrix

    def get_labels(self):
        """
        :return: The list of labels, in the same order as the matrix rows/columns
        """
        return self.labels 