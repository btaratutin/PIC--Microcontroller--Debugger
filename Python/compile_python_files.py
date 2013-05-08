from distutils.core import setup
import py2exe

setup(name="Olin Datalogger Interface",
      version="1.0",
      author="Jason Curtis & Boris Taratutin",
      zipfile=None,
      data_files=[('',["usb.dll", "MSVCP90.dll", "readme.txt"])],
      scripts=["datalogGUI.py"],
      windows=[{"script": "datalogGUI.py"}],
      options={"py2exe": {"compressed": True, "includes": ["sip","os"],
                      "bundle_files":1, "optimize":2}})
