#!/usr/bin/env python
# -*- coding: utf-8 -*-

from distutils.core import setup
import glob
import py2exe

zipfile = None,
compressed = 1,
bundle_files = 2,
opts = {
    "py2exe": {
        "includes": "pygtk,pango,gobject,twisted, cairo, pangocairo, atk",
        "dist_dir": "dist",
    }
}

setup(
    name = "Itaka",
    version = "1.0",
    description = 'On-demand screen capture server',
    author = 'Marc E.',
    author_email = 'santusmarc@gmail.com',
    url = 'http://itaka.jardinpresente.com.ar',
    license = 'GPL',
    windows = [
        {
            "script": "itaka.py",
            "icon_resources": [(1, "share\images\itaka.ico")]
        }],
    options = opts,
    data_files=[
    ("images",
    glob.glob("share\images\\*.png")),
    'uigtk.py',
    'config.py',
    'error.py',
    'console.py',
    'server.py',
    'screenshot.py',
    ]

)
