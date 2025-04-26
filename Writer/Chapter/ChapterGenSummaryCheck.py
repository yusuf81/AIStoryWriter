from pydantic import BaseModel  # Ditambahkan
import json

import Writer.LLMEditor
import Writer.PrintUtils
import Writer.Config
import Writer.Prompts


# Definisikan Skema Pydantic
class SummaryComparisonSchema(BaseModel):
    Suggestions: str
    DidFollowOutline: bool


def LLMSummaryCheck(Interface, _Logger, _RefSummary: str, _Work: str):
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
        Interface.BuildSystemQuery(Writer.Prompts.SUMMARY_CHECK_INTRO)
    )
    SummaryLangchain.append(
        Interface.BuildUserQuery(
            Writer.Prompts.SUMMARY_CHECK_PROMPT.format(_Work=_Work)
        )
    )
    SummaryLangchain = Interface.SafeGenerateText(
        _Logger, SummaryLangchain, Writer.Config.CHAPTER_STAGE1_WRITER_MODEL
    )  # CHANGE THIS MODEL EVENTUALLY - BUT IT WORKS FOR NOW!!!
    WorkSummary: str = Interface.GetLastMessageText(SummaryLangchain)

    # Now Summarize The Outline
    SummaryLangchain: list = []
    SummaryLangchain.append(
        Interface.BuildSystemQuery(Writer.Prompts.SUMMARY_OUTLINE_INTRO)
    )
    SummaryLangchain.append(
        Interface.BuildUserQuery(
            Writer.Prompts.SUMMARY_OUTLINE_PROMPT.format(_RefSummary=_RefSummary)
        )
    )
    SummaryLangchain = Interface.SafeGenerateText(
        _Logger, SummaryLangchain, Writer.Config.CHAPTER_STAGE1_WRITER_MODEL
    )  # CHANGE THIS MODEL EVENTUALLY - BUT IT WORKS FOR NOW!!!
    OutlineSummary: str = Interface.GetLastMessageText(SummaryLangchain)

    # Now, generate a comparison JSON value.
    ComparisonLangchain: list = []
    ComparisonLangchain.append(
        Interface.BuildSystemQuery(Writer.Prompts.SUMMARY_COMPARE_INTRO)
    )
    ComparisonLangchain.append(
        Interface.BuildUserQuery(
            Writer.Prompts.SUMMARY_COMPARE_PROMPT.format(
                WorkSummary=WorkSummary, OutlineSummary=OutlineSummary
            )
        )
    )
    # Menggunakan SafeGenerateJSON dengan skema
    ComparisonLangchain, JSONResponse = Interface.SafeGenerateJSON(
        _Logger,
        ComparisonLangchain,
        Writer.Config.REVISION_MODEL,
        _FormatSchema=SummaryComparisonSchema.model_json_schema(),
    )
    return (
        JSONResponse["DidFollowOutline"],
        "### Extra Suggestions:\n" + JSONResponse["Suggestions"],
    )
