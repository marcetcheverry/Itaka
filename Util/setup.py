from distutils.core import setup
import py2exe

setup(name='Distutils',
      version='1.0',
      description='Itaka Screenshoot Server',
      author='Marc E.',
      author_email='m4rccd@yahoo.com',
      url='http://itaka.sourceforge.net',
     )

setup(console=["itaka.py"],
      data_files=[("modules",
                   ["itaka_globals.py", "__init__.py"]),
                  ("images",
                   glob.glob("images\\*.png"))],
)
zipfile=None
