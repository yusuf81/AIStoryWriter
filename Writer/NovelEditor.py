import Writer.PrintUtils
import Writer.Config
# import Writer.Prompts # Dihapus untuk pemuatan dinamis
import Writer.Statistics  # Add this import


def EditNovel(Interface, _Logger, _Chapters: list, _Outline: str, _TotalChapters: int):
    import Writer.Prompts as ActivePrompts # Ditambahkan untuk pemuatan dinamis

    EditedChapters = _Chapters

    for i in range(1, _TotalChapters + 1):

        current_chapter_index = i - 1

        # Build the context snippet using only adjacent chapters
        context_parts = []
        # Previous Chapter (if it exists)
        if i > 1:
            prev_chapter_text = EditedChapters[current_chapter_index - 1]
            context_parts.append(prev_chapter_text)
        # Current Chapter (the one being edited, before this edit)
        current_chapter_text = EditedChapters[current_chapter_index]
        context_parts.append(current_chapter_text)
        # Next Chapter (if it exists)
        if i < _TotalChapters:
            next_chapter_text = EditedChapters[current_chapter_index + 1]
            context_parts.append(next_chapter_text)

        # Join the parts with a separator to form the limited context
        NovelText = "\n\n---\n\n".join(context_parts)

        # Get original word count before editing
        OriginalWordCount = Writer.Statistics.GetWordCount(
            EditedChapters[current_chapter_index]
        )  # Pastikan menggunakan current_chapter_index

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
