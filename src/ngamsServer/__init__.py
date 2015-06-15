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
# "@(#) $Id: __init__.py,v 1.3 2008/08/19 20:51:50 jknudstr Exp $"
#
# Who       When        What
# --------  ----------  -------------------------------------------------------
# jknudstr  11/06/2001  Created

# Dummy __init__.py file to build up the documentation for the module.

import os, sys

__all__ = ["ngamsArchiveCmd",
"ngamsArchiveUtils",
"ngamsAuthUtils",
"ngamsCacheControlThread",
"ngamsCacheDelCmd",
"ngamsCacheServer",
"ngamsCheckFileCmd",
"ngamsCloneCmd",
"ngamsCmdHandling",
"ngamsConfigCmd",
"ngamsDataCheckThread",
"ngamsDiscardCmd",
"ngamsExitCmd",
"ngamsFileUtils",
"ngamsHelpCmd",
"ngamsInitCmd",
"ngamsJanitorThread",
"ngamsLabelCmd",
"ngamsMirroringControlThread",
"ngamsOfflineCmd",
"ngamsOnlineCmd",
"ngamsRearchiveCmd",
"ngamsRegisterCmd",
"ngamsRemDiskCmd",
"ngamsRemFileCmd",
"ngamsRemUtils",
"ngamsRetrieveCmd",
"ngamsServer",
"ngamsSrvUtils",
"ngamsStatusCmd",
"ngamsSubscribeCmd",
"ngamsSubscriptionThread",
"ngamsUnsubscribeCmd",
"ngamsUserServiceThread",
]
NGAMS_SRC_DIR = __path__[0]
docFile = os.path.normpath(NGAMS_SRC_DIR + "/README")
fo = open(docFile)
__doc__ = fo.read()
fo.close()

# Create man-page for the NG/AMS Server.
srcDocFile = os.path.normpath(NGAMS_SRC_DIR +"/ngamsServer.doc")
trgDocFile = os.path.normpath(NGAMS_SRC_DIR +"/ngamsServer_doc.py")
fo = open(srcDocFile)
srcDoc = fo.read()
fo.close()
fo = open(trgDocFile, "w")
fo.write('"""\n' + srcDoc + '\n"""\n\n# EOF\n')
fo.close()

# EOF:
