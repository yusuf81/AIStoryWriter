import json

import Writer.LLMEditor
import Writer.PrintUtils
import Writer.Config
import Writer.Chapter.ChapterGenSummaryCheck
import Writer.Prompts
import Writer.Statistics # Add near other imports at the top

import Writer.Scene.ChapterByScene


def GenerateChapter(
    Interface,
    _Logger,
    _ChapterNum: int,
    _TotalChapters: int,
    _Outline: str,
    _Chapters: list = [],
    _QualityThreshold: int = 85,
    _BaseContext: str = "",
):

    # Some important notes
    # We're going to remind the author model of the previous chapters here, so it knows what has been written before.

    #### Stage 0: Create base language chain
    _Logger.Log(f"Creating Base Langchain For Chapter {_ChapterNum} Generation", 2)
    MesssageHistory: list = []
    MesssageHistory.append(
        Interface.BuildSystemQuery(Writer.Prompts.CHAPTER_GENERATION_INTRO)
    )

    ContextHistoryInsert: str = ""

    if len(_Chapters) > 0:

        # ChapterSuperlist tidak lagi dibuat atau digunakan untuk konteks
        # sebagai bagian dari Solusi 1 untuk masalah ukuran konteks.

        ContextHistoryInsert += Writer.Prompts.CHAPTER_HISTORY_INSERT.format(
            _Outline=_Outline # ChapterSuperlist dihapus dari format
        )

    # Now, extract the this-chapter-outline segment
    _Logger.Log(f"Extracting Chapter Specific Outline for Chapter {_ChapterNum}/{_TotalChapters}", 4)
    ThisChapterOutline: str = ""
    ChapterSegmentMessages = []
    ChapterSegmentMessages.append(
        Interface.BuildSystemQuery(Writer.Prompts.CHAPTER_GENERATION_INTRO)
    )
    ChapterSegmentMessages.append(
        Interface.BuildUserQuery(
            Writer.Prompts.CHAPTER_GENERATION_PROMPT.format(
                _Outline=_Outline, _ChapterNum=_ChapterNum
            )
        )
    )
    ChapterSegmentMessages = Interface.SafeGenerateText(
        _Logger,
        ChapterSegmentMessages,
        Writer.Config.CHAPTER_STAGE1_WRITER_MODEL,
        _MinWordCount=Writer.Config.MIN_WORDS_CHAPTER_SEGMENT_EXTRACT,  # Menggunakan Config
    )  # CHANGE THIS MODEL EVENTUALLY - BUT IT WORKS FOR NOW!!!
    ThisChapterOutline: str = Interface.GetLastMessageText(ChapterSegmentMessages)
    _Logger.Log(f"Created Chapter Specific Outline for Chapter {_ChapterNum}/{_TotalChapters}", 4)

    # Generate Summary of Last Chapter If Applicable
    FormattedLastChapterSummary: str = ""
    if len(_Chapters) > 0:
        _Logger.Log(f"Creating Summary Of Last Chapter Info for Chapter {_ChapterNum}/{_TotalChapters}", 3)
        ChapterSummaryMessages = []
        ChapterSummaryMessages.append(
            Interface.BuildSystemQuery(Writer.Prompts.CHAPTER_SUMMARY_INTRO)
        )
        ChapterSummaryMessages.append(
            Interface.BuildUserQuery(
                Writer.Prompts.CHAPTER_SUMMARY_PROMPT.format(
                    _ChapterNum=_ChapterNum,
                    _TotalChapters=_TotalChapters,
                    _Outline=_Outline,
                    _LastChapter=_Chapters[-1],
                )
            )
        )
        ChapterSummaryMessages = Interface.SafeGenerateText(
            _Logger,
            ChapterSummaryMessages,
            Writer.Config.CHAPTER_STAGE1_WRITER_MODEL,
            _MinWordCount=Writer.Config.MIN_WORDS_CHAPTER_SUMMARY,  # Menggunakan Config
        )  # CHANGE THIS MODEL EVENTUALLY - BUT IT WORKS FOR NOW!!!
        FormattedLastChapterSummary: str = Interface.GetLastMessageText(
            ChapterSummaryMessages
        )
        _Logger.Log(f"Created Summary Of Last Chapter Info", 3)

    DetailedChapterOutline: str = ThisChapterOutline
    if FormattedLastChapterSummary != "":
        DetailedChapterOutline = ThisChapterOutline

    _Logger.Log(f"Done with base langchain setup for Chapter {_ChapterNum}/{_TotalChapters}", 2)

    # If scene generation disabled, use the normal initial plot generator
    Stage1Chapter = ""
    if not Writer.Config.SCENE_GENERATION_PIPELINE:

        #### STAGE 1: Create Initial Plot
        IterCounter: int = 0
        Feedback: str = ""
        while True:
            Prompt = Writer.Prompts.CHAPTER_GENERATION_STAGE1.format(
                ContextHistoryInsert=ContextHistoryInsert,
                _ChapterNum=_ChapterNum,
                _TotalChapters=_TotalChapters,
                ThisChapterOutline=ThisChapterOutline,
                FormattedLastChapterSummary=FormattedLastChapterSummary,
                Feedback=Feedback,
                _BaseContext=_BaseContext,
            )

            # Generate Initial Chapter
            _Logger.Log(
                f"Generating Initial Chapter (Stage 1: Plot) {_ChapterNum}/{_TotalChapters} (Iteration {IterCounter}/{Writer.Config.CHAPTER_MAX_REVISIONS})",
                5,
            )
            Messages = MesssageHistory.copy()
            Messages.append(Interface.BuildUserQuery(Prompt))

            Messages = Interface.SafeGenerateText(
                _Logger,
                Messages,
                Writer.Config.CHAPTER_STAGE1_WRITER_MODEL,
                _SeedOverride=IterCounter + Writer.Config.SEED,
                _MinWordCount=Writer.Config.MIN_WORDS_CHAPTER_DRAFT,  # Menggunakan Config
            )
            IterCounter += 1
            Stage1Chapter: str = Interface.GetLastMessageText(Messages)
            _Logger.Log(
                f"Finished Initial Generation For Initial Chapter (Stage 1: Plot)  {_ChapterNum}/{_TotalChapters}",
                5,
            )

            # Check if LLM did the work
            if IterCounter > Writer.Config.CHAPTER_MAX_REVISIONS:
                _Logger.Log(
                    f"Chapter Summary-Based Revision Seems Stuck (Stage 1: Plot) - Forcefully Exiting after {IterCounter}/{Writer.Config.CHAPTER_MAX_REVISIONS} iterations.", 7
                )
                break
            Result, Feedback = Writer.Chapter.ChapterGenSummaryCheck.LLMSummaryCheck(
                Interface, _Logger, DetailedChapterOutline, Stage1Chapter
            )
            if Result:
                _Logger.Log(
                    f"Done Generating Initial Chapter (Stage 1: Plot) {_ChapterNum}/{_TotalChapters} after {IterCounter} iteration(s).",
                    5,
                )
                break

    else:

        Stage1Chapter = Writer.Scene.ChapterByScene.ChapterByScene(
            Interface, _Logger, _ChapterNum, _TotalChapters, ThisChapterOutline, _Outline, _BaseContext
        )

    #### STAGE 2: Add Character Development
    Stage2Chapter = ""
    IterCounter: int = 0
    Feedback: str = ""
    while True:
        Prompt = Writer.Prompts.CHAPTER_GENERATION_STAGE2.format(
            ContextHistoryInsert=ContextHistoryInsert,
            _ChapterNum=_ChapterNum,
            _TotalChapters=_TotalChapters,
            ThisChapterOutline=ThisChapterOutline,
            FormattedLastChapterSummary=FormattedLastChapterSummary,
            Stage1Chapter=Stage1Chapter,
            Feedback=Feedback,
            _BaseContext=_BaseContext,
        )

        # Generate Initial Chapter
        _Logger.Log(
            f"Generating Initial Chapter (Stage 2: Character Development) {_ChapterNum}/{_TotalChapters} (Iteration {IterCounter}/{Writer.Config.CHAPTER_MAX_REVISIONS})",
            5,
        )
        Messages = MesssageHistory.copy()
        Messages.append(Interface.BuildUserQuery(Prompt))

        Messages = Interface.SafeGenerateText(
            _Logger,
            Messages,
            Writer.Config.CHAPTER_STAGE2_WRITER_MODEL,
            _SeedOverride=IterCounter + Writer.Config.SEED,
            _MinWordCount=Writer.Config.MIN_WORDS_CHAPTER_DRAFT,  # Menggunakan Config
        )
        IterCounter += 1
        Stage2Chapter: str = Interface.GetLastMessageText(Messages)
        _Logger.Log(
            f"Finished Initial Generation For Initial Chapter (Stage 2: Character Development)  {_ChapterNum}/{_TotalChapters}",
            5,
        )

        # Check if LLM did the work
        if IterCounter > Writer.Config.CHAPTER_MAX_REVISIONS:
            _Logger.Log(
                f"Chapter Summary-Based Revision Seems Stuck (Stage 2: Character Dev) - Forcefully Exiting after {IterCounter}/{Writer.Config.CHAPTER_MAX_REVISIONS} iterations.", 7
            )
            break
        Result, Feedback = Writer.Chapter.ChapterGenSummaryCheck.LLMSummaryCheck(
            Interface, _Logger, DetailedChapterOutline, Stage2Chapter
        )
        if Result:
            _Logger.Log(
                f"Done Generating Initial Chapter (Stage 2: Character Development) {_ChapterNum}/{_TotalChapters} after {IterCounter} iteration(s).",
                5,
            )
            break

    #### STAGE 3: Add Dialogue
    Stage3Chapter = ""
    IterCounter: int = 0
    Feedback: str = ""
    while True:
        Prompt = Writer.Prompts.CHAPTER_GENERATION_STAGE3.format(
            ContextHistoryInsert=ContextHistoryInsert,
            _ChapterNum=_ChapterNum,
            _TotalChapters=_TotalChapters,
            ThisChapterOutline=ThisChapterOutline,
            FormattedLastChapterSummary=FormattedLastChapterSummary,
            Stage2Chapter=Stage2Chapter,
            Feedback=Feedback,
            _BaseContext=_BaseContext,
        )
        # Generate Initial Chapter
        _Logger.Log(
            f"Generating Initial Chapter (Stage 3: Dialogue) {_ChapterNum}/{_TotalChapters} (Iteration {IterCounter}/{Writer.Config.CHAPTER_MAX_REVISIONS})",
            5,
        )
        Messages = MesssageHistory.copy()
        Messages.append(Interface.BuildUserQuery(Prompt))

        Messages = Interface.SafeGenerateText(
            _Logger,
            Messages,
            Writer.Config.CHAPTER_STAGE3_WRITER_MODEL,
            _SeedOverride=IterCounter + Writer.Config.SEED,
            _MinWordCount=Writer.Config.MIN_WORDS_CHAPTER_DRAFT,  # Menggunakan Config
        )
        IterCounter += 1
        Stage3Chapter: str = Interface.GetLastMessageText(Messages)
        _Logger.Log(
            f"Finished Initial Generation For Initial Chapter (Stage 3: Dialogue)  {_ChapterNum}/{_TotalChapters}",
            5,
        )

        # Check if LLM did the work
        if IterCounter > Writer.Config.CHAPTER_MAX_REVISIONS:
            _Logger.Log(
                f"Chapter Summary-Based Revision Seems Stuck (Stage 3: Dialogue) - Forcefully Exiting after {IterCounter}/{Writer.Config.CHAPTER_MAX_REVISIONS} iterations.", 7
            )
            break
        Result, Feedback = Writer.Chapter.ChapterGenSummaryCheck.LLMSummaryCheck(
            Interface, _Logger, DetailedChapterOutline, Stage3Chapter
        )
        if Result:
            _Logger.Log(
                f"Done Generating Initial Chapter (Stage 3: Dialogue) {_ChapterNum}/{_TotalChapters} after {IterCounter} iteration(s).",
                5,
            )
            break

    Chapter: str = Stage3Chapter

    #### Stage 5: Revision Cycle
    if Writer.Config.CHAPTER_NO_REVISIONS:
        _Logger.Log(f"Chapter Revision Disabled In Config, Exiting Now", 5)
        return Chapter

    _Logger.Log(
        f"Entering Feedback/Revision Loop (Stage 5) For Chapter {_ChapterNum}/{_TotalChapters}",
        4,
    )
    WritingHistory = MesssageHistory.copy()
    Rating: int = 0 # Seharusnya boolean, tapi kode saat ini menggunakannya seperti itu
    Iterations: int = 0
    RevisionLoopExitReason = "Unknown" # Tambahkan variabel ini
    while True:
        Iterations += 1
        Feedback = Writer.LLMEditor.GetFeedbackOnChapter(
            Interface, _Logger, Chapter, _Outline
        )
        Rating = Writer.LLMEditor.GetChapterRating(Interface, _Logger, Chapter)

        if Iterations > Writer.Config.CHAPTER_MAX_REVISIONS:
            RevisionLoopExitReason = "Max Revisions Reached" # Set alasan
            break
        if (Iterations > Writer.Config.CHAPTER_MIN_REVISIONS) and (Rating == True):
            RevisionLoopExitReason = "Quality Standard Met" # Set alasan
            break
        # Teruskan _ChapterNum dan _TotalChapters ke ReviseChapter
        Chapter, WritingHistory = ReviseChapter(
            Interface, _Logger, _ChapterNum, _TotalChapters, Chapter, Feedback, WritingHistory, _Iteration=Iterations
        )

    _Logger.Log(
        f"{RevisionLoopExitReason}, Exiting Feedback/Revision Loop (Stage 5) For Chapter {_ChapterNum}/{_TotalChapters} after {Iterations}/{Writer.Config.CHAPTER_MAX_REVISIONS} iteration(s). Final Rating: {Rating}",
        4,
    )

    return Chapter


def ReviseChapter(Interface, _Logger, _ChapterNum: int, _TotalChapters: int, _Chapter, _Feedback, _History: list = [], _Iteration: int = 0): # Tambahkan _ChapterNum, _TotalChapters

    # Get original word count before revising
    OriginalWordCount = Writer.Statistics.GetWordCount(_Chapter)

    RevisionPrompt = Writer.Prompts.CHAPTER_REVISION.format(
        _Chapter=_Chapter, _Feedback=_Feedback
    )

    # Gunakan _ChapterNum dan _TotalChapters yang diteruskan sebagai parameter
    _Logger.Log(f"Revising Chapter {_ChapterNum}/{_TotalChapters} (Stage 5, Iteration {_Iteration}/{Writer.Config.CHAPTER_MAX_REVISIONS})", 5)
    Messages = _History
    Messages.append(Interface.BuildUserQuery(RevisionPrompt))
    Messages = Interface.SafeGenerateText(
        _Logger,
        Messages,
        Writer.Config.CHAPTER_REVISION_WRITER_MODEL,
        _MinWordCount=Writer.Config.MIN_WORDS_REVISE_CHAPTER,  # Menggunakan Config
    )
    SummaryText: str = Interface.GetLastMessageText(Messages)
    NewWordCount = Writer.Statistics.GetWordCount(SummaryText)
    # Gunakan _ChapterNum dan _TotalChapters yang diteruskan sebagai parameter
    _Logger.Log(f"Done Revising Chapter {_ChapterNum}/{_TotalChapters} (Stage 5, Iteration {_Iteration}/{Writer.Config.CHAPTER_MAX_REVISIONS}). Word Count Change: {OriginalWordCount} -> {NewWordCount}", 5)

    return SummaryText, Messages
