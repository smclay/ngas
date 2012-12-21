

#
#    ICRAR - International Centre for Radio Astronomy Research
#    (c) UWA - The University of Western Australia, 2012
#    Copyright by UWA (in the framework of the ICRAR)
#    All rights reserved
#
#    This library is free software; you can redistribute it and/or
#    modify it under the terms of the GNU Lesser General Public
#    License as published by the Free Software Foundation; either
#    version 2.1 of the License, or (at your option) any later version.
#
#    This library is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#    Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public
#    License along with this library; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston,
#    MA 02111-1307  USA
#

#******************************************************************************
#
# "@(#) $Id: ngasHandleNgamsLogFile.py,v 1.2 2008/08/19 20:37:45 jknudstr Exp $"
#
# Who       When        What
# --------  ----------  -------------------------------------------------------
# jknudstr  09/07/2001  Created
#

"""
Utility to handle the log files generated by NG/AMS. This is done by
moving a log files generated to a bak-log area, and to archive
from there the log files. Once, when archived, the files are deleted from
the bak-log directory.
"""

import os, sys, string, glob
import Sybase
import pcc, PccUtTime
from   ngams import *
import ngamsLib, ngamsPlugInApi, ngamsPClient, ngamsStatus


def correctUsage():
    """
    Print out correct usage of the tool on stdout.

    Returns:   Void.
    """
    print "\nCorrect usage is:\n"
    print "% ngasHandleNgamsLogFile -host <NG/AMS host> " +\
          "-port <NG/AMS port> -l <log file> " +\
          "-wd <working dir> [-v <level>]\n"

        
if __name__ == '__main__':
    """
    Main program archiving NG/AMS log files.
    """
    if (len(sys.argv) < 9):
        correctUsage()
        os._exit(1)
    host       = ""
    port       = -1
    logFile    = ""
    workingDir = ""
    logLevel   = 0
    idx        = 1
    while idx < len(sys.argv):
        par = sys.argv[idx]
        if (par == "-host"):
            idx += 1
            host = sys.argv[idx]
        elif (par == "-port"):
            idx += 1
            port = int(sys.argv[idx])
        elif (par == "-l"):
            idx += 1
            logFile = sys.argv[idx]
        elif (par == "-wd"):
            idx += 1
            workingDir = sys.argv[idx]
        elif (par == "-v"):
            idx += 1
            logLevel = int(sys.argv[idx])
        else:
             correctUsage()
             os._exit(1)
        idx += 1
    setLogCond(0, "", 0, "", logLevel)
 
    # Check input parameters.
    if ((host == "") or (port == -1) or (logFile == "") or (workingDir == "")):
        correctUsage()
        os._exit(1)

    # Generate filenames/path names.
    bakLogArea = os.path.join(workingDir, "back-log")
    ngamsLib.checkCreatePath(bakLogArea)
    os.chmod(bakLogArea, 0775)
    tmpLogFile = os.path.join(bakLogArea,
                              PccUtTime.TimeStamp().getTimeStamp() + ".nglog")

    # Move log file to bak-log directory + make new log file.
    if (os.path.exists(logFile)):
        info(1,"Moving log file: " + logFile +\
             " to bak-log area. Target file name: " + tmpLogFile)
        os.system("mv " + logFile + " " + tmpLogFile)
        info(1,"Creating new log file")
        os.system("touch " + logFile)
        os.chmod(logFile, 0664)

    # Try to archive the files in the bak-log area (if any).
    logFiles = glob.glob(bakLogArea + "/*")
    client = ngamsPClient.ngamsPClient(host, port)
    for lf in logFiles:
        info(1,"Archiving log file: " + lf)
        try:
            status = client.archive(lf)
        except Exception, e:
            error("Error occurred archiving log file: " + lf + ". Error: " +\
                  str(e))
            status = ngamsStatus.ngamsStatus().setStatus(NGAMS_FAILURE)

        # If the file was successfully archived, we can delete it.
        if (status.getStatus() == NGAMS_SUCCESS):
            info(1,"Log file: " + lf + " - successfully archived, removing")
            os.system("rm -f " + lf)
        else:
            info(1,"Problem archiving log file: " + lf +\
                 " - keeping in bak-log")


# EOF
