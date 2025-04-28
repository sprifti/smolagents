from langchain_openai.llms import OpenAI
from agent_tools.grammar_checker import GrammarChecker
from agent_tools.tone_analyzer import ToneAnalyzer
from agent_tools.tone_writer import ToneRewriter
from smolagents import CodeAgent, HfApiModel

class AlbanianTextAgent(CodeAgent):
    """Agent that analyzes and improves Albanian text."""

    def __init__(self):
        # Initialize tools
        grammar_checker = GrammarChecker()
        tone_analyzer = ToneAnalyzer()
        tone_rewriter = ToneRewriter()

        llm = HfApiModel(
            model_name="ai-journey/hermes-2-pro-mistral-7b",
            temperature=0.2
        )

        super().__init__(
            tools=[grammar_checker, tone_analyzer, tone_rewriter],
            model=llm,
            name="AlbanianTextAgent",
            additional_authorized_imports=["spacy", "nltk", "textblob"]
        )

        # Store tool instances for structured use
        self.grammar_checker = grammar_checker
        self.tone_analyzer = tone_analyzer
        self.tone_rewriter = tone_rewriter

    def forward(self, text: str, target_tone: str = "") -> dict:
        results = ""

        # Step 1: Grammar check
        grammar_results = self.grammar_checker.forward(text=text)
        print(grammar_results)
        results += grammar_results + "\n"

        # Step 2: Tone analysis
        tone_results = self.tone_analyzer.forward(text=text)
        results += tone_results + "\n"
        # Step 3: Rewriting based on tone
        tone_alternatives = self.tone_rewriter.forward(text=text, target_tone=target_tone)
        results += tone_alternatives + "\n"
        return results
