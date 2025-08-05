import Writer.Config
# import Writer.Prompts # Dihapus untuk pemuatan dinamis
import Writer.Statistics  # Add this import
import copy


def EditNovel(Interface, _Logger, _Chapters: list, _Outline: str, _TotalChapters: int):
    import Writer.Prompts as ActivePrompts  # Ditambahkan untuk pemuatan dinamis

    # Create deep copy to prevent contamination and preserve original for context
    EditedChapters = copy.deepcopy(_Chapters)
    OriginalChapters = copy.deepcopy(_Chapters)  # Keep original for context isolation

    for i in range(1, _TotalChapters + 1):

        current_chapter_index = i - 1

        # Build explicit chapter markup context to prevent confusion
        context_sections = []
        # Previous Chapter (if it exists) - use ORIGINAL to prevent contamination
        if i > 1:
            prev_chapter_text = OriginalChapters[current_chapter_index - 1]
            context_sections.append(f"<PREVIOUS_CHAPTER>\n{prev_chapter_text}\n</PREVIOUS_CHAPTER>")
        # Current Chapter (target for editing) - use ORIGINAL
        current_chapter_text = OriginalChapters[current_chapter_index]
        context_sections.append(f"<CHAPTER_TO_EDIT number=\"{i}\">\n{current_chapter_text}\n</CHAPTER_TO_EDIT>")
        # Next Chapter (if it exists) - use ORIGINAL
        if i < _TotalChapters:
            next_chapter_text = OriginalChapters[current_chapter_index + 1]
            context_sections.append(f"<NEXT_CHAPTER>\n{next_chapter_text}\n</NEXT_CHAPTER>")

        # Join with clear section breaks
        NovelText = "\n\n".join(context_sections)

        # Get original word count before editing
        OriginalWordCount = Writer.Statistics.GetWordCount(
            OriginalChapters[current_chapter_index]
        )

        Prompt: str = ActivePrompts.CHAPTER_EDIT_PROMPT.format(
            _Outline=_Outline, NovelText=NovelText, i=i
        )

        _Logger.Log(
            f"Prompting LLM To Perform Chapter {i}/{_TotalChapters} Second Pass In-Place Edit (Limited Context)",
            5,  # Tambahkan catatan konteks
        )
        Messages = []
        Messages.append(Interface.BuildUserQuery(Prompt))
        Messages, _ = Interface.SafeGenerateText(  # Unpack tuple, ignore token usage
            _Logger,
            Messages,
            Writer.Config.FINAL_NOVEL_EDITOR_MODEL,  # Gunakan nama variabel config baru
            _MinWordCount=Writer.Config.MIN_WORDS_EDIT_NOVEL,
        )
        _Logger.Log(f"Finished Chapter {i} Second Pass In-Place Edit", 5)

        NewChapter = Interface.GetLastMessageText(Messages)
        EditedChapters[current_chapter_index] = (
            NewChapter  # Pastikan menggunakan current_chapter_index
        )
        NewWordCount = Writer.Statistics.GetWordCount(NewChapter)
        _Logger.Log(
            f"Word Count Change (Edit): Chapter {i} {OriginalWordCount} -> {NewWordCount}",
            3,
        )

    return EditedChapters
