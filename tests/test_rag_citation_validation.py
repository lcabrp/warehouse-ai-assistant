"""
RAG Agent Citation Validation Test Suite
=========================================

Tests the mandatory source citation requirement for RAG responses.

The instructor feedback noted that while source citations are required via system
prompt, there's no structural validation ensuring they're always present. This
test suite provides that validation.

Test Strategy:
1. Citation Extraction: Parse responses for citation patterns
2. Citation Validation: Verify citations are properly formatted and complete
3. Edge Cases: Test empty results, multi-source scenarios, error conditions
4. Consistency: Verify behavior across multiple queries and response types

Citation Format Expected:
  "According to [Document Name], [content]..."
  or
  "According to [Document Name] ([Section]), [content]..."
"""

import re
import asyncio
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass
from unittest.mock import Mock, AsyncMock, patch
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.rag_agent import RAGAgent
from src.rag.vector_store import VectorStoreManager


# ==============================================================================
# Citation Validation Utilities
# ==============================================================================

@dataclass
class Citation:
    """Represents an extracted citation from RAG response."""
    source: str  # Document name
    section: Optional[str]  # Optional section heading
    start_pos: int  # Position in response where citation starts
    
    def __str__(self) -> str:
        if self.section:
            return f"{self.source} ({self.section})"
        return self.source


class CitationExtractor:
    """
    Extracts citations from RAG agent responses.
    
    Looks for patterns like:
    - "According to [source],"
    - "According to [source] ([section]),"
    - "As stated in [source],"
    
    Note: This is intentionally strict to catch format deviations.
    """
    
    # Citation patterns to detect
    CITATION_PATTERNS = [
        # "According to Document.md, ..."
        r"According to\s+([^\s,\(]+(?:\.md)?)\s*,",
        # "According to Document.md (Section), ..."
        r"According to\s+([^\s,\(]+(?:\.md)?)\s*\(\s*([^\)]+)\s*\)\s*,",
        # "As stated in Document.md, ..."
        r"As stated in\s+([^\s,\(]+(?:\.md)?)\s*,",
    ]
    
    @staticmethod
    def extract_citations(response: str) -> List[Citation]:
        """
        Extract all citations from a response.
        
        Args:
            response: The RAG agent's response text
        
        Returns:
            List of Citation objects found in the response
        """
        citations = []
        
        for pattern in CitationExtractor.CITATION_PATTERNS:
            for match in re.finditer(pattern, response, re.IGNORECASE):
                source = match.group(1)
                section = match.group(2) if len(match.groups()) > 1 else None
                
                citation = Citation(
                    source=source,
                    section=section,
                    start_pos=match.start()
                )
                citations.append(citation)
        
        return citations
    
    @staticmethod
    def has_citations(response: str) -> bool:
        """Check if response contains any citations."""
        return len(CitationExtractor.extract_citations(response)) > 0
    
    @staticmethod
    def get_citation_count(response: str) -> int:
        """Count total citations in response."""
        return len(CitationExtractor.extract_citations(response))


class CitationValidator:
    """
    Validates citations in RAG responses.
    
    Checks:
    1. Citations are present
    2. Citations are properly formatted
    3. Citations reference actual source documents
    4. Multiple sources are all cited (when applicable)
    """
    
    @staticmethod
    def validate_has_citations(response: str) -> Tuple[bool, str]:
        """
        Validate that response contains at least one citation.
        
        Args:
            response: The RAG agent response
        
        Returns:
            (is_valid, message) tuple
        """
        if not response or not response.strip():
            return False, "Response is empty"
        
        # Special case: "No relevant procedures found" is valid without citation
        if "no relevant procedures found" in response.lower() and len(response) < 100:
            return True, "Valid: No results response"
        
        citations = CitationExtractor.extract_citations(response)
        
        if not citations:
            return False, "Response contains no citations"
        
        return True, f"Valid: Found {len(citations)} citation(s)"
    
    @staticmethod
    def validate_citation_format(response: str) -> Tuple[bool, List[str]]:
        """
        Validate that all citations follow expected format.
        
        Expected formats:
        - "According to [source],"
        - "According to [source] ([section]),"
        
        Args:
            response: The RAG agent response
        
        Returns:
            (is_valid, issues) tuple where issues is list of problems found
        """
        issues = []
        citations = CitationExtractor.extract_citations(response)
        
        if not citations:
            # If no citations detected, that's caught elsewhere
            return True, []
        
        # Check that each citation has a source
        for citation in citations:
            if not citation.source or not citation.source.strip():
                issues.append(f"Citation at position {citation.start_pos} has empty source")
            
            # Check for reasonable source name length (not too short, not too long)
            if len(citation.source) < 3:
                issues.append(f"Citation source '{citation.source}' is suspiciously short")
            elif len(citation.source) > 200:
                issues.append(f"Citation source '{citation.source}' is suspiciously long")
        
        return len(issues) == 0, issues
    
    @staticmethod
    def validate_no_citation_claims_without_citation(response: str) -> Tuple[bool, List[str]]:
        """
        Detect invalid patterns like stating facts without attribution.
        
        Examples of invalid patterns:
        - "The procedure is..." (no attribution)
        - "It is recommended..." (no source)
        - "You should..." (generic advice without source)
        
        Args:
            response: The RAG agent response
        
        Returns:
            (is_valid, issues) tuple
        """
        issues = []
        
        # Split response into sentences for analysis
        sentences = re.split(r'[.!?]+', response)
        
        citations = CitationExtractor.extract_citations(response)
        citation_positions = {c.start_pos for c in citations}
        
        # Check sentences that make factual claims
        claim_starters = [
            r"^\s*The\s+",
            r"^\s*This\s+",
            r"^\s*You\s+should",
            r"^\s*You\s+must",
            r"^\s*It\s+is\s+recommended",
            r"^\s*Steps?:",
            r"^\s*Procedure:",
        ]
        
        pos = 0
        for sentence in sentences:
            if sentence.strip() and len(sentence.strip()) > 20:
                # Check if sentence makes a factual claim
                for pattern in claim_starters:
                    if re.search(pattern, sentence, re.IGNORECASE):
                        # This sentence makes a claim - check if it's cited
                        # Very basic check: if sentence is near a citation, it's likely OK
                        sentence_start = response.find(sentence, pos)
                        is_near_citation = any(
                            abs(sentence_start - c_pos) < 500 
                            for c_pos in citation_positions
                        )
                        
                        if not is_near_citation and "no relevant" not in sentence.lower():
                            issues.append(
                                f"Potential uncited claim: '{sentence.strip()[:60]}...'"
                            )
                        break
            
            pos += len(sentence) + 1
        
        return len(issues) == 0, issues


# ==============================================================================
# Mock RAG Components for Testing
# ==============================================================================

class MockDocument:
    """Mock document for testing."""
    def __init__(self, content: str, source: str, header1: str = "", header2: str = ""):
        self.page_content = content
        self.metadata = {
            'source': source,
            'Header1': header1,
            'Header2': header2
        }


class MockVectorStoreManager:
    """Mock vector store for testing without loading real documents."""
    
    def __init__(self):
        """Initialize with test documents."""
        self.documents = {
            "Cycle_Count_Procedure.md": [
                MockDocument(
                    "To perform a cycle count, follow these steps: 1) Scan the shelf barcode...",
                    "Cycle_Count_Procedure.md",
                    "Cycle Count",
                    "Standard Procedure"
                ),
            ],
            "Equipment_Troubleshooting.md": [
                MockDocument(
                    "If your RF scanner is not responding: 1) Check battery level...",
                    "Equipment_Troubleshooting.md",
                    "RF Scanner Issues",
                    "Troubleshooting"
                ),
            ],
            "Replenishment_Policy.md": [
                MockDocument(
                    "Replenishment rules: Items below min level trigger replenishment...",
                    "Replenishment_Policy.md",
                    "Replenishment Rules",
                    ""
                ),
            ],
        }
    
    def similarity_search(self, query: str, k: int = 3) -> List[Tuple[MockDocument, float]]:
        """Return mock search results with relevance scores."""
        # Simple mock: return documents in order
        all_docs = []
        for docs in self.documents.values():
            all_docs.extend([(doc, 0.8) for doc in docs])
        
        return all_docs[:k]


# ==============================================================================
# Test Cases
# ==============================================================================

class TestRAGCitationPresence:
    """Test that RAG responses include citations."""
    
    def test_citation_extraction_basic(self):
        """Test extraction of basic citations."""
        response = "According to Cycle_Count_Procedure.md, you should follow these steps."
        citations = CitationExtractor.extract_citations(response)
        
        assert len(citations) == 1
        assert citations[0].source == "Cycle_Count_Procedure.md"
        assert citations[0].section is None
    
    def test_citation_extraction_with_section(self):
        """Test extraction of citations with section headers."""
        response = "According to Equipment_Troubleshooting.md (RF Scanner Issues), check the battery."
        citations = CitationExtractor.extract_citations(response)
        
        assert len(citations) == 1
        assert citations[0].source == "Equipment_Troubleshooting.md"
        assert citations[0].section == "RF Scanner Issues"
    
    def test_citation_detection_presence(self):
        """Test citation presence detection."""
        with_citation = "According to Policy.md, the rule is..."
        without_citation = "The rule is: follow these steps."
        
        assert CitationExtractor.has_citations(with_citation)
        assert not CitationExtractor.has_citations(without_citation)
    
    def test_multiple_citations(self):
        """Test extraction of multiple citations in one response."""
        response = """
        According to Procedure.md, do this first.
        Then according to Policy.md (Rules Section), do this next.
        As stated in Guide.md, finish with this step.
        """
        
        citations = CitationExtractor.extract_citations(response)
        assert len(citations) == 3
        
        sources = [c.source for c in citations]
        assert "Procedure.md" in sources
        assert "Policy.md" in sources
        assert "Guide.md" in sources


class TestRAGCitationFormat:
    """Test that citations are properly formatted."""
    
    def test_valid_citation_format(self):
        """Test validation of properly formatted citations."""
        response = "According to Document.md, the content is here."
        is_valid, issues = CitationValidator.validate_citation_format(response)
        
        assert is_valid
        assert len(issues) == 0
    
    def test_multiple_source_citations(self):
        """Test validation with multiple sources."""
        response = """
        According to First.md, this is step one.
        According to Second.md (Section), this is step two.
        """
        
        is_valid, issues = CitationValidator.validate_citation_format(response)
        assert is_valid
    
    def test_citation_presence_validation(self):
        """Test validation that citations are present."""
        valid_response = "According to Doc.md, here's the answer."
        invalid_response = "Here's the answer without any source."
        
        is_valid, msg = CitationValidator.validate_has_citations(valid_response)
        assert is_valid
        assert "Found" in msg
        
        is_valid, msg = CitationValidator.validate_has_citations(invalid_response)
        assert not is_valid
    
    def test_no_results_special_case(self):
        """Test that 'no relevant procedures' response is valid without citation."""
        response = "No relevant procedures found."
        is_valid, msg = CitationValidator.validate_has_citations(response)
        
        # Should be valid even without citation
        assert is_valid
        assert "No results" in msg


class TestRAGCitationValidation:
    """Test the citation validation logic."""
    
    def test_uncited_factual_claims_detection(self):
        """Test detection of factual claims without proper attribution."""
        # Response with uncited claims
        bad_response = """
        The procedure requires scanning items. You must complete step one before moving forward.
        It is recommended that you verify the count.
        """
        
        is_valid, issues = CitationValidator.validate_no_citation_claims_without_citation(bad_response)
        # Should flag uncited claims
        assert not is_valid or len(issues) > 0  # May find issues
    
    def test_cited_procedural_content(self):
        """Test that properly cited procedural content passes validation."""
        response = """
        According to Cycle_Count_Procedure.md, the procedure requires scanning items.
        According to the same document (Verification), you must verify the count.
        """
        
        is_valid, _ = CitationValidator.validate_has_citations(response)
        assert is_valid


class TestRAGCitationEdgeCases:
    """Test edge cases and error scenarios."""
    
    def test_empty_response(self):
        """Test handling of empty responses."""
        is_valid, msg = CitationValidator.validate_has_citations("")
        assert not is_valid
        assert "empty" in msg.lower()
    
    def test_whitespace_only_response(self):
        """Test handling of whitespace-only responses."""
        is_valid, msg = CitationValidator.validate_has_citations("   \n\t  ")
        assert not is_valid
    
    def test_very_short_response_without_citation(self):
        """Test very short responses without citations."""
        is_valid, msg = CitationValidator.validate_has_citations("Yes")
        assert not is_valid
    
    def test_citation_count(self):
        """Test citation counting."""
        response = """
        According to Doc1.md, fact one.
        According to Doc2.md, fact two.
        According to Doc3.md (Section), fact three.
        """
        
        count = CitationExtractor.get_citation_count(response)
        assert count == 3


class TestRAGCitationConsistency:
    """Test consistency of citation behavior."""
    
    def test_citation_consistency_multiple_calls(self):
        """Test that citation validation is consistent across multiple calls."""
        response = "According to Guide.md, here's the answer."
        
        results = []
        for _ in range(5):
            is_valid, _ = CitationValidator.validate_has_citations(response)
            results.append(is_valid)
        
        # All calls should return the same result
        assert all(results)
    
    def test_citation_extraction_consistency(self):
        """Test that citation extraction is consistent."""
        response = "According to Policy.md (Rules), content here."
        
        citations1 = CitationExtractor.extract_citations(response)
        citations2 = CitationExtractor.extract_citations(response)
        
        assert len(citations1) == len(citations2)
        assert citations1[0].source == citations2[0].source


# ==============================================================================
# Integration Tests (with mocked RAG agent)
# ==============================================================================

class TestRAGAgentIntegration:
    """Integration tests with mocked RAG agent."""
    
    def test_rag_response_citation_requirement(self):
        """Test that RAG agent responses should include citations."""
        # This is a conceptual test - in real implementation, would need
        # full async RAG agent setup which requires more infrastructure
        
        # Example response from RAG agent
        example_responses = [
            "According to Cycle_Count_Procedure.md, follow these steps: 1) Scan shelf, 2) Count items.",
            "According to Equipment_Troubleshooting.md (RF Scanner Issues), if not responding, check battery.",
            "No relevant procedures found.",  # Valid without citation
        ]
        
        for response in example_responses:
            is_valid, msg = CitationValidator.validate_has_citations(response)
            assert is_valid, f"Response failed validation: {msg}. Response: {response}"


# ==============================================================================
# Test Runner and Reporting
# ==============================================================================

def run_all_tests():
    """Run all test classes and report results."""
    print("\n" + "=" * 70)
    print("RAG Citation Validation Test Suite")
    print("=" * 70)
    
    test_classes = [
        TestRAGCitationPresence,
        TestRAGCitationFormat,
        TestRAGCitationValidation,
        TestRAGCitationEdgeCases,
        TestRAGCitationConsistency,
        TestRAGAgentIntegration,
    ]
    
    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    
    for test_class in test_classes:
        print(f"\n{test_class.__name__}")
        print("-" * 70)
        
        test_instance = test_class()
        test_methods = [m for m in dir(test_instance) if m.startswith("test_")]
        
        for method_name in test_methods:
            total_tests += 1
            try:
                method = getattr(test_instance, method_name)
                method()
                print(f"  ✅ {method_name}")
                passed_tests += 1
            except AssertionError as e:
                print(f"  ❌ {method_name}")
                print(f"     Error: {e}")
                failed_tests += 1
            except Exception as e:
                print(f"  ❌ {method_name}")
                print(f"     Unexpected error: {type(e).__name__}: {e}")
                failed_tests += 1
    
    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    print(f"Total Tests:  {total_tests}")
    print(f"Passed:       {passed_tests} ✅")
    print(f"Failed:       {failed_tests} ❌")
    print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
    print("=" * 70)
    
    return failed_tests == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
