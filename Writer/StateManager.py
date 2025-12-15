"""
StateManager - Centralized Pydantic serialization for state management

Handles serialization and deserialization of Pydantic objects in state files.
Uses container-based approach to separate Pydantic data from regular data.

No backward compatibility - fresh start with Pydantic-only approach.
"""
import json
from typing import Dict, Any, Union
from pathlib import Path
from Writer.Models import MODEL_REGISTRY, get_model


class StateManager:
    """Centralized Pydantic serialization for state management"""

    PYDANTIC_KEY = "pydantic_objects"
    OTHER_KEY = "other_data"
    MODEL_KEY = "__model__"
    DATA_KEY = "__data__"

    @classmethod
    def save_state(cls, state_data: Dict[str, Any], filepath: Union[str, Path]) -> None:
        """
        Save state with Pydantic objects properly serialized

        Args:
            state_data: Dictionary containing mixed data (Pydantic objects + regular data)
            filepath: Path where to save the state file

        Raises:
            TypeError: If Pydantic model is not in MODEL_REGISTRY
            OSError: If file cannot be written
        """
        pydantic_objects = {}
        other_data = {}

        for key, value in state_data.items():
            if cls._is_pydantic_model(value):
                # It's a Pydantic model - serialize it
                model_name = type(value).__name__

                # Verify model is in registry
                if model_name not in MODEL_REGISTRY:
                    raise TypeError(f"Pydantic model '{model_name}' not found in MODEL_REGISTRY")

                pydantic_objects[key] = {
                    cls.MODEL_KEY: model_name,
                    cls.DATA_KEY: value.model_dump()
                }
            else:
                # Regular data - store as-is
                other_data[key] = value

        # Combine and save
        combined = {
            cls.PYDANTIC_KEY: pydantic_objects,
            cls.OTHER_KEY: other_data
        }

        # Ensure directory exists
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(combined, f, indent=4, ensure_ascii=False)

    @classmethod
    def load_state(cls, filepath: Union[str, Path]) -> Dict[str, Any]:
        """
        Load state and reconstruct Pydantic objects

        Args:
            filepath: Path to the saved state file

        Returns:
            Dictionary with Pydantic objects properly reconstructed

        Raises:
            FileNotFoundError: If state file doesn't exist
            json.JSONDecodeError: If file contains invalid JSON
            ValueError: If model data is malformed
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            loaded = json.load(f)

        result = {}

        # Reconstruct Pydantic objects
        pydantic_objects = loaded.get(cls.PYDANTIC_KEY, {})
        for key, obj_data in pydantic_objects.items():
            try:
                model_name = obj_data[cls.MODEL_KEY]
                model_data = obj_data[cls.DATA_KEY]

                # Get model class from registry
                model_class = get_model(model_name)
                if model_class:
                    result[key] = model_class(**model_data)
                else:
                    # If model not found, keep as dict but log warning
                    import sys
                    print(f"Warning: Model '{model_name}' not found in registry, keeping as dict", file=sys.stderr)
                    result[key] = model_data
            except KeyError as e:
                raise ValueError(f"Malformed Pydantic data for key '{key}': missing {e}")
            except Exception as e:
                # If reconstruction fails, keep as dict but log error
                import sys
                print(f"Warning: Failed to reconstruct {key} as Pydantic: {e}", file=sys.stderr)
                result[key] = obj_data.get(cls.DATA_KEY, obj_data)

        # Add regular data
        other_data = loaded.get(cls.OTHER_KEY, {})
        result.update(other_data)

        return result

    @classmethod
    def _is_pydantic_model(cls, value: Any) -> bool:
        """
        Check if a value is a Pydantic model that's in MODEL_REGISTRY

        Args:
            value: Value to check

        Returns:
            True if value is a Pydantic model in MODEL_REGISTRY
        """
        return (hasattr(value, 'model_dump') and
                hasattr(value, '__class__') and
                type(value).__name__ in MODEL_REGISTRY)


def serialize_for_json(obj: Any) -> Any:
    """
    Recursively convert Pydantic objects to JSON-serializable dicts.

    Processes nested data structures (dict, list, tuple, set) and converts
    any Pydantic model instances to dictionaries using model_dump().
    Non-Pydantic data is preserved unchanged.

    Args:
        obj: Object to serialize. Can be any type including:
            - Pydantic models (converted to dict)
            - dict/list/tuple/set (recursively processed)
            - Primitives (returned as-is)

    Returns:
        JSON-serializable version of obj:
            - Pydantic models become dicts
            - Collections are recursively processed
            - Primitives pass through unchanged

    Raises:
        TypeError: If obj contains types that cannot be JSON-serialized
            (e.g., custom classes not in MODEL_REGISTRY)

    Examples:
        Convert single Pydantic object:
        >>> from Writer.Models import StoryElements
        >>> story = StoryElements(title="Test", genre="Fantasy", themes=["magic"])
        >>> result = serialize_for_json(story)
        >>> isinstance(result, dict)
        True

        Handle nested structures:
        >>> data = {"story": story, "count": 5}
        >>> result = serialize_for_json(data)
        >>> isinstance(result["story"], dict)
        True
        >>> result["count"]
        5

    Note:
        - Does NOT handle circular references (will hit recursion limit)
        - Sets are converted to lists (JSON limitation)
        - Tuples are preserved as tuples
        - Reuses StateManager._is_pydantic_model() for detection (DRY principle)
    """
    from datetime import datetime

    # Base case: None and primitives pass through unchanged
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj

    # Check if it's a Pydantic model (reuse existing detection logic)
    if StateManager._is_pydantic_model(obj):
        # Convert to dict and recursively process to handle nested Pydantic
        return serialize_for_json(obj.model_dump())

    # Handle dict: recursively process both keys and values
    if isinstance(obj, dict):
        return {key: serialize_for_json(value) for key, value in obj.items()}

    # Handle list: recursively process elements
    if isinstance(obj, list):
        return [serialize_for_json(item) for item in obj]

    # Handle tuple: recursively process and preserve tuple type
    if isinstance(obj, tuple):
        return tuple(serialize_for_json(item) for item in obj)

    # Handle set: convert to list (JSON doesn't support sets)
    if isinstance(obj, set):
        return [serialize_for_json(item) for item in obj]

    # Edge case: datetime objects (convert to ISO format string)
    if isinstance(obj, datetime):
        return obj.isoformat()

    # Fallback: return as-is and let json.dump() raise TypeError if needed
    # This provides clearer error messages than catching and re-raising
    return obj


__all__ = ['StateManager', 'serialize_for_json']
