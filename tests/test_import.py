import os
import sys
import importlib

projpath = os.path.normpath(os.path.join(os.path.abspath(__file__), "../.."))
sys.path.insert(0, projpath)

import discordapi


def test_import():
    folderpath = os.path.join(projpath, "discordapi")
    files = os.listdir(folderpath)
    for module in ["." + module[:-3] for module in files
                   if module.endswith(".py") and "_" not in module]:

        module = importlib.import_module(module, "discordapi")
        all_list = getattr(module, "__all__", None)
        if all_list is not None:
            for obj in all_list:
                assert getattr(discordapi, obj, None) is not None
