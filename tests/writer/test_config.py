"""
Tests for Config.py vLLM repetition control settings

Phase: RED - These tests will fail initially because:
1. VLLM_REPETITION_PENALTY doesn't exist yet
2. VLLM_TOP_P and VLLM_TOP_K don't exist yet
3. VLLM_STOP_TOKENS doesn't exist yet
4. MIN_PHRASE_LENGTH and MAX_PHRASE_REPETITIONS have old values
"""
import Writer.Config


class TestVLLMRepetitionConfig:
    """Test Config.py has new vLLM repetition control settings"""

    def test_vllm_repetition_penalty_config_exists(self):
        """Config should have VLLM_REPETITION_PENALTY for vLLM-native penalty"""
        assert hasattr(Writer.Config, 'VLLM_REPETITION_PENALTY'), \
            "VLLM_REPETITION_PENALTY not found in Config"

    def test_vllm_repetition_penalty_value(self):
        """VLLM_REPETITION_PENALTY should be > 1.0 (penalize repetition)"""
        assert hasattr(Writer.Config, 'VLLM_REPETITION_PENALTY'), \
            "VLLM_REPETITION_PENALTY not found in Config"
        assert Writer.Config.VLLM_REPETITION_PENALTY > 1.0, \
            f"VLLM_REPETITION_PENALTY should be > 1.0, got {Writer.Config.VLLM_REPETITION_PENALTY}"

    def test_vllm_top_p_config_exists(self):
        """Config should have VLLM_TOP_P for nucleus sampling"""
        assert hasattr(Writer.Config, 'VLLM_TOP_P'), \
            "VLLM_TOP_P not found in Config"

    def test_vllm_top_p_value(self):
        """VLLM_TOP_P should be in range (0, 1]"""
        assert hasattr(Writer.Config, 'VLLM_TOP_P'), \
            "VLLM_TOP_P not found in Config"
        assert 0 < Writer.Config.VLLM_TOP_P <= 1.0, \
            f"VLLM_TOP_P should be in (0, 1], got {Writer.Config.VLLM_TOP_P}"

    def test_vllm_top_k_config_exists(self):
        """Config should have VLLM_TOP_K for top-k sampling"""
        assert hasattr(Writer.Config, 'VLLM_TOP_K'), \
            "VLLM_TOP_K not found in Config"

    def test_vllm_top_k_value(self):
        """VLLM_TOP_K should be positive integer"""
        assert hasattr(Writer.Config, 'VLLM_TOP_K'), \
            "VLLM_TOP_K not found in Config"
        assert Writer.Config.VLLM_TOP_K > 0, \
            f"VLLM_TOP_K should be > 0, got {Writer.Config.VLLM_TOP_K}"

    def test_vllm_stop_tokens_config_exists(self):
        """Config should have VLLM_STOP_TOKENS for character explosion prevention"""
        assert hasattr(Writer.Config, 'VLLM_STOP_TOKENS'), \
            "VLLM_STOP_TOKENS not found in Config"

    def test_vllm_stop_tokens_is_list(self):
        """VLLM_STOP_TOKENS should be a list of strings"""
        assert hasattr(Writer.Config, 'VLLM_STOP_TOKENS'), \
            "VLLM_STOP_TOKENS not found in Config"
        assert isinstance(Writer.Config.VLLM_STOP_TOKENS, list), \
            f"VLLM_STOP_TOKENS should be a list, got {type(Writer.Config.VLLM_STOP_TOKENS)}"
        # Check that all elements are strings
        for token in Writer.Config.VLLM_STOP_TOKENS:
            assert isinstance(token, str), \
                f"All VLLM_STOP_TOKENS elements should be strings, found {type(token)}"


class TestRepetitionDetectionThresholds:
    """Test Config.py repetition detection threshold updates"""

    def test_min_phrase_length_updated(self):
        """MIN_PHRASE_LENGTH should be 25 (reduced false positives)"""
        assert hasattr(Writer.Config, 'MIN_PHRASE_LENGTH'), \
            "MIN_PHRASE_LENGTH not found in Config"
        assert Writer.Config.MIN_PHRASE_LENGTH == 25, \
            f"MIN_PHRASE_LENGTH should be 25, got {Writer.Config.MIN_PHRASE_LENGTH}"

    def test_max_phrase_repetitions_updated(self):
        """MAX_PHRASE_REPETITIONS should be 3 (reduced false positives)"""
        assert hasattr(Writer.Config, 'MAX_PHRASE_REPETITIONS'), \
            "MAX_PHRASE_REPETITIONS not found in Config"
        assert Writer.Config.MAX_PHRASE_REPETITIONS == 3, \
            f"MAX_PHRASE_REPETITIONS should be 3, got {Writer.Config.MAX_PHRASE_REPETITIONS}"

    def test_max_ngram_repetitions_unchanged(self):
        """MAX_NGRAM_REPETITIONS should remain 3 (consistency)"""
        assert hasattr(Writer.Config, 'MAX_NGRAM_REPETITIONS'), \
            "MAX_NGRAM_REPETITIONS not found in Config"
        assert Writer.Config.MAX_NGRAM_REPETITIONS == 3, \
            f"MAX_NGRAM_REPETITIONS should be 3, got {Writer.Config.MAX_NGRAM_REPETITIONS}"
