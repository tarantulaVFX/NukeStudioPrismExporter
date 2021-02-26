# --------------------------NukeStudioPrismPlugin--------------------------------
# A Nuke Studio exporter subclassed from TranscodeExporter that exports a shot
# and creates the prism shot for it.
#
# (c) 2021 Tarantula
# Authors: Moses Molina, Peter Timberlake
# -------------------------------------------------------------------------------

import os
import os.path as path
import hiero.core

import nuke
from hiero.core import events

from hiero.exporters import FnTranscodeExporter, FnTranscodeExporterUI, FnExternalRenderUI, FnExternalRender, FnAudioHelper


class PrismTranscodeExporter(FnTranscodeExporter.TranscodeExporter):
    def __init__(self, initDict):

        FnTranscodeExporter.TranscodeExporter.__init__(self, initDict)

        self.uploaded = False
        self.upload_started = False
        self.fullFilePath = ""
        self.fileDir = ""
        self.fullFileName = ""
        self.root = ""
        self.ext = ""
        self.upload_progress = 0.0
        self.upload_reply = None
        self._shot_name = None

    def startTask(self):
        self._shot_name = self._preset.properties()["prism_sequence"] + '-' + self.shotName()
        self.fullFilePath = self.resolvedExportPath()
        self.fileDir, self.fullFileName = os.path.split(self.fullFilePath)
        output_range = [self.outputRange()[0], self.outputRange()[1]]
        events.sendEvent(events.EventType.kCreatePrismShot, None, shot_name=self._shot_name, range=output_range)

        # Make yml File
        step = self._preset.properties()["prism_step"]
        cat = self._preset.properties()["prism_category"]
        user = self._preset.properties()["prism_user"]
        common_path = path.abspath(path.join(self.fileDir, '../../..')).replace('\\', '/') + '/Scenefiles/' + \
                      step + "/" + cat + "/" + "shot_" + self._shot_name + "_" + step + "_" + cat + "_" + \
                      self.versionString() + "__" + user
        nk_path = common_path + "_.nk"
        yml_path = common_path + "_versioninfo.yml"
        os.makedirs(path.dirname(yml_path).replace('\\', '/'))
        with open(yml_path, "w+") as yml:
            yml.write("!!omap\n")
            yml.write("- basePath: " + path.dirname(nk_path).replace('\\', '/') + "\n")
            yml.write("- fileName: " + nk_path + "\n")
            yml.write("- entity: shot\n")
            yml.write("- entityName: " + self._shot_name + "\n")
            yml.write("- fullEntityName: " + self._shot_name + "\n")
            yml.write("- step: " + step + "\n")
            yml.write("- category: " + cat + "\n")
            yml.write("- version: " + self.versionString() + "\n")
            yml.write("- comment: \'\'\n")
            yml.write("- user: " + user + "\n")
            yml.write("- extension: .nk\n")
            yml.write("- username: " + self._preset.properties()["prism_username"] + "\n")
            yml.close()

        FnTranscodeExporter.TranscodeExporter.startTask(self)

    def progress(self):
        return float(FnTranscodeExporter.TranscodeExporter.progress(self))

    def finishTask(self):
        pass
        FnTranscodeExporter.TranscodeExporter.finishTask(self)


class PrismTranscodePreset(FnTranscodeExporter.TranscodePreset):
    def __init__(self, name, properties):

        hiero.core.RenderTaskPreset.__init__(self, PrismTranscodeExporter, name, properties)

        # Set any preset defaults here
        self.properties()["keepNukeScript"] = False
        self.properties()["readAllLinesForExport"] = self._defaultReadAllLinesForCodec()
        self.properties()["useSingleSocket"] = False
        self.properties()["burninDataEnabled"] = False
        self.properties()["burninData"] = dict((datadict["knobName"], None) for datadict in FnExternalRender.NukeRenderTask.burninPropertyData)
        self.properties()["additionalNodesEnabled"] = False
        self.properties()["additionalNodesData"] = []
        self.properties()["method"] = "Blend"
        self.properties()["includeEffects"] = True
        self.properties()["includeAudio"] = False
        self.properties()["deleteAudio"] = True

        self.properties()["prism_sequence"] = ""
        self.properties()["prism_step"] = ""
        self.properties()["prism_category"] = ""
        self.properties()["prism_user"] = ""
        self.properties()["prism_username"] = ""
        self.properties()["prism_task"] = ""

        FnAudioHelper.defineExportPresetProperties(self)

        # Give the Write node a name, so it can be referenced elsewhere
        if "writeNodeName" not in self.properties():
          self.properties()["writeNodeName"] = "Write_{ext}"

        self.properties().update(properties)

    def supportedItems(self):
        return hiero.core.TaskPresetBase.kAllItems


class PrismTranscodeExporterUI(FnTranscodeExporterUI.TranscodeExporterUI):
    def __init__(self, preset):
        FnExternalRenderUI.NukeRenderTaskUI.__init__(self, preset, PrismTranscodeExporter, "Prism Transcode")
        self._tags = []