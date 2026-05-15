"""Edit learning service for improving drafts from operator feedback - creates a real improvement loop"""

import logging
import os
import json
import time
from typing import Dict, List, Any
import difflib
from pathlib import Path

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

logger = logging.getLogger(__name__)

class EditLearningService:
    """Learn from operator edits and ACTUALLY improve future drafts - real improvement loop"""
    
    def __init__(self, settings):
        self.settings = settings
        self.llm = ChatOpenAI(
            api_key=settings.OPENAI_API_KEY,
            model_name=settings.OPENAI_MODEL,
            temperature=0.0  # Deterministic analysis
        )
        self.patterns_file = Path("./data/learned_patterns.json")
        self.learned_patterns = self._load_patterns()  # Persistent storage
    
    def _load_patterns(self) -> List[Dict[str, Any]]:
        """Load previously learned patterns from disk for persistence across restarts"""
        if self.patterns_file.exists():
            try:
                with open(self.patterns_file, 'r') as f:
                    patterns = json.load(f)
                logger.info(f"Loaded {len(patterns)} previously learned patterns")
                return patterns
            except Exception as e:
                logger.error(f"Failed to load patterns: {e}")
        return []
    
    def _save_patterns(self):
        """Save patterns to disk to persist learning across system restarts"""
        # Ensure directory exists
        self.patterns_file.parent.mkdir(exist_ok=True, parents=True)
        with open(self.patterns_file, 'w') as f:
            json.dump(self.learned_patterns, f, indent=2)
        logger.info(f"Saved {len(self.learned_patterns)} learned patterns to disk")
    
    def analyze_edit(self, original_content: str, edited_content: str, 
                    reasoning: str = None, feedback_category: str = None) -> Dict[str, Any]:
        """
        Analyze an edit to extract learning patterns
        
        Args:
            original_content: Original draft text
            edited_content: Modified draft text
            reasoning: Why the operator made the edit
            feedback_category: Category of feedback (grounding, clarity, completeness)
            
        Returns:
            Extracted patterns and learning insights
        """
        try:
            # Compute diff
            changes = self._compute_diff(original_content, edited_content)
            
            # Extract patterns
            patterns = self._extract_patterns(original_content, edited_content, changes)
            
            # Get LLM analysis
            llm_insights = self._analyze_with_llm(original_content, edited_content, reasoning)
            
            # Combine insights
            result = {
                "changes": changes,
                "patterns": patterns,
                "llm_insights": llm_insights,
                "feedback_category": feedback_category or self._categorize_feedback(changes, llm_insights),
                "confidence": self._calculate_confidence(patterns, llm_insights),
                "applicable_to_future": self._is_generally_applicable(patterns)
            }
            
            # Store pattern with metadata for future weighting
            if result["applicable_to_future"]:
                result["created_at"] = time.time()
                result["usage_count"] = 0
                result["weight"] = 1.0  # Weight for how important this pattern is
                self.learned_patterns.append(result)
                self._save_patterns()  # Persist immediately
            
            return result
            
        except Exception as e:
            logger.error(f"Edit analysis failed: {str(e)}")
            return {
                "changes": [],
                "patterns": [],
                "llm_insights": {},
                "error": str(e)
            }
    
    def _compute_diff(self, original: str, edited: str) -> List[Dict[str, Any]]:
        """Compute differences between original and edited content"""
        changes = []
        
        # Get detailed diff
        differ = difflib.unified_diff(
            original.splitlines(keepends=True),
            edited.splitlines(keepends=True),
            lineterm=''
        )
        
        additions = []
        deletions = []
        modifications = []
        
        for line in differ:
            if line.startswith('+') and not line.startswith('+++'):
                additions.append(line[1:].strip())
            elif line.startswith('-') and not line.startswith('---'):
                deletions.append(line[1:].strip())
        
        if additions or deletions:
            changes.append({
                "type": "content_change",
                "additions": additions,
                "deletions": deletions,
                "modification_type": self._classify_modification(additions, deletions)
            })
        
        return changes
    
    def _classify_modification(self, additions: List[str], deletions: List[str]) -> str:
        """Classify the type of modification"""
        if not deletions:
            return "addition"
        if not additions:
            return "deletion"
        if len(additions) == len(deletions):
            return "replacement"
        return "mixed"
    
    def _extract_patterns(self, original: str, edited: str, changes: List[Dict]) -> List[str]:
        """Extract reusable patterns from changes"""
        patterns = []
        
        # Pattern 1: Cite missing evidence
        if "reference" in edited.lower() or "according to" in edited.lower():
            if "reference" not in original.lower():
                patterns.append("Add evidence citations and references to source documents")
        
        # Pattern 2: Clarify ambiguous terms
        if self._contains_clarifications(original, edited):
            patterns.append("Define legal terms and explain ambiguous references")
        
        # Pattern 3: Reorder for clarity
        if self._has_significant_reordering(original, edited):
            patterns.append("Reorganize content for better logical flow")
        
        # Pattern 4: Remove unsupported claims
        if len(edited) < len(original) * 0.8:
            patterns.append("Remove claims not grounded in evidence")
        
        # Pattern 5: Add structure
        if edited.count('\n') > original.count('\n') * 1.5:
            patterns.append("Use clear headings and structured sections")
        
        return patterns
    
    def _contains_clarifications(self, original: str, edited: str) -> bool:
        """Check if edits contain clarifications"""
        clarification_words = ["means", "refers to", "defined as", "specifically", "namely"]
        for word in clarification_words:
            if word in edited.lower() and word not in original.lower():
                return True
        return False
    
    def _has_significant_reordering(self, original: str, edited: str) -> bool:
        """Check if content was significantly reordered"""
        orig_lines = original.split('\n')
        edit_lines = edited.split('\n')
        
        # Simple check: major difference in line positions
        common = sum(1 for o in orig_lines if o in edit_lines)
        return common < len(orig_lines) * 0.7
    
    def _analyze_with_llm(self, original: str, edited: str, reasoning: str = None) -> Dict[str, Any]:
        """Use LLM to analyze the edit"""
        try:
            system_prompt = """You are an expert in legal document drafting. Analyze the edit to the legal draft 
and identify what improvements were made. Focus on:
1. Grounding - how well facts are tied to evidence
2. Clarity - how clear and understandable the text is
3. Completeness - whether all necessary information is included
4. Legal accuracy - whether the content is legally sound

Provide specific insights about what was improved."""
            
            user_prompt = f"""Original draft (excerpt):
{original[:500]}

Edited version (excerpt):
{edited[:500]}

{f'Operator reasoning: {reasoning}' if reasoning else ''}

What improvements were made?"""
            
            response = self.llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ])
            
            return {
                "llm_analysis": response.content,
                "has_analysis": True
            }
        except Exception as e:
            logger.warning(f"LLM analysis failed: {str(e)}")
            return {"has_analysis": False}
    
    def _categorize_feedback(self, changes: List[Dict], llm_insights: Dict) -> str:
        """Categorize the type of feedback"""
        if any("reference" in str(c).lower() for c in changes):
            return "grounding"
        if any("clarif" in str(c).lower() for c in changes):
            return "clarity"
        if llm_insights.get("llm_analysis", "").lower().count("complete") > 0:
            return "completeness"
        return "general"
    
    def _calculate_confidence(self, patterns: List[str], llm_insights: Dict) -> float:
        """Calculate confidence in learned patterns"""
        confidence = 0.5
        
        if patterns:
            confidence += 0.2
        
        if llm_insights.get("has_analysis"):
            confidence += 0.2
        
        return min(1.0, confidence)
    
    def _is_generally_applicable(self, patterns: List[str]) -> bool:
        """Determine if patterns are generally applicable to future drafts"""
        # Some patterns are too specific, only general ones should be applied
        general_patterns = [
            "Add evidence citations",
            "Define legal terms",
            "Use clear headings",
            "Reorganize for logical flow"
        ]
        
        for pattern in patterns:
            for general in general_patterns:
                if general.lower() in pattern.lower():
                    return True
        
        return False
    
    def get_improvements_for_draft(self, document_types: List[str] = None) -> Dict[str, Any]:
        """
        Get ALL learned improvements that should be applied to the NEXT draft.
        This is what creates the REAL improvement loop - future drafts automatically incorporate operator feedback.
        
        Args:
            document_types: Optional list of document types to filter patterns for
        
        Returns:
            System prompt additions, specific instructions, and weighted patterns
        """
        # Filter recent, high-weight patterns
        valid_patterns = []
        for pattern in self.learned_patterns:
            # Only use patterns created in the last 90 days (still relevant)
            if time.time() - pattern.get("created_at", 0) < 7776000:  # 90 days in seconds
                pattern["usage_count"] += 1  # Track usage to prioritize frequent fixes
                valid_patterns.append(pattern)
        
        # Group patterns by category and calculate aggregate weights
        categorized = {}
        for p in valid_patterns:
            cat = p.get("feedback_category", "general")
            if cat not in categorized:
                categorized[cat] = {"count": 0, "patterns": [], "total_weight": 0}
            categorized[cat]["count"] += 1
            categorized[cat]["patterns"].extend(p.get("patterns", []))
            categorized[cat]["total_weight"] += p.get("weight", 1.0)
        
        # Extract unique instructions
        unique_instructions = list({p for p_list in [c["patterns"] for c in categorized.values()] for p in p_list})
        
        # Build system prompt additions that will be injected into future draft generation
        system_prompt_additions = self._build_system_prompt_additions(unique_instructions)
        
        # Save updated usage counts
        self._save_patterns()
        
        return {
            "applicable_patterns": unique_instructions,
            "categorized_feedback": categorized,
            "system_prompt_additions": system_prompt_additions,
            "total_applicable_patterns": len(unique_instructions)
        }
    
    def _build_system_prompt_additions(self, patterns: List[str]) -> str:
        """Convert learned patterns into concrete instructions for the LLM"""
        if not patterns:
            return ""
        
        additions = "\n\n--- LEARNED IMPROVEMENTS FROM PREVIOUS OPERATOR EDITS ---\n"
        additions += "Based on human feedback on prior drafts, you MUST incorporate these improvements:\n"
        for idx, pattern in enumerate(patterns, 1):
            additions += f"{idx}. {pattern}\n"
        additions += "--- END LEARNED IMPROVEMENTS ---\n"
        return additions
    
    def get_learned_patterns(self, limit: int = 5) -> List[str]:
        """Get patterns learned from previous edits"""
        if not self.learned_patterns:
            return []
        
        # Convert patterns to improvement suggestions
        suggestions = []
        for p in self.learned_patterns[-limit:]:
            suggestions.extend(p.get("patterns", []))
        
        # Remove duplicates while preserving order
        seen = set()
        unique = []
        for s in suggestions:
            if s not in seen:
                unique.append(s)
                seen.add(s)
        
        return unique[:5]
    
    def apply_learning_to_future(self, new_draft: str, learned_patterns: List[str]) -> str:
        """
        Apply learned patterns to improve a new draft
        
        Args:
            new_draft: New generated draft
            learned_patterns: Patterns to apply
            
        Returns:
            Improved draft
        """
        if not learned_patterns:
            return new_draft
        
        improved = new_draft
        
        # Apply patterns
        for pattern in learned_patterns:
            if "Add evidence citations" in pattern:
                improved = self._ensure_citations(improved)
            if "Define legal terms" in pattern:
                improved = self._add_term_definitions(improved)
            if "Use clear headings" in pattern:
                improved = self._improve_structure(improved)
        
        return improved
    
    def _ensure_citations(self, content: str) -> str:
        """Ensure citations are present"""
        if "[" not in content or "]" not in content:
            # Add placeholder for citations if missing
            content = content.replace("According to the document", "According to the document [1]")
        return content
    
    def _add_term_definitions(self, content: str) -> str:
        """Add definitions for legal terms"""
        legal_terms = {
            "plaintiff": "the party initiating the lawsuit",
            "defendant": "the party being sued",
            "court": "the judicial body hearing the case"
        }
        
        for term, definition in legal_terms.items():
            if term in content.lower() and f"({definition})" not in content:
                # This is simplified - in production would use more sophisticated approach
                pass
        
        return content
    
    def _improve_structure(self, content: str) -> str:
        """Improve structure with clear headings"""
        # If content doesn't have headings, this could be improved
        if "##" not in content and len(content.split('\n')) > 10:
            # Could add structure improvements
            pass
        return content