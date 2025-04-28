"""
Test Script for Albanian Text Analysis Agent

This script tests the functionality of the Albanian Text Analysis Agent
by running it on various sample texts and verifying its outputs with string format.
"""
from dotenv import load_dotenv

import unittest
import re

from agent import AlbanianTextAgent

load_dotenv()


class TestAlbanianTextAgent(unittest.TestCase):
    """Test cases for the Albanian Text Analysis Agent."""

    def setUp(self):
        """Initialize the agent before each test."""
        self.agent = AlbanianTextAgent()

    def test_grammar_checking(self):
        """Test the grammar checking functionality."""
        # Text with deliberate grammar errors in Albanian
        test_text = "Une jam shume i geezuar qe po ju shkruaj. Ky tekst ka disa gabime gramatikore."

        results = self.agent.forward(test_text)

        # Parse the grammar analysis result
        grammar_results = extract_grammar_info(results)

        # Verify that grammar errors were found
        self.assertTrue(len(grammar_results["errors"]) > 0, "Grammar checker should find errors")
        self.assertIsNotNone(grammar_results["corrected_text"], "Grammar checker should provide corrected text")

        print("\nGrammar Check Test:")
        print(f"Original: {test_text}")
        print(f"Errors found: {len(grammar_results['errors'])}")
        print(f"Corrected: {grammar_results['corrected_text']}")

    def test_tone_analysis(self):
        """Test the tone analysis functionality."""
        # Formal Albanian text
        formal_text = """
        I nderuar zotëri, 
        Ju njoftojmë se kërkesa juaj është marrë në konsideratë dhe do të shqyrtohet 
        nga departamenti përkatës. Ju do të njoftoheni për vendimin brenda afatit ligjor.
        Me respekt,
        Administrata
        """

        results = self.agent.forward(formal_text)

        # Parse the tone analysis result
        tone_results = extract_tone_info(results)

        # Verify tone analysis results
        self.assertIn("tone", tone_results, "Tone analysis should identify the tone")
        self.assertIn("formality_level", tone_results, "Tone analysis should provide formality level")

        print("\nTone Analysis Test (Formal Text):")
        print(f"Text: {formal_text[:50]}...")
        print(f"Identified tone: {tone_results['tone']}")
        print(f"Formality level: {tone_results['formality_level']}")

        # Informal Albanian text
        informal_text = """
        Ej shoku, si je? Kam kohë pa të parë! Çfarë ke bërë? 
        Hajde të takohemi për një kafe kur të kesh kohë. Më thuaj kur je i lirë!
        """

        results = self.agent.forward(informal_text)

        # Parse the tone analysis result
        tone_results = extract_tone_info(results)

        print("\nTone Analysis Test (Informal Text):")
        print(f"Text: {informal_text[:50]}...")
        print(f"Identified tone: {tone_results['tone']}")
        print(f"Formality level: {tone_results['formality_level']}")

    def test_tone_rewriting(self):
        """Test the tone rewriting functionality."""
        # Neutral Albanian text
        neutral_text = """
        Projekti do të fillojë më datë 10 Maj. Të gjithë pjesëmarrësit duhet të dorëzojnë 
        dokumentet e nevojshme para kësaj date. Takimi i parë do të mbahet në zyrën qendrore.
        """

        # Test general tone alternatives
        results = self.agent.forward(neutral_text)

        # Parse the tone alternatives result
        tone_alternatives = extract_alternatives_info(results)

        # Verify tone alternatives results
        self.assertIn("tone_options", tone_alternatives, "Tone rewriter should provide alternative tones")
        self.assertTrue(len(tone_alternatives["tone_options"]) > 0, "Multiple tone options should be provided")

        print("\nTone Rewriting Test (Multiple Options):")
        print(f"Original: {neutral_text[:50]}...")
        for i, option in enumerate(tone_alternatives["tone_options"]):
            print(f"Option {i + 1} ({option['tone']}): {option['text'][:50]}...")

        # Test specific tone rewriting
        target_tone = "friendly"
        results = self.agent.forward(neutral_text, target_tone=target_tone)

        # Parse the specific tone rewrite result
        specific_tone = extract_alternatives_info(results)

        # Verify specific tone rewriting
        self.assertIn("target_tone", specific_tone, "Specific tone rewriting should identify target tone")
        self.assertEqual(specific_tone["target_tone"].lower(), target_tone.lower(),
                         "Target tone should match requested tone")

        print(f"\nTone Rewriting Test (Specific {target_tone} tone):")
        print(f"Original: {neutral_text[:50]}...")
        print(f"Rewritten: {specific_tone['rewritten_text'][:50]}...")

    def test_comprehensive_analysis(self):
        """Test the full agent workflow with a complex text."""
        complex_text = """
        Pershendetje koleg! Desha të të informoj për vendimin e mbledhjes se sotme.
        Kemi vendosur të vazhdojme me projektin e ri, por na duhen më shumë burime.
        Ti mund të pershtateni me keto ndryshime? Më thuaj sa më shpejt që të mundesh.
        """

        results = self.agent.forward(complex_text)

        # Verify that we get results (we're not checking specific components since it's a string)
        self.assertTrue(results, "Agent should return results")

        # Check for key indicators that suggest all components are included
        grammar_indicators = ["ORIGINAL TEXT", "GRAMMATICAL ERRORS", "CORRECTED TEXT"]
        tone_indicators = ["TONE", "FORMALITY LEVEL", "SENTIMENT"]
        alternatives_indicators = ["FORMAL TONE VERSION", "FRIENDLY TONE VERSION", "PERSUASIVE TONE VERSION"]

        has_grammar = any(indicator in results for indicator in grammar_indicators)
        has_tone = any(indicator in results for indicator in tone_indicators)
        has_alternatives = any(indicator in results for indicator in alternatives_indicators)

        self.assertTrue(has_grammar, "Results should include grammar analysis")
        self.assertTrue(has_tone, "Results should include tone analysis")
        self.assertTrue(has_alternatives, "Results should include tone alternatives")

        print("\nComprehensive Analysis Test:")
        print(f"Original: {complex_text}")
        print("All analysis components successfully returned results.")


# Helper functions to parse the string output into structured data

def extract_grammar_info(text):
    """Extract grammar information from the text output."""
    result = {
        "original_text": "",
        "errors": [],
        "corrected_text": ""
    }

    # Extract original text
    original_text = extract_text_between(text, "ORIGINAL TEXT:",
                                     ["GRAMMATICAL ERRORS:", "CORRECTED TEXT:"])
    if original_text:
        result["original_text"] = original_text

    # Extract errors
    errors_text = extract_text_between(text, "GRAMMATICAL ERRORS:",
                                    ["CORRECTED TEXT:", "TONE:"])

    if errors_text and "No grammatical errors found" not in errors_text:
        # Try to parse numbered list format
        error_items = []
        number_pattern = re.compile(r'^\d+\.\s')

        if re.search(number_pattern, errors_text):
            error_items = re.split(number_pattern, errors_text)
            # First item may be empty or header text
            error_items = [item for item in error_items if item.strip()]

            for item in error_items:
                lines = item.split('\n')
                error_detail = {}

                for line in lines:
                    line = line.strip()
                    if "Error:" in line:
                        error_detail["error_text"] = line.split("Error:")[1].strip()
                    elif "Correction:" in line:
                        error_detail["correction"] = line.split("Correction:")[1].strip()
                    elif "Explanation:" in line:
                        error_detail["explanation"] = line.split("Explanation:")[1].strip()

                if "error_text" in error_detail:
                    result["errors"].append(error_detail)

        # If we couldn't parse numbered list, try line-by-line
        if not result["errors"]:
            current_error = {}
            lines = errors_text.split('\n')
            for line in lines:
                line = line.strip()
                if "Error:" in line:
                    if current_error and "error_text" in current_error:
                        result["errors"].append(current_error)
                        current_error = {}
                    current_error["error_text"] = line.split("Error:")[1].strip()
                elif "Correction:" in line and current_error:
                    current_error["correction"] = line.split("Correction:")[1].strip()
                elif "Explanation:" in line and current_error:
                    current_error["explanation"] = line.split("Explanation:")[1].strip()

            if current_error and "error_text" in current_error:
                result["errors"].append(current_error)

    # Extract corrected text
    corrected_text = extract_text_between(text, "CORRECTED TEXT:",
                                      ["TONE:", "FORMALITY LEVEL:"])
    if corrected_text:
        result["corrected_text"] = corrected_text

    return result


def extract_tone_info(text):
    """Extract tone information from the text output."""
    result = {
        "tone": "",
        "formality_level": "",
        "sentiment": "",
        "tone_analysis": ""
    }

    # Extract tone
    tone = extract_text_between(text, "TONE:", ["FORMALITY LEVEL:", "SENTIMENT:"])
    if tone:
        result["tone"] = tone

    # Extract formality level
    formality_level = extract_text_between(text, "FORMALITY LEVEL:", ["SENTIMENT:", "TONE ANALYSIS:"])
    if formality_level:
        result["formality_level"] = formality_level

    # Extract sentiment
    sentiment = extract_text_between(text, "SENTIMENT:", ["TONE ANALYSIS:", "ORIGINAL TONE:"])
    if sentiment:
        result["sentiment"] = sentiment

    # Extract tone analysis
    tone_analysis = extract_text_between(text, "TONE ANALYSIS:", ["ORIGINAL TONE:"])
    if tone_analysis:
        result["tone_analysis"] = tone_analysis

    return result


def extract_alternatives_info(text):
    """Extract tone alternatives information from the text output."""
    result = {
        "original_tone": "",
        "tone_options": []
    }

    # Extract original tone
    original_tone = extract_text_between(text, "ORIGINAL TONE:",
                                      ["TARGET TONE:", "FORMAL TONE VERSION:"])
    if original_tone:
        result["original_tone"] = original_tone

    # Check if it's a specific target tone rewrite
    target_tone = extract_text_between(text, "TARGET TONE:", ["REWRITTEN TEXT:"])
    rewritten_text = extract_text_between(text, "REWRITTEN TEXT:", [])

    if target_tone and rewritten_text:
        result["target_tone"] = target_tone
        result["rewritten_text"] = rewritten_text
        return result

    # Check for multiple tone options
    formal_tone = extract_text_between(text, "FORMAL TONE VERSION:",
                                   ["FRIENDLY TONE VERSION:", "PERSUASIVE TONE VERSION:"])

    friendly_tone = extract_text_between(text, "FRIENDLY TONE VERSION:",
                                     ["PERSUASIVE TONE VERSION:"])

    persuasive_tone = extract_text_between(text, "PERSUASIVE TONE VERSION:", [])

    if formal_tone:
        result["tone_options"].append({"tone": "Formal", "text": formal_tone})

    if friendly_tone:
        result["tone_options"].append({"tone": "Friendly", "text": friendly_tone})

    if persuasive_tone:
        result["tone_options"].append({"tone": "Persuasive", "text": persuasive_tone})

    return result


def extract_text_between(text, start_marker, end_markers):
    """
    Extract text between a start marker and the first occurrence of any end marker.

    Args:
        text: The text to search in
        start_marker: The starting marker
        end_markers: List of possible end markers

    Returns:
        Extracted text or empty string if not found
    """
    if not text or not start_marker:
        return ""

    # Find the start position
    start_pos = text.find(start_marker)
    if start_pos == -1:
        return ""

    # Move past the start marker
    start_pos += len(start_marker)

    # Find the earliest end marker
    end_pos = len(text)
    for marker in end_markers:
        if not marker:
            continue
        pos = text.find(marker, start_pos)
        if pos != -1 and pos < end_pos:
            end_pos = pos

    # Extract the text
    extracted = text[start_pos:end_pos].strip()
    return extracted


def main():
    """Run the tests with detailed output."""
    # Create a test suite
    suite = unittest.TestSuite()
    suite.addTest(TestAlbanianTextAgent('test_grammar_checking'))
    suite.addTest(TestAlbanianTextAgent('test_tone_analysis'))
    suite.addTest(TestAlbanianTextAgent('test_tone_rewriting'))
    suite.addTest(TestAlbanianTextAgent('test_comprehensive_analysis'))

    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)


if __name__ == "__main__":
    main()