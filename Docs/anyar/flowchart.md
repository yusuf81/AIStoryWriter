# AIStoryWriter Flowchart

```mermaid
graph TD
    A[Start Write.py] --> B(Parse Command Line Arguments);
    B --> C(Update Writer.Config with Args);
    C --> D(Initialize Logger);
    D --> E(Initialize Interface - Load Models);
    E --> F(Load User Prompt from File);

    F --> G{Translate Prompt?};
    G -- Yes --> H(Call Translator.TranslatePrompt);
    G -- No --> I;
    H --> I(Use (Translated) Prompt);

    I --> J(Call OutlineGenerator.GenerateOutline);
    subgraph J [Outline Generation]
        J1(Extract Base Context) --> J2;
        J2(Generate Story Elements) --> J3;
        J3(Generate Initial Outline) --> J4{Revision Loop};
        J4 -- Revise --> J5(Get Feedback);
        J5 --> J6(Get Rating);
        J6 --> J7{Check Exit Conditions - Min/Max Revisions & Rating};
        J7 -- No --> J8(Call ReviseOutline);
        J8 --> J4;
        J7 -- Yes --> J9(Combine BaseContext, Elements, Final Outline);
    end
    J --> K(Get NumChapters - Call ChapterDetector.LLMCountChapters);

    K --> L{Expand Outline?};
    L -- Yes --> M{Loop NumChapters};
    M -- Next Chapter --> N(Call OutlineGenerator.GeneratePerChapterOutline);
    N --> M;
    M -- Loop Done --> O(Create MegaOutline);
    L -- No --> P(Use Basic Outline);
    O --> P;

    P --> Q{Loop NumChapters - Write Chapters};
    Q -- Next Chapter i --> R(Call ChapterGenerator.GenerateChapter);
    subgraph R [Chapter Generation - Chapter i]
        R1(Extract This Chapter Outline) --> R2;
        R2(Generate Previous Chapter Summary - Optional) --> R3;
        R3{Scene Generation Pipeline Enabled?};
        R3 -- Yes --> R4(Call Scene.ChapterByScene);
        subgraph R4 [Scene-by-Scene Generation]
            R4a(Call ChapterOutlineToScenes) --> R4b;
            R4b(Call ScenesToJSON) --> R4c{Loop Scenes};
            R4c -- Next Scene --> R4d(Call SceneOutlineToScene);
            R4d --> R4c;
            R4c -- Loop Done --> R4e(Concatenate Scenes);
        end
        R3 -- No --> R5(Generate Stage 1 Plot - Loop);
        R4 --> R6(Set Stage1Chapter);
        R5 --> R6;
        R6 --> R7(Generate Stage 2 Character Dev - Loop);
        R7 --> R8(Generate Stage 3 Dialogue - Loop);
        R8 --> R9{Revisions Enabled?};
        R9 -- No --> R10(Return Chapter);
        R9 -- Yes --> R11{Revision Loop};
        R11 -- Revise --> R12(Get Feedback);
        R12 --> R13(Get Rating);
        R13 --> R14{Check Exit Conditions};
        R14 -- No --> R15(Call ReviseChapter);
        R15 --> R11;
        R14 -- Yes --> R10;
    end
    R --> S(Append Chapter to List);
    S --> Q;
    Q -- Loop Done --> T(Chapters List Complete);

    T --> U{Final Edit Pass Enabled?};
    U -- Yes --> V(Call NovelEditor.EditNovel);
    V --> W(Update Chapters List);
    U -- No --> W;

    W --> X{Scrubbing Enabled?};
    X -- Yes --> Y(Call Scrubber.ScrubNovel);
    Y --> Z(Update Chapters List);
    X -- No --> Z;

    Z --> AA{Translate Novel?};
    AA -- Yes --> AB(Call Translator.TranslateNovel);
    AB --> AC(Update Chapters List);
    AA -- No --> AC;

    AC --> AD(Compile Chapters into StoryBodyText);
    AD --> AE(Call StoryInfo.GetStoryInfo);
    AE --> AF(Extract Title, Summary, Tags);
    AF --> AG(Calculate Stats & Format Output String);
    AG --> AH(Save Story to .md File);
    AH --> AI(Save Story Info to .json File);
    AI --> AJ[End];

```
