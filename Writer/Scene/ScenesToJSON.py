from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from Writer.Models import SceneOutline


def _deduplicate_scenes(scenes: List[str]) -> List[str]:
    """
    Remove duplicate scenes while preserving order.
    Uses fuzzy matching to detect similar-but-not-identical duplicates.

    Args:
        scenes: List of scene descriptions

    Returns:
        List with duplicates removed
    """
    if not scenes:
        return scenes

    unique_scenes = []
    seen = set()

    for scene in scenes:
        # Normalize by stripping and lowercasing for exact duplicate check
        normalized = scene.strip().lower()

        # Check for exact duplicate
        if normalized not in seen:
            # Additional fuzzy check for near-duplicates
            is_duplicate = False
            for existing_scene in unique_scenes:
                # Simple similarity check: if most words are the same, consider it a duplicate
                words1 = set(normalized.split())
                words2 = set(existing_scene.lower().split())

                # If both have more than 5 words and share 80%+ similarity, consider duplicate
                if len(words1) > 5 and len(words2) > 5:
                    intersection = words1.intersection(words2)
                    union = words1.union(words2)
                    similarity = len(intersection) / len(union) if union else 0

                    if similarity > 0.8:
                        is_duplicate = True
                        break

            if not is_duplicate:
                unique_scenes.append(scene)
                seen.add(normalized)

    return unique_scenes


def deduplicate_scene_objects(scenes: List['SceneOutline']) -> List['SceneOutline']:
    """
    Deduplicate SceneOutline objects by comparing action fields.
    Convenience wrapper around _deduplicate_scenes for SceneOutline objects.

    Args:
        scenes: List of SceneOutline objects

    Returns:
        List of SceneOutline objects with duplicates removed

    Examples:
        >>> from Writer.Models import SceneOutline
        >>> scenes = [
        ...     SceneOutline(scene_number=1, setting="Cave", characters_present=["Hero"],
        ...                  action="Hero finds treasure", purpose="Climax", estimated_word_count=200),
        ...     SceneOutline(scene_number=2, setting="Cave", characters_present=["Hero"],
        ...                  action="Hero finds treasure", purpose="Climax", estimated_word_count=200),
        ...     SceneOutline(scene_number=3, setting="Exit", characters_present=["Hero"],
        ...                  action="Hero exits", purpose="Resolution", estimated_word_count=150)
        ... ]
        >>> result = deduplicate_scene_objects(scenes)
        >>> len(result)
        2
        >>> result[0].action
        'Hero finds treasure'
        >>> result[1].action
        'Hero exits'
    """
    if not scenes:
        return scenes

    # Extract actions for deduplication
    scene_actions = [scene.action for scene in scenes]
    deduplicated_actions = _deduplicate_scenes(scene_actions)

    # Filter to keep only non-duplicates (preserve order and metadata)
    result = []
    actions_to_keep = set(deduplicated_actions)
    seen_actions = set()

    for scene in scenes:
        if scene.action in actions_to_keep and scene.action not in seen_actions:
            result.append(scene)
            seen_actions.add(scene.action)

    return result
