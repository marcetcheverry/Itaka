#!/usr/bin/env python
# -*- coding: utf-8 -*-

from distutils.core import setup
import glob
import py2exe

opts = {
    "py2exe": {
        "includes": "pygtk,pango,gobject,twisted, cairo, pangocairo, atk",
        "optimize": 2,
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
		glob.glob("share\images\\*.png"))]
)
