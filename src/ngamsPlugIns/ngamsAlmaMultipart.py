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
# "@(#) $Id: ngamsAlmaMultipart.py,v 1.3 2008/08/19 20:51:50 jknudstr Exp $"
#
# Who       When        What
# --------  ----------  -------------------------------------------------------
# awicenec  2004/10/01  Created
#
"""
This Data Archiving Plug-In is used to handle reception and processing
of ALMA multipart related message files containing ALMA UIDs.

Note, that the plug-in is implemented for the usage for ALMA. If used in other
contexts, a dedicated plug-in matching the individual context should be
implemented and NG/AMS configured to use it.
"""

import os

from mx import DateTime
from ngamsLib import ngamsPlugInApi
from ngamsLib.ngamsCore import genLog, info


_PLUGIN_ID = __name__

def specificTreatment(fo):
    """
    Method contains the specific treatment of the file passed from NG/AMS. 

    fo:         File object

    Returns:    (file_id, finalFileName, type); 
                The finalFileName is a string containing the name of the final 
                file without extension. type is the mime-type from the header.
    """
    import rfc822, cgi, re
    _EXT = '.msg'

    filename = fo.name

#    uidTempl = re.compile("[xX][0-9,a-f]{3,}/[xX][0-9,a-f]{1,}$")
# This matches the old UID of type    X0123456789abcdef/X01234567

    uidTempl = re.compile("^[uU][iI][dD]:/(/[xX][0-9,a-f,A-F]+){3}(#\w{1,}){0,}$")
# This matches the new UID structure uid://X1/X2/X3#kdgflf


    try:
        message = rfc822.Message(fo)
        type, tparams = cgi.parse_header(message["Content-Type"])
    except Exception, e:
        err = "Parsing of mime message failed: " + str(e)
        errMsg = genLog("NGAMS_ER_DAPI_BAD_FILE", [os.path.basename(filename),
                                                   _PLUGIN_ID, err])
        raise Exception, errMsg
    try:
       almaUid, aparams = cgi.parse_header(message["alma-uid"])
    except:

        err = "Mandatory alma-uid parameter not found in mime header!"
        errMsg = genLog("NGAMS_ER_DAPI_BAD_FILE", [os.path.basename(filename),
                                               _PLUGIN_ID, err])
        raise Exception, errMsg
    
    if not uidTempl.match(almaUid): 
        err = "Invalid alma-uid found: " + almaUid
        errMsg = genLog("NGAMS_ER_DAPI_BAD_FILE", [os.path.basename(filename),
                                               _PLUGIN_ID, err])
        raise Exception, errMsg
        
# Now, build final filename. We do that by looking for the UID in
# the message mime-header.

# The final filename is built as follows: <almaUidR>.<ext>
# where almaUidR has the slash character in the UID replaced by colons.
    try:
        # get rid of the 'uid://' and of anything following a '#' sign
        almaUid = almaUid.split('//',2)[1].split('#')[0]
        almaUid = almaUid.replace('x','X')
        
        fileId = almaUid
        finalFileName = almaUid.replace('/',':')
# Have no idea why, but the extension is added somewhere else...
#        if os.path.splitext(finalFileName)[-1] != _EXT:
#            finalFileName += _EXT
        
    except Exception, e:
        err = "Problem constructing final file name: " + str(e)
        errMsg = genLog("NGAMS_ER_DAPI_BAD_FILE", [os.path.basename(filename),
                                               _PLUGIN_ID, err])
        raise Exception, errMsg


    return (fileId, finalFileName, type)
  

def ngamsAlmaMultipart(srvObj,
                     reqPropsObj):
    """
    Data Archiving Plug-In to handle archiving of ALMA multipart related 
    message files containing ALMA UIDs.

    srvObj:       Reference to NG/AMS Server Object (ngamsServer).
     
    reqPropsObj:  NG/AMS request properties object (ngamsReqProps).
 
    Returns:      Standard NG/AMS Data Archiving Plug-In Status
                  as generated by: ngamsPlugInApi.genDapiSuccessStat()
                  (ngamsDapiStatus).
    """



    # For now the exception handling is pretty basic:
    # If something goes wrong during the handling it is tried to
    # move the temporary file to the Bad Files Area of the disk.
    info(1,"Plug-In handling data for file: " +
         os.path.basename(reqPropsObj.getFileUri()))
    diskInfo = reqPropsObj.getTargDiskInfo()
    stagingFilename = reqPropsObj.getStagingFilename()
    ext = os.path.splitext(stagingFilename)[1][1:]

    fo = open(stagingFilename, "r")
    (fileId, finalName, format) = specificTreatment(fo)
    
    fo.close()
    try:
        # Compress the file.
        uncomprSize = ngamsPlugInApi.getFileSize(stagingFilename)
        compression = ""
#        info(2,"Compressing file using: %s ..." % compression)
#        exitCode, stdOut = ngamsPlugInApi.execCmd("%s %s" %\
#                                                  (compression,
#                                                   stagingFilename))
#        if (exitCode != 0):
#            errMsg = _PLUGIN_ID+": Problems during archiving! " +\
#                     "Compressing the file failed"
#            raise Exception, errMsg
#        stagingFilename = stagingFilename + ".Z"
        # Remember to update the Temporary Filename in the Request
        # Properties Object.
        reqPropsObj.setStagingFilename(stagingFilename)
#        info(2,"File compressed")    
        
        # ToDo: Handling of non-existing fileId
#        if (fileId == -1):
#            fileId = ngamsPlugInApi.genNgasId(srvObj.getCfg())
        date = DateTime.now().date
        fileVersion, relPath, relFilename,\
                     complFilename, fileExists =\
                     ngamsPlugInApi.genFileInfo(srvObj.getDb(),
                                                srvObj.getCfg(),
                                                reqPropsObj, diskInfo,
                                                stagingFilename, fileId,
                                                finalName, [date])

        # Generate status.
        info(4,"Generating status ...")
        if not format:
            format = ngamsPlugInApi.determineMimeType(srvObj.getCfg(),
                                                  stagingFilename)
        fileSize = ngamsPlugInApi.getFileSize(stagingFilename)
        return ngamsPlugInApi.genDapiSuccessStat(diskInfo.getDiskId(),
                                                 relFilename,
                                                 fileId, fileVersion, format,
                                                 fileSize, uncomprSize,
                                                 compression, relPath,
                                                 diskInfo.getSlotId(),
                                                 fileExists, complFilename)
    except Exception, e:
        errMsg = genLog("NGAMS_ER_DAPI_BAD_FILE", [os.path.basename(stagingFilename),
                                                   _PLUGIN_ID, str(e)])
        raise Exception, errMsg
        
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print "Usage: ngamsAlmaMultipart.py <test_file>"
        sys.exit()
    try:
        fo = open(sys.argv[1],'r')
        (file_id,fileName, type) = specificTreatment(fo)
        print file_id, fileName, type
    except:
        raise
                    
    
#
# ___oOo___
