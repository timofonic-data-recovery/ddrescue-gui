#!/usr/bin/env python
# -*- coding: utf-8 -*- 
# DDRescue-GUI Main Script Version 1.6.2
# This file is part of DDRescue-GUI.
# Copyright (C) 2013-2016 Hamish McIntyre-Bhatty
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

#Do future imports to prepare to support python 3. Use unicode strings rather than ASCII strings, as they fix potential problems.
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

#Import other modules
import wx
from wx.animate import Animation
from wx.animate import AnimationCtrl
import wx.lib.stattext
import wx.lib.statbmp
import threading
import getopt
import logging
import time
import subprocess
import re
import os
import sys
import plistlib
import traceback
from bs4 import BeautifulSoup

#Define the version number and the release date as global variables.
Version = "1.6.2"
ReleaseDate = "13/12/2016"
SessionEnding = False

def usage():
    print("\nUsage: DDRescue-GUI.py [OPTION]\n\n")
    print("Options:\n")
    print("       -h, --help:                   Show this help message")
    print("       -q, --quiet:                  Show only warnings, errors and critical errors in the log file. Very unhelpful for debugging, and not recommended.")
    print("       -v, --verbose:                Enable logging of info messages, as well as warnings, errors and critical errors.")
    print("                                     Not the best for debugging, but acceptable if there is little disk space.")
    print("       -d, --debug:                  Log lots of boring debug messages, as well as information, warnings, errors and critical errors. Usually used for diagnostic purposes.")
    print("                                     The default, as it's very helpful if problems are encountered, and the user needs help\n")
    print("DDRescue-GUI "+Version+" is released under the GNU GPL Version 3")
    print("Copyright (C) Hamish McIntyre-Bhatty 2013-2016")

#Determine if running on Linux or Mac.
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

#Check all cmdline options are valid.
try:
    opts, args = getopt.getopt(sys.argv[1:], "hqvd", ["help", "quiet", "verbose", "debug"])

except getopt.GetoptError as err:
    #Invalid option. Show the help message and then exit.
    #Show the error.
    print(unicode(err))
    usage()
    sys.exit(2)

#Determine the option(s) given, and change the level of logging based on cmdline options.
loggerLevel = logging.DEBUG

for o, a in opts:
    if o in ["-q", "--quiet"]:
        loggerLevel = logging.WARNING
    elif o in ["-v", "--verbose"]:
        loggerLevel = logging.INFO
    elif o in ["-d", "--debug"]:
        loggerLevel = logging.DEBUG
    elif o in ["-h", "--help"]:
        usage()
        sys.exit()
    else:
        assert False, "unhandled option"

#If we aren't running as root, relaunch immediately.
if os.geteuid() != 0:
    #Relaunch as root.
    execfile(RescourcePath+"/AuthenticationDialog.py")
    sys.exit("\nSorry, DDRescue-GUI must be run with root (superuser) privileges.\nRestarting as root...")

#Set up logging with default logging mode as debug.
logger = logging.getLogger('DDRescue-GUI '+Version)
logging.basicConfig(filename='/tmp/ddrescue-gui.log', format='%(asctime)s - %(name)s - %(levelname)s: %(message)s', datefmt='%d/%m/%Y %I:%M:%S %p')
logger.setLevel(loggerLevel)

#Log which OS we're running on (helpful for debugging).
if Linux:
    logger.debug("Detected Linux...")

    if PartedMagic:
        logger.debug("Detected Parted Magic...")

else:
    logger.debug("Detected Mac OS X...")

#Import custom-made modules
import GetDevInfo
import Tools

from GetDevInfo.getdevinfo import Main as DevInfoTools
from Tools.tools import Main as BackendTools

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

#Begin Disk Information Handler thread.
class GetDiskInformation(threading.Thread):
    def __init__(self, ParentWindow):
        """Initialize and start the thread."""
        self.ParentWindow = ParentWindow
        threading.Thread.__init__(self)
        self.start()

    def run(self):
        """Get Disk Information and return it as a list with embedded lists"""
        #Use a module I've written to collect data about connected Disks, and return it.
        wx.CallAfter(self.ParentWindow.ReceiveDiskInfo, DevInfoTools().GetInfo())

#End Disk Information Handler thread.
#Begin Starter Class
class MyApp(wx.App):
    def OnInit(self):
        Splash = ShowSplash()
        Splash.Show()
        return True

    def MacReopenApp(self):
        """Called when the doc icon is clicked, shows the top-level window again even if it's minimised"""
        self.GetTopWindow().Raise()

#End Starter Class
#Begin splash screen
class ShowSplash(wx.SplashScreen):
    def __init__(self, parent=None):
        """Prepare and display a splash screen"""
        #Convert the image to a bitmap.
        Splash = wx.Image(name = RescourcePath+"/images/ddgoestotherescue.jpg").ConvertToBitmap()

        self.AlreadyExited = False

        #Display the splash screen.
        wx.SplashScreen.__init__(self, Splash, wx.SPLASH_CENTRE_ON_SCREEN | wx.SPLASH_TIMEOUT, 1500, parent)
        self.Bind(wx.EVT_CLOSE, self.OnExit)

        #Make sure it's painted, which fixes the problem with the previous tempramental splash screen.
        wx.Yield()

    def OnExit(self, Event=None):
        """Close the splash screen and start MainWindow"""
        self.Hide()

        if self.AlreadyExited == False:
            #Stop this from executing twice when the splash is clicked.
            self.AlreadyExited = True
            MainFrame = MainWindow()
            app.SetTopWindow(MainFrame)
            MainFrame.Show(True)

            #Skip handling the event so the main frame starts.
            Event.Skip()

#End splash screen
#Begin Custom wx.TextCtrl Class.
class CustomTextCtrl(wx.TextCtrl):
    def __init__(self, parent, id, value, style):
        """Initialise the custom wx.TextCtrl"""
        wx.TextCtrl.__init__(self, parent, id, value=value, style=style)

    def CustomPositionToXY(self, InsertionPoint):
        """A custom version of wx.TextCtrl.PositionToXY() that works on OS X (the built-in one isn't implemented on OS X)."""
        #Count the number and position of newline characters.
        Text = self.GetRange(0, InsertionPoint)

        NewLines = [0] #Count the start of the text as a newline.
        Counter = 0
        for Char in Text:
            Counter += 1

            if Char == "\n":
                NewLines.append(Counter)

        #Find the last newline before our insertion point.
        for NewLine in NewLines:
            if NewLines.index(NewLine)+1 == len(NewLines) or NewLine == InsertionPoint:
                #This is the last newline in the text, or the newline at our insertion point, and therefore the one we want.
                LastNewLine = NewLine
                break

            elif NewLine < InsertionPoint:
                pass

            else:
                #When this is triggered, the previous newline (last iteration of the loop) is the one we want.
                index = NewLines.index(NewLine)
                LastNewLine = NewLines[index-1]
                break

        #Figure out what column we're in (how many chars after the last newline).
        Column = InsertionPoint - LastNewLine

        #Figure out which line we're on (the number of the last newline).
        Row = NewLines.index(LastNewLine)

        return (Column,Row)

    def CustomXYToPosition(self, Column, Row):
        """A custom version of wx.TextCtrl.XYToPosition() that works on OS X (the built-in one isn't implemented on OS X).
        This is also helpful for Linux because the built-in one has a quirk when you're at the end of the text and it always returns -1"""
        #Count the number and position of newline characters.
        Text = self.GetValue()

        NewLines = [0] #Count the start of the text as a newline.
        Counter = 0
        for Char in Text:
            Counter += 1

            if Char == "\n":
                NewLines.append(Counter)

        #Get the last newline.
        LastNewLine = NewLines[Row]

        #Our position should be that number plus our column.
        Position = LastNewLine + Column

        return Position

#End Custom wx.TextCtrl Class.
#Begin Main Window   
class MainWindow(wx.Frame):
    def __init__(self):
        """Initialize MainWindow"""
        wx.Frame.__init__(self, None, title="DDRescue-GUI", size=(936,360), style=wx.DEFAULT_FRAME_STYLE)
        self.Panel = wx.Panel(self)
        self.SetClientSize(wx.Size(936,360))

        print("DDRescue-GUI Version "+Version+" Starting...")
        logger.info("DDRescue-GUI Version "+Version+" Starting...")
        logger.info("Release date: "+ReleaseDate)
        logger.info("Running on Python version: "+unicode(sys.version_info)+"...")
        logger.info("Running on wxPython version: "+wx.version()+"...")

        #Set the frame's icon.
        global AppIcon
        AppIcon = wx.Icon(RescourcePath+"/images/Logo.png", wx.BITMAP_TYPE_PNG)
        wx.Frame.SetIcon(self, AppIcon)

        #Set some variables
        logger.debug("MainWindow().__init__(): Setting some essential variables...")
        self.SetVars()
        self.Starting = True

        #Create a Statusbar in the bottom of the window and set the text.
        logger.debug("MainWindow().__init__(): Creating Status Bar...")
        self.MakeStatusBar()

        #Add text
        logger.debug("MainWindow().__init__(): Creating text...")
        self.CreateText()

        #Create some buttons
        logger.debug("MainWindow().__init__(): Creating buttons...")
        self.CreateButtons()

        #Create the choiceboxes.
        logger.debug("MainWindow().__init__(): Creating choiceboxes...")
        self.CreateChoiceBoxes()

        #Create other widgets.
        logger.debug("MainWindow().__init__(): Creating all other widgets...")
        self.CreateOtherWidgets()

        #Create the menus.
        logger.debug("MainWindow().__init__(): Creating menus...")
        self.CreateMenus()

        #Update the Disk info.
        logger.debug("MainWindow().__init__(): Updating Disk info...")
        self.GetDiskInfo()

        #Set up sizers.
        logger.debug("MainWindow().__init__(): Setting up sizers...")
        self.SetupSizers()

        #Bind all events.
        logger.debug("MainWindow().__init__(): Binding events...")
        self.BindEvents()

        #Make sure the window is displayed properly.
        self.OnDetailedInfo()
        self.OnTerminalOutput()
        self.ListCtrl.SetColumnWidth(0, 150)

        #Call Layout() on self.Panel() to ensure it displays properly.
        self.Panel.Layout()

        logger.info("MainWindow().__init__(): Ready. Waiting for events...")

    def SetVars(self):
        """Set some essential variables"""
        global Settings
        Settings = {}

        #Basic settings and info.
        Settings["InputFile"] = None
        Settings["OutputFile"] = None
        Settings["LogFile"] = None
        Settings["RecoveringData"] = False
        Settings["CheckedSettings"] = False

        #DDRescue's options.
        Settings["DirectAccess"] = "-d"
        Settings["OverwriteOutputFile"] = ""
        Settings["Reverse"] = ""
        Settings["Preallocate"] = ""
        Settings["NoSplit"] = ""
        Settings["BadSectorRetries"] = "-r 2"
        Settings["MaxErrors"] = ""
        Settings["ClusterSize"] = "-c 128"

        #Local to this function.
        self.AbortedRecovery = False
        self.RunTimeSecs = 0

        #Set the wildcards and make it easy for the user to find his/her home directory (helps make DDRescue-GUI more user friendly).
        if Linux:
            self.InputWildcard = "SATA HDDs/USB Drives|sd*|Optical Drives|sr*|Floppy Drives|fd*|IMG Disk Image (*.img)|*.img|ISO (CD/DVD) Disk Image (*.iso)|*.iso|All Files/Disks (*)|*"
            self.OutputWildcard = "IMG Disk Image (*.img)|*.img|ISO (CD/DVD) Disk Image (*.iso)|*.iso|SATA HDDs/USB Drives|sd*|Floppy Drives|fd*|All Files/Disks (*)|*"
            self.UserHomeDir = "/home"

        else:
            self.InputWildcard = "Disk Drives|disk*|IMG Disk Image (*.img)|*.img|DMG Disk Image (*.dmg)|*.dmg|ISO (CD/DVD) Disk Image (*.iso)|*.iso|All Files/Disks (*)|*"
            self.OutputWildcard = "IMG Disk Image (*.img)|*.img|DMG Disk Image (*.dmg)|*.dmg|ISO (CD/DVD) Disk Image (*.iso)|*.iso|All Files/Disks (*)|*"
            self.UserHomeDir = "/Users"

    def MakeStatusBar(self):
        """Create and set up a statusbar"""
        self.StatusBar = self.CreateStatusBar()
        self.StatusBar.SetFieldsCount(2)
        self.StatusBar.SetStatusWidths([-1, 150])
        self.StatusBar.SetStatusText("Ready.", 0)
        self.StatusBar.SetStatusText("v"+Version+" ("+ReleaseDate+")", 1)

    def CreateText(self):
        """Create all text for MainWindow"""
        self.TitleText = wx.StaticText(self.Panel, -1, "Welcome to DDRescue-GUI!")
        self.InputText = wx.StaticText(self.Panel, -1, "Image Source:")
        self.LogFileText = wx.StaticText(self.Panel, -1, "Recovery Log File:")
        self.OutputText = wx.StaticText(self.Panel, -1, "Image Destination:") 

        #Also create special text for showing and hiding recovery info and terminal output.
        self.DetailedInfoText = wx.lib.stattext.GenStaticText(self.Panel, -1, "Detailed Info")
        self.TerminalOutputText = wx.lib.stattext.GenStaticText(self.Panel, -1, "Terminal Output")

        #And some text for basic recovery information.
        self.TimeElapsedText = wx.StaticText(self.Panel, -1, "Time Elapsed:")
        self.TimeRemainingText = wx.StaticText(self.Panel, -1, "Estimated Time Remaining:")

    def CreateButtons(self):
        """Create all buttons for MainWindow"""
        self.SettingsButton = wx.Button(self.Panel, -1, "Settings")
        self.UpdateDiskInfoButton = wx.Button(self.Panel, -1, "Update Disk Info")          
        self.ShowDiskInfoButton = wx.Button(self.Panel, -1, "Disk Information")
        self.ControlButton = wx.Button(self.Panel, -1, "Start")

    def CreateChoiceBoxes(self):
        """Create all choiceboxes for MainWindow"""
        self.InputChoiceBox = wx.Choice(self.Panel, -1, choices=['-- Please Select --', 'Select a File/Disk'])
        self.LogChoiceBox = wx.Choice(self.Panel, -1, choices=['-- Please Select --', 'Select a File', 'None (not recommended)'])
        self.OutputChoiceBox = wx.Choice(self.Panel, -1, choices=['-- Please Select --', 'Select a File/Disk'])

        #Set the default value.
        self.InputChoiceBox.SetStringSelection("-- Please Select --")
        self.LogChoiceBox.SetStringSelection("-- Please Select --")
        self.OutputChoiceBox.SetStringSelection("-- Please Select --")

    def CreateOtherWidgets(self):
        """Create all other widgets for MainWindow"""
        #Create the animation for the throbber.
        throb = wx.animate.Animation(RescourcePath+"/images/Throbber.gif")
        self.Throbber = wx.animate.AnimationCtrl(self.Panel, -1, throb)
        self.Throbber.SetUseWindowBackgroundColour(True)
        self.Throbber.SetInactiveBitmap(wx.Bitmap(RescourcePath+"/images/ThrobberRest.png", wx.BITMAP_TYPE_PNG))
        self.Throbber.SetClientSize(wx.Size(30,30))

        #Create the list control for the detailed info.
        self.ListCtrl = wx.ListCtrl(self.Panel, -1, style=wx.LC_REPORT|wx.BORDER_SUNKEN|wx.LC_VRULES)
        self.ListCtrl.InsertColumn(col=0, heading="Category", format=wx.LIST_FORMAT_CENTRE, width=150)
        self.ListCtrl.InsertColumn(col=1, heading="Value", format=wx.LIST_FORMAT_CENTRE, width=-1)
        self.ListCtrl.SetMinSize(wx.Size(50, 240))

        #Create a text control for terminal output.
        self.OutputBox = CustomTextCtrl(self.Panel, -1, "", style=wx.TE_MULTILINE|wx.TE_READONLY|wx.TE_WORDWRAP)
        self.OutputBox.SetBackgroundColour((0,0,0))
        self.OutputBox.SetDefaultStyle(wx.TextAttr(wx.WHITE))
        self.OutputBox.SetMinSize(wx.Size(50, 240))

        #Create the arrows.
        img1 = wx.Image(RescourcePath+"/images/ArrowDown.png", wx.BITMAP_TYPE_PNG)
        img2 = wx.Image(RescourcePath+"/images/ArrowRight.png", wx.BITMAP_TYPE_PNG)
        self.DownArrowImage = wx.BitmapFromImage(img1)
        self.RightArrowImage = wx.BitmapFromImage(img2)

        self.Arrow1 = wx.lib.statbmp.GenStaticBitmap(self.Panel, -1, self.DownArrowImage)
        self.Arrow2 = wx.lib.statbmp.GenStaticBitmap(self.Panel, -1, self.DownArrowImage)

        #Create the progress bar.
        self.ProgressBar = wx.Gauge(self.Panel, -1, 5000)

    def SetupSizers(self):
        """Setup sizers for MainWindow"""
        #Make the main boxsizer.
        self.MainSizer = wx.BoxSizer(wx.VERTICAL)

        #Make the file choices sizer.
        FileChoicesSizer = wx.BoxSizer(wx.HORIZONTAL)

        #Make the input sizer.
        InputSizer = wx.BoxSizer(wx.VERTICAL)

        #Add items to the input sizer.
        InputSizer.Add(self.InputText, 1, wx.TOP|wx.BOTTOM|wx.ALIGN_CENTER, 10)
        InputSizer.Add(self.InputChoiceBox, 1, wx.BOTTOM|wx.ALIGN_CENTER, 10)

        #Make the log sizer.
        LogSizer = wx.BoxSizer(wx.VERTICAL)

        #Add items to the log sizer.
        LogSizer.Add(self.LogFileText, 1, wx.TOP|wx.BOTTOM|wx.ALIGN_CENTER, 10)
        LogSizer.Add(self.LogChoiceBox, 1, wx.BOTTOM|wx.ALIGN_CENTER, 10)

        #Make the output sizer.
        OutputSizer = wx.BoxSizer(wx.VERTICAL)

        #Add items to the output sizer.
        OutputSizer.Add(self.OutputText, 1, wx.TOP|wx.BOTTOM|wx.ALIGN_CENTER, 10)
        OutputSizer.Add(self.OutputChoiceBox, 1, wx.BOTTOM|wx.ALIGN_CENTER, 10)

        #Add items to the file choices sizer.
        FileChoicesSizer.Add(InputSizer, 1, wx.ALIGN_CENTER)
        FileChoicesSizer.Add(LogSizer, 1, wx.ALIGN_CENTER)
        FileChoicesSizer.Add(OutputSizer, 1, wx.ALIGN_CENTER)

        #Make the button sizer.
        ButtonSizer = wx.BoxSizer(wx.HORIZONTAL)

        #Add items to the button sizer.
        ButtonSizer.Add(self.SettingsButton, 1, wx.RIGHT|wx.ALIGN_CENTER|wx.EXPAND, 10)
        ButtonSizer.Add(self.UpdateDiskInfoButton, 1, wx.ALIGN_CENTER|wx.EXPAND, 10)
        ButtonSizer.Add(self.ShowDiskInfoButton, 1, wx.LEFT|wx.ALIGN_CENTER|wx.EXPAND, 10)

        #Make the throbber sizer.
        ThrobberSizer = wx.BoxSizer(wx.HORIZONTAL)

        #Add items to the throbber sizer.
        ThrobberSizer.Add(self.Arrow1, 0, wx.LEFT|wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL, 10)
        ThrobberSizer.Add(self.DetailedInfoText, 1, wx.LEFT|wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL, 10)
        ThrobberSizer.Add(self.Throbber, 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER|wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE, 10)
        ThrobberSizer.Add(self.Arrow2, 0, wx.RIGHT|wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 10)
        ThrobberSizer.Add(self.TerminalOutputText, 1, wx.RIGHT|wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 10)

        #Make the info sizer.
        self.InfoSizer = wx.BoxSizer(wx.HORIZONTAL)

        #Add items to the info sizer.
        self.InfoSizer.Add(self.ListCtrl, 1, wx.RIGHT|wx.LEFT|wx.ALIGN_CENTER|wx.EXPAND, 22)
        self.InfoSizer.Add(self.OutputBox, 1, wx.RIGHT|wx.LEFT|wx.ALIGN_CENTER|wx.EXPAND, 22)

        #Make the info text sizer.
        InfoTextSizer = wx.BoxSizer(wx.HORIZONTAL)

        #Add items to the info text sizer.
        InfoTextSizer.Add(self.TimeElapsedText, 1, wx.RIGHT|wx.ALIGN_CENTER, 22)
        InfoTextSizer.Add(self.TimeRemainingText, 1, wx.LEFT|wx.ALIGN_CENTER, 22)

        #Arrow1 is horizontal when starting, so hide self.ListCtrl.
        self.InfoSizer.Detach(self.ListCtrl)
        self.ListCtrl.Hide()

        #Arrow2 is horizontal when starting, so hide self.OutputBox.
        self.InfoSizer.Detach(self.OutputBox)
        self.OutputBox.Hide()

        #Insert some empty space. (Fixes a GUI bug in wxpython > 2.8.11.1)
        self.InfoSizer.Add((1,1), 1, wx.EXPAND)

        #Make the progress sizer.
        self.ProgressSizer = wx.BoxSizer(wx.HORIZONTAL)

        #Add items to the progress sizer.
        self.ProgressSizer.Add(self.ProgressBar, 1, wx.ALL|wx.ALIGN_CENTER, 10)
        self.ProgressSizer.Add(self.ControlButton, 0, wx.ALL|wx.ALIGN_RIGHT, 10)

        #Add items to the main sizer.
        self.MainSizer.Add(self.TitleText, 0, wx.TOP|wx.ALIGN_CENTER, 10)
        self.MainSizer.Add(wx.StaticLine(self.Panel), 0, wx.ALL|wx.EXPAND, 10)
        self.MainSizer.Add(FileChoicesSizer, 0, wx.ALL|wx.ALIGN_CENTER|wx.EXPAND, 10)
        self.MainSizer.Add(wx.StaticLine(self.Panel), 0, wx.ALL|wx.EXPAND, 10)
        self.MainSizer.Add(ButtonSizer, 0, wx.ALL|wx.ALIGN_CENTER|wx.EXPAND, 10)
        self.MainSizer.Add(wx.StaticLine(self.Panel), 0, wx.TOP|wx.EXPAND, 10)
        self.MainSizer.Add(ThrobberSizer, 0, wx.ALL|wx.ALIGN_CENTER|wx.EXPAND, 5)
        self.MainSizer.Add(self.InfoSizer, 1, wx.TOP|wx.BOTTOM|wx.ALIGN_CENTER|wx.EXPAND, 10)
        self.MainSizer.Add(InfoTextSizer, 0, wx.ALL|wx.ALIGN_CENTER|wx.EXPAND, 10)
        self.MainSizer.Add(self.ProgressSizer, 0, wx.TOP|wx.BOTTOM|wx.ALIGN_CENTER|wx.EXPAND, 10)

        #Get the sizer set up for the frame.
        self.Panel.SetSizer(self.MainSizer)
        self.MainSizer.SetMinSize(wx.Size(936,360))
        self.MainSizer.SetSizeHints(self)

    def CreateMenus(self):
        """Create the menus"""
        FileMenu = wx.Menu()
        EditMenu = wx.Menu()
        ViewMenu = wx.Menu()
        HelpMenu = wx.Menu() 
   
        #Add Menu Items.
        self.MenuExit = FileMenu.Append(wx.ID_ANY, "&Quit", "Close DDRescue-GUI")
        self.MenuSettings = EditMenu.Append(wx.ID_ANY, "&Settings", "Recovery settings")
        self.MenuDiskInfo = ViewMenu.Append(wx.ID_ANY,"&Disk Information", "Information about all detected Disks")
        self.MenuPrivacyPolicy = ViewMenu.Append(wx.ID_ANY,"&Privacy Policy", "View DDRescue-GUI's privacy policy")
        self.MenuAbout = HelpMenu.Append(wx.ID_ANY, "&About DDRescue-GUI", "Information about DDRescue-GUI")

        #Creating the menubar.
        self.MenuBar = wx.MenuBar()

        #Adding menus to the MenuBar
        self.MenuBar.Append(FileMenu,"&File")
        self.MenuBar.Append(EditMenu,"&Edit")
        self.MenuBar.Append(ViewMenu,"&View")
        self.MenuBar.Append(HelpMenu,"&Help")

        #Adding the MenuBar to the Frame content.
        self.SetMenuBar(self.MenuBar)

    def BindEvents(self): 
        """Bind all events for MainWindow"""
        #Menus.
        self.Bind(wx.EVT_MENU, self.ShowSettings, self.MenuSettings)
        self.Bind(wx.EVT_MENU, self.OnAbout, self.MenuAbout)
        self.Bind(wx.EVT_MENU, self.ShowDevInfo, self.MenuDiskInfo)
        self.Bind(wx.EVT_MENU, self.ShowPrivacyPolicy, self.MenuPrivacyPolicy)

        #Choiceboxes.
        self.Bind(wx.EVT_CHOICE, self.SetInputFile, self.InputChoiceBox)
        self.Bind(wx.EVT_CHOICE, self.SetOutputFile, self.OutputChoiceBox)
        self.Bind(wx.EVT_CHOICE, self.SetLogFile, self.LogChoiceBox)

        #Buttons.
        self.Bind(wx.EVT_BUTTON, self.OnControlButton, self.ControlButton)
        self.Bind(wx.EVT_BUTTON, self.GetDiskInfo, self.UpdateDiskInfoButton)
        self.Bind(wx.EVT_BUTTON, self.ShowSettings, self.SettingsButton)
        self.Bind(wx.EVT_BUTTON, self.ShowDevInfo, self.ShowDiskInfoButton)

        #Text.
        self.DetailedInfoText.Bind(wx.EVT_LEFT_DOWN, self.OnDetailedInfo)
        self.TerminalOutputText.Bind(wx.EVT_LEFT_DOWN, self.OnTerminalOutput)

        #Prevent focus on Output Box.
        self.OutputBox.Bind(wx.EVT_SET_FOCUS, self.FocusOnControlButton)

        #Images.
        self.Arrow1.Bind(wx.EVT_LEFT_DOWN, self.OnDetailedInfo)
        self.Arrow2.Bind(wx.EVT_LEFT_DOWN, self.OnTerminalOutput)

        #Size events.
        self.Bind(wx.EVT_SIZE, self.OnSize)

        #OnExit events.
        self.Bind(wx.EVT_END_SESSION, self.SessionEnding)
        self.Bind(wx.EVT_MENU, self.OnExit, self.MenuExit)
        self.Bind(wx.EVT_CLOSE, self.OnExit)

    def FocusOnControlButton(self, Event=None):
        """Focus on the control button instead of the TextCtrl, and reset the insertion point back after 30 milliseconds, preventing the user from changing the insertion point and messing the formatting up."""
        #Just a slightly hacky way of trying to make sure the user can't change the insertion point! Works unless you start doing silly stuff like tapping on the output box constantly :)
        self.ControlButton.SetFocus()
        InsertionPoint = self.OutputBox.GetInsertionPoint()
        wx.CallLater(30, self.OutputBox.SetInsertionPoint, InsertionPoint)

    def OnSize(self, Event=None):
        """Auto resize the ListCtrl columns"""
        #Force the width and height of the ListCtrl to be the right size, as the sizer won't shrink it on wxpython > 2.8.12.1.
        #Get the width and height of the frame.
        Width, Height = self.GetClientSizeTuple()

        #Calculate the correct width for the ListCtrl.
        if self.OutputBox.IsShown():
            ListCtrlWidth = (Width - 88)//2

        else:
            ListCtrlWidth = (Width - 44)

        #Set the size.
        self.ListCtrl.SetColumnWidth(1, ListCtrlWidth - 150)
        self.ListCtrl.SetClientSize(wx.Size(ListCtrlWidth, 240))

        if Event != None:
            Event.Skip()

    def OnDetailedInfo(self, Event=None):
        """Show/Hide the detailed info, and rotate the arrow"""
        #Get the width and height of the frame.
        Width, Height = self.GetClientSizeTuple()

        if self.ListCtrl.IsShown() or self.Starting:
            self.Arrow1.SetBitmap(self.RightArrowImage)

            #Arrow1 is now horizontal, so hide self.ListCtrl.
            self.InfoSizer.Detach(self.ListCtrl)
            self.ListCtrl.Hide()

            if self.OutputBox.IsShown() == False:
                self.SetClientSize(wx.Size(Width,360))
                #Insert some empty space.
                self.InfoSizer.Add((1,1), 1, wx.EXPAND)

        else:
            self.Arrow1.SetBitmap(self.DownArrowImage)

            #Arrow1 is now vertical, so show self.ListCtrl2
            if self.OutputBox.IsShown() == False:
                #Remove the empty space.
                self.InfoSizer.Clear()

            self.InfoSizer.Insert(0, self.ListCtrl, 1, wx.RIGHT|wx.LEFT|wx.ALIGN_CENTER|wx.EXPAND, 22)
            self.ListCtrl.Show()
            self.SetClientSize(wx.Size(Width,600))

        #Call Layout() on self.Panel() and self.OnSize() to ensure it displays properly.
        self.OnSize()
        self.Panel.Layout()
        self.MainSizer.SetSizeHints(self)

    def OnTerminalOutput(self, Event=None):
        """Show/Hide the terminal output, and rotate the arrow"""
        #Get the width and height of the frame.
        Width, Height = self.GetClientSizeTuple()

        if self.OutputBox.IsShown() or self.Starting:
            self.Arrow2.SetBitmap(self.RightArrowImage)

            #Arrow2 is now horizontal, so hide self.OutputBox.
            self.InfoSizer.Detach(self.OutputBox)
            self.OutputBox.Hide()

            if self.ListCtrl.IsShown() == False:
                self.SetClientSize(wx.Size(Width,360))
                #Insert some empty space.
                self.InfoSizer.Add((1,1), 1, wx.EXPAND)

        else:
            self.Arrow2.SetBitmap(self.DownArrowImage)

            #Arrow2 is now vertical, so show self.OutputBox.
            if self.ListCtrl.IsShown():
                self.InfoSizer.Insert(1, self.OutputBox, 1, wx.RIGHT|wx.LEFT|wx.ALIGN_CENTER|wx.EXPAND, 22)

            else:
                #Remove the empty space.
                self.InfoSizer.Clear()
                self.InfoSizer.Insert(0, self.OutputBox, 1, wx.RIGHT|wx.LEFT|wx.ALIGN_CENTER|wx.EXPAND, 22)

            self.OutputBox.Show()
            self.SetClientSize(wx.Size(Width,600))

        #Call Layout() on self.Panel() and self.OnSize to ensure it displays properly.
        self.OnSize()
        self.Panel.Layout()
        self.MainSizer.SetSizeHints(self)

    def GetDiskInfo(self, Event=None):
        """Call the thread to get Disk info, disable the update button, and start the throbber"""
        logger.info("MainWindow().GetDiskInfo(): Getting new Disk information...")
        self.UpdateStatusBar("Getting new Disk information... Please wait...")

        #Disable stuff to prevent problems.
        self.SettingsButton.Disable()
        self.UpdateDiskInfoButton.Disable()
        self.ShowDiskInfoButton.Disable()
        self.InputChoiceBox.Disable()
        self.OutputChoiceBox.Disable()
        self.MenuDiskInfo.Enable(False)
        self.MenuSettings.Enable(False)

        #Call the thread and get the throbber going.
        GetDiskInformation(self)
        self.Throbber.Play()

    def ReceiveDiskInfo(self, Info):
        """Get new Disk info and to call the function that updates the choiceboxes"""
        logger.info("MainWindow().ReceiveDiskInfo(): Getting new Disk information...")
        global DiskInfo
        DiskInfo = Info

        #Update the file choices.
        self.UpdateFileChoices()
        self.Starting = False

        #Stop the throbber and enable stuff again.
        self.Throbber.Stop()

        self.SettingsButton.Enable()
        self.UpdateDiskInfoButton.Enable()
        self.ShowDiskInfoButton.Enable()
        self.InputChoiceBox.Enable()
        self.OutputChoiceBox.Enable()
        self.MenuDiskInfo.Enable()
        self.MenuSettings.Enable()

    def UpdateFileChoices(self):
        """Update the Disk entries in the choiceboxes"""
        logger.info("MainWindow().UpdateFileChoices(): Updating the GUI with the new Disk information...")

        if self.Starting:
            #We are starting up, so do some extra stuff.
            #Prepare some choiceboxes using the newly created Disk list.
            logger.info("MainWindow().UpdateFileChoices(): Preparing choiceboxes...")

            #Make note that there are no custom selections yet, because we haven't even finished the startup routine yet!
            self.CustomInputPathsList = {}
            self.CustomOutputPathsList = {}
            self.CustomLogPaths = {}

        #Keep the user's current selections and any custom paths added to the choiceboxes while we update them.
        logger.info("MainWindow().UpdateFileChoices(): Updating choiceboxes...")

        #Grab Current selection.
        CurrentInputStringSelection = self.InputChoiceBox.GetStringSelection()
        CurrentOutputStringSelection = self.OutputChoiceBox.GetStringSelection()

        #Set all the items.
        self.InputChoiceBox.SetItems(['-- Please Select --', 'Select a File/Disk'] + sorted(DiskInfo.keys() + self.CustomInputPathsList.keys()))
        self.OutputChoiceBox.SetItems(['-- Please Select --', 'Select a File/Disk'] + sorted(DiskInfo.keys() + self.CustomOutputPathsList.keys()))

        #Set the current selections again, if we can (if the selection is a Disk, it may have been removed).
        if self.InputChoiceBox.FindString(CurrentInputStringSelection) != -1:
            self.InputChoiceBox.SetStringSelection(CurrentInputStringSelection)

        else:
            self.InputChoiceBox.SetStringSelection('-- Please Select --')

        if self.OutputChoiceBox.FindString(CurrentOutputStringSelection) != -1:
            self.OutputChoiceBox.SetStringSelection(CurrentOutputStringSelection)

        else:
            self.OutputChoiceBox.SetStringSelection('-- Please Select --')

        #Notify the user with the statusbar.
        self.UpdateStatusBar("Ready.")

    def SetInputFile(self, Event=None):
        """Get the input file/Disk and set a variable to the selected value"""
        logger.debug("MainWindow().SelectInputFile(): Getting user selection...")
        Settings["InputFile"] = self.InputChoiceBox.GetStringSelection()

        if Settings["InputFile"] == "Select a File/Disk":
            InputFileDlg = wx.FileDialog(self.Panel, "Select Input File/Disk...", defaultDir="/dev", wildcard=self.InputWildcard, style=wx.OPEN)

            #Change the default dir on OS X.
            if Linux == False:
                InputFileDlg.SetDirectory("/Users")

            if InputFileDlg.ShowModal() == wx.ID_OK:
                Settings["InputFile"] = InputFileDlg.GetPath()
                logger.info("MainWindow().SelectInputFile(): User selected custom file: "+Settings["InputFile"]+"...")

                #If it's in the dictionary or in DiskInfo, don't add it.
                if BackendTools().FindDataValueInDict(self.CustomInputPathsList, Settings["InputFile"]):
                    #Set the selection using the unique key.
                    self.InputChoiceBox.SetStringSelection(BackendTools().CreateUniqueKey(self.CustomInputPathsList, Settings["InputFile"], 30))

                elif Settings["InputFile"] in DiskInfo.keys():
                    #No need to add it or anything.
                    self.InputChoiceBox.SetStringSelection(Settings["InputFile"])

                else:
                    #Get a unqiue key for the dictionary using the tools function.
                    Key = BackendTools().CreateUniqueKey(self.CustomInputPathsList, Settings["InputFile"], 30)

                    self.CustomInputPathsList[Key] = Settings["InputFile"]
                    self.InputChoiceBox.Append(Key)
                    self.InputChoiceBox.SetStringSelection(Key)

            else:
                logger.info("MainWindow().SelectInputFile(): User declined custom file selection. Resetting InputFile...")
                Settings["InputFile"] = None
                self.InputChoiceBox.SetStringSelection("-- Please Select --")

        elif Settings["InputFile"] not in [None, "-- Please Select --"] and Settings["InputFile"] == Settings["OutputFile"]:
            logger.warning("MainWindow().SelectInputFile(): InputFile equals OutputFile!, resetting to None and warning user...")
            dlg = wx.MessageDialog(self.Panel, "You can't use the same disk/file as both the source and the destination!", 'DDRescue-GUI - Error!', wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            Settings["InputFile"] = None
            self.InputChoiceBox.SetStringSelection("-- Please Select --")

        elif Settings["InputFile"][0:3] == "...":
            #Get the full path name to set the inputfile to.
            Settings["InputFile"] = self.CustomInputPathsList[Settings["InputFile"]]

        elif Settings["InputFile"] == "-- Please Select --":
            logger.info("MainWindow().SelectInputFile(): Input file reset..")
            Settings["InputFile"] = None

        #Call Layout() on self.Panel() to ensure it displays properly.
        self.Panel.Layout()

    def SetOutputFile(self, Event=None):
        """Get the output file/Disk and set a variable to the selected value"""
        logger.debug("MainWindow().SelectOutputFile(): Getting user selection...")
        Settings["OutputFile"] = self.OutputChoiceBox.GetStringSelection()

        if Settings["OutputFile"] == "Select a File/Disk":
            OutputFileDlg = wx.FileDialog(self.Panel, "Select Output File/Disk...", defaultDir=self.UserHomeDir, wildcard=self.OutputWildcard, style=wx.SAVE)

            if OutputFileDlg.ShowModal() == wx.ID_OK:
                Settings["OutputFile"] = OutputFileDlg.GetPath()

                #Automatically add a file extension of .img if there isn't one (fixes bugs on OS X).
                if Settings["OutputFile"][-4] != ".":
                    Settings["OutputFile"] += ".img"

                if PartedMagic and "/root" in Settings["OutputFile"]:
                    logger.warning("MainWindow().SelectOutputFile(): OutputFile is in root's home directory on Parted Magic! There is no space here, warning user and declining selection...")
                    dlg = wx.MessageDialog(self.Panel, "You can't save the output file in root's home directory in Parted Magic! There's not enough space there, please select a new file.", 'DDRescue-GUI - Error!', wx.OK | wx.ICON_ERROR)
                    dlg.ShowModal()
                    dlg.Destroy()

                    Settings["OutputFile"] = None
                    self.OutputChoiceBox.SetStringSelection("-- Please Select --")

                else:
                    logger.info("MainWindow().SelectOutputFile(): User selected custom file: "+Settings["OutputFile"]+"...")

                    #If it's in the dictionary or in DiskInfo, don't add it.
                    if BackendTools().FindDataValueInDict(self.CustomOutputPathsList, Settings["OutputFile"]):
                        #Set the selection using the unique key.
                        self.OutputChoiceBox.SetStringSelection(BackendTools().CreateUniqueKey(self.CustomOutputPathsList, Settings["InputFile"], 30))

                    elif Settings["OutputFile"] in DiskInfo.keys():
                        #No need to add it or anything.
                        self.OutputChoiceBox.SetStringSelection(Settings["OutputFile"])

                    else:
                        #Get a unqiue key for the dictionary using the tools function.
                        Key = BackendTools().CreateUniqueKey(self.CustomOutputPathsList, Settings["OutputFile"], 30)

                        self.CustomOutputPathsList[Key] = Settings["OutputFile"]
                        self.OutputChoiceBox.Append(Key)
                        self.OutputChoiceBox.SetStringSelection(Key)

            else:
                logger.info("MainWindow().SelectOutputFile(): User declined custom file selection. Resetting OutputFile...")
                Settings["OutputFile"] = None
                self.OutputChoiceBox.SetStringSelection("-- Please Select --")

        elif Settings["OutputFile"] not in [None, "-- Please Select --"] and Settings["OutputFile"] == Settings["InputFile"]:
            logger.warning("MainWindow().SelectOutputFile(): OutputFile equals InputFile!, resetting to None and warning user...")
            dlg = wx.MessageDialog(self.Panel, "You can't use the same Disk/file as both the source and the destination!", 'DDRescue-GUI - Error!', wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            Settings["OutputFile"] = None
            self.OutputChoiceBox.SetStringSelection("-- Please Select --")

        elif Settings["OutputFile"][0:3] == "...":
            #Get the full path name to set the outputfile to.
            Settings["OutputFile"] = self.CustomOutputPathsList[Settings["OutputFile"]]

        elif Settings["OutputFile"] == "-- Please Select --":
            logger.debug("MainWindow().SelectInputFile(): Output file reset...")
            Settings["OutputFile"] = None

        #Check with the user if the output file already exists.
        if Settings["OutputFile"] != None:
            if os.path.exists(Settings["OutputFile"]):
                logger.info("MainWindow().SelectInputFile(): Selected file already exists! Showing warning to user...")
                Dlg = wx.MessageDialog(self.Panel, "The file you selected already exists!\n\nIf you're doing a two-stage recovery, *and you've selected a logfile*, DDRescue-GUI will resume where it left off on the previous run, and it is safe to continue.\n\nOtherwise, you will lose data on this file or device.\n\nPlease be sure you selected the right file. Do you want to accept this file as your output file?", 'DDRescue-GUI -- Warning!', wx.YES_NO | wx.ICON_EXCLAMATION)

                if Dlg.ShowModal() == wx.ID_YES:
                    logger.warning("MainWindow().SelectOutputFile(): Accepted already-present file as output file!")

                else:
                    logger.info("MainWindow().SelectOutputFile(): User declined the selection. Resetting OutputFile...")
                    Settings["OutputFile"] = None
                    self.OutputChoiceBox.SetStringSelection("-- Please Select --")

                Dlg.Destroy()

        #If the file selected is a Disk, enable the overwrite output file option, else disable it.
        if Settings["OutputFile"] != None:
            if Settings["OutputFile"][0:5] == "/dev/":
                logger.info("MainWindow().SelectOutputFile(): OutputFile is a disk so enabling ddrescue's overwrite mode...")
                Settings["OverwriteOutputFile"] = "-f"

            else:
                logger.info("MainWindow().SelectOutputFile(): OutputFile isn't a disk so disabling ddrescue's overwrite mode...")
                Settings["OverwriteOutputFile"] = ""

        #Call Layout() on self.Panel() to ensure it displays properly.
        self.Panel.Layout()

    def SetLogFile(self, Event=None):
        """Get the log file position/name and set a variable to the selected value"""
        logger.debug("MainWindow().SelectLogFile(): Getting user selection...")
        Settings["LogFile"] = self.LogChoiceBox.GetStringSelection()

        if Settings["LogFile"] == "None (not recommended)":
            Dlg = wx.MessageDialog(self.Panel, "You have not chosen to use a log file. If you do not use one, you will have to start from scratch in the event of a power outage, or if DDRescue-GUI is interrupted. Additionally, you can't do a two-stage recovery without a log file.\n\nAre you really sure you do not want to use a logfile?", "DDRescue-GUI - Warning", wx.YES_NO | wx.ICON_EXCLAMATION)

            if Dlg.ShowModal() == wx.ID_YES:
                logger.warning("MainWindow().SelectLogFile(): User isn't using a log file, despite our warning!")
                Settings["LogFile"] = ""

            else:
                logger.info("MainWindow().SelectLogFile(): User decided against not using a log file. Good!")
                Settings["LogFile"] = None
                self.LogChoiceBox.SetStringSelection("-- Please Select --")

            Dlg.Destroy()

        elif Settings["LogFile"] == "Select a File":
            LogFileDlg = wx.FileDialog(self.Panel, "Select Log File Position & Name...", defaultDir=self.UserHomeDir, wildcard="Log Files (*.log)|*.log", style=wx.SAVE)

            if LogFileDlg.ShowModal() == wx.ID_OK:
                Settings["LogFile"] = LogFileDlg.GetPath()

                if PartedMagic and "/root" in Settings["LogFile"]:
                    logger.warning("MainWindow().SelectLogFile(): LogFile is in root's home directory on Parted Magic! There is no space here, warning user and declining selection...")
                    dlg = wx.MessageDialog(self.Panel, "You can't save the log file in root's home directory in Parted Magic! There's not enough space there, please select a new file.", 'DDRescue-GUI - Error!', wx.OK | wx.ICON_ERROR)
                    dlg.ShowModal()
                    dlg.Destroy()

                    Settings["LogFile"] = None
                    self.LogChoiceBox.SetStringSelection("-- Please Select --")

                else:
                    logger.debug("MainWindow().SelectLogFile(): User selected custom file: "+Settings["LogFile"]+"...")

                    #If it's in the dictionary already, don't add it again.
                    if BackendTools().FindDataValueInDict(self.CustomLogPaths, Settings["LogFile"]):
                        #Set the selection using the unique key.
                        self.LogChoiceBox.SetStringSelection(BackendTools().CreateUniqueKey(self.CustomLogPaths, Settings["LogFile"], 30))

                    elif Settings["LogFile"] in DiskInfo.keys():
                        #Warn user and reject selection.
                        Dlg = wx.MessageDialog(self.Panel, "You can't save the log file to a device! Please make an appropriate selection.", "DDRescue-GUI - Error!", wx.OK | wx.ICON_ERROR)
                        Dlg.ShowModal()
                        Dlg.Destroy()

                        self.LogChoiceBox.SetStringSelection("-- Please Select --")

                    else:
                        #Get a unqiue key for the dictionary using the tools function.
                        Key = BackendTools().CreateUniqueKey(self.CustomLogPaths, Settings["LogFile"], 30)

                        self.CustomLogPaths[Key] = Settings["LogFile"]
                        self.LogChoiceBox.Append(Key)
                        self.LogChoiceBox.SetStringSelection(Key)

            else:
                logger.debug("MainWindow().SelectLogFile(): User declined custom file selection. Resetting LogFile...")
                Settings["LogFile"] = None
                self.LogChoiceBox.SetStringSelection("-- Please Select --")

            LogFileDlg.Destroy()

        elif Settings["LogFile"][0:3] == "...":
            #Get the full path name to set the logfile to.
            Settings["LogFile"] = self.CustomLogPaths[Settings["LogFile"]]

        elif Settings["LogFile"] == "-- Please Select --":
            logger.debug("MainWindow().SelectLogFile(): LogFile reset.")
            Settings["LogFile"] = None

        #Call Layout() on self.Panel() to ensure it displays properly.
        self.Panel.Layout()

    def OnAbout(self, Event=None):
        """Show the about box"""
        logger.debug("MainWindow().OnAbout(): Showing about box...")
        aboutbox = wx.AboutDialogInfo()
        aboutbox.SetIcon(AppIcon)
        aboutbox.Name = "DDRescue-GUI"
        aboutbox.Version = Version
        aboutbox.Copyright = "(C) 2013-2016 Hamish McIntyre-Bhatty"
        aboutbox.Description = "GUI frontend for GNU ddrescue"
        aboutbox.WebSite = ("https://launchpad.net/ddrescue-gui", "Launchpad page")
        aboutbox.Developers = ["Hamish McIntyre-Bhatty", "Minnie McIntyre-Bhatty (GUI Design)"]
        aboutbox.Artists = ["Holly McIntyre-Bhatty", "Hamish McIntyre-Bhatty (Throbber designs)"]
        aboutbox.License = "DDRescue-GUI is free software: you can redistribute it and/or modify it\nunder the terms of the GNU General Public License version 3 or,\nat your option, any later version.\n\nDDRescue-GUI is distributed in the hope that it will be useful,\nbut WITHOUT ANY WARRANTY; without even the implied warranty of\nMERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the\nGNU General Public License for more details.\n\nYou should have received a copy of the GNU General Public License\nalong with DDRescue-GUI.  If not, see <http://www.gnu.org/licenses/>.\n\nGNU ddrescue and cocoaDialog are released under the GPLv2,\nmay be redistributed under the terms of the GPLv2 or newer, and are\nbundled with the Mac OS X version of DDRescue-GUI, but I am NOT\nthe author of GNU ddrescue or cocoaDialog.\n\nFor more information on GNU ddrescue, visit\nhttp://www.gnu.org/software/ddrescue/ddrescue.html\n\nFor more information on cocoaDialog, visit\nhttp://mstratman.github.io/cocoadialog/#"

        #Show the about box
        wx.AboutBox(aboutbox)

    def ShowSettings(self, Event=None):
        """Show the Settings Window"""
        #If input and output files are set (do not equal None) then continue.
        if None not in [Settings["InputFile"], Settings["OutputFile"]]:
            SettingsWindow(self).Show()

        else:
            dlg = wx.MessageDialog(self.Panel, 'Please select input and output files first!', 'DDRescue-GUI - Error!', wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()

    def ShowDevInfo(self, Event=None):
        """Show the Disk Information Window"""
        DevInfoWindow(self).Show()

    def ShowPrivacyPolicy(self, Event=None):
        """Show PrivPolWindow"""
        PrivPolWindow(self).Show()

    def OnControlButton(self, Event=None):
        """Handle events from the control button, as its purpose changes during and after recovery. Call self.OnAbort() or self.OnStart() as required."""
        if Settings["RecoveringData"]:
            self.OnAbort()

        else:
            self.OnStart()

    def OnStart(self):
        """Check the settings, prepare to start ddrescue and start the backend thread."""
        logger.info("MainWindow().OnStart(): Checking settings...")
        self.UpdateStatusBar("Preparing to start ddrescue...")

        if Settings["CheckedSettings"] == False:
            logger.error("MainWindow().OnStart(): The settings haven't been checked properly! Aborting recovery...")
            dlg = wx.MessageDialog(self.Panel, "Please check the settings before starting the recovery.", "DDRescue-GUI - Warning", wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            self.UpdateStatusBar("Ready.")

        elif None not in [Settings["InputFile"], Settings["LogFile"], Settings["OutputFile"]]:
            #Attempt to unmount input/output Disks now, if needed.
            logger.info("MainWindow().OnStart(): Unmounting input and output files if needed...")

            for Disk in [Settings["InputFile"], Settings["OutputFile"]]:
                if Disk not in DiskInfo:
                    logger.info("MainWindow().OnStart(): "+Disk+" is a file (or not in collected disk info), ignoring it...")
                    continue

                if BackendTools().IsMounted(Disk) or DevInfoTools().IsPartition(Disk) == False:
                    #The Disk is mounted, or may have partitions that are mounted.
                    if DevInfoTools().IsPartition(Disk):
                        #Unmount the disk.
                        logger.debug("MainWindow().OnStart(): "+Disk+" is a partition. Unmounting "+Disk+"...")
                        self.UpdateStatusBar("Unmounting "+Disk+". This may take a few moments...")
                        wx.Yield()
                        Retval = BackendTools().UnmountDisk(Disk)

                    else:
                        #Unmount any partitions belonging to the device.
                        logger.debug("MainWindow().OnStart(): "+Disk+" is a device. Unmounting any partitions contained by "+Disk+"...")
                        self.UpdateStatusBar("Unmounting "+Disk+"'s partitions. This may take a few moments...")
                        wx.Yield()

                        Retvals = []
                        Retval = 0
 
                        for Partition in DiskInfo[Disk]["Partitions"]:
                            logger.info("MainWindow().OnStart(): Unmounting "+Partition+"...")
                            Retvals.append(BackendTools().UnmountDisk(Partition))

                        #Check the return values, and raise an error if any of them aren't 0.
                        for Integer in Retvals:
                            if Integer != 0:
                                Retval = Integer
                                break

                    #Check it worked.
                    if Retval != 0:
                        #It didn't. Warn the user, and exit the function.
                        logger.info("MainWindow().OnStart(): Failed! Warning user...")
                        dlg = wx.MessageDialog(self.Panel, "Could not unmount disk "+Disk+"! Please close all other programs and anything that may be accessing this disk (or any of its partitions), like the file manager perhaps, and try again.", "DDRescue-GUI - Error!", wx.OK | wx.ICON_ERROR)
                        dlg.ShowModal()
                        dlg.Destroy()
                        self.UpdateStatusBar("Ready.")
                        return 0

                    else:
                        logger.info("MainWindow().OnStart(): Success...")

                else:
                    logger.info("MainWindow().OnStart(): "+Disk+" is not mounted...")

            #Create the items for self.ListCtrl.
            Width, Height = self.ListCtrl.GetClientSizeTuple()

            #First column.
            self.ListCtrl.InsertStringItem(index=0, label="Recovered Data")
            self.ListCtrl.InsertStringItem(index=1, label="Unreadable Data")
            self.ListCtrl.InsertStringItem(index=2, label="Current Read Rate")
            self.ListCtrl.InsertStringItem(index=3, label="Average Read Rate")
            self.ListCtrl.InsertStringItem(index=4, label="Bad Sectors")
            self.ListCtrl.InsertStringItem(index=5, label="Input Position")
            self.ListCtrl.InsertStringItem(index=6, label="Output Position")
            self.ListCtrl.InsertStringItem(index=7, label="Time Since Last Read")
            self.ListCtrl.SetColumnWidth(0, 150)

            #Second column.
            self.ListCtrl.SetStringItem(index=0, col=1, label="Unknown")
            self.ListCtrl.SetStringItem(index=1, col=1, label="Unknown")
            self.ListCtrl.SetStringItem(index=2, col=1, label="Unknown")
            self.ListCtrl.SetStringItem(index=3, col=1, label="Unknown")
            self.ListCtrl.SetStringItem(index=4, col=1, label="Unknown")
            self.ListCtrl.SetStringItem(index=5, col=1, label="Unknown")
            self.ListCtrl.SetStringItem(index=6, col=1, label="Unknown")
            self.ListCtrl.SetStringItem(index=7, col=1, label="Unknown")
            self.ListCtrl.SetColumnWidth(1, Width - 150)

            logger.info("MainWindow().OnStart(): Settings check complete. Starting BackendThread()...")
            self.UpdateStatusBar("Starting ddrescue...")
            wx.Yield()

            #Notify the user.
            if Linux:
                BackendTools().StartProcess(Command="notify-send 'DDRescue-GUI' 'The recovery is about to start...' -i /usr/share/pixmaps/ddrescue-gui.png", ReturnOutput=False)

            else:
                subprocess.Popen(RescourcePath+"""/other/CocoaDialog.app/Contents/MacOS/CocoaDialog bubble --title "DDRescue-GUI" --text "The recovery is about to start..." --icon-file """+RescourcePath+"""/images/Logo.png  --background-top EFF7FD --border-color EFF7FD""", shell=True)

            #Disable and enable all necessary items.
            self.SettingsButton.Disable()
            self.UpdateDiskInfoButton.Disable()
            self.InputChoiceBox.Disable()
            self.OutputChoiceBox.Disable()
            self.LogChoiceBox.Disable()
            self.MenuAbout.Enable(False)
            self.MenuExit.Enable(False) 
            self.MenuDiskInfo.Enable(False)
            self.MenuSettings.Enable(False)
            self.ControlButton.SetLabel("Abort")

            #Handle any unexpected errors.
            try:
                #Start the backend thread.
                BackendThread(self)

            except:
                logger.critical("Unexpected error \n\n"+unicode(traceback.format_exc())+"\n\n while recovering data. Warning user and exiting.")
                BackendTools().EmergencyExit("There was an unexpected error:\n\n"+unicode(traceback.format_exc())+"\n\nWhile recovering data!")

        else:
            logger.error("MainWindow().OnStart(): One or more of InputFile, OutputFile or LogFile hasn't been set! Aborting Recovery...")
            dlg = wx.MessageDialog(self.Panel, 'Please set the Input file, Log file and Output file correctly before starting!', 'DDRescue-GUI - Error!', wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            self.UpdateStatusBar("Ready.")

    #The next functions are to update the display with info from the backend.
    def SetProgressBarRange(self, Message):
        """Set the progressbar's range""" 
        logger.debug("MainWindow().SetProgressBarRange(): Setting range "+unicode(Message)+" for self.ProgressBar...")
        self.ProgressBar.SetRange(Message)

    def UpdateTimeElapsed(self, Line):
        """Update the time elapsed text"""
        self.TimeElapsedText.SetLabel(Line)

    def UpdateTimeRemaining(self, TimeLeft):
        self.TimeRemainingText.SetLabel("Time Remaining: "+TimeLeft)

    def UpdateRecoveredData(self, RecoveredData):
        self.ListCtrl.SetStringItem(index=0, col=1, label=RecoveredData)

    def UpdateErrorSize(self, ErrorSize):
        self.ListCtrl.SetStringItem(index=1, col=1, label=ErrorSize)

    def UpdateCurrentReadRate(self, CurrentReadRate):
        self.ListCtrl.SetStringItem(index=2, col=1, label=CurrentReadRate)

    def UpdateAverageReadRate(self, AverageReadRate):
        self.ListCtrl.SetStringItem(index=3, col=1, label=AverageReadRate)

    def UpdateNumErrors(self, NumErrors):
        self.ListCtrl.SetStringItem(index=4, col=1, label=NumErrors)

    def UpdateIpos(self, Ipos):
        self.ListCtrl.SetStringItem(index=5, col=1, label=Ipos)

    def UpdateOpos(self, Opos):
        self.ListCtrl.SetStringItem(index=6, col=1, label=Opos)

    def UpdateTimeSinceLastRead(self, LastRead):
        self.ListCtrl.SetStringItem(index=7, col=1, label=LastRead)

    def CarriageReturn(self):
        """Handles carriage returns in output"""
        #Go back until the last newline character, and overwrite anything in the way on the next write.
        #Get the current insertion point.
        CurrentInsertionPoint = self.OutputBox.GetInsertionPoint()

        #Get the text up to the current insertion point.
        Text = self.OutputBox.GetRange(0, CurrentInsertionPoint)

        #Find the last newline char in the text.
        NewlineNos = []
        Counter = 0
        for Char in Text:
            if Char == "\n":
                NewlineNos.append(Counter)

            Counter += 1

        if NewlineNos != []:
            LastNewline = NewlineNos[-1]

        else:
            #Hacky bit to make the new insertion point 0 :)
            LastNewline = -1

        #Set the insertion point to just after that newline, unless we're already there, and in that case set the insertion point just after the previous newline.
        NewInsertionPoint = LastNewline + 1

        self.OutputBox.SetInsertionPoint(NewInsertionPoint)

    def UpOneLine(self):
        """Handles '\x1b[A' (up one line) in output"""
        #Go up one line.
        #Get our Column and Line numbers.
        Column, Line = self.OutputBox.CustomPositionToXY(self.OutputBox.GetInsertionPoint())

        #We go up one line, but stay in the same column, so find the integer position of the new insertion point.
        NewInsertionPoint = self.OutputBox.CustomXYToPosition(Column, Line-1)

        if NewInsertionPoint == -1:
            #Invalid Column/Line! Maybe we reached the start of the text in self.OutputBox? Do nothing but log the error.
            logger.warning("MainWindow().UpOneLine(): Invalid new insertion point when trying to move up one line! This might mean we've reached that start of the text in the output box.")

        else:
            #Set the new insertion point.
            self.OutputBox.SetInsertionPoint(NewInsertionPoint)

    def UpdateOutputBox(self, Line):
        """Update the output box"""
        CRs = []
        UOLs = []
        CharNo = 0

        for Char in Line:
            CharNo += 1

            if Char == "\r":
                CRs.append(CharNo)

            elif Char == "¬":
                UOLs.append(CharNo)

        CharNo = 0
        TempLine = ""
        for Char in Line:
            CharNo += 1

            if CharNo not in CRs and CharNo not in UOLs:
                TempLine += Char
                if Char == "\n":
                    self.AddLineToOutputBox(TempLine, CRs, UOLs, CharNo)
                    TempLine = ""

            else:
                self.AddLineToOutputBox(TempLine, CRs, UOLs, CharNo)
                TempLine = ""

    def AddLineToOutputBox(self, Line, CRs, UOLs, CharNo):
        InsertionPoint = self.OutputBox.GetInsertionPoint()
        self.OutputBox.Replace(InsertionPoint, InsertionPoint+len(Line), Line)

        if CharNo in CRs:
            self.CarriageReturn()

        elif CharNo in UOLs:
            self.UpOneLine()

    def UpdateStatusBar(self, Message):
        """Update the statusbar with a new message"""
        logger.debug("MainWindow().UpdateStatusBar(): New status bar message: "+Message)
        self.StatusBar.SetStatusText(Message, 0)

    def UpdateProgress(self, RecoveredData, DiskCapacity):
        """Update the progressbar and the title"""
        self.ProgressBar.SetValue(RecoveredData)
        self.SetTitle("DDRescue-GUI - "+unicode(int(RecoveredData * 100 // DiskCapacity))+"%")

    def OnAbort(self):
        """Abort the recovery"""
        #Ask ddrescue to exit.
        logger.info("MainWindow().OnAbort(): Attempting to kill ddrescue...")
        BackendTools().StartProcess("killall ddrescue")
        self.AbortedRecovery = True

        #Disable control button.
        self.ControlButton.Disable()

        if not SessionEnding:
            #Notify user with throbber.
            self.Throbber.Play()

            #Prompt user to try again in 5 seconds time.
            wx.CallLater(5000, self.PromptToKillDdrescue)

    def PromptToKillDdrescue(self):
        """Prompts the user to try killing ddrescue again if it's not exiting"""
        #If we're still recovering data, prompt the user to try killing ddrescue again.
        if Settings["RecoveringData"]:
            logger.warning("MainWindow().PromptToKillDdrescue(): ddrescue is still running 5 seconds after attempted abort! Asking user whether to wait or trying killing it again...")
            dlg = wx.MessageDialog(self.Panel, "Do you want to try to stop ddrescue again, or wait for five more seconds? Click yes to stop ddrescue and no to wait.", "DDRescue is still running!", wx.YES_NO|wx.ICON_QUESTION)

            #Catch errors on wxpython < 2.9.
            try:
                if dlg.SetYesNoLabels("Stop DDRescue", "Wait"):
                    dlg.SetMessage("Do you want to try to stop ddrescue again, or wait for five more seconds?")

            except AttributeError: pass

            if dlg.ShowModal() == wx.ID_YES:
                logger.warning("MainWindow().PromptToKillDdrescue(): Trying to kill ddrescue again...")
                self.OnAbort()

            else:
                #Prompt user to try again in 5 seconds time.
                logger.warning("MainWindow().PromptToKillDdrescue(): Ask user again in 5 sconds time if ddrescue hasn't stopped...")
                wx.CallLater(5000, self.PromptToKillDdrescue)

            dlg.Destroy()

    def RecoveryEnded(self, Result, DiskCapacity, RecoveredData, ReturnCode=None):
        """Called to show FinishedWindow when a recovery is completed or aborted by the user"""
        #Return immediately if session is ending.
        if SessionEnding:
            return True

        #Stop the throbber.
        self.Throbber.Stop()

        #Handle any errors.
        if self.AbortedRecovery:
            logger.info("MainWindow().RecoveryEnded(): ddrescue was aborted by the user...")
            #Notify the user.
            if Linux:
                BackendTools().StartProcess(Command="notify-send 'DDRescue-GUI' 'Recovery aborted by user.' -i /usr/share/pixmaps/ddrescue-gui.png", ReturnOutput=False)

            else:
                subprocess.Popen(RescourcePath+"""/other/CocoaDialog.app/Contents/MacOS/CocoaDialog bubble --title "DDRescue-GUI" --text "Recovery aborted by user." --icon-file """+RescourcePath+"""/images/Logo.png  --background-top EFF7FD --border-color EFF7FD""", shell=True)

            dlg = wx.MessageDialog(self.Panel, "Your recovery has been aborted as you requested.\n\nNote: Your recovered data may be incomplete at this point, so you may now want to run a second recovery to try and grab the remaining data. If you wish to, you may now use DDRescue-GUI to mount your destination drive/file so you can access your data, although some/all of it may be unreadable in its current state.", "DDRescue-GUI - Information", wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()

        elif Result == "NoInitialStatus":
            logger.error("MainWindow().RecoveryEnded(): We didn't get ddrescue's initial status! This probably means ddrescue aborted immediately. Maybe settings are incorrect?")

            #Notify the user.
            if Linux:
                BackendTools().StartProcess(Command="notify-send 'DDRescue-GUI' 'Recovery Error! ddrescue aborted immediately. See GUI for more info.' -i /usr/share/pixmaps/ddrescue-gui.png", ReturnOutput=True)

            else:
                subprocess.Popen(RescourcePath+"""/other/CocoaDialog.app/Contents/MacOS/CocoaDialog bubble --title "DDRescue-GUI" --text "Recovery Error! ddrescue aborted immediately. See GUI for more info." --icon-file """+RescourcePath+"""/images/Logo.png  --background-top EFF7FD --border-color EFF7FD""", shell=True)

            dlg = wx.MessageDialog(self.Panel, "We didn't get ddrescue's initial status! This probably means ddrescue aborted immediately. Please check all of your settings, and try again. Here is ddrescue's output, which may tell you what went wrong:\n\n"+self.OutputBox.GetValue(), "DDRescue-GUI - Error!", wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()

        elif Result == "BadReturnCode":
            logger.error("MainWindow().RecoveryEnded(): ddrescue exited with nonzero exit status "+unicode(ReturnCode)+"! Perhaps the output file/disk is full?")

            #Notify the user.
            if Linux:
                BackendTools().StartProcess(Command="notify-send 'DDRescue-GUI' 'Recovery Error! ddrescue exited with exit status "+unicode(ReturnCode)+"!' -i /usr/share/pixmaps/ddrescue-gui.png", ReturnOutput=False)

            else:
                subprocess.Popen(RescourcePath+"""/other/CocoaDialog.app/Contents/MacOS/CocoaDialog bubble --title "DDRescue-GUI" --text "Recovery Error! ddrescue exited with exit status "+unicode(ReturnCode)+"!" --icon-file """+RescourcePath+"""/images/Logo.png  --background-top EFF7FD --border-color EFF7FD""", shell=True)

            dlg = wx.MessageDialog(self.Panel, "Ddrescue exited with nonzero exit status "+unicode(ReturnCode)+"! Perhaps the output file/disk is full? Please check all of your settings, and try again. Here is ddrescue's output, which may tell you what went wrong:\n\n"+self.OutputBox.GetValue(), "DDRescue-GUI - Error!", wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()

        elif Result == "Success":
            logger.info("MainWindow().RecoveryEnded(): Recovery finished!")

            #Check if we got all the data.
            if self.ProgressBar.GetValue() >= self.ProgressBar.GetRange():
                Message = "Your recovery is complete, with all data recovered from your source disk/file.\n\nNote: If you wish to, you may now use DDRescue-GUI to mount your destination drive/file so you can access your data."
                #Notify the user.
                if Linux:
                    BackendTools().StartProcess(Command="notify-send 'DDRescue-GUI' 'Recovery Finished with all data!' -i /usr/share/pixmaps/ddrescue-gui.png", ReturnOutput=False)

                else:
                    subprocess.Popen(RescourcePath+"""/other/CocoaDialog.app/Contents/MacOS/CocoaDialog bubble --title "DDRescue-GUI" --text "Recovery Finished with all data!" --icon-file """+RescourcePath+"""/images/Logo.png  --background-top EFF7FD --border-color EFF7FD""", shell=True)

            else:
                Message = "Your recovery is finished, but not all of your data appears to have been recovered. You may now want to run a second recovery to try and grab the remaining data. If you wish to, you may now use DDRescue-GUI to mount your destination drive/file so you can access your data, although some/all of it may be unreadable in its current state."

                #Notify the user.
                if Linux:
                    BackendTools().StartProcess(Command="notify-send 'DDRescue-GUI' 'Recovery Finished, but not all data was recovered.' -i /usr/share/pixmaps/ddrescue-gui.png", ReturnOutput=False)

                else:
                    subprocess.Popen(RescourcePath+"""/other/CocoaDialog.app/Contents/MacOS/CocoaDialog bubble --title "DDRescue-GUI" --text "Recovery Finished, but not all data was recovered." --icon-file """+RescourcePath+"""/images/Logo.png  --background-top EFF7FD --border-color EFF7FD""", shell=True)

            dlg = wx.MessageDialog(self.Panel, Message, "DDRescue-GUI - Information", wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()

        #Disable the control button.
        self.ControlButton.Disable()

        FinishedWindow(self, DiskCapacity, RecoveredData).Show()

    def Reload(self):
        """Reload and reset MainWindow, so MainWindow is as it was when DDRescue-GUI was started""" 
        logger.info("MainWindow().Reload(): Reloading and resetting MainWindow...")
        self.UpdateStatusBar("Restarting, please wait...")

        #Set everything back the way it was before
        self.SetTitle("DDRescue-GUI")
        self.UpdateDiskInfoButton.Enable()
        self.ControlButton.Enable()
        self.SettingsButton.Enable()
        self.InputChoiceBox.Enable()
        self.OutputChoiceBox.Enable()
        self.LogChoiceBox.Enable()
        self.MenuAbout.Enable(True)
        self.MenuExit.Enable(True) 
        self.MenuDiskInfo.Enable(True)
        self.MenuSettings.Enable(True)

        #Reset recovery information.
        self.OutputBox.Clear()
        self.ListCtrl.ClearAll()
        self.ListCtrl.InsertColumn(col=0, heading="Category", format=wx.LIST_FORMAT_CENTRE, width=-1)
        self.ListCtrl.InsertColumn(col=1, heading="Value", format=wx.LIST_FORMAT_CENTRE, width=-1)
        self.ControlButton.SetLabel("Start")
        self.TimeRemainingText.SetLabel("Time Remaining:")
        self.TimeElapsedText.SetLabel("Time Elapsed:")

        #Reset the ProgressBar
        self.ProgressBar.SetValue(0)

        #Reset essential variables.
        self.SetVars()

        #Update choice dialogs and reset checked settings to False
        self.UpdateFileChoices()

        #Reset the choice dialogs.
        self.InputChoiceBox.SetStringSelection("-- Please Select --")
        self.OutputChoiceBox.SetStringSelection("-- Please Select --")
        self.LogChoiceBox.SetStringSelection("-- Please Select --")

        #Get new Disk info.
        self.GetDiskInfo()

        logger.info("MainWindow().Reload(): Done. Waiting for events...")
        self.UpdateStatusBar("Ready.")

    def SessionEnding(self, Event):
        """Attempt to veto e.g. a shutdown/logout event if recovering data."""
        #Check if we can veto the shutdown.
        logging.warning("MainWindow().SessionEnding(): Attempting to veto system shutdown / logoff...")

        if Event.CanVeto() and RecoveringData:
            #Veto the shutdown and warn the user.
            Event.Veto(True)
            logging.info("MainWindow().SessionEnding(): Vetoed system shutdown / logoff...")
            dlg = wx.MessageDialog(self.Panel, "You can't shutdown or logoff while recovering data!", "DDRescue-GUI - Error!", wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()

        else:
            #Set SessionEnding to True, call OnExit.
            logging.critical("MainWindow().SessionEnding(): Cannot veto system shutdown / logoff! Cleaning up...")
            global SessionEnding
            SessionEnding = True
            self.OnExit()

    def OnExit(self, Event=None, JustFinishedRec=False):
        """Exit DDRescue-GUI, if certain conditions are met"""
        logger.info("MainWindow().OnExit(): Preparing to exit...")

        #Check if the session is ending.
        if SessionEnding:
            #Stop the backend thread, delete the log file and exit ASAP.
            self.OnAbort()
            #os.remove("/tmp/ddrescue-gui.log")
            self.Destroy()

        #Check if DDRescue-GUI is recovering data.
        if Settings["RecoveringData"]:
            logger.error("MainWindow().OnExit(): Can't exit while recovering data! Aborting exit attempt...")
            dlg = wx.MessageDialog(self.Panel, "You can't exit DDRescue-GUI while recovering data!", "DDRescue-GUI - Error!", wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()

        else:
            logger.info("MainWindow().OnExit(): Double-checking the exit attempt with the user...")
            dlg = wx.MessageDialog(self.Panel, 'Are you sure you want to exit?', 'DDRescue-GUI - Question!', wx.YES_NO | wx.ICON_QUESTION)
            Answer = dlg.ShowModal()
            dlg.Destroy()

            if Answer == wx.ID_YES:
                #Run the exit sequence
                logger.info("MainWindow().OnExit(): Exiting...")

                #Shutdown the logger.
                logging.shutdown()

                #Prompt user to save the log file.
                dlg = wx.MessageDialog(self.Panel, "Do you want to keep DDRescue-GUI's log file? For privacy reasons, DDRescue-GUI will delete its log file when closing. If you want to save it, which is helpful for debugging if something went wrong, click yes, and otherwise click no.", "DDRescue-GUI - Question", style=wx.YES_NO | wx.ICON_QUESTION, pos=wx.DefaultPosition)
                Answer = dlg.ShowModal()
                dlg.Destroy()

                if Answer == wx.ID_YES:
                    #Trap pogram in loop in case same log file as Recovery log file is picked for destination.
                    while True:
                        #Ask the user where to save it.
                        dlg = wx.FileDialog(self.Panel, "Save log file to...", defaultDir=self.UserHomeDir, wildcard="Log Files (*.log)|*.log" , style=wx.SAVE)
                        Answer = dlg.ShowModal()
                        File = dlg.GetPath()
                        dlg.Destroy()

                        if Answer == wx.ID_OK:
                            if File == Settings["LogFile"]:
                                dlg = wx.MessageDialog(self.Panel, 'Error! Your chosen file is the same as the recovery log file! This log file contains only debugging information for DDRescue-GUI, and you must not overwrite the recovery log file with this one. Please select a new destination file.', 'DDRescue-GUI - Error', wx.OK | wx.ICON_ERROR)
                                dlg.ShowModal()
                                dlg.Destroy()

                            else:
                                #Copy it to the specified path, using a one-liner, and don't bother handling any errors, because this is run as root.
                                BackendTools().StartProcess(Command="cp /tmp/ddrescue-gui.log "+File, ReturnOutput=False)

                                dlg = wx.MessageDialog(self.Panel, 'Done! DDRescue-GUI will now exit.', 'DDRescue-GUI - Information', wx.OK | wx.ICON_INFORMATION)
                                dlg.ShowModal()
                                dlg.Destroy()
                                break

                        else:
                            dlg = wx.MessageDialog(self.Panel, 'Okay, DDRescue-GUI will now exit without saving the log file.', 'DDRescue-GUI - Information', wx.OK | wx.ICON_INFORMATION)
                            dlg.ShowModal()
                            dlg.Destroy()

                else:
                    dlg = wx.MessageDialog(self.Panel, 'Okay, DDRescue-GUI will now exit without saving the log file.', 'DDRescue-GUI - Information', wx.OK | wx.ICON_INFORMATION)
                    dlg.ShowModal()
                    dlg.Destroy()

                #Delete the log file, and don't bother handling any errors, because this is run as root.
                os.remove('/tmp/ddrescue-gui.log')

                self.Destroy()

            else:
                #Check if exit was initated by finisheddlg.
                logger.warning("MainWindow().OnExit(): User cancelled exit attempt! Aborting exit attempt...")
                if JustFinishedRec:
                    #If so return to finisheddlg.
                    logger.info("MainWindow().OnExit(): Showing FinishedWindow() again...")
                    FinishedWindow(self).Show()

#End Main Window
#Begin Disk Info Window
class DevInfoWindow(wx.Frame):
    def __init__(self,ParentWindow):
        """Initialize DevInfoWindow"""
        wx.Frame.__init__(self, wx.GetApp().TopWindow, title="DDRescue-GUI - Disk Information", size=(780,310), style=wx.DEFAULT_FRAME_STYLE)
        self.Panel = wx.Panel(self)
        self.SetClientSize(wx.Size(780,310))
        self.ParentWindow = ParentWindow
        wx.Frame.SetIcon(self, AppIcon)

        logger.debug("DevInfoWindow().__init__(): Creating widgets...")
        self.CreateWidgets()

        logger.debug("DevInfoWindow().__init__(): Setting up sizers...")
        self.SetupSizers()

        logger.debug("DevInfoWindow().__init__(): Binding events...")
        self.BindEvents()

        #Use already-present info for the list ctrl if possible.
        if 'DiskInfo' in globals():
            logger.debug("DevInfoWindow().__init__(): Updating list ctrl with Disk info already present...")
            self.UpdateListCtrl()

        #Call Layout() on self.Panel() to ensure it displays properly.
        self.Panel.Layout()

        logger.info("DevInfoWindow().__init__(): Ready. Waiting for events...")

    def CreateWidgets(self):
        """Create all widgets for DevInfoWindow"""
        self.TitleText = wx.StaticText(self.Panel, -1, "Here are all the detected disks on your computer")
        self.ListCtrl = wx.ListCtrl(self.Panel, -1, style=wx.LC_REPORT|wx.LC_VRULES)
        self.OkayButton = wx.Button(self.Panel, -1, "Okay")
        self.RefreshButton = wx.Button(self.Panel, -1, "Refresh")

        #Disable the refresh button if we're recovering data.
        if Settings["RecoveringData"]:
            self.RefreshButton.Disable()

        #Create the animation for the throbber.
        throb = wx.animate.Animation(RescourcePath+"/images/Throbber.gif")
        self.Throbber = wx.animate.AnimationCtrl(self.Panel, -1, throb)
        self.Throbber.SetUseWindowBackgroundColour(True)
        self.Throbber.SetInactiveBitmap(wx.Bitmap(RescourcePath+"/images/ThrobberRest.png", wx.BITMAP_TYPE_PNG))
        self.Throbber.SetClientSize(wx.Size(30,30))

    def SetupSizers(self):
        """Set up the sizers for DevInfoWindow"""
        #Make a button boxsizer.
        BottomSizer = wx.BoxSizer(wx.HORIZONTAL)

        #Add each object to the bottom sizer.
        BottomSizer.Add(self.RefreshButton, 0, wx.LEFT|wx.RIGHT|wx.ALIGN_LEFT, 10)
        BottomSizer.Add((20,20), 1)
        BottomSizer.Add(self.Throbber, 0, wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
        BottomSizer.Add((20,20), 1)
        BottomSizer.Add(self.OkayButton, 0, wx.LEFT|wx.RIGHT|wx.ALIGN_RIGHT, 10)

        #Make a boxsizer.
        MainSizer = wx.BoxSizer(wx.VERTICAL)

        #Add each object to the main sizer.
        MainSizer.Add(self.TitleText, 0, wx.ALL|wx.CENTER, 10)
        MainSizer.Add(self.ListCtrl, 1, wx.EXPAND|wx.ALL, 10)
        MainSizer.Add(BottomSizer, 0, wx.EXPAND|wx.ALL ^ wx.TOP, 10)

        #Get the sizer set up for the frame.
        self.Panel.SetSizer(MainSizer)
        MainSizer.SetMinSize(wx.Size(780,310))
        MainSizer.SetSizeHints(self)

    def BindEvents(self):
        """Bind all events for DevInfoWindow"""
        self.Bind(wx.EVT_BUTTON, self.GetDiskInfo, self.RefreshButton)
        self.Bind(wx.EVT_BUTTON, self.OnExit, self.OkayButton)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_CLOSE, self.OnExit)

    def OnSize(self, Event=None):
        """Auto resize the ListCtrl columns"""
        Width, Height = self.ListCtrl.GetClientSizeTuple()

        self.ListCtrl.SetColumnWidth(0, int(Width * 0.15))
        self.ListCtrl.SetColumnWidth(1, int(Width * 0.1))
        self.ListCtrl.SetColumnWidth(2, int(Width * 0.1))
        self.ListCtrl.SetColumnWidth(3, int(Width * 0.3))
        self.ListCtrl.SetColumnWidth(4, int(Width * 0.15))
        self.ListCtrl.SetColumnWidth(5, int(Width * 0.2))

        if Event != None:
            Event.Skip()

    def GetDiskInfo(self, Event=None):
        """Call the thread to get Disk info, disable the refresh button, and start the throbber"""
        logger.info("DevInfoWindow().UpdateDevInfo(): Generating new Disk info...")
        self.RefreshButton.Disable()
        self.Throbber.Play()
        GetDiskInformation(self)

    def ReceiveDiskInfo(self, Info):
        """Get Disk data, call self.UpdateListCtrl(), and then call MainWindow().UpdateFileChoices() to refresh the file choices with the new info"""
        global DiskInfo
        DiskInfo = Info

        #Update the list control.
        logger.debug("DevInfoWindow().UpdateDevInfo(): Calling self.UpdateListCtrl()...")
        self.UpdateListCtrl()

        #Send update signal to mainwindow.
        logger.debug("DevInfoWindow().UpdateDevInfo(): Calling self.ParentWindow.UpdateFileChoices()...")
        wx.CallAfter(self.ParentWindow.UpdateFileChoices)

        #Stop the throbber and enable the refresh button.
        self.Throbber.Stop()
        self.RefreshButton.Enable()

    def UpdateListCtrl(self, Event=None):
        """Update the list control"""
        logger.debug("DevInfoWindow().UpdateListCtrl(): Clearing all objects in list ctrl...")
        self.ListCtrl.ClearAll()

        #Create the columns.
        logger.debug("DevInfoWindow().UpdateListCtrl(): Inserting columns into list ctrl...")
        self.ListCtrl.InsertColumn(col=0, heading="Name", format=wx.LIST_FORMAT_CENTRE)
        self.ListCtrl.InsertColumn(col=1, heading="Type", format=wx.LIST_FORMAT_CENTRE)
        self.ListCtrl.InsertColumn(col=2, heading="Vendor", format=wx.LIST_FORMAT_CENTRE)
        self.ListCtrl.InsertColumn(col=3, heading="Product", format=wx.LIST_FORMAT_CENTRE)
        self.ListCtrl.InsertColumn(col=4, heading="Size", format=wx.LIST_FORMAT_CENTRE)
        self.ListCtrl.InsertColumn(col=5, heading="Description", format=wx.LIST_FORMAT_CENTRE) 

        #Add info from the custom module.
        logger.debug("DevInfoWindow().UpdateListCtrl(): Adding Disk info to list ctrl...")

        #Do all of the data at the same time.
        Number = -1
        Disks = DiskInfo.keys()
        Disks.sort()

        #Make sure we display human-readable sizes on OS X.
        if Linux:
            Headings = ("Name", "Type", "Vendor", "Product", "Capacity", "Description")

        else:
            Headings = ("Name", "Type", "Vendor", "Product", "HumanCapacity", "Description")

        for Disk in Disks:
            Number += 1
            Column = 0

            for Heading in Headings:
                if Column == 0:
                    self.ListCtrl.InsertStringItem(index=Number, label=DiskInfo[Disk][Heading])

                else:
                    self.ListCtrl.SetStringItem(index=Number, col=Column, label=DiskInfo[Disk][Heading])

                Column += 1

        #Auto Resize the columns.
        self.OnSize()

    def OnExit(self, Event=None):
        """Exit DevInfoWindow"""
        logger.info("DevInfoWindow().OnExit(): Closing DevInfoWindow...")
        self.Destroy()

#End Disk Info Window
#Begin Settings Window
class SettingsWindow(wx.Frame):
    def __init__(self,ParentWindow):
        """Initialize SettingsWindow"""
        wx.Frame.__init__(self, wx.GetApp().TopWindow, title="DDRescue-GUI - Settings", size=(569,479), style=wx.DEFAULT_FRAME_STYLE)
        self.Panel = wx.Panel(self)
        self.SetClientSize(wx.Size(569,479))
        self.ParentWindow = ParentWindow
        wx.Frame.SetIcon(self, AppIcon)

        #Notify MainWindow that this has been run.
        logger.debug("SettingsWindow().__init__(): Setting CheckedSettings to True...")
        Settings["CheckedSettings"] = True

        #Create all of the widgets first.
        logger.debug("SettingsWindow().__init__(): Creating buttons...")
        self.CreateButtons()

        logger.debug("SettingsWindow().__init__(): Creating text...")
        self.CreateText()

        logger.debug("SettingsWindow().__init__(): Creating Checkboxes...")
        self.CreateCheckBoxes()

        logger.debug("SettingsWindow().__init__(): Creating Choiceboxes...")
        self.CreateChoiceBoxes()

        #Then setup the sizers and bind events, and finally the options in the window.
        logger.debug("SettingsWindow().__init__(): Setting up sizers...")
        self.SetupSizers()

        logger.debug("SettingsWindow().__init__(): Binding events...")
        self.BindEvents()

        logger.debug("SettingsWindow().__init__(): Setting up options...")
        self.SetupOptions()

        #Call Layout() on self.Panel() to ensure it displays properly.
        self.Panel.Layout()

        logger.info("SettingsWindow().__init__(): Ready. Waiting for events...")

    def CreateButtons(self):
        """Create all buttons for SettingsWindow"""
        self.FastRecButton = wx.Button(self.Panel, -1, "Set to fastest recovery")
        self.BestRecButton = wx.Button(self.Panel, -1, "Set to best recovery")
        self.DefaultRecButton = wx.Button(self.Panel, -1, "Balanced (default)")
        self.ExitButton = wx.Button(self.Panel, -1, "Save settings and close") 

    def CreateText(self):
        """Create all text for SettingsWindow"""
        self.TitleText = wx.StaticText(self.Panel, -1, "Welcome to Settings.")
        self.BadSectText = wx.StaticText(self.Panel, -1, "No. of times to retry bad sectors:")
        self.MaxErrorsText = wx.StaticText(self.Panel, -1, "Maximum number of errors before exiting:")
        self.ClustSizeText = wx.StaticText(self.Panel, -1, "Number of clusters to copy at a time:")

    def CreateCheckBoxes(self):
        """Create all CheckBoxes for SettingsWindow, and set their default states (all unchecked)"""
        self.DirectAccessCB = wx.CheckBox(self.Panel, -1, "Use Direct Disk Access (Recommended)")
        self.OverwriteCB = wx.CheckBox(self.Panel, -1, "Overwrite output file/disk (Enable if recovering to a disk)")
        self.ReverseCB = wx.CheckBox(self.Panel, -1, "Read the input file/disk backwards")
        self.PreallocCB = wx.CheckBox(self.Panel, -1, "Preallocate space on disc for output file/disk")
        self.NoSplitCB = wx.CheckBox(self.Panel, -1, "Do a soft run (don't attempt to read bad sectors)")

    def CreateChoiceBoxes(self):
        """Create all ChoiceBoxes for SettingsWindow, and call self.SetDefaultRec()"""
        self.BadSectChoice = wx.Choice(self.Panel, -1, choices=['0', '1', 'Default (2)', '3', '5', 'Forever'])  
        self.MaxErrorsChoice = wx.Choice(self.Panel, -1, choices=['Default (Infinite)', '1000', '500', '100', '50', '10'])
        self.ClustSizeChoice = wx.Choice(self.Panel, -1, choices=['256', 'Default (128)', '64', '32']) 

        #Set default settings.
        self.SetDefaultRec()

    def SetupSizers(self):
        """Set up all sizers for SettingsWindow"""
        #Make a sizer for each choicebox with text, and add the objects for each sizer.
        #Retry bad sectors sizer.
        RetryBSSizer = wx.BoxSizer(wx.HORIZONTAL)
        RetryBSSizer.Add(self.BadSectText, 1, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER, 10)
        RetryBSSizer.Add(self.BadSectChoice, 1, wx.RIGHT|wx.ALIGN_CENTER, 10)

        #Max errors sizer.
        MaxErrorsSizer = wx.BoxSizer(wx.HORIZONTAL)
        MaxErrorsSizer.Add(self.MaxErrorsText, 1, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER, 10)
        MaxErrorsSizer.Add(self.MaxErrorsChoice, 1, wx.RIGHT|wx.ALIGN_CENTER, 10)

        #Cluster Size Sizer.
        ClustSizeSizer = wx.BoxSizer(wx.HORIZONTAL)
        ClustSizeSizer.Add(self.ClustSizeText, 1, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER, 10)
        ClustSizeSizer.Add(self.ClustSizeChoice, 1, wx.RIGHT|wx.ALIGN_CENTER, 10)

        #Make a sizer for the best and fastest recovery buttons now, and add the objects.
        ButtonSizer = wx.BoxSizer(wx.HORIZONTAL)
        ButtonSizer.Add(self.BestRecButton, 3, wx.LEFT|wx.EXPAND, 10)
        ButtonSizer.Add((20,20), 1)
        ButtonSizer.Add(self.FastRecButton, 3, wx.RIGHT|wx.EXPAND, 10)

        #Now create and add all objects to the main sizer in order.
        MainSizer = wx.BoxSizer(wx.VERTICAL)

        #Checkboxes.
        MainSizer.Add(self.TitleText, 3, wx.CENTER|wx.TOP, 10)
        MainSizer.Add(self.DirectAccessCB, 3, wx.CENTER|wx.ALL, 5)
        MainSizer.Add(self.ReverseCB, 3, wx.CENTER|wx.ALL, 5)
        MainSizer.Add(self.PreallocCB, 3, wx.CENTER|wx.ALL, 5)
        MainSizer.Add(self.NoSplitCB, 3, wx.CENTER|wx.ALL, 5)
        MainSizer.Add(self.OverwriteCB, 3, wx.CENTER|wx.ALL, 5)

        #Choice box sizers.
        MainSizer.Add(RetryBSSizer, 4, wx.CENTER|wx.EXPAND|wx.ALL, 10)
        MainSizer.Add(MaxErrorsSizer, 4, wx.CENTER|wx.EXPAND|wx.ALL, 10)
        MainSizer.Add(ClustSizeSizer, 4, wx.CENTER|wx.EXPAND|wx.ALL, 10)

        #Add the buttons, and the button sizer.
        MainSizer.Add(self.DefaultRecButton, 4, wx.CENTER|wx.ALL, 10)
        MainSizer.Add(ButtonSizer, 4, wx.CENTER|wx.EXPAND|wx.ALL, 10)
        MainSizer.Add(self.ExitButton, 4, wx.CENTER|wx.ALL, 10)

        #Get the main sizer set up for the frame.
        self.Panel.SetSizer(MainSizer)
        MainSizer.SetMinSize(wx.Size(569,479))
        MainSizer.SetSizeHints(self)

    def BindEvents(self):
        """Bind all events for SettingsWindow"""
        self.Bind(wx.EVT_CHECKBOX, self.SetSoftRun, self.NoSplitCB)
        self.Bind(wx.EVT_BUTTON, self.SetDefaultRec, self.DefaultRecButton)
        self.Bind(wx.EVT_BUTTON, self.SetFastRec, self.FastRecButton)
        self.Bind(wx.EVT_BUTTON, self.SetBestRec, self.BestRecButton)
        self.Bind(wx.EVT_BUTTON, self.SaveOptions, self.ExitButton)
        self.Bind(wx.EVT_CLOSE, self.SaveOptions)

    def SetupOptions(self):
        """Set all options in the window so we remember them if the user checks back"""
        #Checkboxes:
        #Direct disk access setting.
        if Settings["DirectAccess"] == "-d":
            self.DirectAccessCB.SetValue(True)

        else:
            self.DirectAccessCB.SetValue(False)

        #Overwrite output Disk setting.
        if Settings["OverwriteOutputFile"] == "-f":
            self.OverwriteCB.SetValue(True)

        else:
            self.OverwriteCB.SetValue(False)

        #Reverse (read data from the end to the start of the input file) setting.
        if Settings["Reverse"] == "-R":
            self.ReverseCB.SetValue(True)

        else:
            self.ReverseCB.SetValue(False)

        #Preallocate (preallocate space in the output file) setting.
        if Settings["Preallocate"] == "-p":
            self.PreallocCB.SetValue(True)

        else:
            self.PreallocCB.SetValue(False)

        #NoSplit (Don't split failed blocks) option.
        if Settings["NoSplit"] == "-n":
            self.NoSplitCB.SetValue(True)

            #Disable self.BadSectChoice.
            self.BadSectChoice.Disable()

        else:
            self.NoSplitCB.SetValue(False)

            #Enable self.BadSectChoice.
            self.BadSectChoice.Enable()

        #ChoiceBoxes:
        #Retry bad sectors option.
        if Settings["BadSectorRetries"] == "-r 2":
            self.BadSectChoice.SetSelection(2)

        elif Settings["BadSectorRetries"] == "-r -1":
            self.BadSectChoice.SetSelection(5)

        else:
            self.BadSectChoice.SetSelection(int(Settings["BadSectorRetries"][3:]))

        #Maximum errors before exiting option.
        if Settings["MaxErrors"] == "":
            self.MaxErrorsChoice.SetStringSelection("Default (Infinite)")

        else:
            self.MaxErrorsChoice.SetStringSelection(Settings["MaxErrors"][3:])

        #ClusterSize (No. of sectors to copy at a time) option.
        if Settings["ClusterSize"] == "-c 128":
            self.ClustSizeChoice.SetStringSelection("Default (128)")

        else:
            self.ClustSizeChoice.SetStringSelection(Settings["ClusterSize"][3:])

    def SetSoftRun(self, Event=None):
        """Set up SettingsWindow based on the value of self.NoSplitCB (the "do soft run" CheckBox)"""
        logger.debug("SettingsWindow().SetSoftRun(): Do soft run: "+unicode(self.NoSplitCB.GetValue())+". Setting up SettingsWindow accordingly...")

        if self.NoSplitCB.IsChecked():
            self.BadSectChoice.SetSelection(0)
            self.BadSectChoice.Disable()

        else:
            self.BadSectChoice.Enable()
            self.SetDefaultRec()

    def SetDefaultRec(self, Event=None):
        """Set selections for the Choiceboxes to default settings"""
        logger.debug("SettingsWindow().SetDefaultRec(): Setting up SettingsWindow for default recovery settings...")

        if self.BadSectChoice.IsEnabled():
            self.BadSectChoice.SetSelection(2)

        self.MaxErrorsChoice.SetSelection(0)
        self.ClustSizeChoice.SetSelection(1)

    def SetFastRec(self, Event=None):
        """Set selections for the Choiceboxes to fast recovery settings"""
        logger.debug("SettingsWindow().SetFastRec(): Setting up SettingsWindow for fast recovery settings...")

        if self.BadSectChoice.IsEnabled():
            self.BadSectChoice.SetSelection(0)

        self.MaxErrorsChoice.SetSelection(0)
        self.ClustSizeChoice.SetSelection(0)

    def SetBestRec(self, Event=None):
        """Set selections for the Choiceboxes to best recovery settings"""
        logger.debug("SettingsWindow().SetBestRec(): Setting up SettingsWindow for best recovery settings...")
        if self.BadSectChoice.IsEnabled():
            self.BadSectChoice.SetSelection(2)

        self.MaxErrorsChoice.SetSelection(0)
        self.ClustSizeChoice.SetSelection(3)

    def SaveOptions(self, Event=None):
        """Save all options, and exit SettingsWindow"""
        logger.info("SettingsWindow().SaveOptions(): Saving Options...")

        #Checkboxes:
        #Direct disk access setting.
        if self.DirectAccessCB.IsChecked():
            Settings["DirectAccess"] = "-d"

        else:
            Settings["DirectAccess"] = ""

        logger.info("SettingsWindow().SaveOptions(): Use Direct Disk Access: "+unicode(bool(Settings["DirectAccess"]))+".")

        #Overwrite output Disk setting.
        if self.OverwriteCB.IsChecked():
            Settings["OverwriteOutputFile"] = "-f"

        else:
            Settings["OverwriteOutputFile"] = ""

        logger.info("SettingsWindow().SaveOptions(): Overwriting output file: "+unicode(bool(Settings["OverwriteOutputFile"]))+".")

        #Disk Size setting (OS X only).
        if Linux == False:
            #If the input file is in DiskInfo, use the Capacity from that.
            if Settings["InputFile"] in DiskInfo:
                Settings["DiskSize"] = "-s "+DiskInfo[Settings["InputFile"]]["Capacity"]
                logger.info("SettingsWindow().SaveOptions(): Using disk size: "+Settings["DiskSize"]+".")

            #Otherwise, it isn't needed.
            else:
                Settings["DiskSize"] = ""

        else:
            Settings["DiskSize"] = ""

        #Reverse (read data from the end to the start of the input file) setting.
        if self.ReverseCB.IsChecked():
            Settings["Reverse"] = "-R"

        else:
            Settings["Reverse"] = ""

        logger.info("SettingsWindow().SaveOptions(): Reverse direction of read operations: "+unicode(bool(Settings["Reverse"]))+".")

        #Preallocate (preallocate space in the output file) setting.
        if self.PreallocCB.IsChecked():
            Settings["Preallocate"] = "-p"

        else:
            Settings["Preallocate"] = ""

        logger.info("SettingsWindow().SaveOptions(): Preallocate disk space: "+unicode(bool(Settings["Preallocate"]))+".")

        #NoSplit (Don't split failed blocks) option.
        if self.NoSplitCB.IsChecked():
            Settings["NoSplit"] = "-n"

        else:
            Settings["NoSplit"] = ""

        logger.info("SettingsWindow().SaveOptions(): Split failed blocks: "+unicode(bool(Settings["NoSplit"]))+".") #*** Wrong way around? ***

        #ChoiceBoxes:
        #Retry bad sectors option.
        BadSectSelection = self.BadSectChoice.GetCurrentSelection()

        if BadSectSelection == 2:
            Settings["BadSectorRetries"] = "-r 2"

        elif BadSectSelection == 5:
            Settings["BadSectorRetries"] = "-r -1"

        else:
            Settings["BadSectorRetries"] = "-r "+unicode(BadSectSelection)

        logger.info("SettingsWindow().SaveOptions(): Retrying bad sectors "+Settings["BadSectorRetries"][3:]+" times.")

        #Maximum errors before exiting option.
        MaxErrorsSelection = self.MaxErrorsChoice.GetStringSelection()

        if MaxErrorsSelection == "Default (Infinite)":
            Settings["MaxErrors"] = ""
            logger.info("SettingsWindow().SaveOptions(): Allowing an infinite number of errors before exiting.")

        else:
            Settings["MaxErrors"] = "-e "+MaxErrorsSelection
            logger.info("SettingsWindow().SaveOptions(): Allowing "+Settings["MaxErrors"][3:]+" errors before exiting.")

        #ClusterSize (No. of sectors to copy at a time) option.
        ClustSizeSelection = self.ClustSizeChoice.GetStringSelection()

        if ClustSizeSelection == "Default (128)":
            Settings["ClusterSize"] = "-c 128"

        else:
            Settings["ClusterSize"] = "-c "+ClustSizeSelection

        logger.info("SettingsWindow().SaveOptions(): ClusterSize is "+Settings["ClusterSize"][3:]+".")

        #BlockSize detection.
        logger.info("SettingsWindow().SaveOptions(): Determining blocksize of input file...")
        Settings["InputFileBlockSize"] = DevInfoTools().GetBlockSize(Settings["InputFile"])

        if Settings["InputFileBlockSize"] != None:
            logger.info("SettingsWindow().SaveOptions(): BlockSize of input file: "+Settings["InputFileBlockSize"]+" (bytes).")
            Settings["InputFileBlockSize"] = "-b "+Settings["InputFileBlockSize"]

        else:
            #Input file is standard file, don't set blocksize, notify user.
            Settings["InputFileBlockSize"] = ""
            logger.info("SettingsWindow().SaveOptions(): Input file is a standard file, and therefore has no blocksize.")

        #Finally, exit
        logger.info("SettingsWindow().SaveOptions(): Finished saving options. Closing Settings Window...")
        self.Destroy()

#End Settings Window
#Begin Privacy Policy Window.
class PrivPolWindow(wx.Frame):
    def __init__(self, ParentWindow):
        """Initialize PrivPolWindow"""
        wx.Frame.__init__(self, parent=wx.GetApp().TopWindow, title="DDRescue-GUI - Privacy Policy", size=(400,310), style=wx.DEFAULT_FRAME_STYLE)
        self.Panel = wx.Panel(self)
        self.SetClientSize(wx.Size(400,310))
        self.ParentWindow = ParentWindow
        wx.Frame.SetIcon(self, AppIcon)

        logger.debug("PrivPolWindow().__init__(): Creating widgets...")
        self.CreateWidgets()

        logger.debug("PrivPolWindow().__init__(): Setting up sizers...")
        self.SetupSizers()

        logger.debug("PrivPolWindow().__init__(): Binding Events...")
        self.BindEvents()

        #Call Layout() on self.Panel() to ensure it displays properly.
        self.Panel.Layout()

        logger.debug("PrivPolWindow().__init__(): Ready. Waiting for events...")

    def CreateWidgets(self):
        """Create all widgets for PrivPolWindow"""
        #Make a text box to contain the policy's text.
        self.TextBox = wx.TextCtrl(self.Panel, -1, "", style=wx.TE_MULTILINE|wx.TE_READONLY|wx.TE_WORDWRAP)

        #Populate the text box.
        self.TextBox.LoadFile(RescourcePath+"/other/privacypolicy.txt")

        #Scroll the text box back up to the top.
        self.TextBox.SetInsertionPoint(0)

        #Make a button to close the dialog.
        self.CloseButton = wx.Button(self.Panel, -1, "Okay")

    def SetupSizers(self):
        """Set up sizers for PrivPolWindow"""
        #Make a boxsizer.
        MainSizer = wx.BoxSizer(wx.VERTICAL)

        #Add each object to the main sizer.
        MainSizer.Add(self.TextBox, 1, wx.EXPAND|wx.ALL, 10)
        MainSizer.Add(self.CloseButton, 0, wx.BOTTOM|wx.CENTER, 10)

        #Get the sizer set up for the frame.
        self.Panel.SetSizer(MainSizer)
        MainSizer.SetMinSize(wx.Size(400,310))
        MainSizer.SetSizeHints(self)

    def BindEvents(self):
        """Bind events so we can close this window."""
        self.Bind(wx.EVT_BUTTON, self.OnClose, self.CloseButton)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self,Event=None):
        """Close PrivPolWindow"""
        self.Destroy()

#End Privacy Policy Window.
#Begin Finished Window
class FinishedWindow(wx.Frame):  
    def __init__(self, ParentWindow, DiskCapacity, RecoveredData):
        """Initialize FinishedWindow"""
        wx.Frame.__init__(self, wx.GetApp().TopWindow, title="DDRescue-GUI - Finished!", size=(350,120), style=wx.DEFAULT_FRAME_STYLE)
        self.Panel = wx.Panel(self)
        self.SetClientSize(wx.Size(350,120))
        self.ParentWindow = ParentWindow
        self.DiskCapacity = DiskCapacity
        self.RecoveredData = RecoveredData
        self.OutputFileType = None
        self.OutputFileMountPoint = None
        wx.Frame.SetIcon(self, AppIcon)

        logger.debug("FinishedWindow().__init__(): Creating buttons...")
        self.CreateButtons()

        logger.debug("FinishedWindow().__init__(): Creating Text...")
        self.CreateText()

        logger.debug("FinishedWindow().__init__(): Setting up sizers...")
        self.SetupSizers()

        logger.debug("FinishedWindow().__init__(): Binding events...")
        self.BindEvents()

        #Call Layout() on self.Panel() to ensure it displays properly.
        self.Panel.Layout()

        logger.info("FinishedWindow().__init__(): Ready. Waiting for events...")

    def CreateButtons(self):
        """Create all buttons for FinishedWindow"""
        self.RestartButton = wx.Button(self.Panel, -1, "Reset")
        self.MountButton = wx.Button(self.Panel, -1, "Mount Image/Disk")
        self.QuitButton = wx.Button(self.Panel, -1, "Quit")

    def CreateText(self):
        """Create all text for FinishedWindow"""
        self.StatsText = wx.StaticText(self.Panel, -1, "Successfully recovered "+self.RecoveredData+" out of "+self.DiskCapacity+".")
        self.TopText = wx.StaticText(self.Panel, -1, "Your recovered data is at:")
        self.PathText = wx.StaticText(self.Panel, -1, Settings["OutputFile"])
        self.BottomText = wx.StaticText(self.Panel, -1, "What do you want to do now?")
    
    def SetupSizers(self):
        """Set up all sizers for FinishedWindow"""
        #Make a button boxsizer.
        ButtonSizer = wx.BoxSizer(wx.HORIZONTAL)

        #Add each object to the button sizer.
        ButtonSizer.Add(self.RestartButton, 4, wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 10)
        ButtonSizer.Add((5,5), 1)
        ButtonSizer.Add(self.MountButton, 8, wx.ALIGN_CENTER_VERTICAL)
        ButtonSizer.Add((5,5), 1)
        ButtonSizer.Add(self.QuitButton, 4, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 10)

        #Make a boxsizer.
        MainSizer = wx.BoxSizer(wx.VERTICAL)

        #Add each object to the main sizer.
        MainSizer.Add(self.StatsText, 1, wx.ALL ^ wx.BOTTOM|wx.CENTER, 10)
        MainSizer.Add(self.TopText, 1, wx.ALL ^ wx.BOTTOM|wx.CENTER, 10)
        MainSizer.Add(self.PathText, 1, wx.ALL ^ wx.BOTTOM|wx.CENTER, 10)
        MainSizer.Add(self.BottomText, 1, wx.ALL ^ wx.BOTTOM|wx.CENTER, 10)
        MainSizer.Add(ButtonSizer, 0, wx.BOTTOM|wx.EXPAND, 10)

        #Get the sizer set up for the frame.
        self.Panel.SetSizer(MainSizer)
        MainSizer.SetMinSize(wx.Size(350,120))
        MainSizer.SetSizeHints(self)

    def Restart(self, Event=None):
        """Close FinishedWindow and call MainWindow().Reload() to re-display and reset MainWindow"""
        logger.debug("FinishedWindow().Restart(): Triggering restart and closing FinishedWindow()...")
        wx.CallAfter(self.ParentWindow.Reload)
        self.Destroy()

    def OnMountButton(self, Event=None):
        """Triggered when mount button is pressed"""
        if self.MountButton.GetLabel() == "Mount Image/Disk":
            Success = self.MountOutputFile()

            #Change some stuff if it worked.
            if Success:
                self.TopText.SetLabel("Your recovered data is now mounted at:")
                self.PathText.SetLabel(self.OutputFileMountPoint)
                self.MountButton.SetLabel("Unmount Image/Disk")
                self.RestartButton.Disable()
                self.QuitButton.Disable()

                #Call Layout() on self.Panel() to ensure it displays properly.
                self.Panel.Layout()

                dlg = wx.MessageDialog(self.Panel, "Your output file is now mounted. Leave DDRescue-GUI open and click unmount when you're finished.", "DDRescue-GUI - Information", style=wx.OK | wx.ICON_INFORMATION, pos=wx.DefaultPosition)
                dlg.ShowModal()
                dlg.Destroy()

        else:
            Retvals = self.UnmountOutputFile()

            #Change some stuff if it worked.
            if Retvals == [0, 0] or Retvals == [0]:
                self.TopText.SetLabel("Your recovered data is at:")
                self.PathText.SetLabel(Settings["OutputFile"])
                self.MountButton.SetLabel("Mount Image/Disk")
                self.RestartButton.Enable()
                self.QuitButton.Enable()

                #Call Layout() on self.Panel() to ensure it displays properly.
                self.Panel.Layout()

        wx.CallAfter(self.ParentWindow.UpdateStatusBar, "Finished")

    def MountOutputFile(self, Event=None):
        """Handle errors and call the platform-dependent mounter function to mount the output file"""
        logger.debug("FinishedWindow().MountOutputFile(): Preparing to mount the output file...")

        #Use different methods for OS X and Linux. Also catch any unhandled errors.
        if Linux:
            MountFunction = self.MountDiskLinux

        else:
            MountFunction = self.MountDiskOSX


        try:
            return MountFunction()

        except:
            #An error has occured!
            Error = sys.exc_info()[0]
            logger.error("FinishedWindow().MountOutputFile(): Couldn't mount output file. The error was: "+unicode(Error)+". Warning user...")
            dlg = wx.MessageDialog(self.Panel, "Your output file could not be mounted!\n\nThe most likely reason for this is that the disk image is incomplete. If the disk image is complete, it may use an unsupported filesystem.\n\nIf you were asked which partition to mount, try again and choose a different one.\n\nThe error was: "+unicode(Error)+".", "DDRescue-GUI - Error!", style=wx.OK | wx.ICON_ERROR, pos=wx.DefaultPosition)
            dlg.ShowModal()
            dlg.Destroy()
            return False

    def UnmountOutputFile(self, Event=None):
        """Unmount the output file"""
        logger.info("FinishedWindow().UnmountOutputFile(): Attempting to unmount output file...")
        wx.CallAfter(self.ParentWindow.UpdateStatusBar, "Unmounting output file. This may take a few moments...")
        wx.Yield()
        Retvals = []
        Retvals.append(BackendTools().UnmountDisk(self.OutputFileMountPoint))

        #Check if it worked.
        if Retvals == [0]:
            logger.info("FinishedWindow().UnmountOutputFile(): Successfully unmounted output file...")

        else:
            logger.error("FinishedWindow().UnmountOutputFile(): Error unmounting output file! Return value: "+Retval+"...")

        #Linux: Pull down loops if the OutputFile is a Device. OS X: Detach the image's device file.
        if self.OutputFileType == "Device" and Linux:
            logger.debug("FinishedWindow().UnmountOutputFile(): Pulling down loop device...")
            Retvals.append(BackendTools().StartProcess(Command="kpartx -d "+Settings["OutputFile"], ReturnOutput=False))

        elif Linux == False:
            logger.error("FinishedWindow().UnmountOutputFile(): Detaching the device that represents the image...")
            Retvals.append(BackendTools().StartProcess(Command="hdiutil detach "+self.OutputFileDeviceName, ReturnOutput=False))

        if Retvals[-1] == 0:
            logger.info("FinishedWindow().UnmountOutputFile(): Successfully pulled down loop device...")

        else:
            logger.info("FinishedWindow().UnmountOutputFile(): Failed to pull down the loop device...")

        return Retvals

    def MountDiskOSX(self):
        """Mount the output file on OS X"""
        logger.info("FinishedWindow().MountDiskOSX(): Mounting Disk: "+Settings["OutputFile"]+"...")
        wx.CallAfter(self.ParentWindow.UpdateStatusBar, "Preparing to mount output file. Please Wait...")
        wx.Yield()

        #Determine if the OutputFile is a partition.
        Output = BackendTools().StartProcess(Command="hdiutil imageinfo "+Settings["OutputFile"]+" -plist", ReturnOutput=True)[1]

        if "whole disk" in Output:
            #The Output File must be a partition.
            logger.debug("FinishedWindow().MountDiskOSX(): Output file is a partition! Continuing...")
            wx.CallAfter(self.ParentWindow.UpdateStatusBar, "Mounting output file. This may take a few moments...")
            wx.Yield()
            self.OutputFileType = "Partition"

            #Attempt to mount the disk.
            Retval, Output = BackendTools().StartProcess(Command="hdiutil mount "+Settings["OutputFile"]+" -plist", ReturnOutput=True)

            #Parse the plist (Property List).
            Plist = plistlib.readPlistFromString(Output)

            #Get the mountpoint.
            MountedDisk = Plist["system-entities"][0]

            self.OutputFileDeviceName = MountedDisk["dev-entry"]
            self.OutputFileMountPoint = MountedDisk["mount-point"]

            #Check it worked.
            if Retval == 0:
                logger.info("FinishedWindow().MountDiskOSX(): Success! Waiting for user to finish with it and prompt to unmount it...")
                return True

            else:
                logger.error("FinishedWindow().MountDiskOSX(): Error! Warning the user...")
                dlg = wx.MessageDialog(self.Panel, "Couldn't mount your output file. Perhaps it uses an unsupported filesystem?", "DDRescue-GUI - Error!", style=wx.OK | wx.ICON_ERROR, pos=wx.DefaultPosition)
                dlg.ShowModal()
                dlg.Destroy()
                return False

        else:
            #The Output File must NOT be a partition!
            logger.debug("FinishedWindow().MountDiskOSX(): Output file isn't a partition! Getting list of contained partitions...")
            self.OutputFileType = "Device"

            #Parse the plist (Property List).
            Plist = plistlib.readPlistFromString(Output)

            Partitions = []

            #Find real partitions, not GPT headers and similar. If there's no partition number, ignore it.
            for Partition in Plist["partitions"]["partitions"]:
                if "partition-number" in Partition:
                     Partitions.append(Partition)

            #Get the block size of the image.
            Blocksize = Plist["partitions"]["block-size"]

            #Smarten this list up, and make it appear intuitive to the user.
            Choices = []

            for Partition in Partitions:
                #Get the info related to this partition.
                #Partition number.
                PartNum = Partition["partition-number"]

                #Disk size.
                DiskSize = (Partition["partition-length"] * Blocksize) // 1000000

                #Add stuff in an intuitive way.
                Choices.append("Partition "+unicode(PartNum)+" with size "+unicode(DiskSize)+" MB")

            #Ask the user which partition to mount.
            logger.debug("FinishedWindow().MountDiskOSX(): Asking user which partition to mount...")
            dlg = wx.SingleChoiceDialog(self.Panel, "Please select which partition you wish to mount", "DDRescue-GUI - Select a Partition", Choices, pos=wx.DefaultPosition)

            #Respond to the user's action.
            if dlg.ShowModal() != wx.ID_OK:
                self.OutputFileMountPoint = None
                logger.debug("FinishedWindow().MountDiskOSX(): User declined to mount any partitions...")
                return False

            else:
                SelectedPartNum = dlg.GetStringSelection().split()[1]

            #Attempt to mount the disk.
            wx.CallAfter(self.ParentWindow.UpdateStatusBar, "Mounting output file. This may take a few moments...")
            wx.Yield()
            logger.info("FinishedWindow().MountDiskOSX(): Mounting disk "+Settings["OutputFile"]+"...")
            Retval, Output = BackendTools().StartProcess(Command="hdiutil mount "+Settings["OutputFile"]+" -plist", ReturnOutput=True)

            try:
                #Parse the plist (Property List).
                Plist = plistlib.readPlistFromString(Output)
                Temp = Plist["system-entities"]

                #Get the device name (it doesn't matter which partition Temp[0] is, as hdiutil detach removes all of them anyway).
                self.OutputFileDeviceName = Temp[0]["dev-entry"]

                for Partition in Temp:
                    Disk = Partition["dev-entry"]

                    if Disk.split("s")[-1] == SelectedPartNum:
                        #Check if the partition we want was mounted (hdiutil mounts all mountable partitions in the image automatically).
                        if "mount-point" in Partition:
                            self.OutputFileMountPoint = Partition["mount-point"]
                            Retval = 0

                        else:
                            #It wasn't! Set Retval to 1 so we can handle the error and unmount the image again
                            Retval = 1
                            self.UnmountOutputFile()

            except:
                Retval = 1

            #Check it worked.
            if Retval == 0:
                logger.info("FinishedWindow().MountDiskOSX(): Success! Waiting for user to finish with it and prompt to unmount it...")
                return True

            else:
                logger.error("FinishedWindow().MountDiskOSX(): Error! Warning the user...")
                dlg = wx.MessageDialog(self.Panel, "Couldn't mount your selected partition. Perhaps it uses an unsupported filesystem?", "DDRescue-GUI - Error!", style=wx.OK | wx.ICON_ERROR, pos=wx.DefaultPosition)
                dlg.ShowModal()
                dlg.Destroy()
                return False

    def MountDiskLinux(self):
        """Mount the output file on Linux"""
        logger.info("FinishedWindow().MountDiskLinux(): Mounting Disk: "+Settings["OutputFile"]+"...")
        wx.CallAfter(self.ParentWindow.UpdateStatusBar, "Preparing to mount output file. Please Wait...")
        wx.Yield()

        #Determine if the OutputFile is a partition.
        if Settings["InputFile"] in DiskInfo:
            Type = DiskInfo[Settings["InputFile"]]["Type"]
            Partitions = BackendTools().StartProcess(Command="kpartx -l "+Settings["OutputFile"], ReturnOutput=True)[1].split('\n')

        else:
            Partitions = BackendTools().StartProcess(Command="kpartx -l "+Settings["OutputFile"], ReturnOutput=True)[1].split('\n')

            if Partitions == [""] or len(Partitions) == 1:
                Type = "Partition"

            else:
                Type = "Device"

        if Type == "Partition":
            logger.debug("FinishedWindow().MountDiskLinux(): Output file is a partition! Continuing...")
            wx.CallAfter(self.ParentWindow.UpdateStatusBar, "Mounting output file. This may take a few moments...")
            wx.Yield()
            self.OutputFileType = "Partition"
            self.OutputFileMountPoint = "/mnt"+Settings["InputFile"]

            #Attempt to mount the disk.
            if BackendTools().MountPartition(Partition=Settings["OutputFile"], MountPoint=self.OutputFileMountPoint) == 0:
                logger.info("FinishedWindow().MountDiskLinux(): Success! Waiting for user to finish with it and prompt to unmount it...")
                return True

            else:
                logger.error("FinishedWindow().MountDiskLinux(): Error! Warning the user...")
                dlg = wx.MessageDialog(self.Panel, "Couldn't mount your output file. Perhaps it uses an unsupported filesystem? Alternatively, it may still be too damaged to mount.", "DDRescue-GUI - Error!", style=wx.OK | wx.ICON_ERROR, pos=wx.DefaultPosition)
                dlg.ShowModal()
                dlg.Destroy()
                return False

        else:
            #The Output File must NOT be a partition!
            logger.debug("FinishedWindow().MountDiskLinux(): Output file isn't a partition! Getting list of contained partitions...")
            self.OutputFileType = "Device"

            #Create loop devices for all contained partitions.
            logger.info("FinishedWindow().MountDiskLinux(): Creating loop device...")
            BackendTools().StartProcess(Command="kpartx -a "+Settings["OutputFile"], ReturnOutput=False)

            #Get some Disk information.
            Output = BackendTools().StartProcess(Command="lsblk -r -o NAME,FSTYPE,SIZE", ReturnOutput=True)[1].split('\n')

            #Smarten this list up, and make it appear intuitive to the user.
            Choices = []

            for Partition in Partitions:
                #Skip non-partition things.
                if Partition[0:12] == "loop deleted" or "/dev/" not in Partition:
                    continue

                #Get the info related to this partition.
                for Line in Output:
                    if Partition.split()[0] in Line:
                        #Add stuff in an intuitive way.
                        Choices.append("Partition "+Partition.split()[0].split("p")[-1]+", Filesystem: "+Line.split()[-2]+", Size: "+Line.split()[-1])

            #Ask the user which partition to mount.
            logger.debug("FinishedWindow().MountDiskLinux(): Asking user which partition to mount...")
            dlg = wx.SingleChoiceDialog(self.Panel, "Please select which partition you wish to mount", "DDRescue-GUI - Select a Partition", Choices, pos=wx.DefaultPosition)

            #Respond to the user's action.
            if dlg.ShowModal() != wx.ID_OK:
                self.OutputFileMountPoint = None
                logger.debug("FinishedWindow().MountDiskLinux(): Pulling down loop device...")
                BackendTools().StartProcess(Command="kpartx -d "+Settings["OutputFile"], ReturnOutput=False)
                return False

            else:
                for Partition in Partitions:
                    if Partition[0:12] != "loop deleted" and "/dev/" in Partition:
                        CorrectDisk = Partition[0:6]+dlg.GetStringSelection().split()[1].replace(",", "")
                        break

                PartitionToMount = "/dev/mapper/"+CorrectDisk
                self.OutputFileMountPoint = "/mnt"+PartitionToMount

            #Attempt to mount the disk.
            logger.info("FinishedWindow().MountDiskLinux(): Mounting disk "+PartitionToMount+"...")
            wx.CallAfter(self.ParentWindow.UpdateStatusBar, "Mounting output file. This may take a few moments...")
            wx.Yield()
            Retval = BackendTools().MountPartition(Partition=PartitionToMount, MountPoint=self.OutputFileMountPoint)
            
            #Check it worked.
            if Retval == 0:
                logger.info("FinishedWindow().MountDiskLinux(): Success! Waiting for user to finish with it and prompt to unmount it...")
                return True

            else:
                logger.error("FinishedWindow().MountDiskLinux(): Error! Warning the user...")
                dlg = wx.MessageDialog(self.Panel, "Couldn't mount your selected partition. Perhaps it uses an unsupported filesystem?", "DDRescue-GUI - Error!", style=wx.OK | wx.ICON_ERROR, pos=wx.DefaultPosition)
                dlg.ShowModal()
                dlg.Destroy()
                return False

    def CloseFinished(self, Event=None):
        """Close FinishedWindow and trigger closure of MainWindow"""
        logger.info("FinishedWindow().CloseFinished(): Closing FinishedWindow() and calling self.ParentWindow().OnExit()...")
        self.Destroy()
        wx.CallAfter(self.ParentWindow.OnExit, JustFinishedRec=True)

    def BindEvents(self):
        """Bind all events for FinishedWindow"""
        self.Bind(wx.EVT_BUTTON, self.Restart, self.RestartButton)
        self.Bind(wx.EVT_BUTTON, self.OnMountButton, self.MountButton)
        self.Bind(wx.EVT_BUTTON, self.CloseFinished, self.QuitButton)
        self.Bind(wx.EVT_CLOSE, self.CloseFinished)

#End Finished Window
#Begin Elapsed Time Thread.
class ElapsedTimeThread(threading.Thread):
    def __init__(self, ParentWindow):
        """Initialize and start the thread"""
        self.ParentWindow = ParentWindow

        #This starts a little after ddrescue, so start at 2 seconds.
        self.RunTimeSecs = 2

        threading.Thread.__init__(self)
        self.start()

    def run(self):
        """Main body of the thread, started with self.start()"""
        while Settings["RecoveringData"]:
            #Elapsed time.
            self.RunTimeSecs += 1

            #Convert between Seconds, Minutes, Hours, and Days to make the value as understandable as possible.
            if self.RunTimeSecs <= 60:
                RunTime = self.RunTimeSecs
                Unit = " seconds"

            elif self.RunTimeSecs >= 60 and self.RunTimeSecs <= 3600: 
                RunTime = self.RunTimeSecs//60
                Unit = " minutes"

            elif self.RunTimeSecs > 3600 and self.RunTimeSecs <= 86400:
                RunTime = round(self.RunTimeSecs/3600,2)
                Unit = " hours"

            elif self.RunTimeSecs > 86400:
                RunTime = round(self.RunTimeSecs/86400,2)
                Unit = " days"

            #Update the text.
            wx.CallAfter(self.ParentWindow.UpdateTimeElapsed, "Time Elapsed: "+unicode(RunTime)+Unit)

            #Wait for a second.
            time.sleep(1)

#End Elapsed Time Thread
#Begin Backend Thread
class BackendThread(threading.Thread):
    def __init__(self, ParentWindow):
        """Initialize and start the thread."""
        self.ParentWindow = ParentWindow
        self.OldStatus = ""
        self.GotInitialStatus = False
        self.UnitList = ['null', 'B', 'k', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y']
        self.DDRescue121 = False
        self.InputPos = "0 B"

        threading.Thread.__init__(self)
        self.start()

    def run(self):
        """Main body of the thread, started with self.start()"""
        #Prepare to start ddrescue.
        logger.debug("MainBackendThread(): Preparing to start ddrescue...")
        OptionsList = [Settings["DirectAccess"], Settings["OverwriteOutputFile"], Settings["DiskSize"], Settings["Reverse"], Settings["Preallocate"], Settings["NoSplit"], Settings["BadSectorRetries"], Settings["MaxErrors"], Settings["ClusterSize"], Settings["InputFileBlockSize"], Settings["InputFile"], Settings["OutputFile"], Settings["LogFile"]]

        if Linux:
            ExecList = ["ddrescue", "-v"]

        else:
            ExecList = [RescourcePath+"/ddrescue", "-v"]

        for Option in OptionsList:
            #Handle direct disk access on OS X.
            if Linux == False and OptionsList.index(Option) == 0 and Option != "":
                #If we're recovering from a file, don't enable direct disk access (it won't work).
                if Settings["InputFile"][0:5] == "/dev/":
                    #Remove InputFile and switch it with a string that uses /dev/rdisk (raw disk) instead of /dev/disk.
                    OptionsList.pop(10)
                    OptionsList.insert(10, "/dev/r" + Settings["InputFile"].split("/dev/")[1])

                else:
                    #Make sure "-d" isn't added to the ExecList (continue to next iteration of loop).
                    continue
 
            elif Option != "":
                ExecList.append(Option)

        #Set initial values for some variables.
        self.DiskCapacity = "An unknown amount of"
        self.DiskCapacityUnit = "data."
        self.RecoveredData = 0
        self.RecoveredDataUnit = "B"

        #Start ddrescue.
        logger.debug("MainBackendThread(): Running ddrescue with: '"+' '.join(ExecList)+"'...")

        #Ensure the rest of the program knows we are recovering data.
        Settings["RecoveringData"] = True

        cmd = subprocess.Popen(ExecList, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        Line = ""
        LineList = []
        counter = 0

        #Give ddrescue plenty of time to start.
        time.sleep(2)

        #Grab information from ddrescue. (After ddrescue exits, attempt to read an extra 1000 chars to grab any remaining output)
        while cmd.poll() == None or counter < 1000:
            if cmd.poll() != None:
                counter += 1

            Char = cmd.stdout.read(1)
            Line += Char

            #If this is the end of the line, process it, and send the results to the GUI thread.
            if Char == "\n":
                TidyLine = Line.replace("\n", "").replace("\r", "").replace("\x1b[A", "")

                if TidyLine != "":
                    self.ProcessLine(TidyLine)

                wx.CallAfter(self.ParentWindow.UpdateOutputBox, Line.replace("\x1b[A", "¬"))

                #Reset Line.
                Line = ""

        #Let the GUI know that we are no longer recovering any data.
        Settings["RecoveringData"] = False

        #Check if we got ddrescue's init status, and if ddrescue exited with a status other than 0.
        if self.GotInitialStatus == False:
            logger.error("MainBackendThread(): We didn't get the initial status before ddrescue exited! Something has gone wrong. Telling MainWindow and exiting...")
            wx.CallAfter(self.ParentWindow.RecoveryEnded, DiskCapacity=unicode(self.DiskCapacity)+" "+self.DiskCapacityUnit, RecoveredData=unicode(int(self.RecoveredData))+" "+self.RecoveredDataUnit, Result="NoInitialStatus", ReturnCode=int(cmd.returncode))

        elif int(cmd.returncode) != 0:
            logger.error("MainBackendThread(): ddrescue exited with exit status "+unicode(cmd.returncode)+"! Something has gone wrong. Telling MainWindow and exiting...")
            wx.CallAfter(self.ParentWindow.RecoveryEnded, DiskCapacity=unicode(self.DiskCapacity)+" "+self.DiskCapacityUnit, RecoveredData=unicode(int(self.RecoveredData))+" "+self.RecoveredDataUnit, Result="BadReturnCode", ReturnCode=int(cmd.returncode))

        else:
            logger.info("MainBackendThread(): ddrescue finished recovering data. Telling MainWindow and exiting...")
            wx.CallAfter(self.ParentWindow.RecoveryEnded, DiskCapacity=unicode(self.DiskCapacity)+" "+self.DiskCapacityUnit, RecoveredData=unicode(int(self.RecoveredData))+" "+self.RecoveredDataUnit, Result="Success", ReturnCode=int(cmd.returncode))

    def ProcessLine(self, Line):
        """Process a given line to get ddrescue's current status and recovery information and send it to the GUI Thread""" 
        SplitLine = Line.split()

        if SplitLine[0] == "About":
            #Initial status.
            logger.info("MainBackendThread().Processline(): Got Initial Status... Setting up the progressbar...")
            self.GotInitialStatus = True

            #Use ddrescue's output. We can do this on OS X too cos ddrescue knows the disk size now.
            self.DiskCapacity = int(SplitLine[3])
            self.DiskCapacityUnit = SplitLine[4]

            wx.CallAfter(self.ParentWindow.SetProgressBarRange, self.DiskCapacity)

            #Start time elapsed thread.
            ElapsedTimeThread(self.ParentWindow)

        elif SplitLine[0] == "ipos:" and not self.DDRescue121:
            self.InputPos = ' '.join(SplitLine[1:3]).replace(",", "")
            self.NumErrors = SplitLine[4].replace(",", "")
            self.AverageReadRate = SplitLine[7]
            self.AverageReadRateUnit = SplitLine[8]

            wx.CallAfter(self.ParentWindow.UpdateIpos, self.InputPos)
            wx.CallAfter(self.ParentWindow.UpdateNumErrors, self.NumErrors)
            wx.CallAfter(self.ParentWindow.UpdateAverageReadRate, unicode(self.AverageReadRate)+" "+self.AverageReadRateUnit)

        elif SplitLine[0] == "opos:":
            self.OutputPos = ' '.join(SplitLine[1:3]).replace(",", "")

            wx.CallAfter(self.ParentWindow.UpdateOpos, self.OutputPos)

            #Add compatibility for newer versions of ddrescue (the output format changed when 'run time' was introduced with v1.18, and 'time remaining' in v1.20). Not on ddrescue 1.21.
            if self.DDRescue121:
                #Get average read rate (ddrescue 1.21).
                self.AverageReadRate = SplitLine[8]
                self.AverageReadRateUnit = SplitLine[9]
                wx.CallAfter(self.ParentWindow.UpdateAverageReadRate, unicode(self.AverageReadRate)+" "+self.AverageReadRateUnit)

            else:
                if SplitLine[-1] == "ago":
                    self.TimeSinceLastRead = ' '.join(SplitLine[-3:-1]) #v1.14 to v1.18.

                else:
                    self.TimeSinceLastRead = ' '.join(SplitLine[-2:]) #v1.18 to v1.20

                wx.CallAfter(self.ParentWindow.UpdateTimeSinceLastRead, self.TimeSinceLastRead)

        elif SplitLine[0] == "non-tried:":
            #Unreadable data (ddrescue 1.21).
            self.ErrorSize = ' '.join(SplitLine[4:6]).replace(",", "")

            wx.CallAfter(self.ParentWindow.UpdateErrorSize, self.ErrorSize)

        elif SplitLine[0] == "time":
            #Time since last read (ddrescue v1.20).
            self.TimeSinceLastRead = SplitLine[-1]

            wx.CallAfter(self.ParentWindow.UpdateTimeSinceLastRead, self.TimeSinceLastRead)

        elif SplitLine[0] == "percent":
            #Time since last read (ddrescue 1.21).
            self.TimeSinceLastRead = SplitLine[-1]

            wx.CallAfter(self.ParentWindow.UpdateTimeSinceLastRead, self.TimeSinceLastRead)

        elif SplitLine[-1] == "1.21":
            #We're on ddrescue 1.21.
            self.DDRescue121 = True

        elif SplitLine[0] == "rescued:" and self.DDRescue121:
            #Recovered data and number of errors (ddrescue 1.21).
            #Don't crash if we're reading the initial status from the logfile.
            try:
                self.RecoveredData = SplitLine[1]
                self.RecoveredDataUnit = SplitLine[2][:2]
                self.NumErrors = SplitLine[4].replace(",", "")

                #Change the unit of measurement of the current amount of recovered data if needed.
                self.RecoveredData, self.RecoveredDataUnit = self.ChangeUnits(float(self.RecoveredData), self.RecoveredDataUnit, self.DiskCapacityUnit)
                self.RecoveredData = round(self.RecoveredData,3)

                self.TimeRemaining = self.CalculateTimeRemaining()

                wx.CallAfter(self.ParentWindow.UpdateRecoveredData, unicode(self.RecoveredData)+" "+self.RecoveredDataUnit)
                wx.CallAfter(self.ParentWindow.UpdateNumErrors, self.NumErrors)
                wx.CallAfter(self.ParentWindow.UpdateProgress, self.RecoveredData, self.DiskCapacity)
                wx.CallAfter(self.ParentWindow.UpdateTimeRemaining, self.TimeRemaining)

            except AttributeError:
                pass

        elif ("rescued:" in Line and SplitLine[0] != "rescued:") or "ipos:" in Line:
            if self.DDRescue121:
                Status, Info = Line.split("ipos:")

            else:
                Status, Info = Line.split("rescued:")

            #Status Line.
            if Status != self.OldStatus:
                wx.CallAfter(self.ParentWindow.UpdateStatusBar, Status)
                self.OldStatus = Status

            SplitLine = Info.split()

            if self.DDRescue121:
                self.CurrentReadRate = ' '.join(SplitLine[7:9])
                self.InputPos = ' '.join(SplitLine[0:2]).replace(",", "")

                wx.CallAfter(self.ParentWindow.UpdateIpos, self.InputPos)

            else:
                self.CurrentReadRate = ' '.join(SplitLine[7:9])
                self.ErrorSize = ' '.join(SplitLine[3:5]).replace(",", "")
                self.RecoveredData = SplitLine[0]
                self.RecoveredDataUnit = SplitLine[1][:2]

                #Change the unit of measurement of the current amount of recovered data if needed.
                self.RecoveredData, self.RecoveredDataUnit = self.ChangeUnits(float(self.RecoveredData), self.RecoveredDataUnit, self.DiskCapacityUnit)
                self.RecoveredData = round(self.RecoveredData,3)

                self.TimeRemaining = self.CalculateTimeRemaining()

                wx.CallAfter(self.ParentWindow.UpdateErrorSize, self.ErrorSize)
                wx.CallAfter(self.ParentWindow.UpdateRecoveredData, unicode(self.RecoveredData)+" "+self.RecoveredDataUnit)
                wx.CallAfter(self.ParentWindow.UpdateProgress, self.RecoveredData, self.DiskCapacity)
                wx.CallAfter(self.ParentWindow.UpdateTimeRemaining, self.TimeRemaining)

            wx.CallAfter(self.ParentWindow.UpdateCurrentReadRate, self.CurrentReadRate)
            
    def ChangeUnits(self, NumberToChange, CurrentUnit, RequiredUnit):
        """Convert data so it uses the correct unit of measurement"""
        #Prepare for the change.
        CurrentUnitNumber = self.UnitList.index(CurrentUnit[0])
        RequiredUnitNumber = self.UnitList.index(RequiredUnit[0])
        ChangeInUnitNumber = RequiredUnitNumber - CurrentUnitNumber
        Power = -ChangeInUnitNumber * 3

        #Do it.
        return NumberToChange * 10**Power, RequiredUnit[:2]

    def CalculateTimeRemaining(self):
        """Calculate remaining time based on the average read rate and the current amount of data recovered"""
        #Make sure everything's in the correct units.
        NewAverageReadRate = self.ChangeUnits(float(self.AverageReadRate), self.AverageReadRateUnit, self.DiskCapacityUnit)[0]

        try:
            #Perform the calculation and round it.
            Result = (int(self.DiskCapacity) - self.RecoveredData) / NewAverageReadRate

            #Convert between Seconds, Minutes, Hours, and Days to make the value as understandable as possible.
            if Result <= 60:
                return unicode(int(round(Result)))+" seconds"
            elif Result >= 60 and Result <= 3600: 
                return unicode(round(Result/60,1))+" minutes"
            elif Result > 3600 and Result <= 86400:
                return unicode(round(Result/3600,2))+" hours"
            elif Result > 86400:
                return unicode(round(Result/86400,2))+" days"

        except ZeroDivisionError as Error:
            #We can't divide by zero!
            logger.warning("MainBackendThread().CalculateTimeRemaining(): Attempted to divide by zero! Error: "+unicode(Error)+". Returning 'Unknown'")
            return "Unknown"

#End Backend thread

if __name__ == "__main__":
    app = MyApp(False)
    app.MainLoop()
