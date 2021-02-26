# --------------------------NukeStudioPrismPlugin--------------------------------
# This file registers the custom processor and exporter with Nuke Studio
#
# (c) 2021 Tarantula
# Authors: Moses Molina, Peter Timberlake
# -------------------------------------------------------------------------------

import hiero.core

from prism import (PrismShotProcessor, PrismShotProcessorUI, PrismShotProcessorPreset,
                   PrismTranscodeExporter, PrismTranscodeExporterUI, PrismTranscodePreset)
                   
hiero.core.taskRegistry.registerProcessor(PrismShotProcessorPreset, PrismShotProcessor)
hiero.ui.taskUIRegistry.registerProcessorUI(PrismShotProcessorPreset, PrismShotProcessorUI)

hiero.core.taskRegistry.registerTask(PrismTranscodePreset, PrismTranscodeExporter)
hiero.ui.taskUIRegistry.registerTaskUI(PrismTranscodePreset, PrismTranscodeExporterUI)