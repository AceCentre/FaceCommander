# Standard library imports.
#
# Object oriented path handling.
# https://docs.python.org/3/library/pathlib.html
from pathlib import Path
#
# URL parsing module.
# https://docs.python.org/3/library/urllib.parse.html#urllib.parse.urlunsplit
from urllib.parse import urlunsplit
#
# Local imports.
#
from src.singleton_meta import Singleton
#
# PIP modules.
#
# https://platformdirs.readthedocs.io/en/latest/api.html
from platformdirs import user_data_dir
#
# Local imports.
#
from src.utils.readini import get_ini_value
import sys

APP_NAME = "FaceCommander"
APP_AUTHOR = "AceCentre"

LOG_FILENAME = "log.txt"

VERSION_INI_FILE = ("assets", "Version.ini")
VERSION_INI_SECTION = "Release"
VERSION_INI_KEY = "VersionNumber"

PROFILES_SUBDIRECTORY = ("configs",)
UPDATE_SUBDIRECTORY = ("update",)

# https://github.com/AceCentre/FaceCommander
REPOSITORY_UNSPLIT = (
    "https", "github.com", "/".join((APP_AUTHOR, APP_NAME)) , None, None)

# https://github.com/AceCentre/FaceCommander/releases
RELEASES_WEBSITE_UNSPLIT = (
    "https", "github.com", "/".join((APP_AUTHOR, APP_NAME, "releases"))
    , None, None)

# https://api.github.com/repos/AceCentre/FaceCommander/releases
RELEASES_API_UNSPLIT = (
    "https", "api.github.com"
    , "/".join(("repos", APP_AUTHOR, APP_NAME, "releases"))
    , None, None)

class App(metaclass=Singleton):

    def __init__(self):
        self._name = APP_NAME

        # Diagnostic command line options.
        self._userAgentHeader = True
        self._releaseInformationDelay = 0
        self._includePrereleases = False

        # Top-level paths.
        if getattr(sys, 'frozen', False):  # Check if running in PyInstaller bundle
            self._installationRoot = Path(sys._MEIPASS)
        else:
            self._installationRoot = Path(__file__).parents[1]
        self._dataRoot = None

        self._version = None

        self._logPath = None
        self._profilesDirectory = None
        self._builtInProfilesDirectory = None
        self._updateDirectory = None

        self._repositoryURL = urlunsplit(REPOSITORY_UNSPLIT)
        self._releasesWebsite = urlunsplit(RELEASES_WEBSITE_UNSPLIT)
        self._releasesAPI = urlunsplit(RELEASES_API_UNSPLIT)

    # Properties for command line switches.

    @property
    def userAgentHeader(self):
        return self._userAgentHeader
    @userAgentHeader.setter
    def userAgentHeader(self, userAgentHeader):
        self._userAgentHeader = userAgentHeader

    @property
    def releaseInformationDelay(self):
        return self._releaseInformationDelay
    @releaseInformationDelay.setter
    def releaseInformationDelay(self, releaseInformationDelay):
        self._releaseInformationDelay = releaseInformationDelay

    @property
    def includePrereleases(self):
        return self._includePrereleases
    @includePrereleases.setter
    def includePrereleases(self, includePrereleases):
        self._includePrereleases = includePrereleases

    # End of command line switches.

    @property
    def name(self):
        return self._name

    @property
    def installationRoot(self):
        return self._installationRoot
    
    @property
    def dataRoot(self):
        if self._dataRoot is None:
            self._dataRoot = Path(user_data_dir(
                appname=APP_NAME, appauthor=APP_AUTHOR))
        return self._dataRoot
    
    @property
    def version(self):
        if self._version is None:
            self._version = get_ini_value(
                Path(self.installationRoot, *VERSION_INI_FILE),
                VERSION_INI_SECTION, VERSION_INI_KEY)
        return self._version

    @property
    def logPath(self):
        if self._logPath is None:
            self._logPath = Path(self.dataRoot, LOG_FILENAME)
        return self._logPath
    
    @property
    def profilesDirectory(self):
        if self._profilesDirectory is None:
            self._profilesDirectory = Path(
                self.dataRoot, *PROFILES_SUBDIRECTORY)
        return self._profilesDirectory

    @property
    def builtInProfilesDirectory(self):
        if self._builtInProfilesDirectory is None:
            self._builtInProfilesDirectory = Path(
                self.installationRoot, *PROFILES_SUBDIRECTORY)
        return self._builtInProfilesDirectory

    @property
    def updateDirectory(self):
        if self._updateDirectory is None:
            self._updateDirectory = Path(self.dataRoot, *UPDATE_SUBDIRECTORY)
        return self._updateDirectory

    @property
    def repositoryURL(self):
        return self._repositoryURL

    @property
    def releasesAPI(self):
        return self._releasesAPI

    @property
    def releasesWebsite(self):
        return self._releasesWebsite