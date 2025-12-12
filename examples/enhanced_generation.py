#!/usr/bin/env python3
"""
Example: Enhanced story generation with LangChain features

This example demonstrates how to use AIStoryWriter with all LangChain enhancements:
- Lorebook for story consistency
- Pydantic for structured output
- Reasoning chain for better content quality
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from Writer.Interface.Wrapper import Interface
from Writer.Models import ChapterOutput, OutlineOutput
from Writer.ReasoningChain import ReasoningChain
from Writer.Lorebook import LorebookManager
from Writer.PrintUtils import Logger
import Writer.Config as Config


def demonstrate_enhancements():
    """Demonstrate all LangChain enhancements"""

    print("🚀 AIStoryWriter LangChain Enhancements Demo")
    print("=" * 50)

    # Ensure all features are enabled
    Config.USE_LOREBOOK = True
    Config.USE_PYDANTIC_PARSING = True
    Config.USE_REASONING_CHAIN = True

    print("\n✅ Configuration:")
    print(f"  - USE_LOREBOOK: {Config.USE_LOREBOOK}")
    print(f"  - USE_PYDANTIC_PARSING: {Config.USE_PYDANTIC_PARSING}")
    print(f"  - USE_REASONING_CHAIN: {Config.USE_REASONING_CHAIN}")

    # Initialize components
    logger = Logger()
    interface = Interface()

    print("\n📚 Demonstrating Lorebook System:")
    print("-" * 30)

    # Create and populate lorebook
    lorebook = LorebookManager("./examples/demo_lorebook")

    # Add some sample lore entries
    lorebook.add_entry(
        "Elena is a skilled mage from the northern kingdoms, known for her ice magic and determination.",
        {"type": "character", "name": "Elena", "importance": "protagonist"}
    )

    lorebook.add_entry(
        "The Frozen Citadel is an ancient fortress made of eternal ice, located in the heart of the tundra.",
        {"type": "location", "name": "Frozen Citadel", "climate": "arctic"}
    )

    lorebook.add_entry(
        "The Shadow Council is a clandestine organization that manipulates kingdoms from behind the scenes.",
        {"type": "faction", "name": "Shadow Council", "alignment": "evil"}
    )

    # Test retrieval
    chapter_outline = "Elena must journey to the Frozen Citadel to retrieve the Ice Crystal while avoiding the Shadow Council."
    relevant_lore = lorebook.retrieve(chapter_outline, k=3)

    print("Chapter Outline:", chapter_outline)
    print("\nRetrieved Lore:")
    for i, lore in enumerate(relevant_lore, 1):
        print(f"{i}. {lore[:100]}...")

    print("\n🤖 Demonstrating Reasoning Chain:")
    print("-" * 30)

    # Create reasoning chain
    reasoning_chain = ReasoningChain(interface, Config, logger)

    # Generate different types of reasoning
    context = f"""
STORY OUTLINE: {chapter_outline}
RELEVANT LORE: {relevant_lore}
"""

    # Check if we have active models for reasoning
    if not interface.Clients:
        print("\n⚠️ No active models detected. Mocking reasoning demonstration...")
        plot_reasoning = "PLOT REASONING MOCK: The story should establish Elena's motivation clearly in the first chapter by connecting her mage training to the urgent need for the Ice Crystal. The pacing should build tension between her preparation and the Shadow Council's pursuit..."
        char_reasoning = "CHARACTER REASONING MOCK: Elena should show both her magical prowess and her vulnerability. Her internal conflict about leaving her northern home should be evident through her actions and decisions..."
    else:
        # Plot reasoning
        try:
            plot_reasoning = reasoning_chain.reason(context, "plot", None, 1)
        except Exception as e:
            print(f"\n⚠️ Could not generate plot reasoning: {e}")
            plot_reasoning = "REASONING FAILED - Would analyze story structure, pacing, and key plot points..."

        # Character reasoning
        try:
            char_reasoning = reasoning_chain.reason(context, "character", None, 1)
        except Exception as e:
            print(f"\n⚠️ Could not generate character reasoning: {e}")
            char_reasoning = "REASONING FAILED - Would analyze character development, motivations, and interactions..."

    print("\n=== PLOT REASONING ===")
    print(plot_reasoning[:300] + "..." if len(plot_reasoning) > 300 else plot_reasoning)

    print("\n=== CHARACTER REASONING ===")
    print(char_reasoning[:300] + "..." if len(char_reasoning) > 300 else char_reasoning)

    print("\n📝 Demonstrating Structured Output with Pydantic:")
    print("-" * 30)

    # Mock the interface for demonstration if no real model available
    if not interface.Clients:
        print("⚠️ No LLM clients configured. Showing expected structure demonstration...")

        # Create a mock Pydantic model to demonstrate validation
        try:
            # Valid chapter output
            chapter = ChapterOutput(
                text="Elena stood at the gates of the Frozen Citadel, her breath forming mist in the frigid air. The towering walls of ice gleamed under the faint light of the aurora. She knew the Shadow Council's agents were hunting her, but the fate of her kingdom depended on retrieving the Ice Crystal from within these frozen halls. With practiced ease, she drew upon her magic, forming a small ball of blue flame to ward off the biting cold.",
                word_count=75,
                chapter_number=1,
                chapter_title="The Gates of Ice",
                scenes=["Approaching the citadel", "Magic preparation"],
                characters_present=["Elena"]
            )

            print("✅ Valid Pydantic ChapterOutput created:")
            print(f"  - Title: {chapter.chapter_title}")
            print(f"  - Word Count: {chapter.word_count}")
            print(f"  - Scenes: {', '.join(chapter.scenes)}")
            print(f"  - Characters: {', '.join(chapter.characters_present)}")
            print(f"  - Text Preview: {chapter.text[:100]}...")

            # Show model schema
            print("\n📋 ChapterOutput Schema:")
            schema = chapter.model_json_schema()
            print(f"  Required Fields: {', '.join(schema['required'])}")
            print(f"  Optional Fields: {', '.join([f for f in schema['properties'] if f not in schema['required']])}")

        except Exception as e:
            print(f"❌ Error creating ChapterOutput: {e}")
    else:
        print("🎯 Real LLM clients detected. To test with actual models:")
        print("1. Configure your LM clients in Writer/Config.py")
        print("2. Run: python -m pytest tests/test_write.py::test_full_pipeline")

    print("\n📊 Current System Status:")
    print("-" * 30)

    # Show lorebook stats
    lorebook_stats = lorebook.get_stats()
    print(f"Lorebook: {lorebook_stats['total_entries']} entries")

    # Show reasoning stats
    reasoning_stats = reasoning_chain.get_stats()
    print(f"Reasoning: Cache enabled={reasoning_stats['cache_enabled']}, "
          f"Cached items={reasoning_stats['cached_items']}")

    # Show configuration
    print(f"Pydantic: Available={Config.USE_PYDANTIC_PARSING}")
    print(f"Reasoning Log: {Config.REASONING_LOG_SEPARATE}")

    print("\n🎉 Demo Complete!")
    print("\nTo use these enhancements in your story generation:")
    print("1. Ensure the features are enabled in Writer/Config.py")
    print("2. Run: python Write.py -Prompt Prompts/YourStory.txt")
    print("3. Check Logs/Reasoning/ for reasoning logs (if enabled)")
    print("4. Review the enhanced chapter output")


def performance_comparison():
    """Compare performance with and without enhancements"""
    import time
    from unittest.mock import Mock

    print("\n⚡ Performance Comparison:")
    print("=" * 50)

    # Mock interface for consistent timing
    mock_interface = Mock(spec=Interface)
    mock_interface.SafeGenerateText.return_value = ([], {"tokens": 100})
    mock_interface.GetLastMessageText.return_value = "Generated text"
    mock_interface.BuildSystemQuery.return_value = {"role": "system", "content": "system"}
    mock_interface.BuildUserQuery.return_value = {"role": "user", "content": "user"}

    # Test without enhancements
    Config.USE_LOREBOOK = False
    Config.USE_PYDANTIC_PARSING = False
    Config.USE_REASONING_CHAIN = False

    start = time.time()
    for _ in range(5):
        # Simulate chapter generation
        from Writer.Chapter.ChapterGenerator import _generate_stage1_plot
        _generate_stage1_plot(
            mock_interface, Mock(), Mock(), 1, 10, [], "",
            "Test outline", "", "Context", "Outline", Config, Mock()
        )
    time_without = time.time() - start

    # Test with all enhancements
    Config.USE_LOREBOOK = True
    Config.USE_PYDANTIC_PARSING = True
    Config.USE_REASONING_CHAIN = True

    mock_interface.SafeGeneratePydantic.return_value = ([], Mock(text="Text"), {"tokens": 100})

    start = time.time()
    for _ in range(5):
        # Simulate enhanced chapter generation
        from Writer.Chapter.ChapterGenerator import _generate_stage1_plot
        _generate_stage1_plot(
            mock_interface, Mock(), Mock(), 1, 10, [], "",
            "Test outline", "", "Context", "Outline", Config, Mock()
        )
    time_with = time.time() - start

    print(f"Time without enhancements: {time_without:.2f}s")
    print(f"Time with enhancements: {time_with:.2f}s")
    print(f"Overhead: {(time_with - time_without)/time_without*100:.1f}%")


if __name__ == "__main__":
    print("Starting LangChain Enhancements Demo...")

    # Run main demonstration
    demonstrate_enhancements()

    # Run performance comparison
    try:
        performance_comparison()
    except Exception as e:
        print(f"\nPerformance comparison unavailable: {e}")

    print("\n" + "=" * 50)
    print("For more information, see: docs/langchain_enhancements.md")
    print("=" * 50)