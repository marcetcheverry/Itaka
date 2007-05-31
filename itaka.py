#! /usr/bin/env python
# -*- coding: utf8 -*-
""" Itaka core """

import sys, os, traceback 

# Itaka core modules
try:
    # Initiate the configuration engine.
        import config as iconfig
        configinstance = iconfig.ConfigParser()
        configinstance.load()

        # Import our GUI
        import uigtk as igui
except ImportError:
    print "[*] ERROR: Failed to import Itaka modules."
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    try:
        gui = igui.Gui(configinstance)
        gui.main()
    except AttributeError:
        print "[*] ERROR: Could not initiate GUI."
        traceback.print_exc()
        sys.exit(1)
