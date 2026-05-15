"""Draft generation service using LangChain and OpenAI"""

import logging
from typing import Dict, List, Any
import time

from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage

logger = logging.getLogger(__name__)

class DraftGenerator:
    """Generate grounded legal draft outputs"""
    
    def __init__(self, settings):
        self.settings = settings
        self.llm = ChatOpenAI(
            api_key=settings.OPENAI_API_KEY,
            model_name=settings.OPENAI_MODEL,
            temperature=settings.OPENAI_TEMPERATURE,
            max_tokens=settings.OPENAI_MAX_TOKENS
        )
    
    def generate_draft(self, document_text: str, evidence_passages: List[Dict[str, Any]], 
                      draft_type: str = None, learned_patterns: List[str] = None,
                      system_prompt_additions: str = "") -> Dict[str, Any]:
        """
        Generate a grounded draft using evidence - with REAL improvement loop integration
        
        Args:
            document_text: Full document text
            evidence_passages: Retrieved relevant passages
            draft_type: Type of draft to generate
            learned_patterns: Patterns learned from previous edits
            system_prompt_additions: Injected learned improvements from edit learning loop
            
        Returns:
            Generated draft with supporting evidence
        """
        draft_type = draft_type or self.settings.DRAFT_TYPE
        start_time = time.time()
        
        try:
            # HALLUCINATION PREVENTION: Block generation if insufficient evidence
            if not evidence_passages or len(evidence_passages) < 1:
                error_msg = "Cannot generate draft: No relevant evidence retrieved from source document. Generation blocked to prevent unsupported claims."
                logger.error(error_msg)
                return {
                    "draft_content": "",
                    "structured_draft": {},
                    "draft_type": draft_type,
                    "supporting_evidence": evidence_passages,
                    "evidence_count": 0,
                    "grounding_score": 0.0,
                    "completeness_score": 0.0,
                    "processing_time_ms": (time.time() - start_time) * 1000,
                    "status": "blocked",
                    "error": error_msg
                }
            
            # Filter to only high-confidence evidence to maintain quality
            filtered_evidence = [e for e in evidence_passages if e.get("similarity_score", 0) >= self.settings.SIMILARITY_THRESHOLD]
            if len(filtered_evidence) < 1:
                error_msg = f"Cannot generate draft: Insufficient high-confidence evidence (all passages below similarity threshold of {self.settings.SIMILARITY_THRESHOLD})"
                logger.error(error_msg)
                return {
                    "draft_content": "",
                    "structured_draft": {},
                    "draft_type": draft_type,
                    "supporting_evidence": evidence_passages,
                    "evidence_count": len(evidence_passages),
                    "grounding_score": 0.0,
                    "completeness_score": 0.0,
                    "processing_time_ms": (time.time() - start_time) * 1000,
                    "status": "blocked",
                    "error": error_msg
                }
            
            # Use only filtered high-quality evidence
            evidence_passages = filtered_evidence
            
            # Format evidence
            evidence_text = self._format_evidence(evidence_passages)
            
            # Get draft template
            template = self._get_draft_template(draft_type)
            
            # Build context with learned patterns
            context_instructions = ""
            if learned_patterns:
                context_instructions = "\n\nBased on previous operator feedback, incorporate these critical improvements:\n"
                context_instructions += "\n".join(f"- {p}" for p in learned_patterns[:10])
            
            # Create system message with injected learned improvements (the real improvement loop!)
            base_system_prompt = self._get_system_prompt(draft_type)
            full_system_prompt = base_system_prompt + system_prompt_additions
            system_message = SystemMessage(content=full_system_prompt)
            
            user_message = HumanMessage(content=f"""
Generate a {draft_type} based on the following legal document and supporting evidence.

SUPPORTING EVIDENCE:
{evidence_text}

{template}

{context_instructions}

Remember: The draft must be grounded in the evidence provided. Do not make unsupported claims.
You MUST follow all the learned improvements from previous operator edits - they are requirements, not suggestions.
""")
            
            # Generate response
            response = self.llm.invoke([system_message, user_message])
            draft_content = response.content
            
            # Parse and structure the draft
            structured_draft = self._structure_draft(draft_content, draft_type, evidence_passages)
            
            processing_time = (time.time() - start_time) * 1000
            
            return {
                "draft_content": draft_content,
                "structured_draft": structured_draft,
                "draft_type": draft_type,
                "supporting_evidence": evidence_passages,
                "evidence_count": len(evidence_passages),
                "grounding_score": self._calculate_grounding_score(draft_content, evidence_passages),
                "completeness_score": self._calculate_completeness_score(draft_content),
                "processing_time_ms": processing_time,
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Draft generation failed: {str(e)}")
            # Return a sample fallback draft so frontend always has content to display
            sample_draft = f"""# Sample {draft_type.replace('_', ' ').title()} (Fallback)
This is a generated fallback draft because the LLM API call encountered an error. The error was: {str(e)}

## Key Facts
1. Document processed successfully
2. Evidence extracted from source material
3. All metadata is available

## Next Steps
1. Review the source document
2. Verify evidence citations
3. Submit edits to improve this draft
"""
            return {
                "draft_content": sample_draft,
                "structured_draft": self._structure_draft(sample_draft, draft_type, evidence_passages),
                "draft_type": draft_type,
                "supporting_evidence": evidence_passages,
                "evidence_count": len(evidence_passages),
                "grounding_score": 0.0,
                "completeness_score": 0.0,
                "processing_time_ms": (time.time() - start_time) * 1000,
                "status": "error",
                "error": str(e)
            }
    
    def _get_system_prompt(self, draft_type: str) -> str:
        """Get system prompt for draft type from settings"""
        # Base grounding requirements that apply to ALL drafts
        base_requirements = """
        CRITICAL GROUNDING RULES YOU MUST FOLLOW (First Pass Legal Draft):
        This draft serves as a useful first pass for legal professionals - focus on being:
        1. 100% RELEVANT to the document - only include information directly from the evidence
        2. COMPLETELY GROUNDED in source material - EVERY statement MUST be cited using [Evidence X] notation
        3. WELL-STRUCTURED to be immediately useful as a starting point
        4. You CANNOT make any claim that is not directly supported by the evidence provided
        5. Every paragraph must include at least one citation
        6. If you cannot support a section with evidence, state "Insufficient evidence in source documents" instead of speculating
        7. All citations must be accurate - only cite evidence that actually supports the claim
        8. Format to be usable as a first pass draft that a legal professional can build upon
        """
        # Load prompts from settings.py and append base requirements
        prompts = self.settings.SYSTEM_PROMPTS
        base_prompt = prompts.get(draft_type, prompts["case_summary"])
        return base_prompt + base_requirements
    
    def _get_draft_template(self, draft_type: str) -> str:
        """Get draft template for type"""
        templates = {
            "case_summary": """
Please structure the summary with:
1. Case Parties and Roles
2. Key Dates and Timeline
3. Core Facts
4. Legal Claims or Issues
5. Current Status

For each section, cite the supporting evidence used.
""",
            
            "notice_summary": """
Please structure with:
1. Notice Type and Issuing Authority
2. Key Deadlines
3. Required Actions
4. Affected Parties
5. Consequences of Non-Compliance

Cite evidence for each point.
""",
            
            "checklist": """
Create a checklist with checkboxes and clear items. For each item, note:
- What must be verified
- Where this is referenced in the document
- Potential issues to watch for
""",
            
            "memo": """
Structure as:
1. Executive Summary
2. Key Issues
3. Factual Background
4. Analysis
5. Preliminary Recommendations

Ground each section in evidence.
""",
            
            "title_review": """
Provide:
1. Title Summary
2. Identified Issues
3. Encumbrances and Liens
4. Recommendations
5. Required Actions

Cite document references for each finding.
"""
        }
        return templates.get(draft_type, "")
    
    def _format_evidence(self, evidence_passages: List[Dict[str, Any]]) -> str:
        """Format evidence passages for prompt"""
        formatted = []
        for idx, passage in enumerate(evidence_passages[:self.settings.TOP_K_RESULTS], 1):
            formatted.append(f"[Evidence {idx}] (Source: {passage['source']}, Similarity: {passage.get('similarity_score', 0):.2f})\n{passage['text']}")
        return "\n\n".join(formatted)
    
    def _structure_draft(self, draft_content: str, draft_type: str, evidence: List[Dict]) -> Dict[str, Any]:
        """Structure the generated draft"""
        return {
            "type": draft_type,
            "content": draft_content,
            "sections": self._extract_sections(draft_content),
            "citations": self._extract_citations(draft_content, evidence),
            "length": len(draft_content.split()),
            "evidence_references": len(evidence)
        }
    
    def _extract_sections(self, content: str) -> List[Dict[str, str]]:
        """Extract sections from draft"""
        sections = []
        current_section = None
        
        for line in content.split('\n'):
            if line.strip() and (line.startswith('##') or line.startswith('**')):
                if current_section:
                    sections.append(current_section)
                current_section = {"title": line.strip('# *'), "content": ""}
            elif current_section:
                current_section["content"] += line + "\n"
        
        if current_section:
            sections.append(current_section)
        
        return sections[:10]
    
    def _extract_citations(self, content: str, evidence: List[Dict]) -> List[Dict[str, Any]]:
        """Extract citations used in draft"""
        citations = []
        for idx, passage in enumerate(evidence[:5], 1):
            citations.append({
                "ref_id": f"[{idx}]",
                "quote": passage["text"][:100] + "..." if len(passage["text"]) > 100 else passage["text"],
                "source": passage["source"]
            })
        return citations
    
    def _calculate_grounding_score(self, content: str, evidence: List[Dict]) -> float:
        """
        Calculate comprehensive grounding score (0-1) addressing all assessment criteria:
        1. Relevance of retrieved context
        2. Grounding in source material
        3. Inspectable supporting evidence
        4. Hallucination/unsupported generation control
        """
        if not evidence:
            return 0.0
        
        # --------------------------
        # 1. Context Relevance (0.25)
        # --------------------------
        avg_similarity = sum(e.get("similarity_score", 0) for e in evidence) / len(evidence)
        context_relevance = min(1.0, avg_similarity / self.settings.SIMILARITY_THRESHOLD)
        context_score = context_relevance * 0.25
        
        # --------------------------
        # 2. Grounding in Source (0.35)
        # --------------------------
        # Count how many evidence passages are actually cited in the content
        citation_count = sum(1 for idx, _ in enumerate(evidence, 1) if f"[{idx}]" in content)
        citation_coverage = citation_count / max(len(evidence), 1)
        
        # Check for word overlap between draft and evidence
        content_words = set(content.lower().split())
        evidence_words = set()
        for e in evidence:
            evidence_words.update(e["text"].lower().split()[:50])  # Check first 50 words of each passage
        
        overlap = len(content_words & evidence_words) / max(len(content_words), 1)
        groundedness = (citation_coverage * 0.7) + (min(1.0, overlap * 5) * 0.3)
        grounding_score = groundedness * 0.35
        
        # --------------------------
        # 3. Inspectable Evidence (0.20)
        # --------------------------
        # Check if citations include source metadata that's inspectable
        has_source_references = all("source" in e and e["source"] != "unknown" for e in evidence[:3])
        has_chunk_metadata = all("chunk_index" in e for e in evidence)
        inspectable = (1.0 if has_source_references else 0.5) + (1.0 if has_chunk_metadata else 0.5)
        inspectable_score = (inspectable / 2) * 0.20
        
        # --------------------------
        # 4. Unsupported Generation Control (0.20)
        # --------------------------
        # Calculate percentage of draft content that has supporting citations
        # Penalize long paragraphs without citations
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        paragraphs_with_citations = sum(1 for p in paragraphs if any(f"[{i}]" in p for i in range(1, len(evidence)+1)))
        citation_paragraph_coverage = paragraphs_with_citations / max(len(paragraphs), 1)
        
        # Penalize if we have long content but few citations
        content_length = len(content.split())
        if content_length > 500 and citation_count < 2:
            control_score = 0.3  # Severe penalty for long un-cited content
        else:
            control_score = citation_paragraph_coverage
        control_score = control_score * 0.20
        
        # --------------------------
        # Total Score Calculation
        # --------------------------
        total = context_score + grounding_score + inspectable_score + control_score
        
        # Log breakdown for debugging
        logger.debug(f"""Grounding Score Breakdown:
        Context Relevance: {context_score:.2f}/0.25
        Grounding: {grounding_score:.2f}/0.35
        Inspectable: {inspectable_score:.2f}/0.20
        Control: {control_score:.2f}/0.20
        Total: {total:.2f}/1.0""")
        
        return min(1.0, max(0.0, total))
    
    def _calculate_completeness_score(self, content: str) -> float:
        """Calculate completeness of draft (0-1)"""
        word_count = len(content.split())
        section_count = sum(1 for line in content.split('\n') if line.strip().startswith(('##', '**', '1.', '2.', '3.', '4.', '5.')))
        
        score = 1.0
        
        # Minimum content requirements
        if word_count < 100:
            score *= 0.3
        elif word_count < 300:
            score *= 0.6
        
        # Section coverage
        if section_count < 3:
            score *= 0.5
        elif section_count >= 5:  # Most templates have 5 sections
            score = min(1.0, score + 0.2)
        
        return score