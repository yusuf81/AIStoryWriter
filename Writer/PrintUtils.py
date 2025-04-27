import termcolor
import datetime
import os
import json


def PrintMessageHistory(_Messages):
    print("------------------------------------------------------------")
    for Message in _Messages:
        print(Message)
    print("------------------------------------------------------------")


class Logger:

    def __init__(self, _LogfilePrefix="Logs", _ExistingLogDir=None):

        # Make Paths For Log
        if _ExistingLogDir:
            LogDirPath = _ExistingLogDir
            # Pastikan direktori LangchainDebug ada jika melanjutkan
            os.makedirs(LogDirPath + "/LangchainDebug", exist_ok=True)
            # self.Log("Resuming logging in existing directory.", 5) # Tidak bisa log sebelum file dibuka
            log_mode = "a"  # Append mode for resuming
        else:
            LogDirPath = (
                _LogfilePrefix
                + "/Generation_"
                + datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            )
            os.makedirs(LogDirPath + "/LangchainDebug", exist_ok=True)
            log_mode = "a"  # Mulai dengan append juga tidak masalah

        # Setup Log Path
        self.LogDirPrefix = LogDirPath
        self.LogPath = LogDirPath + "/Main.log"
        # Gunakan mode yang ditentukan dan encoding utf-8
        self.File = open(self.LogPath, log_mode, encoding="utf-8")
        self.LangchainID = 0
        self.LogItems = [] # Initialize LogItems here

        # Hitung LangchainID awal jika melanjutkan
        if _ExistingLogDir:
            self.Log(
                "Resuming logging in existing directory.", 5
            )  # Log setelah file dibuka
            try:
                langchain_debug_path = os.path.join(LogDirPath, "LangchainDebug")
                if os.path.exists(langchain_debug_path):
                    langchain_files = [
                        f
                        for f in os.listdir(langchain_debug_path)
                        if f.endswith(".md") or f.endswith(".json")
                    ]
                    if langchain_files:
                        # Cari ID tertinggi dari nama file
                        ids = []
                        for f in langchain_files:
                            try:
                                # Ambil bagian pertama sebelum '_' dan coba konversi ke int
                                file_id = int(f.split("_")[0])
                                ids.append(file_id)
                            except (ValueError, IndexError):
                                continue  # Abaikan file yang tidak sesuai format ID_...
                        self.LangchainID = max(ids) + 1 if ids else 0
                        self.Log(
                            f"Resuming Langchain ID counter at {self.LangchainID}", 6
                        )
                    else:
                        self.LangchainID = 0  # Tidak ada file, mulai dari 0
                else:
                    self.LangchainID = 0  # Direktori debug tidak ada
            except Exception as e:
                self.Log(f"Could not determine last Langchain ID: {e}", 7)
                self.LangchainID = 0  # Fallback


    # Helper function that saves the entire language chain object as both json and markdown for debugging later
    def SaveLangchain(self, _LangChainID: str, _LangChain: list):

        # Calculate Filepath For This Langchain
        ThisLogPathJSON: str = (
            self.LogDirPrefix
            + f"/LangchainDebug/{self.LangchainID}_{_LangChainID}.json"
        )
        ThisLogPathMD: str = (
            self.LogDirPrefix + f"/LangchainDebug/{self.LangchainID}_{_LangChainID}.md"
        )
        LangChainDebugTitle: str = f"{self.LangchainID}_{_LangChainID}"
        self.LangchainID += 1

        # Generate and Save JSON Version
        with open(
            ThisLogPathJSON, "w", encoding="utf-8"
        ) as f:  # Tambahkan encoding utf-8
            f.write(json.dumps(_LangChain, indent=4, sort_keys=True))

        # Now, Save Markdown Version
        with open(
            ThisLogPathMD, "w", encoding="utf-8"
        ) as f:  # Tambahkan encoding utf-8
            MarkdownVersion: str = (
                f"# Debug LangChain {LangChainDebugTitle}\n**Note: '```' tags have been removed in this version.**\n"
            )
            for Message in _LangChain:
                MarkdownVersion += f"\n\n\n# Role: {Message['role']}\n"
                MarkdownVersion += f"```{Message['content'].replace('```', '')}```"
            f.write(MarkdownVersion)

        self.Log(
            f"Wrote This Language Chain ({LangChainDebugTitle}) To Debug File {ThisLogPathMD}",
            5,
        )

    # Saves the given story to disk
    def SaveStory(self, _StoryContent: str):

        with open(
            f"{self.LogDirPrefix}/Story.md", "w", encoding="utf-8"
        ) as f:  # Tambahkan encoding utf-8
            f.write(_StoryContent)

        self.Log(f"Wrote Story To Disk At {self.LogDirPrefix}/Story.md", 5)

    # Logs an item
    def Log(self, _Item, _Level: int):

        # Create Log Entry
        LogEntry = f"[{str(_Level).ljust(2)}] [{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}] {_Item}"

        # Write it to file
        self.File.write(LogEntry + "\n")
        self.LogItems.append(LogEntry)

        # Now color and print it
        if _Level == 0:
            LogEntry = termcolor.colored(LogEntry, "white")
        elif _Level == 1:
            LogEntry = termcolor.colored(LogEntry, "grey")
        elif _Level == 2:
            LogEntry = termcolor.colored(LogEntry, "blue")
        elif _Level == 3:
            LogEntry = termcolor.colored(LogEntry, "cyan")
        elif _Level == 4:
            LogEntry = termcolor.colored(LogEntry, "magenta")
        elif _Level == 5:
            LogEntry = termcolor.colored(LogEntry, "green")
        elif _Level == 6:
            LogEntry = termcolor.colored(LogEntry, "yellow")
        elif _Level == 7:
            LogEntry = termcolor.colored(LogEntry, "red")

        print(LogEntry)

    def __del__(self):
        self.File.close()
