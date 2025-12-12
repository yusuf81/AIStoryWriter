# AIStoryWriter Flowchart

```mermaid
graph TD
    A[Start Write.py] --> B(Parse Command Line Arguments);
    B --> C{Resume from State?};
    C -- Yes --> D(Load State File);
    C -- No --> E;
    D --> F(Restore Configuration from State);
    F --> G(Initialize Logger & Interface);
    G --> H;

    E --> I(Update Writer.Config with Args);
    I --> J(Set NATIVE_LANGUAGE from Args/Config);
    J --> K(Initialize Logger);
    K --> L(Initialize Interface - Load Models);
    L --> M(Dynamic Prompt Loading based on NATIVE_LANGUAGE);
    M --> N(Load User Prompt from File);
    N --> H;

    H --> O{Translate Prompt?};
    O -- Yes --> P(Call Translator.TranslatePrompt);
    O -- No --> Q;
    P --> Q(Use (Translated) Prompt);

    Q --> R(Call OutlineGenerator.GenerateOutline);
    subgraph R [Outline Generation]
        R1(Extract Base Context) --> R2;
        R2(Generate Story Elements) --> R3;
        R3(Generate Initial Outline) --> R4{Revision Loop};
        R4 -- Revise --> R5(Get Feedback);
        R5 --> R6(Get Rating);
        R6 --> R7{Check Exit Conditions - Min/Max Revisions & Rating};
        R7 -- No --> R8(Call ReviseOutline);
        R8 --> R4;
        R7 -- Yes --> R9(Combine BaseContext, Elements, Final Outline);
    end
    R --> S(Get NumChapters - Call ChapterDetector.LLMCountChapters);

    S --> T{Expand Outline?};
    T -- Yes --> U{Loop NumChapters};
    U -- Next Chapter --> V(Call OutlineGenerator.GeneratePerChapterOutline);
    V --> U;
    U -- Loop Done --> W(Create MegaOutline);
    T -- No --> X(Use Basic Outline);
    W --> X;

    X --> Y{Loop NumChapters - Write Chapters};
    Y -- Next Chapter i --> Z(Call ChapterGenerator.GenerateChapter);
    subgraph Z [Chapter Generation - Chapter i]
        Z1(Extract This Chapter Outline) --> Z2;
        Z2(Generate Previous Chapter Summary - Optional) --> Z3;
        Z3{Scene Generation Pipeline Enabled?};
        Z3 -- Yes --> Z4(Call Scene.ChapterByScene);
        subgraph Z4 [Scene-by-Scene Generation]
            Z4a(Call ChapterOutlineToScenes) --> Z4b;
            Z4b(Call ScenesToJSON) --> Z4c{Loop Scenes};
            Z4c -- Next Scene --> Z4d(Call SceneOutlineToScene);
            Z4d --> Z4c;
            Z4c -- Loop Done --> Z4e(Concatenate Scenes);
        end
        Z3 -- No --> Z5(Generate Stage 1 Plot - Loop);
        Z4 --> Z6(Set Stage1Chapter);
        Z5 --> Z6;
        Z6 --> Z7(Generate Stage 2 Character Dev - Loop);
        Z7 --> Z8(Generate Stage 3 Dialogue - Loop);
        Z8 --> Z9{Revisions Enabled?};
        Z9 -- No --> Z10(Return Chapter);
        Z9 -- Yes --> Z11{Revision Loop};
        Z11 -- Revise --> Z12(Get Feedback);
        Z12 --> Z13(Get Rating);
        Z13 --> Z14{Check Exit Conditions};
        Z14 -- No --> Z15(Call ReviseChapter);
        Z15 --> Z11;
        Z14 -- Yes --> Z10;
    end
    Z --> AA(Save Chapter to State);
    AA --> Y;
    Y -- Loop Done --> AB(Chapters List Complete);

    AB --> AC{Final Edit Pass Enabled?};
    AC -- Yes --> AD(Call NovelEditor.EditNovel);
    AD --> AE(Update Chapters List);
    AC -- No --> AE;

    AE --> AF{Scrubbing Enabled?};
    AF -- Yes --> AG(Call Scrubber.ScrubNovel);
    AG --> AH(Update Chapters List);
    AF -- No --> AH;

    AH --> AI{Translate Novel?};
    AI -- Yes --> AJ(Call Translator.TranslateNovel);
    AJ --> AK(Update Chapters List);
    AI -- No --> AK;

    AK --> AL(Compile Chapters into StoryBodyText);
    AL --> AM(Call StoryInfo.GetStoryInfo);
    AM --> AN(Extract Title, Summary, Tags);
    AN --> AO(Calculate Stats & Format Output String);
    AO --> AP(Build OutputFiles Structure);
    AP --> AQ(Save Story to .md File);
    AQ --> AR(Save Story Info to .json File);
    AR --> AS{PDF Generation Enabled?};
    AS -- Yes --> AT(Call PDFGenerator.GeneratePDF);
    AT --> AU{PDF Success?};
    AU -- Yes --> AV(Add PDF Path to OutputFiles);
    AU -- No --> AW(Log PDF Error);
    AS -- No --> AV;
    AV --> AX[End];
    AW --> AX;

```
