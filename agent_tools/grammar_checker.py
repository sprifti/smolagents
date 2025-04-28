from smolagents import Tool
from langchain_openai.llms import OpenAI

from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

import nltk


class GrammarChecker(Tool):
    name = "GrammarChecker"
    description = "Checks grammar in Albanian text and returns corrections in structured JSON."
    inputs = {
        "text": {
            "type": "string",
            "description": "Albanian text",
        }
    }

    output_type = "string"

    def __init__(self):

        try:
            nltk.download('punkt')
            self.tokenizer = nltk.tokenize.word_tokenize
        except:
            print("Could not initialize NLTK resources")

        self.llm = OpenAI(temperature=0)

        grammar_template = """
        You are an expert in Albanian language grammar. 
        You are an expert in Albanian language grammar. 
        Analyze the following Albanian text for grammatical errors, spelling mistakes, and improper punctuation.
        
        Text to analyze: {text}
        
        ORIGINAL TEXT:
        [The original text]
        
        GRAMMATICAL ERRORS:
        1. Error: [first error]
           Correction: [correction]
           Explanation: [brief explanation]
        2. Error: [second error]
           Correction: [correction]
           Explanation: [brief explanation]
        
        CORRECTED TEXT:
        [The fully corrected text]
        
        If no errors are found, simply state "No grammatical errors found" under GRAMMATICAL ERRORS. """

        grammar_prompt = PromptTemplate(
            input_variables=["text"],
            template=grammar_template
        )

        self.grammar_chain = grammar_prompt | self.llm

    def forward(self, text: str):
        try:
            result = self.grammar_chain.invoke({"text": text})
            return result
        except Exception as e:
            return str({"error": str(e)})
