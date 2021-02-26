# --------------------------NukeStudioPrismPlugin--------------------------------
# This file initializes PrismCore for Nuke Studio only, and registers hiero
# events so that we can access the pcore object later.
#
# (c) 2021 Tarantula
# Authors: Moses Molina, Peter Timberlake
# -------------------------------------------------------------------------------

from .PrismShotProcessor import (PrismShotProcessor, PrismShotProcessorUI, PrismShotProcessorPreset)
from .PrismTranscodeExporter import (PrismTranscodeExporter, PrismTranscodeExporterUI, PrismTranscodePreset)

from hiero.core import events

import nuke

if nuke.env["studio"] and nuke.env.get("gui"):
    if "pcore" in locals():
        nuke.message("Prism is loaded multiple times. This can cause unexpected errors. Please clean this file from all Prism related content:\n\n%s\n\nYou can add a new Prism integration through the Prism Settings dialog" % __file__)
    else:
        import os
        import sys

        prismRoot = os.getenv("PRISM_ROOT")
        if not prismRoot:
            prismRoot = "C:/Prism"

        scriptDir = os.path.join(prismRoot, "Scripts")
        if scriptDir not in sys.path:
            sys.path.append(scriptDir)

        import PrismCore

        pcore = PrismCore.PrismCore(app="Nuke")


def createPrismShot(event):
    for g in globals().keys():
        if g == "pcore":
            pcore.entities.createShot(event.shot_name, event.range)


def loadPrismShots(event):
    sequences, shots = pcore.entities.getShots()
    events.sendEvent(events.EventType.kLoadedPrismShots, None, seqs=sequences)


def requestPCore(event):
    events.sendEvent(events.EventType.kLoadedPCore, None, pcore=pcore)


events.registerEventType("kCreatePrismShot")
events.registerEventType("kLoadPrismShots")
events.registerEventType("kLoadedPrismShots")

events.registerEventType("kRequestPCore")
events.registerEventType("kLoadedPCore")

events.registerInterest(events.EventType.kCreatePrismShot, createPrismShot)
events.registerInterest(events.EventType.kLoadPrismShots, loadPrismShots)
events.registerInterest(events.EventType.kRequestPCore, requestPCore)
