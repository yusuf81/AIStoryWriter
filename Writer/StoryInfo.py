from pydantic import BaseModel  # Ditambahkan
import Writer.Config
# import Writer.Prompts  # Dihapus untuk pemuatan dinamis


# Definisikan Skema Pydantic
class StoryInfoSchema(BaseModel):
    Title: str
    Summary: str
    Tags: str
    OverallRating: int


def GetStoryInfo(
    Interface, _Logger, _Messages: list, _Model: str = None  # type: ignore[assignment]
):  # Tambahkan parameter _Model opsional
    import Writer.Prompts as ActivePrompts  # Ditambahkan untuk pemuatan dinamis

    Prompt: str = ActivePrompts.STATS_PROMPT

    # Tentukan model yang akan digunakan: parameter _Model jika ada, jika tidak fallback ke Config
    ModelToUse = _Model if _Model is not None else Writer.Config.INFO_MODEL

    _Logger.Log(
        f"Prompting LLM ({ModelToUse}) To Generate Stats", 5
    )  # Log model yang digunakan

    # FIX: Ensure proper role alternation for vLLM (OpenAI-compatible API)
    # Build messages in correct order: system -> user (combined content)
    Messages = []

    # Start with system message
    Messages.append(Interface.BuildSystemQuery(Interface._get_text('default_system_message')))

    # Combine existing user content with new prompt into a single user message
    existing_content = ""
    if _Messages and _Messages[0].get("role") == "user":
        existing_content = _Messages[0].get("content", "")

    combined_prompt = existing_content + "\n\n" + Prompt
    Messages.append(Interface.BuildUserQuery(combined_prompt))
    # Use SafeGeneratePydantic with existing StoryInfoSchema (already a Pydantic model)
    Messages, info_obj, TokenUsage = Interface.SafeGeneratePydantic(
        _Logger,
        Messages,
        ModelToUse,
        StoryInfoSchema
    )
    _Logger.Log("Finished Getting Stats Feedback", 5)
    # Convert Pydantic object to dict for backward compatibility
    return info_obj.model_dump(), TokenUsage
