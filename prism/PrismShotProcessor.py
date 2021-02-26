# --------------------------NukeStudioPrismPlugin--------------------------------
# A Nuke Studio shot processor subclassed from ShotProcessor that creates shots
# for the current prism pipeline.
#
# (c) 2021 Tarantula
# Authors: Moses Molina, Peter Timberlake
# -------------------------------------------------------------------------------

import os
import json

import nuke

import hiero.core

from hiero.exporters import FnShotProcessor
from hiero.exporters.FnExportKeywords import kFileBaseKeyword, kFileHeadKeyword, kFilePathKeyword, KeywordTooltips

from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtCore import *

try:
    from hiero.exporters.FnShotProcessorUI import ShotProcessorUI
except ImportError:
    ShotProcessorUI = FnShotProcessor.ShotProcessor

from hiero.core import events


class PrismShotProcessorUI(ShotProcessorUI):
    def __init__(self, preset):
        ShotProcessorUI.__init__(self, preset)
        # events.registerInterest(events.EventType.kLoadedPrismShots, self.onSeqsLoaded)
        self.pcore = None
        self.steps = None

    def getPCore(self, event):
        self.pcore = event.pcore
        if self.seqsC:
            self.seqsC.clear()
            sequences, shots = self.pcore.entities.getShots()
            for seq in sequences:
                if seq != "no sequence":
                    self.seqsC.addItem(seq)

        if self.stepsC:
            self.stepsC.clear()
            self.steps = self.pcore.getConfig("globals", "pipeline_steps", configPath=self.pcore.prismIni)
            for step in self.steps:
                self.stepsC.addItem(str(step))
            self.stepsC.setCurrentText("cmp")
        self.preset().properties()["prism_user"] = self.pcore.user
        self.preset().properties()["prism_username"] = self.pcore.username

    def displayName(self):
        return "Prism Shot Export"

    def toolTip(self):
        return "Update Shots In Prism"

    def onSeqsLoaded(self, event):
        for seq in event.seqs:
            if seq != "no sequence":
                self.seqsC.addItem(seq)

    def loadSeqs(self):
        events.sendEvent(events.EventType.kLoadPrismShots, None)

    def onStepSelected(self, step):
        if step != "":
            self.catsE.setText(self.steps[step])

    def validate(self, exportItems):
        if self.seqsC.currentText() == "":
            nuke.message("Please provide a prism sequence name.")
            return False
        elif self.taskE.text() == "":
            nuke.message("Please provide a prism task name.")
            return False

        self.preset().properties()["prism_sequence"] = self.seqsC.currentText()
        self.preset().properties()["prism_step"] = self.stepsC.currentText()
        self.preset().properties()["prism_category"] = self.catsE.text()
        self.preset().properties()["prism_task"] = self.taskE.text()
        return ShotProcessorUI.validate(self, exportItems)

    def populateUI(self, *args, **kwargs):
        events.registerInterest(events.EventType.kLoadedPCore, self.getPCore)

        # Create proxy widget so we can add our own ui
        (widget, taskUIWidget, exportItems) = args
        main_layout = QVBoxLayout(widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        default = QWidget(None)
        main_layout.addWidget(default)

        # Call super function
        ShotProcessorUI.populateUI(self, default, taskUIWidget, exportItems)

        # Header Widgets
        logo_path = "C:/Prism/Scripts/UserInterfacesPrism/p_tray.png"
        if os.path.exists(logo_path):
            self.logo = QPixmap(logo_path)
        else:
            self.logo = QPixmap()

        self.lineF = QFrame()
        self.lineF.setFrameShape(QFrame.HLine)
        self.lineF.setFrameShadow(QFrame.Sunken)
        self.logoL = QLabel()
        self.logoL.setPixmap(self.logo.scaled(16, 16, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        logo_layout = QHBoxLayout()
        logo_layout.addWidget(self.logoL)
        logo_layout.addWidget(QLabel("Prism Settings"))
        logo_layout.addStretch()

        # Sequence Selection
        self.seqsC = QComboBox()
        self.seqsC.setEditable(True)
        self.seqsL = QLabel("sequence")
        self.seqsC.setToolTip("{prism_sequence} - The prism sequence to add these shots to. Can be a new sequence name.")

        # Step Selection
        self.stepsC = QComboBox()
        self.stepsC.setEditable(False)
        self.stepsC.currentTextChanged.connect(self.onStepSelected)
        self.stepsC.setToolTip("{prism_step} - This is the prism step to add the shot's nuke script to.")
        self.stepsL = QLabel("step")

        # Category Selection
        self.catsE = QLineEdit()
        self.catsE.setReadOnly(True)
        self.catsE.setToolTip("{prism_category} - This is the prism category that is the full name of the step above.")
        self.catsL = QLabel("category")

        # Task Selection
        self.taskE = QLineEdit()
        self.taskL = QLabel("task")
        self.taskE.setToolTip("{prism_task} - This is the task name prism uses to track renders.")

        # Layout Setup
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.seqsL, 0, 0, alignment=Qt.AlignRight)
        grid_layout.addWidget(self.seqsC, 0, 1)
        grid_layout.addItem(QSpacerItem(1, 1, QSizePolicy.Expanding, QSizePolicy.Minimum), 0, 2)
        grid_layout.setColumnStretch(2, 3)
        grid_layout.addWidget(self.stepsL, 1, 0, alignment=Qt.AlignRight)
        grid_layout.addWidget(self.stepsC, 1, 1)
        grid_layout.addWidget(self.catsL, 2, 0, alignment=Qt.AlignRight)
        grid_layout.addWidget(self.catsE, 2, 1)
        grid_layout.addWidget(self.taskL, 3, 0, alignment=Qt.AlignRight)
        grid_layout.addWidget(self.taskE, 3, 1)

        main_layout.addWidget(self.lineF)
        main_layout.addLayout(logo_layout)
        main_layout.addLayout(grid_layout)

        # Load Prism Info
        events.sendEvent(events.EventType.kRequestPCore, None)


class PrismShotProcessor(FnShotProcessor.ShotProcessor):
    def __init__(self, preset, submission=None, synchronous=False):
        FnShotProcessor.ShotProcessor.__init__(self, preset, submission, synchronous)

    def startProcessing(self, exportItems, preview=False):
        if preview:
            return FnShotProcessor.ShotProcessor.startProcessing(self, exportItems, preview)

        for (exportPath, preset) in self._exportTemplate.flatten():
            if "prism_sequence" in preset.properties():
                preset.properties()["prism_sequence"] = self.preset().properties()["prism_sequence"]
                preset.properties()["prism_user"] = self.preset().properties()["prism_user"]
                preset.properties()["prism_username"] = self.preset().properties()["prism_username"]
                preset.properties()["prism_step"] = self.preset().properties()["prism_step"]
                preset.properties()["prism_category"] = self.preset().properties()["prism_category"]
                preset.properties()["prism_task"] = self.preset().properties()["prism_task"]

        FnShotProcessor.ShotProcessor.startProcessing(self, exportItems, preview)


class PrismShotProcessorPreset(hiero.core.ProcessorPreset):
    def __init__(self, name, properties):
        hiero.core.ProcessorPreset.__init__(self, PrismShotProcessor, name)

        # setup defaults
        self._excludedTrackIDs = []
        self.nonPersistentProperties()["excludedTracks"] = []
        self.properties()["excludeTags"] = []
        self.properties()["includeTags"] = []
        self.properties()["versionIndex"] = 1
        self.properties()["versionPadding"] = 2
        self.properties()["exportTemplate"] = ( )
        self.properties()["exportRoot"] = "{projectroot}"
        self.properties()["cutHandles"] = 12
        self.properties()["cutUseHandles"] = False
        self.properties()["cutLength"] = False
        self.properties()["includeRetimes"] = False
        self.properties()["startFrameIndex"] = 1001
        self.properties()["startFrameSource"] = PrismShotProcessor.kStartFrameSource

        self.properties()["prism_sequence"] = ""
        self.properties()["prism_user"] = ""
        self.properties()["prism_username"] = ""
        self.properties()["prism_step"] = ""
        self.properties()["prism_category"] = ""
        self.properties()["prism_task"] = ""

        self.properties().update(properties)

        # This remaps the project root if os path remapping has been set up in the preferences
        self.properties()["exportRoot"] = hiero.core.remapPath(self.properties()["exportRoot"])

    def getPrismProject(self):
        return os.getenv("PRISM_JOB")

    def getPrismUser(self):
        pass

    def addCustomResolveEntries(self, resolver):
        """addDefaultResolveEntries(self, resolver)
        Create resolve entries for default resolve tokens shared by all task types.
        @param resolver : ResolveTable object"""

        resolver.addResolver("{filename}", "Filename of the media being processed", lambda keyword, task: task.fileName())
        resolver.addResolver(kFileBaseKeyword, KeywordTooltips[kFileBaseKeyword], lambda keyword, task: task.filebase())
        resolver.addResolver(kFileHeadKeyword, KeywordTooltips[kFileHeadKeyword], lambda keyword, task: task.filehead())
        resolver.addResolver(kFilePathKeyword, KeywordTooltips[kFilePathKeyword], lambda keyword, task: task.filepath())
        resolver.addResolver("{filepadding}", "Source Filename padding for formatting frame indices", lambda keyword, task: task.filepadding())
        resolver.addResolver("{fileext}", "Filename extension part of the media being processed", lambda keyword, task: task.fileext())
        resolver.addResolver("{clip}", "Name of the clip used in the shot being processed", lambda keyword, task: task.clipName())
        resolver.addResolver("{shot}", "Name of the shot being processed", lambda keyword, task: task.shotName())
        resolver.addResolver("{track}", "Name of the track being processed", lambda keyword, task: task.trackName())
        resolver.addResolver("{sequence}", "Name of the sequence being processed", lambda keyword, task: task.sequenceName())
        resolver.addResolver("{event}", "EDL event of the track item being processed", lambda keyword, task: task.editId())
        resolver.addResolver("{_nameindex}", "Index of the shot name in the sequence preceded by an _, for avoiding clashes with shots of the same name", lambda keyword, task: task.shotNameIndex())
        resolver.addResolver("{prism_project}", "Currently Active Prism Directory", lambda keyword, task: self.getPrismProject())
        resolver.addResolver("{prism_sequence}", "Currently Selected Prism Sequence", self.properties()["prism_sequence"])
        resolver.addResolver("{prism_user}", "Current Prism User", self.properties()["prism_user"])
        resolver.addResolver("{prism_step}", "Currently Selected Prism Step", self.properties()["prism_step"])
        resolver.addResolver("{prism_category}", "Currently Selected Prism Category", self.properties()["prism_category"])
        resolver.addResolver("{prism_task}", "Desired prism task name", self.properties()["prism_task"])

    # check that all nuke shot exporters have at least one write node
    def isValid(self):
        allNukeShotsHaveWriteNodes = True
        
        for itemPath, itemPreset in self.properties()["exportTemplate"]:
            isNukeShot = isinstance(itemPreset, hiero.exporters.FnNukeShotExporter.NukeShotPreset)
            if isNukeShot and not itemPreset.properties()["writePaths"]:
                allNukeShotsHaveWriteNodes = False
                return (False, "Your Export Structure has no Write Nodes defined.")
        return (True, "")
