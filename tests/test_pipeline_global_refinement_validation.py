"""
Tests for Global Outline Refinement Validation Loop in Pipeline.py

This test suite validates that the global refinement stage in Pipeline.py
uses a proper validation loop (similar to GenerateOutline) to ensure
quality standards are met before accepting refined outlines.

TDD London School Methodology:
- Tests written FIRST (RED phase)
- Implementation follows to make tests PASS (GREEN phase)
- Ensures no low-quality outlines pass through (fixes Qwen Kuntilanak bug)
"""
import sys
sys.path.insert(0, '/var/www/AIStoryWriter')

import pytest
from unittest.mock import MagicMock, call
from Writer.Pipeline import StoryPipeline
from Writer.Models import StoryElements, CharacterDetail

# Import modules needed for patching
import Writer.LLMEditor  # noqa: F401


class TestPipelineGlobalRefinementValidationLoop:
    """Test validation loop for global outline refinement"""

    def test_global_refinement_exits_when_quality_met_first_iteration(
        self, mock_interface, mock_logger, mocker
    ):
        """
        Verify loop exits immediately when quality standards met on first iteration.

        This is the happy path - LLM produces good outline on first try,
        GetOutlineRating returns True, loop exits after 1 iteration.
        """
        # Arrange
        # Patch Config attributes
        mocker.patch('Writer.Config.ENABLE_GLOBAL_OUTLINE_REFINEMENT', True)
        mocker.patch('Writer.Config.OUTLINE_MIN_REVISIONS', 1)
        mocker.patch('Writer.Config.OUTLINE_MAX_REVISIONS', 3)
        mocker.patch('Writer.Config.EXPAND_OUTLINE', True)

        # Mock LLMEditor functions
        mock_llm_editor = mocker.patch('Writer.LLMEditor')
        mock_llm_editor.GetFeedbackOnOutline.return_value = "Good outline, well structured"
        mock_llm_editor.GetOutlineRating.return_value = True  # Quality met!

        # Mock OutlineGenerator
        mock_outline_generator = MagicMock()
        mock_outline_generator.ReviseOutline.return_value = (
            "Revised outline text with improvements",
            [{"role": "assistant", "content": "revision response"}]
        )
        mock_outline_generator.GeneratePerChapterOutline.return_value = (
            "Chapter outline text", "Chapter Title"
        )

        # Mock ActivePrompts
        mock_prompts = MagicMock()
        mock_prompts.REVISE_OUTLINE_CHARACTER_CONSTRAINT = "Expand outline. Use only these characters: {character_list}"
        mock_prompts.REVISE_OUTLINE_FALLBACK = "Expand outline. Keep existing characters."

        # Create Pipeline instance
        import Writer.Config as Config
        mock_iface = mock_interface()
        mock_log = mock_logger()

        pipeline = StoryPipeline(
            interface=mock_iface,
            sys_logger=mock_log,
            config=Config,
            active_prompts=mock_prompts,
            is_fresh_run=True
        )

        # Override generators with mocks
        pipeline.OutlineGenerator = mock_outline_generator
        pipeline.ChapterDetector = MagicMock()
        pipeline.ChapterGenerator = MagicMock()

        # Setup state with story elements
        story_elements = StoryElements(
            title="Test Story",
            genre="Fantasy",
            themes=["adventure", "courage"],
            characters={
                "protagonists": [CharacterDetail(name="Hero", physical_description="Brave warrior")]
            },
            conflict="Hero vs Dragon",
            resolution="Hero wins"
        )

        current_state = {
            "story_elements": story_elements,
            "last_completed_step": "detect_chapters"
        }

        # Act
        result = pipeline._expand_chapter_outlines_stage(
            current_state,
            "Base outline text for expansion",
            num_chapters=5,
            state_filepath="/tmp/test_state.json"
        )

        # Assert
        # Verify GetOutlineRating was called (at least once for quality check)
        assert mock_llm_editor.GetOutlineRating.called

        # Verify log contains quality met message
        log_messages = [msg for _, msg in mock_log.logs]
        quality_met_logs = [msg for msg in log_messages if "Quality Standard Met" in msg and "Global Outline Refinement" in msg]
        assert len(quality_met_logs) > 0, "Should log 'Quality Standard Met' exit reason"

        # Verify state saved with refined outline
        assert "refined_global_outline" in current_state
        # Note: last_completed_step will be "expand_chapters" since method continues to chapter expansion
        assert current_state["last_completed_step"] == "expand_chapters"

    def test_global_refinement_exits_after_max_revisions(
        self, mock_interface, mock_logger, mocker
    ):
        """
        Verify loop respects OUTLINE_MAX_REVISIONS limit.

        When quality never meets standards, loop should exit after
        MAX_REVISIONS iterations and accept best available outline.
        """
        # Arrange
        mocker.patch('Writer.Config.ENABLE_GLOBAL_OUTLINE_REFINEMENT', True)
        mocker.patch('Writer.Config.OUTLINE_MIN_REVISIONS', 1)
        mocker.patch('Writer.Config.OUTLINE_MAX_REVISIONS', 3)
        mocker.patch('Writer.Config.EXPAND_OUTLINE', True)

        # Mock LLMEditor - always returns False (quality never met)
        mock_llm_editor = mocker.patch('Writer.LLMEditor')
        mock_llm_editor.GetFeedbackOnOutline.return_value = "Needs improvement"
        mock_llm_editor.GetOutlineRating.return_value = False  # Always fails quality check

        # Mock OutlineGenerator with side_effect for multiple calls
        mock_outline_generator = MagicMock()
        mock_outline_generator.ReviseOutline.side_effect = [
            ("Revised outline iteration 1", [{"role": "assistant", "content": "rev1"}]),
            ("Revised outline iteration 2", [{"role": "assistant", "content": "rev2"}]),
            ("Revised outline iteration 3", [{"role": "assistant", "content": "rev3"}]),
        ]
        mock_outline_generator.GeneratePerChapterOutline.return_value = (
            "Chapter outline", "Chapter Title"
        )

        # Mock ActivePrompts
        mock_prompts = MagicMock()
        mock_prompts.REVISE_OUTLINE_CHARACTER_CONSTRAINT = "Expand. Use: {character_list}"
        mock_prompts.REVISE_OUTLINE_FALLBACK = "Expand. Keep existing."

        # Create Pipeline
        import Writer.Config as Config
        mock_iface = mock_interface()
        mock_log = mock_logger()

        pipeline = StoryPipeline(
            interface=mock_iface,
            sys_logger=mock_log,
            config=Config,
            active_prompts=mock_prompts,
            is_fresh_run=True
        )

        pipeline.OutlineGenerator = mock_outline_generator
        pipeline.ChapterDetector = MagicMock()
        pipeline.ChapterGenerator = MagicMock()

        story_elements = StoryElements(
            title="Test Story",
            genre="SciFi",
            themes=["technology"],
            characters={},
            conflict="AI vs Humans",
            resolution="Coexistence"
        )

        current_state = {
            "story_elements": story_elements,
            "last_completed_step": "detect_chapters"
        }

        # Act
        result = pipeline._expand_chapter_outlines_stage(
            current_state,
            "Base outline",
            num_chapters=3,
            state_filepath="/tmp/test_state.json"
        )

        # Assert
        # Verify ReviseOutline called exactly 3 times (max revisions)
        assert mock_outline_generator.ReviseOutline.call_count == 3

        # Verify iteration numbers passed correctly (1, 2, 3)
        call_args_list = mock_outline_generator.ReviseOutline.call_args_list
        for i, call_args in enumerate(call_args_list, 1):
            # Check _Iteration kwarg
            assert '_Iteration' in call_args.kwargs
            assert call_args.kwargs['_Iteration'] == i, f"Iteration {i} should have _Iteration={i}"

        # Verify log contains "Max Revisions Reached"
        log_messages = [msg for _, msg in mock_log.logs]
        max_revisions_logs = [msg for msg in log_messages if "Max Revisions Reached" in msg]
        assert len(max_revisions_logs) > 0, "Should log 'Max Revisions Reached' exit reason"

        # Verify state still saved (best available outline accepted)
        # Note: last_completed_step will be "expand_chapters" since method continues to chapter expansion
        assert current_state["last_completed_step"] == "expand_chapters"

    def test_global_refinement_quality_met_after_min_revisions(
        self, mock_interface, mock_logger, mocker
    ):
        """
        Verify MIN_REVISIONS enforced before accepting quality.

        Even if quality is True on iteration 1, loop should continue
        until MIN_REVISIONS iterations completed.
        """
        # Arrange
        mocker.patch('Writer.Config.ENABLE_GLOBAL_OUTLINE_REFINEMENT', True)
        mocker.patch('Writer.Config.OUTLINE_MIN_REVISIONS', 2)  # Minimum 2 revisions required
        mocker.patch('Writer.Config.OUTLINE_MAX_REVISIONS', 5)
        mocker.patch('Writer.Config.EXPAND_OUTLINE', True)

        # Mock LLMEditor - always returns True (quality always met)
        mock_llm_editor = mocker.patch('Writer.LLMEditor')
        mock_llm_editor.GetFeedbackOnOutline.return_value = "Excellent outline"
        mock_llm_editor.GetOutlineRating.return_value = True  # Always True

        # Mock OutlineGenerator
        mock_outline_generator = MagicMock()
        mock_outline_generator.ReviseOutline.side_effect = [
            ("Revised outline iter 1", [{"role": "assistant", "content": "r1"}]),
            ("Revised outline iter 2", [{"role": "assistant", "content": "r2"}]),
        ]
        mock_outline_generator.GeneratePerChapterOutline.return_value = (
            "Chapter outline", "Chapter Title"
        )

        # Mock ActivePrompts
        mock_prompts = MagicMock()
        mock_prompts.REVISE_OUTLINE_CHARACTER_CONSTRAINT = "Expand. Use: {character_list}"
        mock_prompts.REVISE_OUTLINE_FALLBACK = "Expand. Keep existing."

        # Create Pipeline
        import Writer.Config as Config
        mock_iface = mock_interface()
        mock_log = mock_logger()

        pipeline = StoryPipeline(
            interface=mock_iface,
            sys_logger=mock_log,
            config=Config,
            active_prompts=mock_prompts,
            is_fresh_run=True
        )

        pipeline.OutlineGenerator = mock_outline_generator
        pipeline.ChapterDetector = MagicMock()
        pipeline.ChapterGenerator = MagicMock()

        current_state = {
            "story_elements": StoryElements(
                title="Test Story",
                genre="Horror",
                themes=["fear"],
                characters={},
                conflict="Ghost",
                resolution="Exorcism"
            ),
            "last_completed_step": "detect_chapters"
        }

        # Act
        result = pipeline._expand_chapter_outlines_stage(
            current_state,
            "Base outline",
            num_chapters=4,
            state_filepath="/tmp/test_state.json"
        )

        # Assert
        # Verify ReviseOutline called exactly 2 times (MIN_REVISIONS)
        assert mock_outline_generator.ReviseOutline.call_count == 2, \
            "Should run 2 iterations despite quality met on iteration 1"

        # Verify exit reason is "Quality Standard Met" (not "Max Revisions")
        log_messages = [msg for _, msg in mock_log.logs]
        quality_met_logs = [msg for msg in log_messages if "Quality Standard Met" in msg]
        assert len(quality_met_logs) > 0

    def test_global_refinement_skipped_when_config_disabled(
        self, mock_interface, mock_logger, mocker
    ):
        """
        Verify feature flag controls execution.

        When ENABLE_GLOBAL_OUTLINE_REFINEMENT=False, validation loop
        should be skipped entirely and outline passed through unchanged.
        """
        # Arrange
        mocker.patch('Writer.Config.ENABLE_GLOBAL_OUTLINE_REFINEMENT', False)  # Feature disabled
        mocker.patch('Writer.Config.EXPAND_OUTLINE', True)

        # Mock LLMEditor - should NOT be called
        mock_llm_editor = mocker.patch('Writer.LLMEditor')

        # Mock OutlineGenerator - should NOT be called for refinement
        mock_outline_generator = MagicMock()
        mock_outline_generator.GeneratePerChapterOutline.return_value = (
            "Chapter outline", "Chapter Title"
        )

        # Mock ActivePrompts
        mock_prompts = MagicMock()

        # Create Pipeline
        import Writer.Config as Config
        mock_iface = mock_interface()
        mock_log = mock_logger()

        pipeline = StoryPipeline(
            interface=mock_iface,
            sys_logger=mock_log,
            config=Config,
            active_prompts=mock_prompts,
            is_fresh_run=True
        )

        pipeline.OutlineGenerator = mock_outline_generator
        pipeline.ChapterDetector = MagicMock()
        pipeline.ChapterGenerator = MagicMock()

        current_state = {
            "story_elements": StoryElements(
                title="Test Story",
                genre="Drama",
                themes=["loss"],
                characters={},
                conflict="Internal",
                resolution="Acceptance"
            ),
            "last_completed_step": "detect_chapters"
        }

        base_outline = "Original base outline text"

        # Act
        result = pipeline._expand_chapter_outlines_stage(
            current_state,
            base_outline,
            num_chapters=2,
            state_filepath="/tmp/test_state.json"
        )

        # Assert
        # Verify LLMEditor functions NOT called
        assert not mock_llm_editor.GetFeedbackOnOutline.called, \
            "GetFeedbackOnOutline should NOT be called when feature disabled"
        assert not mock_llm_editor.GetOutlineRating.called, \
            "GetOutlineRating should NOT be called when feature disabled"

        # Verify ReviseOutline NOT called for global refinement
        assert not mock_outline_generator.ReviseOutline.called, \
            "ReviseOutline should NOT be called when feature disabled"

        # Verify refined_global_outline = base_outline (passthrough)
        assert current_state["refined_global_outline"] == base_outline, \
            "Should pass through original outline unchanged"

        # Verify log confirms skipping
        log_messages = [msg for _, msg in mock_log.logs]
        skipping_logs = [msg for msg in log_messages if "Skipping" in msg and "Global Outline Refinement" in msg]
        assert len(skipping_logs) > 0

    def test_global_refinement_i18n_english_prompts(
        self, mock_interface, mock_logger, mocker, english_language_config
    ):
        """
        Verify English prompts loaded correctly.

        With NATIVE_LANGUAGE='en', should use Writer.Prompts (not Prompts_id).
        """
        # Arrange
        mocker.patch('Writer.Config.ENABLE_GLOBAL_OUTLINE_REFINEMENT', True)
        mocker.patch('Writer.Config.OUTLINE_MIN_REVISIONS', 1)
        mocker.patch('Writer.Config.OUTLINE_MAX_REVISIONS', 1)
        mocker.patch('Writer.Config.EXPAND_OUTLINE', True)

        # Mock LLMEditor
        mock_llm_editor = mocker.patch('Writer.LLMEditor')
        mock_llm_editor.GetFeedbackOnOutline.return_value = "Good outline"
        mock_llm_editor.GetOutlineRating.return_value = True

        # Mock OutlineGenerator
        mock_outline_generator = MagicMock()
        mock_outline_generator.ReviseOutline.return_value = (
            "Revised outline", []
        )
        mock_outline_generator.GeneratePerChapterOutline.return_value = (
            "Chapter outline", "Chapter Title"
        )

        # Get actual English prompts
        from Writer.PromptsHelper import get_prompts
        ActivePrompts = get_prompts()

        # Create Pipeline
        import Writer.Config as Config
        mock_iface = mock_interface()
        mock_log = mock_logger()

        pipeline = StoryPipeline(
            interface=mock_iface,
            sys_logger=mock_log,
            config=Config,
            active_prompts=ActivePrompts,
            is_fresh_run=True
        )

        pipeline.OutlineGenerator = mock_outline_generator
        pipeline.ChapterDetector = MagicMock()
        pipeline.ChapterGenerator = MagicMock()

        # Setup state with English characters
        story_elements = StoryElements(
            title="Dragon Quest",
            genre="Fantasy",
            themes=["courage"],
            characters={
                "protagonists": [CharacterDetail(name="Alice", physical_description="Brave knight")]
            },
            conflict="Dragon attack",
            resolution="Victory"
        )

        current_state = {
            "story_elements": story_elements,
            "last_completed_step": "detect_chapters"
        }

        # Act
        result = pipeline._expand_chapter_outlines_stage(
            current_state,
            "Base outline",
            num_chapters=3,
            state_filepath="/tmp/test_state.json"
        )

        # Assert
        # Check that English prompt templates are loaded
        assert hasattr(ActivePrompts, 'REVISE_OUTLINE_CHARACTER_CONSTRAINT')
        constraint_prompt = ActivePrompts.REVISE_OUTLINE_CHARACTER_CONSTRAINT

        # English prompts should contain English text, not Indonesian
        assert 'character' in constraint_prompt.lower(), \
            "English prompt should contain 'character'"
        assert 'karakter' not in constraint_prompt.lower(), \
            "English prompt should NOT contain Indonesian 'karakter'"

    def test_global_refinement_i18n_indonesian_prompts(
        self, mock_interface, mock_logger, mocker, indonesian_language_config
    ):
        """
        Verify Indonesian prompts loaded correctly.

        With NATIVE_LANGUAGE='id', should use Writer.Prompts_id.
        """
        # Arrange
        mocker.patch('Writer.Config.ENABLE_GLOBAL_OUTLINE_REFINEMENT', True)
        mocker.patch('Writer.Config.OUTLINE_MIN_REVISIONS', 1)
        mocker.patch('Writer.Config.OUTLINE_MAX_REVISIONS', 1)
        mocker.patch('Writer.Config.EXPAND_OUTLINE', True)

        # Mock LLMEditor
        mock_llm_editor = mocker.patch('Writer.LLMEditor')
        mock_llm_editor.GetFeedbackOnOutline.return_value = "Outline bagus"
        mock_llm_editor.GetOutlineRating.return_value = True

        # Mock OutlineGenerator
        mock_outline_generator = MagicMock()
        mock_outline_generator.ReviseOutline.return_value = (
            "Outline yang direvisi", []
        )
        mock_outline_generator.GeneratePerChapterOutline.return_value = (
            "Chapter outline", "Chapter Title"
        )

        # Get actual Indonesian prompts
        from Writer.PromptsHelper import get_prompts
        ActivePrompts = get_prompts()

        # Create Pipeline
        import Writer.Config as Config
        mock_iface = mock_interface()
        mock_log = mock_logger()

        pipeline = StoryPipeline(
            interface=mock_iface,
            sys_logger=mock_log,
            config=Config,
            active_prompts=ActivePrompts,
            is_fresh_run=True
        )

        pipeline.OutlineGenerator = mock_outline_generator
        pipeline.ChapterDetector = MagicMock()
        pipeline.ChapterGenerator = MagicMock()

        # Setup state with Indonesian characters
        story_elements = StoryElements(
            title="Petualangan Naga",
            genre="Fantasi",
            themes=["keberanian"],
            characters={
                "protagonists": [CharacterDetail(name="Budi", physical_description="Ksatria pemberani")]
            },
            conflict="Serangan naga",
            resolution="Kemenangan"
        )

        current_state = {
            "story_elements": story_elements,
            "last_completed_step": "detect_chapters"
        }

        # Act
        result = pipeline._expand_chapter_outlines_stage(
            current_state,
            "Outline dasar",
            num_chapters=3,
            state_filepath="/tmp/test_state.json"
        )

        # Assert
        # Check that Indonesian prompt templates are loaded
        assert hasattr(ActivePrompts, 'REVISE_OUTLINE_CHARACTER_CONSTRAINT')
        constraint_prompt = ActivePrompts.REVISE_OUTLINE_CHARACTER_CONSTRAINT

        # Indonesian prompts should contain Indonesian text
        assert 'karakter' in constraint_prompt.lower(), \
            "Indonesian prompt should contain 'karakter'"

    def test_global_refinement_preserves_message_history(
        self, mock_interface, mock_logger, mocker
    ):
        """
        Verify message history chained across iterations.

        First ReviseOutline call should get empty history [],
        subsequent calls should receive history from previous call.
        """
        # Arrange
        mocker.patch('Writer.Config.ENABLE_GLOBAL_OUTLINE_REFINEMENT', True)
        mocker.patch('Writer.Config.OUTLINE_MIN_REVISIONS', 1)
        mocker.patch('Writer.Config.OUTLINE_MAX_REVISIONS', 3)
        mocker.patch('Writer.Config.EXPAND_OUTLINE', True)

        # Mock LLMEditor - quality not met, will hit MAX_REVISIONS
        mock_llm_editor = mocker.patch('Writer.LLMEditor')
        mock_llm_editor.GetFeedbackOnOutline.return_value = "Needs work"
        # Need 4 values: iterations 1, 2, 3, and check after iteration 3
        mock_llm_editor.GetOutlineRating.side_effect = [False, False, False, False]

        # Track history passed to each ReviseOutline call
        history_tracker = []

        def track_revise_outline(*args, **kwargs):
            # ReviseOutline signature: (Interface, _Logger, _Outline, _Feedback, _History, _Iteration)
            # Get _History from args[4]
            history = args[4] if len(args) > 4 else []
            history_tracker.append(list(history))  # Store copy

            # Return new history with message appended
            new_history = list(history) + [{"role": "assistant", "content": f"revision {len(history_tracker)}"}]
            return (f"Revised outline {len(history_tracker)}", new_history)

        mock_outline_generator = MagicMock()
        mock_outline_generator.ReviseOutline.side_effect = track_revise_outline
        mock_outline_generator.GeneratePerChapterOutline.return_value = (
            "Chapter outline", "Chapter Title"
        )

        # Mock ActivePrompts
        mock_prompts = MagicMock()
        mock_prompts.REVISE_OUTLINE_FALLBACK = "Expand. Keep existing."

        # Create Pipeline
        import Writer.Config as Config
        mock_iface = mock_interface()
        mock_log = mock_logger()

        pipeline = StoryPipeline(
            interface=mock_iface,
            sys_logger=mock_log,
            config=Config,
            active_prompts=mock_prompts,
            is_fresh_run=True
        )

        pipeline.OutlineGenerator = mock_outline_generator
        pipeline.ChapterDetector = MagicMock()
        pipeline.ChapterGenerator = MagicMock()

        current_state = {
            "story_elements": StoryElements(
                title="Test Story",
                genre="Mystery",
                themes=["truth"],
                characters={},
                conflict="Whodunit",
                resolution="Solved"
            ),
            "last_completed_step": "detect_chapters"
        }

        # Act
        result = pipeline._expand_chapter_outlines_stage(
            current_state,
            "Base outline",
            num_chapters=2,
            state_filepath="/tmp/test_state.json"
        )

        # Assert
        assert len(history_tracker) == 3, "Should have 3 ReviseOutline calls"

        # First call should get empty history []
        assert history_tracker[0] == [], "First iteration should start with empty history"

        # Second call should get history from first call
        assert len(history_tracker[1]) == 1, "Second iteration should have 1 message from first"

        # Third call should get history from second call
        assert len(history_tracker[2]) == 2, "Third iteration should have 2 messages from previous iterations"

    def test_global_refinement_state_saved_after_loop_completes(
        self, mock_interface, mock_logger, mocker
    ):
        """
        Verify state saved ONCE after loop completes (not during iterations).

        _save_state_wrapper should be called exactly once for global refinement,
        after the validation loop exits, not during loop iterations.
        """
        # Arrange
        mocker.patch('Writer.Config.ENABLE_GLOBAL_OUTLINE_REFINEMENT', True)
        mocker.patch('Writer.Config.OUTLINE_MIN_REVISIONS', 1)
        mocker.patch('Writer.Config.OUTLINE_MAX_REVISIONS', 2)
        mocker.patch('Writer.Config.EXPAND_OUTLINE', True)

        # Mock LLMEditor
        mock_llm_editor = mocker.patch('Writer.LLMEditor')
        mock_llm_editor.GetFeedbackOnOutline.return_value = "Feedback"
        mock_llm_editor.GetOutlineRating.side_effect = [False, True]  # Quality met on 2nd

        # Mock OutlineGenerator
        mock_outline_generator = MagicMock()
        mock_outline_generator.ReviseOutline.side_effect = [
            ("Revision 1", []),
            ("Revision 2", []),
        ]
        mock_outline_generator.GeneratePerChapterOutline.return_value = (
            "Chapter outline", "Chapter Title"
        )

        # Mock ActivePrompts
        mock_prompts = MagicMock()
        mock_prompts.REVISE_OUTLINE_FALLBACK = "Expand. Keep existing."

        # Create Pipeline
        import Writer.Config as Config
        mock_iface = mock_interface()
        mock_log = mock_logger()

        pipeline = StoryPipeline(
            interface=mock_iface,
            sys_logger=mock_log,
            config=Config,
            active_prompts=mock_prompts,
            is_fresh_run=True
        )

        pipeline.OutlineGenerator = mock_outline_generator
        pipeline.ChapterDetector = MagicMock()
        pipeline.ChapterGenerator = MagicMock()

        # Track _save_state_wrapper calls
        save_state_calls = []
        original_save = pipeline._save_state_wrapper

        def track_save_state(state, filepath):
            save_state_calls.append((state, filepath))
            return original_save(state, filepath)

        pipeline._save_state_wrapper = track_save_state

        current_state = {
            "story_elements": StoryElements(
                title="Test Story",
                genre="Thriller",
                themes=["suspense"],
                characters={},
                conflict="Chase",
                resolution="Escape"
            ),
            "last_completed_step": "detect_chapters"
        }

        # Act
        result = pipeline._expand_chapter_outlines_stage(
            current_state,
            "Base outline",
            num_chapters=1,
            state_filepath="/tmp/test_state.json"
        )

        # Assert
        # Verify state was saved (at least once for refinement)
        assert len(save_state_calls) >= 1, "_save_state_wrapper should be called at least once"

        # Verify state contains refined_global_outline
        assert "refined_global_outline" in current_state
        assert "Revision" in current_state["refined_global_outline"]

    def test_global_refinement_character_whitelist_extraction(
        self, mock_interface, mock_logger, mocker
    ):
        """
        Verify character names extracted from StoryElements.

        When story_elements contains characters, feedback instruction
        should use REVISE_OUTLINE_CHARACTER_CONSTRAINT with character list.
        """
        # Arrange
        mocker.patch('Writer.Config.ENABLE_GLOBAL_OUTLINE_REFINEMENT', True)
        mocker.patch('Writer.Config.OUTLINE_MIN_REVISIONS', 1)
        mocker.patch('Writer.Config.OUTLINE_MAX_REVISIONS', 1)
        mocker.patch('Writer.Config.EXPAND_OUTLINE', True)

        # Mock LLMEditor
        mock_llm_editor = mocker.patch('Writer.LLMEditor')
        mock_llm_editor.GetFeedbackOnOutline.return_value = "Good"
        mock_llm_editor.GetOutlineRating.return_value = True

        # Track feedback argument passed to ReviseOutline
        feedback_tracker = []

        def track_feedback(*args, **kwargs):
            # ReviseOutline signature: (Interface, _Logger, _Outline, _Feedback, _History, _Iteration)
            feedback = args[3] if len(args) > 3 else ""
            feedback_tracker.append(feedback)
            return ("Revised outline", [])

        mock_outline_generator = MagicMock()
        mock_outline_generator.ReviseOutline.side_effect = track_feedback
        mock_outline_generator.GeneratePerChapterOutline.return_value = (
            "Chapter outline", "Chapter Title"
        )

        # Mock ActivePrompts with character constraint template
        mock_prompts = MagicMock()
        mock_prompts.REVISE_OUTLINE_CHARACTER_CONSTRAINT = "Expand outline. ONLY use these characters: {character_list}. DO NOT add new characters."

        # Create Pipeline
        import Writer.Config as Config
        mock_iface = mock_interface()
        mock_log = mock_logger()

        pipeline = StoryPipeline(
            interface=mock_iface,
            sys_logger=mock_log,
            config=Config,
            active_prompts=mock_prompts,
            is_fresh_run=True
        )

        pipeline.OutlineGenerator = mock_outline_generator
        pipeline.ChapterDetector = MagicMock()
        pipeline.ChapterGenerator = MagicMock()

        # Setup state with multiple characters
        story_elements = StoryElements(
            title="Character Test",
            genre="Adventure",
            themes=["friendship"],
            characters={
                "protagonists": [
                    CharacterDetail(name="Alice", physical_description="Hero"),
                    CharacterDetail(name="Bob", physical_description="Sidekick")
                ],
                "antagonists": [
                    CharacterDetail(name="Villain", physical_description="Evil")
                ]
            },
            conflict="Good vs Evil",
            resolution="Good wins"
        )

        current_state = {
            "story_elements": story_elements,
            "last_completed_step": "detect_chapters"
        }

        # Act
        result = pipeline._expand_chapter_outlines_stage(
            current_state,
            "Base outline",
            num_chapters=2,
            state_filepath="/tmp/test_state.json"
        )

        # Assert
        assert len(feedback_tracker) > 0, "Should have captured feedback"
        first_feedback = feedback_tracker[0]

        # Verify character names appear in feedback (comma-separated)
        assert "Alice" in first_feedback, "Feedback should contain character Alice"
        assert "Bob" in first_feedback, "Feedback should contain character Bob"
        assert "Villain" in first_feedback, "Feedback should contain character Villain"

        # Verify it's using character constraint template (not fallback)
        # Check for restrictive language in both English and Indonesian
        assert ("ONLY" in first_feedback or "DO NOT" in first_feedback or
                "HANYA" in first_feedback or "DILARANG" in first_feedback), \
            "Should use character constraint template with restrictive language"

    def test_global_refinement_fallback_when_no_characters(
        self, mock_interface, mock_logger, mocker
    ):
        """
        Verify fallback feedback when no characters available.

        When story_elements has no characters or characters is empty,
        should use REVISE_OUTLINE_FALLBACK template instead.
        """
        # Arrange
        mocker.patch('Writer.Config.ENABLE_GLOBAL_OUTLINE_REFINEMENT', True)
        mocker.patch('Writer.Config.OUTLINE_MIN_REVISIONS', 1)
        mocker.patch('Writer.Config.OUTLINE_MAX_REVISIONS', 1)
        mocker.patch('Writer.Config.EXPAND_OUTLINE', True)

        # Mock LLMEditor
        mock_llm_editor = mocker.patch('Writer.LLMEditor')
        mock_llm_editor.GetFeedbackOnOutline.return_value = "Good"
        mock_llm_editor.GetOutlineRating.return_value = True

        # Track feedback argument
        feedback_tracker = []

        def track_feedback(*args, **kwargs):
            # ReviseOutline signature: (Interface, _Logger, _Outline, _Feedback, _History, _Iteration)
            feedback = args[3] if len(args) > 3 else ""
            feedback_tracker.append(feedback)
            return ("Revised outline", [])

        mock_outline_generator = MagicMock()
        mock_outline_generator.ReviseOutline.side_effect = track_feedback
        mock_outline_generator.GeneratePerChapterOutline.return_value = (
            "Chapter outline", "Chapter Title"
        )

        # Mock ActivePrompts
        mock_prompts = MagicMock()
        mock_prompts.REVISE_OUTLINE_CHARACTER_CONSTRAINT = "Use only: {character_list}"
        mock_prompts.REVISE_OUTLINE_FALLBACK = "Expand outline. KEEP ALL character names that already exist in the original outline!"

        # Create Pipeline
        import Writer.Config as Config
        mock_iface = mock_interface()
        mock_log = mock_logger()

        pipeline = StoryPipeline(
            interface=mock_iface,
            sys_logger=mock_log,
            config=Config,
            active_prompts=mock_prompts,
            is_fresh_run=True
        )

        pipeline.OutlineGenerator = mock_outline_generator
        pipeline.ChapterDetector = MagicMock()
        pipeline.ChapterGenerator = MagicMock()

        # Setup state with NO characters
        story_elements = StoryElements(
            title="No Characters Test",
            genre="Abstract",
            themes=["void"],
            characters={},  # Empty characters dict
            conflict="Existential",
            resolution="Acceptance"
        )

        current_state = {
            "story_elements": story_elements,
            "last_completed_step": "detect_chapters"
        }

        # Act - should not crash despite missing characters
        result = pipeline._expand_chapter_outlines_stage(
            current_state,
            "Base outline",
            num_chapters=1,
            state_filepath="/tmp/test_state.json"
        )

        # Assert
        assert len(feedback_tracker) > 0, "Should have captured feedback"
        first_feedback = feedback_tracker[0]

        # Verify it's using fallback template (should mention "KEEP" or "existing" or "Jaga" in Indonesian)
        assert ("KEEP" in first_feedback or "existing" in first_feedback or
                "Jaga" in first_feedback or "karakter" in first_feedback), \
            "Should use fallback template mentioning keeping existing characters"

        # Verify no specific character names in template (since there are none)
        assert "Alice" not in first_feedback and "Bob" not in first_feedback, \
            "Fallback template shouldn't contain specific character names"
