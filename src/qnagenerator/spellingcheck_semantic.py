"""
True AI Agent System for Grammatical Error Detection and Fixing
Uses LangChain with Ollama for agentic tool orchestration
Agent decides which tools to use based on reasoning
"""

import json
import streamlit as st
import requests
from typing import Optional, Any
from pydantic import BaseModel, Field
from enum import Enum

# ============================================================================
# Ollama Client Wrapper
# ============================================================================

class OllamaLLM:
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "neural-chat"):
        self.base_url = base_url
        self.model = model
    
    def set_model(self, model: str):
        self.model = model
    
    def call(self, prompt: str, max_tokens: int = 2048, temperature: float = 0.7) -> str:
        """Call Ollama LLM"""
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "num_predict": max_tokens,
                    "temperature": temperature,
                },
                timeout=120
            )
            response.raise_for_status()
            return response.json()["response"]
        except requests.exceptions.ConnectionError:
            raise Exception(
                f"Cannot connect to Ollama at {self.base_url}. "
                "Make sure Ollama is running: `ollama serve`"
            )


# ============================================================================
# Data Models
# ============================================================================

class ErrorType(str, Enum):
    SPELLING = "spelling"
    GRAMMAR = "grammar"
    PUNCTUATION = "punctuation"
    TYPO = "typo"
    STYLE = "style"
    WORD_ORDER = "word_order"
    EXTRA_WORD = "extra_word"
    MISSING_WORD = "missing_word"
    OTHER = "other"


class GrammaticalError(BaseModel):
    error_type: str = Field(description="Type of error")  # Accept any string, validate later
    start_pos: int = Field(description="Start position")
    end_pos: int = Field(description="End position")
    error_text: str = Field(description="Erroneous text")
    explanation: str = Field(description="Why it's an error")
    
    def validate_error_type(self):
        """Normalize error type to valid enum value"""
        valid_types = [e.value for e in ErrorType]
        error_type_lower = self.error_type.lower().strip()
        
        # Direct match
        if error_type_lower in valid_types:
            return error_type_lower
        
        # Map common variations to valid types
        type_mapping = {
            'extra_word': 'extra_word',
            'extra': 'extra_word',
            'missing_word': 'missing_word',
            'missing': 'missing_word',
            'word_order': 'word_order',
            'scrambled': 'word_order',
            'word_scramble': 'word_order',
            'misspelling': 'spelling',
            'misspelled': 'spelling',
            'spelling_error': 'spelling',
            'typo': 'typo',
            'grammar': 'grammar',
            'grammatical': 'grammar',
            'punctuation': 'punctuation',
            'style': 'style',
        }
        
        # Try to find a match
        for key, value in type_mapping.items():
            if key in error_type_lower:
                return value
        
        # Default to 'other'
        return 'other'


class DetectionResult(BaseModel):
    has_errors: bool
    errors: list[GrammaticalError] = Field(default_factory=list)
    original_text: str


class CorrectionProposal(BaseModel):
    error_index: int
    original_text: str
    suggested_correction: str
    explanation: str


class FixerResult(BaseModel):
    corrected_text: str
    corrections: list[CorrectionProposal] = Field(default_factory=list)


# ============================================================================
# Tools (Reusable Components)
# ============================================================================

class GrammarTools:
    """Specialized tools for grammar operations"""
    
    @staticmethod
    def detect_errors(text: str, llm: OllamaLLM) -> dict:
        """Tool: Detect grammatical errors"""
        prompt = f"""Analyze this text for errors: "{text}"
        
Return ONLY valid JSON:
{{"has_errors": bool, "errors": [{{"error_type": "string (spelling, grammar, punctuation, typo, style, word_order, extra_word, missing_word, or other)", "start_pos": int, "end_pos": int, "error_text": "string", "explanation": "string"}}]}}"""
        
        response = llm.call(prompt, max_tokens=1024, temperature=0.3)
        
        try:
            # Extract JSON
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            if start_idx != -1:
                json_str = response[start_idx:end_idx]
                result = json.loads(json_str)
                
                # Validate and normalize error types
                errors = result.get('errors', [])
                normalized_errors = []
                for error in errors:
                    try:
                        err = GrammaticalError(**error)
                        err.error_type = err.validate_error_type()
                        normalized_errors.append(err)
                    except Exception as e:
                        # Skip invalid errors
                        pass
                
                result['errors'] = [e.model_dump() for e in normalized_errors]
                return result
        except:
            pass
        
        return {"has_errors": False, "errors": []}
    
    @staticmethod
    def fix_errors(text: str, errors_data: dict, llm: OllamaLLM) -> dict:
        """Tool: Fix detected errors"""
        errors = errors_data.get('errors', [])
        
        # If no errors, return as-is
        if not errors:
            return {
                "corrected_text": text,
                "corrections": []
            }
        
        # Build detailed prompt with each error clearly listed
        errors_list_str = ""
        for i, error in enumerate(errors):
            error_text = error.get('error_text', '') if isinstance(error, dict) else error.error_text
            explanation = error.get('explanation', '') if isinstance(error, dict) else error.explanation
            errors_list_str += f"{i}. '{error_text}': {explanation}\n"
        
        prompt = f"""You are fixing errors in text. Be VERY CAREFUL - only fix the EXACT errors listed.

Current text:
"{text}"

Errors to fix (ONLY these):
{errors_list_str}

Instructions:
1. Only replace the exact words/phrases listed in errors
2. Do NOT make other changes
3. Do NOT "improve" the text beyond the errors listed
4. Return the corrected text with ONLY the specified corrections applied

Return ONLY valid JSON with NO markdown:
{{"corrected_text": "the text with ONLY the listed errors corrected", "corrections": [{{"error_index": 0, "original_text": "original", "suggested_correction": "fixed", "explanation": "reason"}}]}}

Important: corrected_text must only have the listed errors fixed, nothing else changed."""
        
        response = llm.call(prompt, max_tokens=1024, temperature=0.2)  # Lower temp for more precision
        
        try:
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            if start_idx != -1:
                json_str = response[start_idx:end_idx]
                result = json.loads(json_str)
                
                corrected = result.get('corrected_text', text)
                
                # If LLM didn't apply corrections, do it manually as fallback
                if corrected == text and result.get('corrections'):
                    corrected = text
                    for correction in result.get('corrections', []):
                        original = correction.get('original_text', '')
                        fixed = correction.get('suggested_correction', '')
                        if original and fixed:
                            corrected = corrected.replace(original, fixed)
                    result['corrected_text'] = corrected
                
                return result
        except Exception as e:
            pass
        
        return {"corrected_text": text, "corrections": []}
    
    @staticmethod
    def semantic_reconstruction(text: str, llm: OllamaLLM) -> dict:
        """Tool: Reconstruct semantically garbled or scrambled text"""
        prompt = f"""This text is scrambled, garbled, or has serious word order issues: "{text}"

Your task is to figure out what the INTENDED meaning/phrase is:
1. What common phrases or sentences might this be?
2. What words are present? (even if misspelled)
3. What is the likely intended message?
4. Reconstruct the correct version

Return ONLY valid JSON:
{{"original": "string", "reconstructed": "string", "issues": ["list of issues"], "confidence": 0-100}}

Example:
Input: "to err is forgie to gice sis human"
Words present: to, err, is, forgie(forgive), to, gice(give), sis(is), human
Known phrase: "to err is human, to forgive is divine"
Output: {{"original": "to err is forgie to gice sis human", "reconstructed": "to err is human, to forgive is divine", "issues": ["word scrambling", "misspellings: forgie→forgive, gice→give, sis→is"], "confidence": 95}}"""
        
        response = llm.call(prompt, max_tokens=1024, temperature=0.3)
        
        try:
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            if start_idx != -1:
                json_str = response[start_idx:end_idx]
                return json.loads(json_str)
        except:
            pass
        
        return {"original": text, "reconstructed": text, "issues": [], "confidence": 0}


# ============================================================================
# True Agentic System with Tool Use
# ============================================================================

class GrammarCorrectionAgent:
    """
    Agentic system that decides which tools to use.
    Uses reasoning loop: Observe → Think → Decide Tools → Execute → Reflect
    """
    
    def __init__(self, llm: OllamaLLM):
        self.llm = llm
        self.tools = GrammarTools()
        self.memory = []
        self.environment = {
            "text": None,
            "error_analysis": None,
            "corrections": None,
            "goal_achieved": False
        }
    
    def _add_memory(self, role: str, content: str):
        """Add to agent memory"""
        self.memory.append({"role": role, "content": content})
    
    def _build_system_prompt(self) -> str:
        """Build system prompt for agentic reasoning"""
        return """You are an AI agent responsible for correcting grammatical errors. You have access to these tools:

1. DETECT_ERRORS: Analyze text and find grammatical mistakes
2. FIX_ERRORS: Propose corrections for identified errors

Your workflow:
1. OBSERVE: Understand the input text
2. PLAN: Decide which tools to use and in what order
3. EXECUTE: Call the appropriate tools
4. REFLECT: Analyze results and decide if goal is achieved
5. RESPOND: Report findings to user

Always think step-by-step about what tool to use next."""
    
    def observe(self, text: str) -> str:
        """Agent observes the environment"""
        observation = f"User provided text: '{text}'"
        self.environment["text"] = text
        self._add_memory("observation", observation)
        return observation
    
    def think(self, text: str) -> str:
        """Agent reasons about what to do"""
        thinking_prompt = f"""Analyze this text: "{text}"

Check for these issues (in order of priority):
1. Is the text SCRAMBLED or REARRANGED? (words in wrong order, sentence structure broken)
2. Does it have HEAVY misspellings that obscure meaning?
3. Are there just minor spelling/grammar errors?
4. Is the text already correct?

For each issue, think:
- What tool should I use first?
- What is the semantic meaning the user intended?
- Should I reconstruct first, then detect errors, then fix?

Respond with your step-by-step reasoning (2-3 sentences max)."""
        
        thought = self.llm.call(thinking_prompt, max_tokens=256, temperature=0.7)
        self._add_memory("thought", thought)
        return thought
    
    def decide_next_action(self, thought: str) -> str:
        """Agent decides which tool to call next"""
        decision_prompt = f"""Based on this analysis: "{thought}"

Priority order for tool selection:
1. SEMANTIC_RECONSTRUCTION - if text is scrambled, rearranged, or heavily garbled
2. DETECT_ERRORS - if text structure is okay but has spelling/grammar issues
3. FIX_ERRORS - if we already detected errors and need to correct them
4. COMPLETE - if goal is achieved

Which tool should you call NOW?
Respond with ONLY one: SEMANTIC_RECONSTRUCTION, DETECT_ERRORS, FIX_ERRORS, or COMPLETE"""
        
        decision = self.llm.call(decision_prompt, max_tokens=50, temperature=0.3).strip()
        self._add_memory("decision", f"Next action: {decision}")
        return decision
    
    def execute_tool(self, tool_name: str) -> Any:
        """Execute the chosen tool"""
        if tool_name == "SEMANTIC_RECONSTRUCTION":
            result = self.tools.semantic_reconstruction(self.environment["text"], self.llm)
            self.environment["semantic_result"] = result
            self.environment["text"] = result.get("reconstructed", self.environment["text"])
            self._add_memory("tool_execution", f"Semantic reconstruction: {result.get('confidence', 0)}% confidence")
            return result
        
        elif tool_name == "DETECT_ERRORS":
            result = self.tools.detect_errors(self.environment["text"], self.llm)
            self.environment["error_analysis"] = result
            self._add_memory("tool_execution", f"Detected {len(result.get('errors', []))} errors")
            return result
        
        elif tool_name == "FIX_ERRORS":
            if self.environment["error_analysis"] is None:
                return {"error": "Must detect errors first"}
            result = self.tools.fix_errors(
                self.environment["text"],
                self.environment["error_analysis"],
                self.llm
            )
            self.environment["corrections"] = result
            self._add_memory("tool_execution", "Applied corrections")
            return result
        
        return None
    
    def reflect(self) -> bool:
        """Agent reflects on whether goal is achieved"""
        error_analysis = self.environment.get('error_analysis') or {}
        corrections = self.environment.get('corrections') or {}
        semantic_result = self.environment.get('semantic_result') or {}
        
        errors_count = len(error_analysis.get('errors', []))
        corrections_count = len(corrections.get('corrections', []))
        semantic_confidence = semantic_result.get('confidence', 0)
        
        # Goal is achieved if:
        # 1. Semantic reconstruction with high confidence (95%+) and no errors found
        # 2. No errors were found
        # 3. Corrections were successfully applied
        
        if semantic_confidence >= 95 and errors_count == 0:
            goal_achieved = True
            reflection = f"YES - Semantic reconstruction successful with {semantic_confidence}% confidence, no errors"
        elif errors_count == 0:
            goal_achieved = True
            reflection = "YES - No errors found, text is correct"
        elif corrections_count > 0:
            goal_achieved = True
            reflection = f"YES - {corrections_count} correction(s) applied"
        else:
            goal_achieved = False
            reflection = "NO - Still have errors to process"
        
        self.environment["goal_achieved"] = goal_achieved
        self._add_memory("reflection", reflection)
        return goal_achieved
    
    def run(self, text: str) -> dict:
        """Execute the full agentic loop"""
        self.observe(text)
        thought = self.think(text)
        
        # Agentic loop: Keep deciding and executing until goal is achieved
        max_iterations = 3
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            # Decide what to do next
            action = self.decide_next_action(thought)
            
            if action == "COMPLETE":
                break
            
            # Execute the chosen tool
            if action in ["DETECT_ERRORS", "FIX_ERRORS"]:
                self.execute_tool(action)
            
            # Reflect on progress
            if self.reflect():
                break
            
            # Think about next step
            thought = self.think(text)
        
        # Prepare results
        error_analysis = self.environment.get("error_analysis", {})
        corrections = self.environment.get("corrections", {})
        
        detection_result = DetectionResult(
            has_errors=error_analysis.get("has_errors", False),
            errors=[GrammaticalError(**e) for e in error_analysis.get("errors", [])],
            original_text=text
        ) if error_analysis else DetectionResult(has_errors=False, original_text=text)
        
        fixer_result = FixerResult(
            corrected_text=corrections.get("corrected_text", text),
            corrections=[CorrectionProposal(**c) for c in corrections.get("corrections", [])]
        ) if corrections else FixerResult(corrected_text=text)
        
        return {
            "status": "success",
            "original_text": text,
            "detection": detection_result,
            "corrections": fixer_result,
            "agent_memory": self.memory,
            "iterations": iteration,
            "goal_achieved": self.environment["goal_achieved"]
        }


# ============================================================================
# Real-time Streaming Execution
# ============================================================================

def run_agent_with_streaming(agent: GrammarCorrectionAgent, text: str, status_text, steps_container):
    """Run agent with real-time step visualization"""
    
    step_num = 1
    step_displays = {}
    
    def log_step(phase: str, content: str, icon: str = "▶️", is_complete: bool = False):
        """Log a step with real-time update"""
        nonlocal step_num
        
        if phase not in step_displays:
            with steps_container:
                step_displays[phase] = st.empty()
        
        status = "✅" if is_complete else icon
        step_displays[phase].markdown(f"""
{status} **Step {step_num}: {phase}**
```
{content}
```
""")
        step_num += 1
    
    # Step 1: OBSERVE
    status_text.markdown("🔍 **Step 1: OBSERVE** - Reading input text...")
    observation = agent.observe(text)
    log_step("OBSERVE", observation, "👀", True)
    
    # Step 2: THINK
    status_text.markdown("💭 **Step 2: THINK** - Agent reasoning about task...")
    thought = agent.think(text)
    log_step("THINK", thought, "💭", True)
    
    # Agentic loop with streaming
    max_iterations = 5
    iteration = 0
    
    while iteration < max_iterations:
        iteration += 1
        
        # Step 3: DECIDE
        status_text.markdown(f"🧠 **Step {2+iteration}: DECIDE** - Determining next action...")
        action = agent.decide_next_action(thought)
        log_step(f"DECIDE (Iteration {iteration})", f"Action: {action}", "🎯", True)
        
        if action == "COMPLETE":
            log_step("COMPLETION CHECK", "Agent decided task is complete", "🏁", True)
            break
        
        # Step 4: EXECUTE TOOL
        if action in ["SEMANTIC_RECONSTRUCTION", "DETECT_ERRORS", "FIX_ERRORS"]:
            status_text.markdown(f"⚙️ **Step {2+iteration+1}: EXECUTE** - Calling {action} tool...")
            
            if action == "SEMANTIC_RECONSTRUCTION":
                result = agent.execute_tool(action)
                confidence = result.get('confidence', 0)
                reconstructed_text = result.get('reconstructed', '')
                
                # ✅ CRITICAL: Update agent's text to the reconstructed version
                agent.environment["text"] = reconstructed_text
                
                log_step(f"EXECUTE: {action}", 
                        f"Confidence: {confidence}%\nOriginal: '{result.get('original', '')}'\nReconstructed: '{reconstructed_text}'\nIssues: {result.get('issues', [])}", 
                        "🔧", True)
            elif action == "DETECT_ERRORS":
                result = agent.execute_tool(action)
                error_count = len(result.get('errors', []))
                log_step(f"EXECUTE: {action}", 
                        f"Found {error_count} error(s)\n{json.dumps(result, indent=2)[:500]}...", 
                        "🔧", True)
            else:  # FIX_ERRORS
                result = agent.execute_tool(action)
                correction_count = len(result.get('corrections', []))
                log_step(f"EXECUTE: {action}", 
                        f"Applied {correction_count} correction(s)\n{json.dumps(result, indent=2)[:500]}...", 
                        "🔧", True)
        
        # Step 5: REFLECT
        status_text.markdown(f"🤔 **Step {2+iteration+2}: REFLECT** - Evaluating progress...")
        reflection_status = agent.reflect()
        log_step(f"REFLECT (Iteration {iteration})", 
                f"Goal Achieved: {reflection_status}", 
                "📊", True)
        
        if reflection_status:
            log_step("COMPLETION", "Agent determined goal is achieved!", "🎉", True)
            break
        
        # Next thought
        status_text.markdown(f"💭 **THINK (Iteration {iteration+1})** - Planning next action...")
        thought = agent.think(text)
        log_step(f"THINK (Iteration {iteration+1})", thought, "💭", True)
    
    # Prepare results
    error_analysis = agent.environment.get("error_analysis") or {}
    corrections = agent.environment.get("corrections") or {}
    
    # Parse and normalize errors
    errors_list = []
    for e in error_analysis.get("errors", []):
        try:
            if isinstance(e, dict):
                err = GrammaticalError(**e)
                err.error_type = err.validate_error_type()
                errors_list.append(err)
            elif isinstance(e, GrammaticalError):
                e.error_type = e.validate_error_type()
                errors_list.append(e)
        except Exception as ex:
            pass
    
    detection_result = DetectionResult(
        has_errors=error_analysis.get("has_errors", False),
        errors=errors_list,
        original_text=text
    ) if error_analysis else DetectionResult(has_errors=False, original_text=text)
    
    fixer_result = FixerResult(
        corrected_text=corrections.get("corrected_text", text),
        corrections=[CorrectionProposal(**c) for c in corrections.get("corrections", []) if c]
    ) if corrections else FixerResult(corrected_text=text)
    
    return {
        "status": "success",
        "original_text": text,
        "detection": detection_result,
        "corrections": fixer_result,
        "semantic_result": agent.environment.get("semantic_result"),
        "agent_memory": agent.memory,
        "iterations": iteration,
        "goal_achieved": agent.environment["goal_achieved"]
    }


# ============================================================================
# Streamlit Interface
# ============================================================================

def main():
    st.set_page_config(page_title="Agentic Grammar System", layout="wide")
    
    st.title("🤖 Agentic Grammar Correction System")
    st.markdown("""
    **True Agentic System** with reasoning loop:
    Observe → Think → Decide → Execute Tools → Reflect
    
    The agent autonomously decides which tools to use and when to stop.
    """)
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        ollama_url = st.text_input(
            "Ollama URL",
            value="http://localhost:11434",
            help="URL where Ollama is running"
        )
        
        model_name = st.selectbox(
            "Model Selection",
            ["qwen3:8b","deepseek-r1:14b"],
            help="Select a local model. Make sure it's pulled: `ollama pull <model>`"
        )
        
        st.info("""
        **Setup:**
        1. `ollama pull neural-chat`
        2. `ollama serve`
        3. Refresh this page
        """)
    
    # Initialize LLM
    try:
        llm = OllamaLLM(base_url=ollama_url, model=model_name)
        st.sidebar.success("✅ Ollama initialized")
    except Exception as e:
        st.sidebar.error(f"❌ Error: {str(e)}")
        return
    
    # Main interface
    col1, col2 = st.columns([1, 1], gap="large")
    
    with col1:
        st.header("📝 Input Text")
        user_text = st.text_area(
            "Enter text:",
            height=200,
            placeholder="Your text here...",
            label_visibility="collapsed"
        )
    
    if st.button("🧠 Run Agent", use_container_width=True, type="primary"):
        if not user_text.strip():
            st.warning("Please enter text")
        else:
            with col2:
                st.header("🔄 Agent Execution")
                
                # Create placeholder for real-time updates
                status_container = st.container(border=True)
                steps_container = st.container()
                results_container = st.container()
                
                with status_container:
                    status_text = st.empty()
                    status_text.markdown("⏳ **Initializing agent...**")
                
                # Custom streaming version with real-time updates
                agent = GrammarCorrectionAgent(llm)
                result = run_agent_with_streaming(agent, user_text, status_text, steps_container)
                
                # Clear spinners and show final results
                status_text.markdown("✅ **Agent execution complete!**")
                
                with results_container:
                    st.header("✅ Final Results")
                with results_container:
                    st.header("✅ Final Results")
                    
                    st.info(f"**Agent Completed in {result['iterations']} iteration(s)** | Goal Achieved: {'✓' if result['goal_achieved'] else '✗'}")
                    
                    # Semantic reconstruction results
                    if "semantic_result" in result and result["semantic_result"]:
                        st.subheader("🧠 Semantic Reconstruction")
                        semantic = result["semantic_result"]
                        with st.container(border=True):
                            st.markdown(f"**Confidence:** {semantic.get('confidence', 0)}%")
                            st.markdown(f"**Original:** `{semantic.get('original', '')}`")
                            st.markdown(f"**Reconstructed:** `{semantic.get('reconstructed', '')}`")
                            if semantic.get('issues'):
                                st.markdown(f"**Issues Found:**")
                                for issue in semantic.get('issues', []):
                                    st.markdown(f"- {issue}")
                    
                    # Detection results
                    detection = result["detection"]
                    st.subheader("🔍 Errors Detected")
                    
                    if detection.has_errors:
                        st.warning(f"Found {len(detection.errors)} error(s)")
                        for i, error in enumerate(detection.errors, 1):
                            with st.container(border=True):
                                error_type_str = error.error_type if isinstance(error.error_type, str) else error.error_type.value
                                st.markdown(f"**Error {i}: {error_type_str.upper()}**")
                                st.code(error.error_text)
                                st.markdown(f"**Reason:** {error.explanation}")
                    else:
                        st.success("✨ No errors found!")
                    
                    # Corrections
                    st.subheader("✏️ Corrections Applied")
                    corrections = result["corrections"]
                    
                    if corrections.corrections:
                        for i, corr in enumerate(corrections.corrections, 1):
                            with st.container(border=True):
                                col_a, col_b = st.columns(2)
                                with col_a:
                                    st.markdown("**Before:**")
                                    st.code(corr.original_text)
                                with col_b:
                                    st.markdown("**After:**")
                                    st.code(corr.suggested_correction)
                                st.markdown(f"*{corr.explanation}*")
                    
                    # Final result
                    st.subheader("📄 Final Corrected Text")
                    st.success(corrections.corrected_text)
                    st.code(corrections.corrected_text)


if __name__ == "__main__":
    main()
