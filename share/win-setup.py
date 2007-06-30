# NOTICE: This script is not finished and does not work correctly.

from distutils.core import setup
import py2exe

# Copiar etc, share, lib de GTK a la cosa. No funciona con un all-in-one
# Tampoco copia imagenes.
# zipfile = None

setup (
	console=['itaka.py'],
	name = 'Itaka',
    	description = 'On-demand screenshooting server',
    	version = '1.1',
    	author='Marc E.',
    	author_email='santusmarc@gmail.com',
    	url='http://itaka.jardinpresente.com.ar',
	
	options = {
        	'py2exe': {
                      'packages':'encodings',
                      'includes': 'cairo, pango, pangocairo, atk, gobject',
                  }
        }
)
