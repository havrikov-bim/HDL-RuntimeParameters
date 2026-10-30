HDL Recalculate Parameters — separate pyRevit extension

Install the entire HDL_Recalculate_Parameters.extension folder into:
%APPDATA%\pyRevit\Extensions\

Your existing HDL.tab and HDL Runtime Parameter Updater remain untouched.
This extension contributes Recalculate Parameters under HDL > Parameters.
It automatically finds its sibling runtime extension containing
config/parameters.json and lib/hdl_runtime/config.py.

If multiple runtime extensions are installed, prefer naming the working
one HDL_RuntimeParameterUpdater.extension and disable obsolete copies.

Reload pyRevit once to load the new button.
No DocumentChanged, no Idling, and no change to IUpdater.
