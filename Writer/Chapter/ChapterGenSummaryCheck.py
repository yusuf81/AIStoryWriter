from pydantic import BaseModel
import Writer.Config
# import Writer.Prompts # Dihapus untuk pemuatan dinamis

# Cache untuk outline summaries - untuk menghindari summary ulang outline yang sama
_outline_summary_cache = {}


# Definisikan Skema Pydantic
class SummaryComparisonSchema(BaseModel):
    Suggestions: str
    DidFollowOutline: bool


def LLMSummaryCheck(Interface, _Logger, _RefSummary: str, _Work: str):
    import Writer.Prompts as ActivePrompts  # Ditambahkan untuk pemuatan dinamis
    """
    Generates a summary of the work provided, and compares that to the reference summary, asking if they answered the prompt correctly.
    """

    # LLM Length Check - Firstly, check if the length of the response was at least 100 words.
    if len(_Work.split(" ")) < 100:
        _Logger.Log(
            "Previous response didn't meet the length requirement, so it probably tried to cheat around writing.",
            7,
        )
        return False, ""

    # Build Summariziation Langchain
    SummaryLangchain: list = []
    SummaryLangchain.append(
        Interface.BuildSystemQuery(ActivePrompts.SUMMARY_CHECK_INTRO)
    )
    SummaryLangchain.append(
        Interface.BuildUserQuery(
            ActivePrompts.SUMMARY_CHECK_PROMPT.format(_Work=_Work)
        )
    )
    # Tambahkan log sebelum memanggil SafeGenerateJSON pertama
    _Logger.Log(
        "Generating summary of generated work for comparison.", 6
    )  # Tambahkan log ini
    SummaryLangchain, summary_json, _ = (
        Interface.SafeGenerateJSON(
            _Logger, SummaryLangchain, Writer.Config.CHAPTER_STAGE1_WRITER_MODEL
        )
    )
    WorkSummary: str = summary_json.get('summary', '') or summary_json.get('text', '')
    _Logger.Log(
        "Finished generating summary of generated work.", 6
    )  # Tambahkan log ini

    # Check if we already have a cached summary for this outline
    outline_hash = hash(_RefSummary)
    if outline_hash in _outline_summary_cache:
        OutlineSummary = _outline_summary_cache[outline_hash]
        _Logger.Log(
            "Using cached summary of reference outline.", 6
        )
    else:
        # Now Summarize The Outline (first time only)
        SummaryLangchain: list = []
        SummaryLangchain.append(
            Interface.BuildSystemQuery(ActivePrompts.SUMMARY_OUTLINE_INTRO)
        )
        SummaryLangchain.append(
            Interface.BuildUserQuery(
                ActivePrompts.SUMMARY_OUTLINE_PROMPT.format(_RefSummary=_RefSummary)
            )
        )
        # Tambahkan log sebelum memanggil SafeGenerateJSON kedua
        _Logger.Log(
            "Generating summary of reference outline for comparison.", 6
        )  # Tambahkan log ini
        SummaryLangchain, summary_json, _ = (
            Interface.SafeGenerateJSON(
                _Logger, SummaryLangchain, Writer.Config.CHAPTER_STAGE1_WRITER_MODEL
            )
        )
        OutlineSummary: str = summary_json.get('summary', '') or summary_json.get('text', '')
        # Cache the summary for future use
        _outline_summary_cache[outline_hash] = OutlineSummary
        _Logger.Log(
            "Finished generating and cached summary of reference outline.", 6
        )  # Tambahkan log ini

    # Now, generate a comparison JSON value.
    ComparisonLangchain: list = []
    ComparisonLangchain.append(
        Interface.BuildSystemQuery(ActivePrompts.SUMMARY_COMPARE_INTRO)
    )
    ComparisonLangchain.append(
        Interface.BuildUserQuery(
            ActivePrompts.SUMMARY_COMPARE_PROMPT.format(
                WorkSummary=WorkSummary, OutlineSummary=OutlineSummary
            )
        )
    )
    # Tambahkan log sebelum memanggil SafeGenerateJSON
    _Logger.Log(
        "Comparing generated work summary vs reference outline summary.", 6
    )  # Tambahkan log ini
    # Use SafeGeneratePydantic with existing SummaryComparisonSchema (already a Pydantic model)
    _, comparison_obj, _ = Interface.SafeGeneratePydantic(
        _Logger,
        ComparisonLangchain,
        Writer.Config.REVISION_MODEL,
        SummaryComparisonSchema
    )
    _Logger.Log("Finished comparing summaries.", 6)
    # Access fields via Pydantic object attributes (structured access)
    suggestions_text = "### Extra Suggestions:\n" + comparison_obj.Suggestions

    return (
        comparison_obj.DidFollowOutline,
        suggestions_text,
    )
