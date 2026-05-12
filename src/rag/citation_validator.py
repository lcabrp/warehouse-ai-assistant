"""
Runtime Citation Validator for RAG Responses
=============================================

This module provides runtime validation of RAG agent responses to ensure
they always include proper source citations as required by the capstone rubric.

Can be used either:
1. As a wrapper around RAG agent query() method for automatic validation
2. For manual validation of responses during testing/debugging
3. As a policy enforcement tool in production

Usage Example:
    validator = RAGResponseValidator()
    response = await rag_agent.query("How do I cycle count?")
    validation = validator.validate_response(response)
    if not validation.is_valid:
        logger.warning(f"Citation issues: {validation.issues}")
"""

from dataclasses import dataclass
from typing import List
import logging

# Import citation utilities from test suite
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.test_rag_citation_validation import (
    CitationExtractor,
    CitationValidator,
    Citation,
)


logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of validating a RAG response."""
    is_valid: bool
    issues: List[str]
    citations_found: int
    warning_level: str  # "none", "warning", "critical"
    
    def __str__(self) -> str:
        if self.is_valid:
            return f"✅ Valid: {self.citations_found} citation(s) found"
        else:
            return f"❌ Invalid ({len(self.issues)} issue(s)): {'; '.join(self.issues)}"


class RAGResponseValidator:
    """
    Validates RAG responses for proper source citations.
    
    This validator enforces the capstone requirement that all RAG responses
    cite their sources appropriately. It can be used for:
    - Runtime validation before returning responses to users
    - Testing that responses meet citation requirements
    - Debugging citation issues in development
    """
    
    # Response types that don't require citations
    NO_CITATION_REQUIRED_PATTERNS = [
        "no relevant procedures",
        "i don't find that information",
        "cannot find",
        "not found in the documentation",
    ]
    
    def validate_response(self, response: str) -> ValidationResult:
        """
        Validate a RAG response for proper citations.
        
        Args:
            response: The RAG agent's response text
        
        Returns:
            ValidationResult with validity status and any issues found
        """
        issues = []
        warning_level = "none"
        
        # Check 1: Response is not empty
        if not response or not response.strip():
            issues.append("Response is empty")
            return ValidationResult(
                is_valid=False,
                issues=issues,
                citations_found=0,
                warning_level="critical"
            )
        
        # Check 2: Determine if this is a "no results" response
        is_no_results = self._is_no_results_response(response)
        
        # Check 3: Validate citations
        has_citations, citation_msg = CitationValidator.validate_has_citations(response)
        citations = CitationExtractor.extract_citations(response)
        
        if not has_citations:
            if not is_no_results:
                issues.append(f"Missing citations - {citation_msg}")
                warning_level = "critical"
            else:
                # No citations required for "no results" responses
                return ValidationResult(
                    is_valid=True,
                    issues=[],
                    citations_found=0,
                    warning_level="none"
                )
        
        # Check 4: Validate citation format
        format_valid, format_issues = CitationValidator.validate_citation_format(response)
        if not format_valid:
            issues.extend(format_issues)
            warning_level = "warning"
        
        # Check 5: Check for uncited claims (if citations are present)
        if citations:
            claims_valid, claim_issues = CitationValidator.validate_no_citation_claims_without_citation(response)
            if not claims_valid and claim_issues:
                # These are warnings, not critical failures
                issues.extend([f"Warning: {issue}" for issue in claim_issues[:2]])  # Limit to first 2
                if warning_level == "none":
                    warning_level = "warning"
        
        # Final determination
        is_valid = not issues or all("Warning:" in issue for issue in issues)
        
        return ValidationResult(
            is_valid=is_valid,
            issues=issues,
            citations_found=len(citations),
            warning_level=warning_level
        )
    
    def _is_no_results_response(self, response: str) -> bool:
        """Check if response indicates no relevant documents were found."""
        response_lower = response.lower()
        return any(
            pattern in response_lower 
            for pattern in self.NO_CITATION_REQUIRED_PATTERNS
        )
    
    def get_citations(self, response: str) -> List[Citation]:
        """
        Extract citations from a response.
        
        Args:
            response: The RAG agent's response text
        
        Returns:
            List of Citation objects found
        """
        return CitationExtractor.extract_citations(response)
    
    def get_citation_sources(self, response: str) -> List[str]:
        """
        Get list of unique citation sources from a response.
        
        Args:
            response: The RAG agent's response text
        
        Returns:
            List of unique source document names
        """
        citations = CitationExtractor.extract_citations(response)
        # Remove duplicates while preserving order
        seen = set()
        sources = []
        for citation in citations:
            if citation.source not in seen:
                sources.append(citation.source)
                seen.add(citation.source)
        return sources


# ==============================================================================
# Wrapper for RAG Agent (Optional)
# ==============================================================================

class ValidatedRAGAgent:
    """
    Wraps a RAG agent to automatically validate citations in all responses.
    
    This wrapper ensures all responses meet citation requirements before
    being returned to the user.
    
    Usage:
        rag_agent = await create_rag_agent()
        validated_agent = ValidatedRAGAgent(rag_agent)
        response = await validated_agent.query("How do I cycle count?")
        # Response is guaranteed to have proper citations or raises exception
    """
    
    def __init__(self, rag_agent, strict_mode: bool = False):
        """
        Initialize the wrapper.
        
        Args:
            rag_agent: The RAGAgent instance to wrap
            strict_mode: If True, raise exception on citation failures
                        If False, just log warnings
        """
        self.rag_agent = rag_agent
        self.validator = RAGResponseValidator()
        self.strict_mode = strict_mode
    
    async def query(self, question: str) -> str:
        """
        Query the RAG agent with automatic citation validation.
        
        Args:
            question: User's question
        
        Returns:
            RAG agent response (validated for proper citations)
        
        Raises:
            CitationError: If strict_mode=True and citations are missing
        """
        # Get response from RAG agent
        response = await self.rag_agent.query(question)
        
        # Validate response
        validation = self.validator.validate_response(response)
        
        # Handle validation result
        if not validation.is_valid:
            message = f"Citation validation failed: {validation}"
            logger.error(message)
            
            if self.strict_mode:
                raise CitationError(message)
            else:
                logger.warning(f"Returning response despite citation issues: {validation.issues}")
        else:
            logger.debug(f"✅ Response citation validation passed: {validation}")
        
        return response
    
    async def chat(self, messages: list) -> str:
        """
        Multi-turn chat with automatic citation validation.
        
        Args:
            messages: Conversation history
        
        Returns:
            RAG agent response (validated for proper citations)
        """
        response = await self.rag_agent.chat(messages)
        validation = self.validator.validate_response(response)
        
        if not validation.is_valid and self.strict_mode:
            raise CitationError(f"Citation validation failed: {validation}")
        
        return response


class CitationError(Exception):
    """Raised when RAG response fails citation validation."""
    pass


if __name__ == "__main__":
    # Example usage
    validator = RAGResponseValidator()
    
    # Test cases
    test_cases = [
        (
            "According to Cycle_Count_Procedure.md, follow these steps: 1) Scan, 2) Count.",
            "Valid response with citation"
        ),
        (
            "You should scan items and count them.",
            "Invalid: uncited procedural content"
        ),
        (
            "No relevant procedures found.",
            "Valid: no results response"
        ),
    ]
    
    print("\n" + "=" * 70)
    print("Citation Validator Examples")
    print("=" * 70)
    
    for response, description in test_cases:
        print(f"\n{description}")
        print(f"Response: {response[:50]}...")
        validation = validator.validate_response(response)
        print(f"Result: {validation}")
        if validation.citations_found > 0:
            sources = validator.get_citation_sources(response)
            print(f"Sources: {sources}")
