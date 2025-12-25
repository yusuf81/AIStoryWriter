import Writer.Config
# import Writer.Prompts # Dihapus untuk pemuatan dinamis
import Writer.Statistics  # Add this import
import copy
import re
from Writer.Models import ChapterOutput
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


def validate_chapter_editing(original_chapter, edited_chapter, logger):
    """
    Validate chapter editing using 2-layer approach:
    Layer 1: TF-IDF Content Similarity
    Layer 2: Length Change Detection
    """

    if not SKLEARN_AVAILABLE:
        logger.Log("SKLEARN not available, skipping TF-IDF validation", 4)
        # Fallback to simple length check
        char_ratio = len(edited_chapter) / len(original_chapter) if original_chapter else 0
        word_ratio = len(edited_chapter.split()) / len(original_chapter.split()) if original_chapter.split() else 0

        is_valid = char_ratio >= 0.7 and word_ratio >= 0.7
        return is_valid, {
            'is_valid': is_valid,
            'content_similarity': 'N/A (SKLEARN unavailable)',
            'key_preservation': 'N/A (SKLEARN unavailable)',
            'char_ratio': char_ratio,
            'word_ratio': word_ratio,
            'validation_method': 'fallback_length_only'
        }

    try:
        # Preprocessing function
        def preprocess(text):
            words = re.findall(r'\b\w+\b', text.lower())
            # Indonesian stop words
            stop_words = {'dan', 'atau', 'yang', 'ini', 'itu', 'adalah', 'dengan', 'pada', 'untuk', 'dari', 'ke', 'di', 'ia', 'dia', 'mereka', 'tidak', 'akan', 'sudah', 'juga', 'ada'}
            return ' '.join([w for w in words if w not in stop_words and len(w) > 2])

        # Preprocess both texts
        original_processed = preprocess(original_chapter)
        edited_processed = preprocess(edited_chapter)

        if not original_processed or not edited_processed:
            logger.Log("Warning: Empty processed text, using fallback validation", 4)
            char_ratio = len(edited_chapter) / len(original_chapter) if original_chapter else 0
            return char_ratio >= 0.7, {'validation_method': 'empty_text_fallback'}

        texts = [original_processed, edited_processed]

        # Layer 1: TF-IDF Analysis
        vectorizer = TfidfVectorizer(
            ngram_range=(1, 3),  # Capture single words and phrases
            min_df=1,            # Include all terms
            max_features=5000    # Limit vocabulary size
        )

        tfidf_matrix = vectorizer.fit_transform(texts)

        # Calculate overall similarity
        content_similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]

        # Get feature names and scores for key preservation analysis
        feature_names = vectorizer.get_feature_names_out()
        original_scores = tfidf_matrix[0].toarray()[0]  # type: ignore
        edited_scores = tfidf_matrix[1].toarray()[0]    # type: ignore

        # Get top important terms from original (top 20)
        top_indices = np.argsort(original_scores)[-20:]
        original_key_elements = [feature_names[i] for i in top_indices if original_scores[i] > 0]
        preserved_elements = [feature_names[i] for i in top_indices if edited_scores[i] > 0]

        key_preservation = len(preserved_elements) / len(original_key_elements) if original_key_elements else 0

        # Layer 2: Length Change Detection
        char_ratio = len(edited_chapter) / len(original_chapter) if original_chapter else 0
        word_ratio = len(edited_chapter.split()) / len(original_chapter.split()) if original_chapter.split() else 0

        # Decision Logic
        is_valid = (
            content_similarity >= 0.6 and      # 60% content similarity threshold
            key_preservation >= 0.5 and        # 50% key elements preserved
            char_ratio >= 0.7 and             # Max 30% character reduction
            word_ratio >= 0.7                  # Max 30% word reduction
        )

        validation_report = {
            'is_valid': is_valid,
            'content_similarity': content_similarity,
            'key_preservation': key_preservation,
            'char_ratio': char_ratio,
            'word_ratio': word_ratio,
            'original_key_elements': original_key_elements[:10],  # Top 10 for logging
            'preserved_elements': preserved_elements[:10],
            'validation_method': 'tfidf_plus_length',
            'failure_reasons': []
        }

        # Detailed failure analysis
        if not is_valid:
            if content_similarity < 0.6:
                validation_report['failure_reasons'].append(f'Low content similarity: {content_similarity:.2%}')
            if key_preservation < 0.5:
                validation_report['failure_reasons'].append(f'Key elements lost: {key_preservation:.2%}')
            if char_ratio < 0.7:
                validation_report['failure_reasons'].append(f'Content too short (chars): {char_ratio:.2%}')
            if word_ratio < 0.7:
                validation_report['failure_reasons'].append(f'Content too short (words): {word_ratio:.2%}')

        return is_valid, validation_report

    except Exception as e:
        logger.Log(f"Error in TF-IDF validation: {e}, using fallback", 3)
        # Fallback to simple length check
        char_ratio = len(edited_chapter) / len(original_chapter) if original_chapter else 0
        word_ratio = len(edited_chapter.split()) / len(original_chapter.split()) if original_chapter.split() else 0

        is_valid = char_ratio >= 0.7 and word_ratio >= 0.7
        return is_valid, {
            'is_valid': is_valid,
            'validation_method': 'error_fallback',
            'char_ratio': char_ratio,
            'word_ratio': word_ratio,
            'error': str(e)
        }


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
            5,
        )
        Messages = []
        Messages.append(Interface.BuildUserQuery(Prompt))
        Messages, Chapter_obj, _ = Interface.SafeGeneratePydantic(  # Use Pydantic model
            _Logger,
            Messages,
            Writer.Config.FINAL_NOVEL_EDITOR_MODEL,
            ChapterOutput
        )
        _Logger.Log(f"Finished Chapter {i} Second Pass In-Place Edit", 5)

        # Extract text from validated ChapterOutput model
        NewChapter = Chapter_obj.text

        # Validate the editing result
        original_chapter = OriginalChapters[current_chapter_index]
        is_valid, validation_report = validate_chapter_editing(original_chapter, NewChapter, _Logger)

        if is_valid:
            # Validation passed - use edited chapter
            EditedChapters[current_chapter_index] = NewChapter
            NewWordCount = Writer.Statistics.GetWordCount(NewChapter)
            _Logger.Log(f"Chapter {i} editing validation PASSED", 4)
            _Logger.Log(f"Validation details: Similarity={validation_report.get('content_similarity', 'N/A')}, Key preservation={validation_report.get('key_preservation', 'N/A')}", 5)
        else:
            # Validation failed - revert to original
            EditedChapters[current_chapter_index] = original_chapter  # Keep original
            NewWordCount = OriginalWordCount
            _Logger.Log(f"Chapter {i} editing validation FAILED - reverted to original", 2)
            _Logger.Log(f"Validation failures: {', '.join(validation_report.get('failure_reasons', ['Unknown']))}", 3)
            if validation_report.get('original_key_elements'):
                _Logger.Log(f"Original key elements: {validation_report['original_key_elements']}", 5)
            if validation_report.get('preserved_elements'):
                _Logger.Log(f"Preserved key elements: {validation_report['preserved_elements']}", 5)

        _Logger.Log(
            f"Word Count Change (Edit): Chapter {i} {OriginalWordCount} -> {NewWordCount}",
            3,
        )

    return EditedChapters
