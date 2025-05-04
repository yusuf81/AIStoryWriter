#!/bin/python3

import argparse
from pydantic import BaseModel, Literal  # Ditambahkan
import time
import json
import datetime
import os

import Writer.Interface.Wrapper
import Writer.Config
import Writer.PrintUtils
import Writer.Prompts


# Definisikan Skema Pydantic
class OutlineEvalSchema(BaseModel):
    Thoughts: str
    Reasoning: str
    Plot: Literal["A", "B", "Tie"]
    PlotExplanation: str
    Style: Literal["A", "B", "Tie"]
    StyleExplanation: str
    Chapters: Literal["A", "B", "Tie"]
    ChaptersExplanation: str
    Tropes: Literal["A", "B", "Tie"]
    TropesExplanation: str
    Genre: Literal["A", "B", "Tie"]
    GenreExplanation: str
    Narrative: Literal["A", "B", "Tie"]
    NarrativeExplanation: str
    OverallWinner: Literal["A", "B", "Tie"]


class ChapterEvalSchema(BaseModel):
    Plot: Literal["A", "B", "Tie"]
    PlotExplanation: str
    Style: Literal["A", "B", "Tie"]
    StyleExplanation: str
    Dialogue: Literal["A", "B", "Tie"]
    DialogueExplanation: str
    Tropes: Literal["A", "B", "Tie"]
    TropesExplanation: str
    Genre: Literal["A", "B", "Tie"]
    GenreExplanation: str
    Narrative: Literal["A", "B", "Tie"]
    NarrativeExplanation: str
    OverallWinner: Literal["A", "B", "Tie"]


def EvaluateOutline(_Client, _Logger, _Outline1, _Outline2):

    _Logger.Log(f"Evaluating Outlines", 4)
    Messages = [
        _Client.BuildSystemQuery(Writer.Prompts.EVALUATE_SYSTEM_PROMPT)
    ]  # Menggunakan prompt terpusat
    Messages.append(
        _Client.BuildUserQuery(
            Writer.Prompts.EVALUATE_OUTLINES.format(
                _Outline1=_Outline1, _Outline2=_Outline2
            )  # Menggunakan prompt terpusat
        )
    )
    # Menggunakan SafeGenerateJSON dengan skema
    # Unpack 3 values, ignore messages and tokens
    _, JSONResponse, _ = _Client.SafeGenerateJSON( # Unpack 3 values, ignore messages and tokens
    # Messages, JSONResponse = _Client.SafeGenerateJSON( # Baris lama
        _Logger,  # Menggunakan _Logger, bukan Logger global
        Messages,
        Args.Model,
        _FormatSchema=OutlineEvalSchema.model_json_schema(),
    )
    Report = ""
    Report += f"Winner of Plot: {JSONResponse['Plot']}\n"
    Report += f"Winner of Chapters: {JSONResponse['Chapters']}\n"
    Report += f"Winner of Style: {JSONResponse['Style']}\n"
    Report += f"Winner of Tropes: {JSONResponse['Tropes']}\n"
    Report += f"Winner of Genre: {JSONResponse['Genre']}\n"
    Report += f"Winner of Narrative: {JSONResponse['Narrative']}\n"
    Report += f"Overall Winner: {JSONResponse['OverallWinner']}\n"

    _Logger.Log(f"Finished Evaluating Outlines", 4)

    return Report, JSONResponse


def EvaluateChapter(_Client, _Logger, _ChapterNum: int, _TotalChapters: int, _ChapterA, _ChapterB): # Tambahkan _TotalChapters

    _Logger.Log(f"Evaluating Chapter {_ChapterNum}/{_TotalChapters}", 4)
    Messages = [
        _Client.BuildSystemQuery(Writer.Prompts.EVALUATE_SYSTEM_PROMPT)
    ]  # Menggunakan prompt terpusat
    Messages.append(
        _Client.BuildUserQuery(
            Writer.Prompts.EVALUATE_CHAPTERS.format(
                _ChapterA=_ChapterA, _ChapterB=_ChapterB
            )  # Menggunakan prompt terpusat
        )
    )

    # Menggunakan SafeGenerateJSON dengan skema
    # Unpack 3 values, ignore messages and tokens
    _, JSONResponse, _ = _Client.SafeGenerateJSON( # Unpack 3 values, ignore messages and tokens
    # Messages, JSONResponse = _Client.SafeGenerateJSON( # Baris lama
        _Logger,  # Menggunakan _Logger, bukan Logger global
        Messages,
        Args.Model,
        _FormatSchema=ChapterEvalSchema.model_json_schema(),
    )
    Report = ""
    Report += f"Winner of Plot: {JSONResponse['Plot']}\n"
    Report += f"Winner of Style: {JSONResponse['Style']}\n"
    Report += f"Winner of Dialogue: {JSONResponse['Dialogue']}\n"
    Report += f"Winner of Tropes: {JSONResponse['Tropes']}\n"
    Report += f"Winner of Genre: {JSONResponse['Genre']}\n"
    Report += f"Winner of Narrative: {JSONResponse['Narrative']}\n"
    Report += f"Overall Winner: {JSONResponse['OverallWinner']}\n"

    _Logger.Log(f"Finished Evaluating Chapter {_ChapterNum}/{_TotalChapters}", 4)

    return Report, JSONResponse


# Setup Argparser
Parser = argparse.ArgumentParser()
Parser.add_argument("-Story1", help="Path to JSON file for story 1")
Parser.add_argument("-Story2", help="Path to JSON file for story 2")
Parser.add_argument(
    "-Output",
    default="Report.md",
    type=str,
    help="Optional file output path, if none is specified, we will only print the rating to terminal",
)
Parser.add_argument(
    "-Host",
    default="localhost:11434",
    type=str,
    help="HTTP URL to OLLAMA instance",
)
Parser.add_argument(
    "-Model",
    default="ollama://command-r-plus",
    type=str,
    help="Model to use for writing the base outline content. Note, command-r-plus really should be used here (or something bigger), 70b models are just too small as of now.",
)

Args = Parser.parse_args()

Writer.Config.OLLAMA_HOST = Args.Host
# Writer.Config.DEBUG = True


# Measure Generation Time
StartTime_s = time.time()

# Setup Logger
Logger = Writer.PrintUtils.Logger("EvalLogs")

# Setup Logger
Interface = Writer.Interface.Wrapper.Interface([Args.Model])

# Load the initial story
Story1: dict = {}
Story2: dict = {}
with open(Args.Story1, "r") as f:
    Story1 = json.loads(f.read())
with open(Args.Story2, "r") as f:
    Story2 = json.loads(f.read())


# Begin Report
Report: str = "# Story Evaluation Report\n\n"
Report += f"Story A: {Args.Story1}\n"
Report += f"Story B: {Args.Story2}\n\n\n"

## Evaluate Outlines
Report += f"## Outline\n"
OutlineReport, OutlineJSON = EvaluateOutline(
    Interface, Logger, Story1["Outline"], Story2["Outline"]
)
Report += OutlineReport


ShortestStory = min(
    len(Story1["UnscrubbedChapters"]), len(Story2["UnscrubbedChapters"])
)
ChapterJSONs: list = []
for i in range(ShortestStory):

    Report += f"## Chapter {i+1}\n" # Gunakan i+1 untuk nomor bab 1-based
    ChapterReport, ChapterJSON = EvaluateChapter(
        Interface,
        Logger,
        i + 1, # Teruskan nomor bab (1-based)
        ShortestStory, # Teruskan total bab yang dievaluasi
        Story1["UnscrubbedChapters"][i],
        Story2["UnscrubbedChapters"][i],
    )
    Report += ChapterReport

Report += "\n\n# Vote Totals\nTotal A Votes: " + str(Report.count(": A\n")) + "\n"
Report += "Total B Votes: " + str(Report.count(": B\n")) + "\n"
Report += "Total Tie Votes: " + str(Report.count(": Tie\n")) + "\n"

# Calculate Eval Time
EndTime_s = time.time()
TotalEvalTime_s = round(EndTime_s - StartTime_s)


# Optionally write Report To Disk
if Args.Output != "":
    with open(Args.Output, "w") as f:
        f.write(Report)
