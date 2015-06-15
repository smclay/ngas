#******************************************************************************
# ESO/DMD
#
# "@(#) $Id: ngasTarBallPlugIn.py,v 1.1 2009/01/16 13:57:59 awicenec Exp $"
#
# Who       When        What
# --------  ----------  -------------------------------------------------------
# jknudstr  05/11/2003  Created
#
"""
This Data Archiving Plug-In is used to handle archiving of tarball files.
The File ID is derived from the filename. This means that the filename
must be of the form: '<File ID>.tar'.

Note, that the plug-in is implemented for the usage at ESO. If used in other
contexts, a dedicated plug-in matching the individual context should be
implemented and NG/AMS configured to use it.
"""

import os, commands

from pccUt import PccUtTime
from ngamsLib import ngamsPlugInApi
from ngamsLib.ngamsCore import rmFile, genLog, error, info


def checkTarball(filename):
    """
    Check that the tarball is correct
    
    filename:  Name of tarball file (string).

    Returns:   Void.
    """
    err = 0
    tmpFilename = filename.replace(":", "_") + "_tmp"
    try:
        commands.getstatusoutput("ln -s " + filename + " " + tmpFilename)
        stat, out = commands.getstatusoutput("tar -tf " + tmpFilename)
        rmFile(tmpFilename)
        if (stat != 0):
            errMsg = str(out).replace("\n", " --- ")
            err = 1
    except Exception, e:
        rmFile(tmpFilename)
        errMsg = str(e)
        err = 1
    if (err):
        errMsg = "Error checking tarball: " + errMsg
        errMsg = genLog("NGAMS_ER_DAPI_BAD_FILE",
                        [filename, "ngasTarBallPlugIn", errMsg])
        error(errMsg)
        raise Exception, errMsg
        

# DAPI function.
def ngasTarBallPlugIn(srvObj,
                      reqPropsObj):
    """
    Data Archiving Plug-In to handle archiving of tarballs.

    srvObj:       Reference to NG/AMS Server Object (ngamsServer).
    
    reqPropsObj:  NG/AMS request properties object (ngamsReqProps).

    Returns:      Standard NG/AMS Data Archiving Plug-In Status
                  as generated by: ngamsPlugInApi.genDapiSuccessStat()
                  (ngamsDapiStatus).
    """
    stagingFilename = reqPropsObj.getStagingFilename()
    info(1,"Plug-In handling data for file with URI: " +
         os.path.basename(reqPropsObj.getFileUri()))
    diskInfo = reqPropsObj.getTargDiskInfo()

    # Check file.
    checkTarball(stagingFilename)

    # Get various information about the file being handled.
    fileId       = os.path.basename(reqPropsObj.getFileUri())
    obsDay = (PccUtTime.TimeStamp(fileId[fileId.find(".") + 1:]).getMjd()-0.5)
    obsDayTime = PccUtTime.TimeStamp(obsDay).getTimeStamp()
    dateDirName = obsDayTime.split("T")[0]
    baseFilename = fileId[0:-4]
    fileVersion, relPath, relFilename,\
                 complFilename, fileExists =\
                 ngamsPlugInApi.genFileInfo(srvObj.getDb(), srvObj.getCfg(),
                                            reqPropsObj, diskInfo,
                                            stagingFilename, fileId,
                                            baseFilename, [dateDirName], [])

    # Generate status.
    info(4,"Generating status ...")
    format       = "application/x-tar"
    fileSize     = ngamsPlugInApi.getFileSize(stagingFilename)
    info(3,"DAPI finished processing of file")
    return ngamsPlugInApi.genDapiSuccessStat(diskInfo.getDiskId(), relFilename,
                                             fileId, fileVersion, format,
                                             fileSize, fileSize, "NONE",
                                             relPath, diskInfo.getSlotId(),
                                             fileExists, complFilename)

#
# ___oOo___
