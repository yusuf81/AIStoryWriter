# Writer/ReasoningChain.py - Two-pass reasoning for cleaner generation
import Writer.Config as Config
from Writer.Interface.Wrapper import Interface
from Writer.PrintUtils import Logger
from Writer.Models import ReasoningOutput
from typing import Optional


class ReasoningChain:
    """
    Implements two-pass reasoning chain to separate thinking from generation.

    This follows the "Chain of Thought" pattern where the model first reasons
    about the approach, then generates the content based on that reasoning.
    """

    def __init__(self, interface: Interface, config, logger: Logger):
        """
        Initialize the ReasoningChain.

        Args:
            interface: LLM interface for generating responses
            config: Configuration module
            logger: Logger for tracking reasoning steps
        """
        self.interface = interface
        self.config = config
        self.logger = logger
        self.reasoning_cache = {} if config.REASONING_CACHE_RESULTS else None

        # Log reasoning chain status
        if config.USE_REASONING_CHAIN:
            logger.Log(
                f"Reasoning chain ENABLED using model: {config.REASONING_MODEL}",
                4
            )
            logger.Log(
                f"Reasoning logging: {'separate file' if config.REASONING_LOG_SEPARATE else 'main log'}",
                5
            )
        else:
            logger.Log("Reasoning chain DISABLED by config", 5)

    def reason(self,
               context: str,
               task_type: str,
               additional_context: Optional[str] = None,
               chapter_number: Optional[int] = None) -> str:
        """
        Generate reasoning for a specific task.

        Args:
            context: Main context (outline, previous chapter, etc.)
            task_type: Type of reasoning task (plot, character, dialogue)
            additional_context: Optional additional context
            chapter_number: Optional chapter number for logging

        Returns:
            str: Reasoning text to guide generation
        """
        # Log reasoning request
        self.logger.Log(
            f"Generating {task_type} reasoning for Chapter {chapter_number or 'N/A'}",
            5
        )

        # Check cache if enabled
        if self.reasoning_cache is not None:
            cache_key = f"{task_type}_{hash(context)}_{chapter_number or 0}"
            if cache_key in self.reasoning_cache:
                self.logger.Log(f"Using cached reasoning for {task_type} (Chapter {chapter_number})", 4)
                return self.reasoning_cache[cache_key]

        # Generate reasoning based on task type
        if task_type == "plot":
            reasoning = self._reason_about_plot(context, additional_context, chapter_number)
        elif task_type == "character":
            reasoning = self._reason_about_character(context, additional_context, chapter_number)
        elif task_type == "dialogue":
            reasoning = self._reason_about_dialogue(context, additional_context, chapter_number)
        elif task_type == "outline":
            reasoning = self._reason_about_outline(context)
        else:
            reasoning = self._reason_general(context, task_type, additional_context, chapter_number)

        # Cache result if enabled
        if self.reasoning_cache is not None:
            self.reasoning_cache[cache_key] = reasoning

        # Log reasoning completion (always to main log for visibility)
        self.logger.Log(
            f"Generated {task_type} reasoning for Chapter {chapter_number or 'N/A'}: {len(reasoning)} chars",
            4
        )

        # Log reasoning separately if enabled
        if self.config.REASONING_LOG_SEPARATE:
            self._log_reasoning(task_type, chapter_number, reasoning)

        return reasoning

    def _reason_about_plot(self,
                          context: str,
                          additional_context: Optional[str] = None,
                          chapter_number: Optional[int] = None) -> str:
        """Generate reasoning about plot development."""
        additional_text = ""
        if additional_context:
            additional_text = f"ADDITIONAL CONTEXT:\n{additional_context}\n\n"

        prompt = f"""
I need to reason about the plot development for Chapter {chapter_number or 'N/A'}.

CONTEXT:
{context}

{additional_text}
Please think step by step about:
1. What are the key plot points that must happen in this chapter?
2. How should the pacing flow to maintain reader engagement?
3. What are the cause-and-effect relationships that need to be established?
4. How does this chapter advance the overall story arc?
5. What are the potential plot holes or inconsistencies to avoid?

Provide clear, actionable reasoning that will guide the writing of this chapter's plot.
Focus on the logical flow and narrative structure.
Do not write the chapter content, only reason about the approach.
"""

        messages = [self.interface.BuildSystemQuery("You are a skilled story analyst providing structured reasoning for plot development.")]
        messages.append(self.interface.BuildUserQuery(prompt))

        messages, reasoning_obj, _ = self.interface.SafeGeneratePydantic(
            self.logger, messages, self.config.REASONING_MODEL,
            ReasoningOutput
        )

        return reasoning_obj.reasoning

    def _reason_about_character(self,
                               context: str,
                               additional_context: Optional[str] = None,
                               chapter_number: Optional[int] = None) -> str:
        """Generate reasoning about character development."""
        additional_text = ""
        if additional_context:
            additional_text = f"EXISTING CONTENT TO ENHANCE:\n{additional_context}\n\n"

        prompt = f"""
I need to reason about the character development for Chapter {chapter_number or 'N/A'}.

CONTEXT:
{context}

{additional_text}
Please think step by step about:
1. Which characters are present in this chapter and what are their motivations?
2. How do characters evolve or change during this chapter?
3. What are the key character interactions and their purposes?
4. How can we show character traits through actions rather than telling?
5. What are the character arcs that need to be advanced?

Provide clear, actionable reasoning that will guide the character development writing.
Focus on authenticity, growth, and meaningful interactions.
Do not write the chapter content, only reason about the character approach.
"""

        messages = [self.interface.BuildSystemQuery("You are a skilled character analyst providing structured reasoning for character development.")]
        messages.append(self.interface.BuildUserQuery(prompt))

        messages, reasoning_obj, _ = self.interface.SafeGeneratePydantic(
            self.logger, messages, self.config.REASONING_MODEL,
            ReasoningOutput
        )

        return reasoning_obj.reasoning

    def _reason_about_dialogue(self,
                              context: str,
                              additional_context: Optional[str] = None,
                              chapter_number: Optional[int] = None) -> str:
        """Generate reasoning about dialogue enhancement."""
        additional_text = ""
        if additional_context:
            additional_text = f"EXISTING CONTENT TO ENHANCE:\n{additional_context}\n\n"

        prompt = f"""
I need to reason about the dialogue enhancement for Chapter {chapter_number or 'N/A'}.

CONTEXT:
{context}

{additional_text}
Please think step by step about:
1. What dialogue needs to be added to enhance the existing content?
2. How should each character's voice sound (word choice, tone, speech patterns)?
3. What subtext or underlying meanings should the dialogue convey?
4. How does dialogue serve the plot and character development simultaneously?
5. What are the natural conversation flows that need to be established?

Provide clear, actionable reasoning that will guide the dialogue enhancement.
Focus on naturalness, character voice, and meaningful exchanges.
Do not write the dialogue, only reason about the approach.
"""

        messages = [self.interface.BuildSystemQuery("You are a skilled dialogue analyst providing structured reasoning for dialogue enhancement.")]
        messages.append(self.interface.BuildUserQuery(prompt))

        messages, reasoning_obj, _ = self.interface.SafeGeneratePydantic(
            self.logger, messages, self.config.REASONING_MODEL,
            ReasoningOutput
        )

        return reasoning_obj.reasoning

    def _reason_about_outline(self, context: str) -> str:
        """Generate reasoning about outline creation."""
        prompt = f"""
I need to reason about the story outline structure.

STORY PROMPT:
{context}

Please think step by step about:
1. What is the optimal chapter count for this story given its complexity?
2. How should the story be structured (three-act, five-act, etc.)?
3. What are the major plot points that need to be distributed across chapters?
4. How can we ensure proper pacing and escalation of tension?
5. What are the potential structural issues to avoid?

Provide clear, actionable reasoning that will guide the outline creation.
Focus on structure, pacing, and narrative arc.
"""

        messages = [self.interface.BuildSystemQuery("You are a skilled story structure analyst providing reasoning for outline creation.")]
        messages.append(self.interface.BuildUserQuery(prompt))

        messages, reasoning_obj, _ = self.interface.SafeGeneratePydantic(
            self.logger, messages, self.config.REASONING_MODEL,
            ReasoningOutput
        )

        return reasoning_obj.reasoning

    def _reason_general(self,
                       context: str,
                       task_type: str,
                       additional_context: Optional[str] = None,
                       chapter_number: Optional[int] = None) -> str:
        """Generate general reasoning for other task types."""
        additional_text = ""
        if additional_context:
            additional_text = f"ADDITIONAL CONTEXT:\n{additional_context}\n\n"

        prompt = f"""
I need to reason about the {task_type} task for Chapter {chapter_number or 'N/A'}.

CONTEXT:
{context}

{additional_text}
Please provide structured reasoning about how to approach this task effectively.
Consider the requirements, constraints, and best practices for {task_type}.
Focus on providing actionable guidance that will improve the quality of the output.
"""

        messages = [self.interface.BuildSystemQuery(f"You are a skilled AI assistant providing structured reasoning for {task_type} tasks.")]
        messages.append(self.interface.BuildUserQuery(prompt))

        messages, reasoning_obj, _ = self.interface.SafeGeneratePydantic(
            self.logger, messages, self.config.REASONING_MODEL,
            ReasoningOutput
        )

        return reasoning_obj.reasoning

    def _log_reasoning(self, task_type: str, chapter_number: Optional[int], reasoning: str):
        """Log reasoning to separate file if configured."""
        import os
        from datetime import datetime

        if not hasattr(self, '_reasoning_log_file'):
            log_dir = "Logs/Reasoning"
            os.makedirs(log_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            self._reasoning_log_file = f"{log_dir}/Reasoning_{timestamp}.md"

        with open(self._reasoning_log_file, 'a', encoding='utf-8') as f:
            f.write(f"\n\n# {task_type.title()} Reasoning")
            if chapter_number:
                f.write(f" - Chapter {chapter_number}")
            f.write(f"\n\n{reasoning}\n")

    def get_stats(self) -> dict:
        """Get reasoning chain statistics."""
        stats = {
            "cache_enabled": self.reasoning_cache is not None,
            "cached_items": len(self.reasoning_cache) if self.reasoning_cache else 0,
            "separate_logging": self.config.REASONING_LOG_SEPARATE
        }
        if hasattr(self, '_reasoning_log_file'):
            stats["log_file"] = self._reasoning_log_file
        return stats

    def clear_cache(self):
        """Clear the reasoning cache if enabled."""
        if self.reasoning_cache is not None:
            self.reasoning_cache.clear()
            self.logger.Log("Reasoning cache cleared", 4)