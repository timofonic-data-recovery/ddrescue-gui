#!/usr/bin/env python
# -*- coding: utf-8 -*- 
# Unit tests for DDRescue-GUI Version 1.6.2
# This file is part of DDRescue-GUI.
# Copyright (C) 2013-2017 Hamish McIntyre-Bhatty
# DDRescue-GUI is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 3 or,
# at your option, any later version.
#
# DDRescue-GUI is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with DDRescue-GUI.  If not, see <http://www.gnu.org/licenses/>.

#Import modules.
import unittest
import wx
import subprocess
import re
import logging
import plistlib
import os
import time
import getopt
import sys
from bs4 import BeautifulSoup

#Global vars.
Version = "1.6.2"

#Custom made modules.
import GetDevInfo
import Tools

from GetDevInfo.getdevinfo import Main as DevInfoTools
from Tools.tools import Main as BackendTools

#Import test modules.
import Tests

from Tests import GetDevInfoTests
from Tests import BackendToolsTests

def usage():
    print("\nUsage: Tests.py [OPTION]\n\n")
    print("Options:\n")
    print("       -h, --help:                   Display this help text.")
    print("       -g, --getdevinfo:             Run tests for GetDevInfo module.")
    print("       -b, --backendtools:           Run tests for BackendTools module.")
    print("       -m, --main:                   Run tests for main file (DDRescue-GUI.py).")
    print("       -a, --all:                    Run all the tests. The default.\n")
    print("DDRescue-GUI "+Version+" is released under the GNU GPL Version 3")
    print("Copyright (C) Hamish McIntyre-Bhatty 2013-2017")

#Check all cmdline options are valid.
try:
    opts, args = getopt.getopt(sys.argv[1:], "hgbma", ["help", "getdevinfo", "backendtools", "main", "all"])

except getopt.GetoptError as err:
    #Invalid option. Show the help message and then exit.
    #Show the error.
    print(unicode(err))
    usage()
    sys.exit(2)

#Set up which tests to run based on options given.
TestSuites = [GetDevInfoTests, BackendToolsTests] #*** Set up full defaults when finished ***

for o, a in opts:
    if o in ["-g", "--getdevinfo"]:
        TestSuites = [GetDevInfoTests]
    elif o in ["-b", "--backendtools"]:
        TestSuites = [BackendToolsTests]
    elif o in ["-m", "--main"]:
        #TestSuites = [MainTests]
        assert False, "Not implemented yet"
    elif o in ["-a", "--all"]:
        TestSuites = [GetDevInfoTests, BackendToolsTests]
        #TestSuites.append(MainTests)
    elif o in ["-h", "--help"]:
        usage()
        sys.exit()
    else:
        assert False, "unhandled option"

#Set up the logger (silence all except critical logging messages).
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s: %(message)s', datefmt='%d/%m/%Y %I:%M:%S %p', level=logging.CRITICAL)
logger = logging

#Set up resource path and determine OS.
if "wxGTK" in wx.PlatformInfo:
    #Set the resource path to /usr/share/ddrescue-gui/
    RescourcePath = '/usr/share/ddrescue-gui'
    Linux = True

    #Check if we're running on Parted Magic.
    if os.uname()[1] == "PartedMagic":
        PartedMagic = True

    else:
        PartedMagic = False

elif "wxMac" in wx.PlatformInfo:
    try:
        #Set the resource path from an environment variable, as mac .apps can be found in various places.
        RescourcePath = os.environ['RESOURCEPATH']

    except KeyError:
        #Use '.' as the rescource path instead as a fallback.
        RescourcePath = "."

    Linux = False
    PartedMagic = False

#Setup custom-made modules (make global variables accessible inside the packages).
GetDevInfo.getdevinfo.subprocess = subprocess
GetDevInfo.getdevinfo.re = re
GetDevInfo.getdevinfo.logger = logger
GetDevInfo.getdevinfo.Linux = Linux
GetDevInfo.getdevinfo.plistlib = plistlib
GetDevInfo.getdevinfo.BeautifulSoup = BeautifulSoup

Tools.tools.wx = wx
Tools.tools.os = os
Tools.tools.subprocess = subprocess
Tools.tools.logger = logger
Tools.tools.logging = logging
Tools.tools.time = time
Tools.tools.Linux = Linux
Tools.tools.RescourcePath = RescourcePath

#Setup test modules.
GetDevInfoTests.DevInfoTools = DevInfoTools
GetDevInfoTests.GetDevInfo = GetDevInfo

BackendToolsTests.BackendTools = BackendTools
BackendToolsTests.Tools = Tools

if __name__ == "__main__":
    for SuiteModule in TestSuites:
        print("\n\n---------------------------- Tests for "+unicode(SuiteModule)+" ----------------------------\n\n")
        unittest.TextTestRunner(verbosity=2).run(unittest.TestLoader().loadTestsFromModule(SuiteModule))
