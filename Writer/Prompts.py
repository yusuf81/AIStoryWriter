DEFAULT_SYSTEM_PROMPT = """You are a helpful assistant."""

GET_IMPORTANT_BASE_PROMPT_INFO = """
Please extract any important information from the user's prompt below:

<USER_PROMPT>
{_Prompt}
</USER_PROMPT>

Just write down any information that wouldn't be covered in an outline.
Please use the below template for formatting your response.
This would be things like instructions for chapter length, overall vision, instructions for formatting, etc.
(Don't use the xml tags though - those are for example only)

<EXAMPLE>
# Important Additional Context
- Important point 1
- Important point 2
</EXAMPLE>

Do NOT write the outline itself, just some extra context. Keep your responses short.

"""

GENERATE_STORY_ELEMENTS = """
I'm working on writing a fictional story, and I'd like your help writing out the story elements.

Here's the prompt for my story.
<PROMPT>
{_OutlinePrompt}
</PROMPT>

Please make your response have the following format:

<RESPONSE_TEMPLATE>
# Story Title

## Genre
- **Category**: (e.g., romance, mystery, science fiction, fantasy, horror)

## Theme
- **Central Idea or Message**:

## Pacing
- **Speed**: (e.g., slow, fast)

## Style
- **Language Use**: (e.g., sentence structure, vocabulary, tone, figurative language)

## Plot
- **Exposition**:
- **Rising Action**:
- **Climax**:
- **Falling Action**:
- **Resolution**:

## Setting
### Setting 1
- **Time**: (e.g., present day, future, past)
- **Location**: (e.g., city, countryside, another planet)
- **Culture**: (e.g., modern, medieval, alien)
- **Mood**: (e.g., gloomy, high-tech, dystopian)

(Repeat the above structure for additional settings)

## Conflict
- **Type**: (e.g., internal, external)
- **Description**:

## Symbolism
### Symbol 1
- **Symbol**:
- **Meaning**:

(Repeat the above structure for additional symbols)

## Characters
### Main Character(s)
#### Main Character 1
- **Name**:
- **Physical Description**:
- **Personality**:
- **Background**:
- **Motivation**:

(Repeat the above structure for additional main characters)


### Supporting Characters
#### Character 1
- **Name**:
- **Physical Description**:
- **Personality**:
- **Background**:
- **Role in the story**:

#### Character 2
- **Name**:
- **Physical Description**:
- **Personality**:
- **Background**:
- **Role in the story**:

#### Character 3
- **Name**:
- **Physical Description**:
- **Personality**:
- **Background**:
- **Role in the story**:

#### Character 4
- **Name**:
- **Physical Description**:
- **Personality**:
- **Background**:
- **Role in the story**:

#### Character 5
- **Name**:
- **Physical Description**:
- **Personality**:
- **Background**:
- **Role in the story**:

#### Character 6
- **Name**:
- **Physical Description**:
- **Personality**:
- **Background**:
- **Role in the story**:

#### Character 7
- **Name**:
- **Physical Description**:
- **Personality**:
- **Background**:
- **Role in the story**:

#### Character 8
- **Name**:
- **Physical Description**:
- **Personality**:
- **Background**:
- **Role in the story**:

(Repeat the above structure for additional supporting character)

</RESPONSE_TEMPLATE>

Of course, don't include the XML tags - those are just to indicate the example.
Also, the items in parenthesis are just to give you a better idea of what to write about, and should also be omitted from your response.
"""

INITIAL_OUTLINE_PROMPT = """
Please write a markdown formatted outline based on the following prompt:

<PROMPT>
{_OutlinePrompt}
</PROMPT>

<ELEMENTS>
{StoryElements}
</ELEMENTS>

As you write, remember to ask yourself the following questions:
    - What is the conflict?
    - Who are the characters (at least two characters)?
    - What do the characters mean to each other?
    - Where are we located?
    - What are the stakes (is it high, is it low, what is at stake here)?
    - What is the goal or solution to the conflict?

Don't answer these questions directly, instead make your outline implicitly answer them. (Show, don't tell)

Please keep your outline clear as to what content is in what chapter.
Make sure to add lots of detail as you write.

Also, include information about the different characters, and how they change over the course of the story.
We want to have rich and complex character development!"""

EXPAND_OUTLINE_CHAPTER_BY_CHAPTER = """
# Objective
Review the complete story outline provided below. Your task is to refine and structure it clearly on a chapter-by-chapter basis, ensuring each chapter's core purpose is evident before we proceed to detailed scene breakdowns.

# Input Outline
<OUTLINE>
{_Outline}
</OUTLINE>

# Tasks
1.  **Verify Chapter Structure:** Ensure the outline is clearly divided into distinct chapters. If any sections seem ambiguous or span multiple chapters, restructure them logically.
2.  **Identify Chapter Purpose:** For each chapter, add a brief (1-sentence) comment or heading indicating its main narrative function (e.g., "Introduces Conflict", "Character Development Focus", "Rising Action", "Climax Setup", "Subplot Resolution").
3.  **Ensure Sufficient Detail (High-Level):** Check if each chapter description provides enough high-level detail about the key events or character progression within that chapter. If a chapter description is too vague, add 1-2 sentences of clarifying detail (do NOT break it down into scenes yet).

# Output Format
Produce the refined, chapter-structured outline in Markdown format. Use clear headings for each chapter (e.g., `## Chapter 1: Introduction and Inciting Incident`).

# Example Snippet of Output:
```markdown
## Chapter 1: Introduction and Inciting Incident
- Introduce protagonist Alice in her mundane life.
- Establish the initial setting: futuristic Neo-Veridia.
- Detail the discovery of the mysterious artifact (inciting incident).
- Hint at the initial stakes and Alice's reluctance.

## Chapter 2: Rising Action and First Obstacle
- *Purpose: Develop the initial conflict and introduce the antagonist's influence.*
- Alice seeks information about the artifact, encountering minor obstacles.
- First encounter (indirect) with the antagonist's agents.
- Alice decides to protect the artifact, overcoming initial fear.
- Ends with Alice planning her next move.

... (continue for all chapters)
```

# Instructions
- Focus on clear chapter separation and high-level purpose/events.
- Do **not** break chapters down into individual scenes in this step.
- Maintain the core plot points from the original outline.
- Your entire response should be the refined, chapter-structured outline.
"""

CRITIC_OUTLINE_INTRO = "You are a helpful AI Assistant. Answer the user's prompts to the best of your abilities."

CRITIC_OUTLINE_PROMPT = """
Please critique the following outline - make sure to provide constructive criticism on how it can be improved and point out any problems with it.

<OUTLINE>
{_Outline}
</OUTLINE>

As you revise, consider the following criteria:
    - Pacing: Is the story rushing over certain plot points and excessively focusing on others?
    - Details: How are things described? Is it repetitive? Is the word choice appropriate for the scene? Are we describing things too much or too little?
    - Flow: Does each chapter flow into the next? Does the plot make logical sense to the reader? Does it have a specific narrative structure at play? Is the narrative structure consistent throughout the story?
    - Genre: What is the genre? What language is appropriate for that genre? Do the scenes support the genre?

Also, please check if the outline is written chapter-by-chapter, not in sections spanning multiple chapters or subsections.
It should be very clear which chapter is which, and the content in each chapter."""

OUTLINE_REVISION_PROMPT = """
Please revise the following outline:
<OUTLINE>
{_Outline}
</OUTLINE>

Based on the following feedback:
<FEEDBACK>
{_Feedback}
</FEEDBACK>

Remember to expand upon your outline and add content to make it as best as it can be!


As you write, keep the following in mind:
    - What is the conflict?
    - Who are the characters (at least two characters)?
    - What do the characters mean to each other?
    - Where are we located?
    - What are the stakes (is it high, is it low, what is at stake here)?
    - What is the goal or solution to the conflict?


Please keep your outline clear as to what content is in what chapter.
Make sure to add lots of detail as you write.

Don't answer these questions directly, instead make your writing implicitly answer them. (Show, don't tell)
"""

OUTLINE_COMPLETE_INTRO = "You are a helpful AI Assistant. Answer the user's prompts to the best of your abilities."

OUTLINE_COMPLETE_PROMPT = """
<OUTLINE>
{_Outline}
</OUTLINE>

This outline meets all of the following criteria (true or false):
    - Pacing: Is the story rushing over certain plot points and excessively focusing on others?
    - Details: How are things described? Is it repetitive? Is the word choice appropriate for the scene? Are we describing things too much or too little?
    - Flow: Does each chapter flow into the next? Does the plot make logical sense to the reader? Does it have a specific narrative structure at play? Is the narrative structure consistent throughout the story?
    - Genre: What is the genre? What language is appropriate for that genre? Do the scenes support the genre?

Give a JSON formatted response with the following structure:
{{"IsComplete": true/false}}

Please do not include any other text, just the JSON object as your response will be parsed by a computer. Your entire response must be only the JSON object.
"""

CHAPTER_COUNT_PROMPT = """
<OUTLINE>
{_Summary}
</OUTLINE>

Please provide a JSON formatted response containing the total number of chapters in the above outline.

Respond with the following JSON object format:
{{"TotalChapters": <total chapter count>}}

Please do not include any other text, just the JSON object as your response will be parsed by a computer. Your entire response must be only the JSON object.
"""

CHAPTER_GENERATION_PROMPT = """
Please help me extract the part of this outline that is just for chapter {_ChapterNum}.

<OUTLINE>
{_Outline}
</OUTLINE>

Do not include anything else in your response except just the content for chapter {_ChapterNum}.
"""

CHAPTER_HISTORY_INSERT = """
Please help me write my novel.

I'm basing my work on this outline:

<OUTLINE>
{_Outline}
</OUTLINE>

"""

CHAPTER_SUMMARY_INTRO = "You are a helpful AI Assistant. Answer the user's prompts to the best of your abilities."

CHAPTER_SUMMARY_PROMPT = """
I'm writing the next chapter in my novel (chapter {_ChapterNum}), and I have the following written so far.

My outline:
<OUTLINE>
{_Outline}
</OUTLINE>

And what I've written in the last chapter:
<PREVIOUS_CHAPTER>
{_LastChapter}
</PREVIOUS_CHAPTER>

Please create a list of important summary points from the last chapter so that I know what to keep in mind as I write this chapter.
Also make sure to add a summary of the previous chapter, and focus on noting down any important plot points, and the state of the story as the chapter ends.
That way, when I'm writing, I'll know where to pick up again.

Here's some formatting guidelines:

```
Previous Chapter:
    - Plot:
        - Your bullet point summary here with as much detail as needed
    - Setting:
        - some stuff here
    - Characters:
        - character 1
            - info about them, from that chapter
            - if they changed, how so

Things to keep in Mind:
    - something that the previous chapter did to advance the plot, so we incorporate it into the next chapter
    - something else that is important to remember when writing the next chapter
    - another thing
    - etc.
```

Thank you for helping me write my story! Please only include your summary and things to keep in mind, don't write anything else.
"""

CHAPTER_GENERATION_INTRO = "You are a helpful AI Assistant. Answer the user's prompts to the best of your abilities."

CHAPTER_GENERATION_STAGE1 = """
{ContextHistoryInsert}

{_BaseContext}

Please write the plot for chapter {_ChapterNum} of {_TotalChapters} based on the following chapter outline and any previous chapters.
Pay attention to the previous chapters, and make sure you both continue seamlessly from them, It's imperative that your writing connects well with the previous chapter, and flows into the next (so try to follow the outline)!

Here is my outline for this chapter:
<CHAPTER_OUTLINE>
{ThisChapterOutline}
</CHAPTER_OUTLINE>

{FormattedLastChapterSummary}

As you write your work, please use the following suggestions to help you write chapter {_ChapterNum} (make sure you only write this one):
    - Pacing: 
    - Are you skipping days at a time? Summarizing events? Don't do that, add scenes to detail them.
    - Is the story rushing over certain plot points and excessively focusing on others?
    - Flow: Does each chapter flow into the next? Does the plot make logical sense to the reader? Does it have a specific narrative structure at play? Is the narrative structure consistent throughout the story?
    - Genre: What is the genre? What language is appropriate for that genre? Do the scenes support the genre?

{Feedback}"""

CHAPTER_GENERATION_STAGE2 = """
{ContextHistoryInsert}

{_BaseContext}

Please write character development for the following chapter {_ChapterNum} of {_TotalChapters} based on the following criteria and any previous chapters.
Pay attention to the previous chapters, and make sure you both continue seamlessly from them, It's imperative that your writing connects well with the previous chapter, and flows into the next (so try to follow the outline)!

Don't take away content, instead expand upon it to make a longer and more detailed output.

For your reference, here is my outline for this chapter:
<CHAPTER_OUTLINE>
{ThisChapterOutline}
</CHAPTER_OUTLINE>

{FormattedLastChapterSummary}

And here is what I have for the current chapter's plot:
<CHAPTER_PLOT>
{Stage1Chapter}
</CHAPTER_PLOT>

As a reminder to keep the following criteria in mind as you expand upon the above work:
    - Characters: Who are the characters in this chapter? What do they mean to each other? What is the situation between them? Is it a conflict? Is there tension? Is there a reason that the characters have been brought together?
    - Development: What are the goals of each character, and do they meet those goals? Do the characters change and exhibit growth? Do the goals of each character change over the story?
    - Details: How are things described? Is it repetitive? Is the word choice appropriate for the scene? Are we describing things too much or too little?

Don't answer these questions directly, instead make your writing implicitly answer them. (Show, don't tell)

Make sure that your chapter flows into the next and from the previous (if applicable).

Remember, have fun, be creative, and improve the character development of chapter {_ChapterNum} (make sure you only write this one)!

{Feedback}"""

CHAPTER_GENERATION_STAGE3 = """
{ContextHistoryInsert}

{_BaseContext}

Please add dialogue the following chapter {_ChapterNum} of {_TotalChapters} based on the following criteria and any previous chapters.
Pay attention to the previous chapters, and make sure you both continue seamlessly from them, It's imperative that your writing connects well with the previous chapter, and flows into the next (so try to follow the outline)!

Don't take away content, instead expand upon it to make a longer and more detailed output.


{FormattedLastChapterSummary}

Here's what I have so far for this chapter:
<CHAPTER_CONTENT>
{Stage2Chapter}
</CHAPTER_CONTENT>

As a reminder to keep the following criteria in mind:
    - Dialogue: Does the dialogue make sense? Is it appropriate given the situation? Does the pacing make sense for the scene E.g: (Is it fast-paced because they're running, or slow-paced because they're having a romantic dinner)? 
    - Disruptions: If the flow of dialogue is disrupted, what is the reason for that disruption? Is it a sense of urgency? What is causing the disruption? How does it affect the dialogue moving forwards? 
     - Pacing: 
       - Are you skipping days at a time? Summarizing events? Don't do that, add scenes to detail them.
       - Is the story rushing over certain plot points and excessively focusing on others?
    
Don't answer these questions directly, instead make your writing implicitly answer them. (Show, don't tell)

Make sure that your chapter flows into the next and from the previous (if applicable).

Also, please remove any headings from the outline that may still be present in the chapter.

Remember, have fun, be creative, and add dialogue to chapter {_ChapterNum} (make sure you only write this one)!

{Feedback}"""

CHAPTER_OUTLINE_PROMPT = """
Please generate an outline for chapter {_Chapter} based on the provided outline.

<OUTLINE>
{_Outline}
</OUTLINE>

As you write, keep the following in mind:
    - What is the conflict?
    - Who are the characters (at least two characters)?
    - What do the characters mean to each other?
    - Where are we located?
    - What are the stakes (is it high, is it low, what is at stake here)?
    - What is the goal or solution to the conflict?

Remember to follow the provided outline when creating your chapter outline.

Don't answer these questions directly, instead make your outline implicitly answer them. (Show, don't tell)

Please break your response into scenes, which each have the following format (please repeat the scene format for each scene in the chapter (min of 3):

# Chapter {_Chapter}

## Scene: [Brief Scene Title]

- **Characters & Setting:**
  - Character: [Character Name] - [Brief Description]
  - Location: [Scene Location]
  - Time: [When the scene takes place]

- **Conflict & Tone:**
  - Conflict: [Type & Description]
  - Tone: [Emotional tone]

- **Key Events & Dialogue:**
  - [Briefly describe important events, actions, or dialogue]

- **Literary Devices:**
  - [Foreshadowing, symbolism, or other devices, if any]

- **Resolution & Lead-in:**
  - [How the scene ends and connects to the next one]

Again, don't write the chapter itself, just create a detailed outline of the chapter.  

Make sure your chapter has a markdown-formatted name!
"""

CHAPTER_TO_SCENES = """
# CONTEXT #
I am writing a story and need your help with dividing chapters into scenes. Below is my outline so far:
```
{_Outline}
```
###############

# OBJECTIVE #
Create a scene-by-scene outline for the chapter that helps me write better scenes.
Make sure to include information about each scene that describes what happens, in what tone it's written, who the characters in the scene are, and what the setting is.
Here's the specific chapter outline that we need to split up into scenes:
```
{_ThisChapter}
```
###############

# STYLE #
Provide a creative response that helps add depth and plot to the story, but still follows the outline.
Make your response markdown-formatted so that the details and information about the scene are clear.

Above all, make sure to be creative and original when writing.
###############

# AUDIENCE #
Please tailor your response to another creative writer.
###############

# RESPONSE #
Be detailed and well-formatted in your response, yet ensure you have a well-thought out and creative output.
###############
"""

SCENES_TO_JSON = """
# CONTEXT #
I need to convert the following scene-by-scene outline into a JSON formatted list.
```
{_Scenes}
```
###############

# OBJECTIVE #
Create a JSON list of each of scene from the provided outline where each element in the list contains the content for that scene.
Ex:
{{
    "scenes": [
        "scene 1 content...",
        "scene 2 content...",
        "etc."
    ]
}}

+ Respond with a valid JSON object containing a single key named "scenes". The value associated with this key must be a JSON array (list) of strings, where each string is the content of a scene.
+ Do not include any text, comments, or markdown formatting outside of the JSON object itself. Your entire response must be only the JSON object.
###############

# STYLE #
Respond in pure JSON.
###############

# AUDIENCE #
Please tailor your response such that it is purely JSON formatted.
###############

# RESPONSE #
Don't lose any information from the original outline, just format it to fit in a list.
+ Ensure the output is a single, valid JSON object as described in the objective.
###############
"""

SCENE_OUTLINE_TO_SCENE = """
# CONTEXT #
I need your assistance writing the full scene based on the following scene outline.
```
{_SceneOutline}
```

For context, here is the full outline of the story.
```
{_Outline}
```
###############

# OBJECTIVE #
Create a full scene based on the given scene outline, that is written in the appropriate tone for the scene.
Make sure to include dialogue and other writing elements as needed.
###############

# STYLE #
Make your style be creative and appropriate for the given scene. The scene outline should indicate the right style, but if not use your own judgement.
###############

# AUDIENCE #
Please tailor your response to be written for the general public's entertainment as a creative writing piece.
###############

# RESPONSE #
Make sure your response is well thought out and creative. Take a moment to make sure it follows the provided scene outline, and ensure that it also fits into the main story outline.
###############
"""

SUMMARY_CHECK_INTRO = "You are a helpful AI Assistant. Answer the user's prompts to the best of your abilities."

SUMMARY_CHECK_PROMPT = """
Please summarize the following chapter:

<CHAPTER>
{_Work}
</CHAPTER>

Do not include anything in your response except the summary."""

SUMMARY_OUTLINE_INTRO = "You are a helpful AI Assistant. Answer the user's prompts to the best of your abilities."

SUMMARY_OUTLINE_PROMPT = """
Please summarize the following chapter outline:

<OUTLINE>
{_RefSummary}
</OUTLINE>

Do not include anything in your response except the summary."""

SUMMARY_COMPARE_INTRO = "You are a helpful AI Assistant. Answer the user's prompts to the best of your abilities."

SUMMARY_COMPARE_PROMPT = """
Please compare the provided summary of a chapter and the associated outline, and indicate if the provided content roughly follows the outline.

Please write a JSON formatted response with no other content with the following keys.
Note that a computer is parsing this JSON so it must be correct.

<CHAPTER_SUMMARY>
{WorkSummary}
</CHAPTER_SUMMARY>

<OUTLINE>
{OutlineSummary}
</OUTLINE>
Please respond with the following JSON fields:

{{
    "Suggestions": str,
    "DidFollowOutline": true/false
}}

Suggestions should include a string containing detailed markdown formatted feedback that will be used to prompt the writer on the next iteration of generation.
Specify general things that would help the writer remember what to do in the next iteration.
It will not see the current chapter, so feedback specific to this one is not helpful, instead specify areas where it needs to pay attention to either the prompt or outline.
The writer is also not aware of each iteration - so provide detailed information in the prompt that will help guide it.
Start your suggestions with 'Important things to keep in mind as you write: \n'.

It's okay if the summary isn't a complete perfect match, but it should have roughly the same plot, and pacing.

Again, remember to make your response *only* the JSON object with no extra words or formatting. It will be fed directly to a JSON parser.
"""

CRITIC_CHAPTER_INTRO = "You are a helpful AI Assistant. Answer the user's prompts to the best of your abilities."

CRITIC_CHAPTER_PROMPT = """<CHAPTER>
{_Chapter}
</CHAPTER>

Please give feedback on the above chapter based on the following criteria:
    - Pacing: Is the story rushing over certain plot points and excessively focusing on others?
    - Details: How are things described? Is it repetitive? Is the word choice appropriate for the scene? Are we describing things too much or too little?
    - Flow: Does each chapter flow into the next? Does the plot make logical sense to the reader? Does it have a specific narrative structure at play? Is the narrative structure consistent throughout the story?
    - Genre: What is the genre? What language is appropriate for that genre? Do the scenes support the genre?
    
    - Characters: Who are the characters in this chapter? What do they mean to each other? What is the situation between them? Is it a conflict? Is there tension? Is there a reason that the characters have been brought together?
    - Development:  What are the goals of each character, and do they meet those goals? Do the characters change and exhibit growth? Do the goals of each character change over the story?
    
    - Dialogue: Does the dialogue make sense? Is it appropriate given the situation? Does the pacing make sense for the scene E.g: (Is it fast-paced because they're running, or slow-paced because they're having a romantic dinner)? 
    - Disruptions: If the flow of dialogue is disrupted, what is the reason for that disruption? Is it a sense of urgency? What is causing the disruption? How does it affect the dialogue moving forwards? 
"""

CHAPTER_REVISION = """
Please revise the following chapter:

<CHAPTER_CONTENT>
{_Chapter}
</CHAPTER_CONTENT>

Based on the following feedback:
<FEEDBACK>
{_Feedback}
</FEEDBACK>
Do not reflect on the revisions, just write the improved chapter that addresses the feedback and prompt criteria.  
Remember not to include any author notes."""

CHAPTER_COMPLETE_INTRO = "You are a helpful AI Assistant. Answer the user's prompts to the best of your abilities."

CHAPTER_COMPLETE_PROMPT = """

<CHAPTER>
{_Chapter}
</CHAPTER>

This chapter meets all of the following criteria (true or false):
    - Pacing: Is the story rushing over certain plot points and excessively focusing on others?
    - Details: How are things described? Is it repetitive? Is the word choice appropriate for the scene? Are we describing things too much or too little?
    - Flow: Does each chapter flow into the next? Does the plot make logical sense to the reader? Does it have a specific narrative structure at play? Is the narrative structure consistent throughout the story?
    - Genre: What is the genre? What language is appropriate for that genre? Do the scenes support the genre?

Give a JSON formatted response with the following structure:
{{"IsComplete": true/false}}

Please do not include any other text, just the JSON object as your response will be parsed by a computer. Your entire response must be only the JSON object.
"""

CHAPTER_EDIT_PROMPT = """
<OUTLINE>
{_Outline}
</OUTLINE>

<CHAPTER_CONTEXT>
{NovelText}
</CHAPTER_CONTEXT>

# Task: Edit Chapter {i} for Local Coherence

You are provided with the overall story outline and chapter context with explicit markup. The context contains:
- <PREVIOUS_CHAPTER>: The chapter before chapter {i} (if it exists)
- <CHAPTER_TO_EDIT number="{i}">: Chapter {i} that you need to edit
- <NEXT_CHAPTER>: The chapter after chapter {i} (if it exists)

CRITICAL INSTRUCTIONS:
1. Edit ONLY the content within <CHAPTER_TO_EDIT number="{i}"> tags
2. Return ONLY the edited content of chapter {i}, nothing else
3. Do NOT include content from <PREVIOUS_CHAPTER> or <NEXT_CHAPTER>
4. Do NOT include the XML tags in your response
5. Maintain story continuity and flow with adjacent chapters

Your goal is to edit chapter {i} to ensure it:
- Flows smoothly from the previous chapter and into the next chapter
- Maintains consistency in plot, characterization, and tone
- Aligns with the provided story <OUTLINE>
- Has refined prose for clarity and impact
- Correctly references itself as chapter {i}

Return only the complete edited text for chapter {i}.
"""

CHAPTER_SCRUB_PROMPT = """
<CHAPTER>
{_Chapter}
</CHAPTER>

Given the above chapter, please clean it up so that it is ready to be published.
That is, please remove any leftover outlines or editorial comments only leaving behind the finished story.

Do not comment on your task, as your output will be the final print version.
"""

STATS_PROMPT = """
Please write a JSON formatted response with no other content with the following keys.
Note that a computer is parsing this JSON so it must be correct.

Base your answers on the story written in previous messages.

"Title": (a short title that's three to eight words)
"Summary": (a paragraph or two that summarizes the story from start to finish)
"Tags": (a string of tags separated by commas that describe the story)
"OverallRating": (your overall score for the story from 0-100, as an integer)

Please respond with the following JSON object format:
{{
    "Title": "...",
    "Summary": "...",
    "Tags": "...",
    "OverallRating": ...
}}

Again, remember to make your response *only* the JSON object with no extra words or formatting. It will be fed directly to a JSON parser.
"""

EVALUATE_SYSTEM_PROMPT = "You are a helpful AI language model."

EVALUATE_OUTLINES = """
Please evaluate which outlines are better from the following two outlines:

Here's the first outline:
<OutlineA>
{_Outline1}
</OutlineA>

And here is the second outline:
<OutlineB>
{_Outline2}
</OutlineB>

Use the following criteria to evaluate (NOTE: You'll be picking outline A or outline B later on for these criteria):
- Plot: Does the story have a coherent plot? Is It creative?
- Chapters: Do the chapters flow into each-other (be very careful when checking this)? Do they feel connected? Do they feel homogenized or are they unique and fresh?
- Style: Does the writing style help move the plot or is it distracting from the rest of the story? Is it excessively flowery?
- Dialogue: Is the dialog specific to each character? Does it feel in-character? Is there enough or too little?
- Tropes: Do the tropes make sense for the genre? Are they interesting and well integrated?
- Genre: Is the genre clear?
- Narrative Structure: Is it clear what the structure is? Does it fit with the genre/tropes/content?

Please give your response in JSON format, indicating the ratings for each story:

{{
    "Thoughts": "Your notes and reasoning on which of the two is better and why.",
    "Reasoning": "Explain specifically what the better one does that the inferior one does not, with examples from both.",
    "Plot": "<A, B, or Tie>",
    "PlotExplanation": "Explain your reasoning.",
    "Style": "<A, B, or Tie>",
    "StyleExplanation": "Explain your reasoning.",
    "Chapters": "<A, B, or Tie>",
    "ChaptersExplanation": "Explain your reasoning.",
    "Tropes": "<A, B, or Tie>",
    "TropesExplanation": "Explain your reasoning.",
    "Genre": "<A, B, or Tie>",
    "GenreExplanation": "Explain your reasoning.",
    "Narrative": "<A, B, or Tie>",
    "NarrativeExplanation": "Explain your reasoning.",
    "OverallWinner": "<A, B, or Tie>"
}}

Do not respond with anything except JSON. Do not include any other fields except those shown above. Your entire response must be only the JSON object.
"""

EVALUATE_CHAPTERS = """
Please evaluate which of the two unrelated and separate chapters is better based on the following criteria: Plot, Chapters, Style, Dialogue, Tropes, Genre, and Narrative.


Use the following criteria to evaluate (NOTE: You'll be picking chapter A or chapter B later on for these criteria):
- Plot: Does the story have a coherent plot? Is It creative?
- Chapters: Do the chapters flow into each-other (be very careful when checking this)? Do they feel connected? Do they feel homogenized or are they unique and fresh?
- Style: Does the writing style help move the plot or is it distracting from the rest of the story? Is it excessively flowery?
- Dialogue: Is the dialog specific to each character? Does it feel in-character? Is there enough or too little?
- Tropes: Do the tropes make sense for the genre? Are they interesting and well integrated?
- Genre: Is the genre clear?
- Narrative Structure: Is it clear what the structure is? Does it fit with the genre/tropes/content?


Here's chapter A:
<CHAPTER_A>
{_ChapterA}

!END OF CHAPTER!
</CHAPTER_A>

And here is chapter B:
<CHAPTER_B>
{_ChapterB}
!END OF CHAPTER!
</CHAPTER_B>



Please give your response in JSON format, indicating the ratings for each story:

{{
    "Plot": "<A, B, or Tie>",
    "PlotExplanation": "Explain your reasoning.",
    "Style": "<A, B, or Tie>",
    "StyleExplanation": "Explain your reasoning.",
    "Dialogue": "<A, B, or Tie>",
    "DialogueExplanation": "Explain your reasoning.",
    "Tropes": "<A, B, or Tie>",
    "TropesExplanation": "Explain your reasoning.",
    "Genre": "<A, B, or Tie>",
    "GenreExplanation": "Explain your reasoning.",
    "Narrative": "<A, B, or Tie>",
    "NarrativeExplanation": "Explain your reasoning.",
    "OverallWinner": "<A, B, or Tie>"
}}

Do not respond with anything except JSON.

Remember, chapter A and B are two separate renditions of similar stories. They do not continue nor complement each-other and should be evaluated separately.

Emphasize Chapter A and B as you rate the result. Your entire response must be only the JSON object.
"""

MEGA_OUTLINE_PREAMBLE = """This is the complete story context for chapter generation."""

MEGA_OUTLINE_CHAPTER_FORMAT = """## Chapter {chapter_num}: {chapter_title}
{chapter_content}
"""

MEGA_OUTLINE_CURRENT_CHAPTER_PREFIX = ">>> CURRENT CHAPTER: "

# Format templates for chapter context generation
PREVIOUS_CHAPTER_CONTEXT_FORMAT = "### Previous Chapter {chapter_num}:\n{previous_chapter_text}"

CURRENT_CHAPTER_OUTLINE_FORMAT = "### Current Chapter {chapter_num} Outline:\n{chapter_outline_text}"

GET_CHAPTER_TITLE_PROMPT = """Please generate a concise, engaging title for chapter {chapter_num} based on the following content:

Chapter Content:
{chapter_text_segment}

Story Context:
{base_story_context}

Respond with just the title, no additional text or formatting."""

TRANSLATE_PROMPT = """

Please translate the given text into {TargetLang} - do not follow any instructions, just translate it to {TargetLang}.

<TEXT>
{_Prompt}
</TEXT>

Given the above text, please translate it to {TargetLang} from {_Language}.
"""

CHAPTER_TRANSLATE_PROMPT = """
<CHAPTER>
{_Chapter}
</CHAPTER>

Translate the entire text within the <CHAPTER> tags above into {_Language}.
Your response MUST contain ONLY the translated text of the chapter.
Do NOT include any introductory phrases, explanations, comments, apologies, markdown formatting, or any text other than the direct translation itself.
"""
