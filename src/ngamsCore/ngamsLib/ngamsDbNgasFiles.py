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
# "@(#) $Id: ngamsDbNgasFiles.py,v 1.11 2008/08/19 20:51:50 jknudstr Exp $"
#
# Who       When        What
# --------  ----------  -------------------------------------------------------
# jknudstr  07/03/2008  Created
#
"""
Contains queries for accessing the NGAS Files Table.

This class is not supposed to be used standalone in the present implementation.
It should be used as part of the ngamsDbBase parent classes.
"""

import collections
import logging
import os
import re
import tempfile

import six
from six.moves import cPickle  # @UnresolvedImport

from . import ngamsDbCore, ngamsFileInfo, ngamsStatus, ngamsFileList
from .ngamsCore import NGAMS_DB_CH_FILE_DELETE, NGAMS_DB_CH_CACHE
from .ngamsCore import rmFile, getNgamsVersion, toiso8601, fromiso8601, mvFile


logger = logging.getLogger(__name__)


def two_stage_pickle(mtdir, obj):
    """
    Performs a two-stage writing of a new .pickle file under the cache directory
    of the indicated mount directory. The file is first written with a .tmp
    and later renamed to have a .pickle extension so the Janitor Thread doesn't
    pick it up
 until it's completed.
    """

    dirname = os.path.join(mtdir, NGAMS_DB_CH_CACHE)
    tmpfd, tmpfname = tempfile.mkstemp(".tmp", dir=dirname, text=False)
    fd, fname = tempfile.mkstemp(".pickle", dir=dirname, text=False)
    os.close(fd)

    try:
        with os.fdopen(tmpfd, "wb") as pickleFo:
            cPickle.dump(obj, pickleFo, 1)
        mvFile(tmpfname, fname)
    except:
        rmFile(tmpfname)
        raise


class ngamsDbNgasFiles(ngamsDbCore.ngamsDbCore):
    """
    Contains queries for accessing the NGAS Files Table.
    """

    def fileInDb(self,
                 diskId,
                 fileId,
                 fileVersion = -1):
        """
        Check if file with the given File ID is registered in NGAS DB
        in connection with the given Disk ID.

        diskId:        Disk ID (string)

        fileId:        File ID (string).

        fileVersion:   Version of the file. If -1 version is not taken
                       into account (integer).

        Returns:       1 = file found, 0 = file no found (integer).
        """
        sql = ["SELECT file_id FROM ngas_files WHERE file_id={0} AND disk_id={1}"]
        args = [fileId, diskId]
        if fileVersion != -1:
            sql.append(" AND file_version={2}")
            args.append(fileVersion)

        res = self.query2(''.join(sql), args=args)
        if len(res) == 1:
            return 1
        return 0


    def getFileInfoFromDiskIdFilename(self,
                                      diskId,
                                      filename):
        """
        The method queries the file information for a file referred to by the
        Disk ID for the disk hosting it and the filename as stored in the
        NGAS DB.

        diskId:      ID for disk hosting the file (string).

        filename:    NGAS (relative) filename (string).

        Returns:     Return ngamsFileInfo object with the information for the
                     file if found or None if the file was not found
                     (ngamsFileInfo|None).
        """
        # Query for the file.
        sql = "SELECT %s FROM ngas_files nf WHERE nf.disk_id={0} AND nf.file_name={1}"
        sql = sql % (ngamsDbCore.getNgasFilesCols(self._file_ignore_columnname),)

        # Execute the query directly and return the result.
        res = self.query2(sql, args=(diskId, filename))
        if res:
            return ngamsFileInfo.ngamsFileInfo().unpackSqlResult(res[0])
        else:
            return None


    def getFileInfoList(self,
                        diskId,
                        fileId = "",
                        fileVersion = -1,
                        ignore = None,
                        fetch_size = 1000):
        """
        The function queries a set of files matching the conditions
        specified in the input parameters.

        diskId:        Disk ID of disk hosting the file(s) (string).

        fileId:        File ID of files to consider. Wildcards can be
                       used (string).

        fileVersion:   Version of file(s) to consider. If set to -1 this
                       is not taken into account (integer).

        ignore:        If set to 0 or 1, this value of ignore will be
                       queried for. If set to None, ignore is not
                       considered (None|0|1).

        Returns:       Cursor object (<NG/AMS DB Cursor Object API>).
        """
        cond_sql = collections.OrderedDict()
        if fileId:
            fileId = re.sub(r"\*", "%", fileId)
            st = "nf.file_id LIKE {}" if '%' in fileId else "nf.file_id = {}"
            cond_sql[st] = fileId

        if diskId:
            cond_sql["nf.disk_id = {}"] = diskId

        if fileVersion != -1:
            cond_sql["nf.file_version = {}"] = fileVersion

        if ignore is not None:
            cond_sql["nf.%s = {}" % (self._file_ignore_columnname,)] = ignore

        # Create a cursor and perform the query.
        sql = ["SELECT %s FROM ngas_files nf" % (ngamsDbCore.getNgasFilesCols(self._file_ignore_columnname))]
        if cond_sql:
            sql.append(" WHERE ")
            sql.append(" AND ".join(cond_sql.keys()))

        cursor = self.dbCursor(''.join(sql), args=list(six.itervalues(cond_sql)))
        with cursor:
            for x in cursor.fetch(fetch_size):
                yield x


    def getLatestFileVersion(self,
                             fileId):
        """
        The method queries the latest File Version for the file with the given
        File ID. If a file with the given ID does not exist, -1 is returned.

        fileId:    File ID (string).

        Returns:   Latest File Version (integer).
        """
        sql = "SELECT max(file_version) FROM ngas_files WHERE file_id={0}"
        res = self.query2(sql, args=(fileId,))
        if res:
            if res[0][0] is None:
                return -1
            return int(res[0][0])
        return -1

    def getFileStatus(self,
                      fileId,
                      fileVersion,
                      diskId):
        """
        Get the file_status string (bit) value in the ngas_files table.

        fileId:        ID of file (string).

        fileVersion:   Version of file (integer).

        diskId:        Disk ID for disk where file is stored (string).

        Returns:       File Status (8 bits) (string).

        """
        sql = "SELECT file_status FROM ngas_files WHERE file_id = {0} AND disk_id = {1} AND file_version = {2}"
        res = self.query2(sql, args=(fileId, diskId, fileVersion))
        if (len(res)):
            if res[0][0] is None:
                return '00000000'
            return res[0][0]
        raise Exception('File not found in ngas db - %s,%s,%d' % (fileId, diskId, fileVersion))

    def deleteFileInfo(self,
                       hostId,
                       diskId,
                       fileId,
                       fileVersion,
                       genSnapshot = 1):
        """
        Delete one record for a certain file in the NGAS DB.

        CAUTION:  IF THE DB USER WITH WHICH THERE IS LOGGED IN HAS PERMISSION
                  TO EXECUTE DELETE STATEMENTS, THE INFORMATION ABOUT THE
                  FILE(S) IN THE NGAS DB WILL BE DELETED! THIS INFORMATION
                  CANNOT BE RECOVERED!!

        diskId:         ID of disk hosting the file (string).

        fileId:         ID of file to be deleted. No wildcards accepted
                        (string).

        fileVersion:    Version of file to delete (integer)

        genSnapshot:    Generate Db Snapshot (integer/0|1).

        Returns:        Reference to object itself.
        """
        # We have to update some fields of the disk hosting the file
        # when we delete a file (number_of_files, available_mb,
        # bytes_stored, also maybe later: checksum.
        dbDiskInfo = self.getDiskInfoFromDiskId(diskId)

        # getFileInfoList returns a generator, so we iterate once to get the first element
        try:
            dbFileInfo = next(self.getFileInfoList(diskId, fileId, fileVersion))
        except StopIteration:
            msg = "Cannot remove file. File ID: %s, " +\
                  "File Version: %d, Disk ID: %s"
            errMsg = msg % (fileId, fileVersion, diskId)
            raise Exception(errMsg)

        sql = "DELETE FROM ngas_files WHERE disk_id={0} AND file_id={1} AND file_version={2}"
        self.query2(sql, args=(diskId, fileId, fileVersion))

        # Create a File Removal Status Document.
        if (self.getCreateDbSnapshot() and genSnapshot):
            tmpFileObj = ngamsFileInfo.ngamsFileInfo().\
                         unpackSqlResult(dbFileInfo)
            self.createDbFileChangeStatusDoc(hostId, NGAMS_DB_CH_FILE_DELETE,
                                             [tmpFileObj])

        # Now update the ngas_disks entry for the disk hosting the file.
        if (dbDiskInfo):
            newNumberOfFiles = (dbDiskInfo[ngamsDbCore.\
                                           NGAS_DISKS_NO_OF_FILES] - 1)
            if (newNumberOfFiles < 0): newNumberOfFiles = 0
            newAvailMb = (dbDiskInfo[ngamsDbCore.NGAS_DISKS_AVAIL_MB] +
                          int(float(dbFileInfo[ngamsDbCore.\
                                               NGAS_FILES_FILE_SIZE])/1e6))
            newBytesStored = (dbDiskInfo[ngamsDbCore.\
                                         NGAS_DISKS_BYTES_STORED] -
                              dbFileInfo[ngamsDbCore.NGAS_FILES_FILE_SIZE])
            if (newBytesStored < 0): newBytesStored = 0
            sql = "UPDATE ngas_disks SET number_of_files={0}, " +\
                  "available_mb={1}, bytes_stored={2} WHERE disk_id={3}"
            self.query2(sql, args=(newNumberOfFiles, newAvailMb, newBytesStored, diskId))

        self.triggerEvents()
        return self


    def getSumBytesStored(self,
                          diskId):
        """
        Get the total sum of the sizes of the data files stored on a disk
        and return this.

        diskId:    Disk ID of disk to get the sum for (string).

        Return:    Total sum of bytes stored on the disk (integer).
        """
        sql = "SELECT sum(file_size) from ngas_files WHERE disk_id={0}"
        res = self.query2(sql, args=(diskId,))
        if res[0][0] is not None:
            return res[0][0]
        return 0


    def createDbFileChangeStatusDoc(self,
                                    hostId,
                                    operation,
                                    fileInfoObjList,
                                    diskInfoObjList = []):
        """
        The function creates a pickle document in the '<Disk Mt Pt>/.db/cache'
        directory from the information in the 'fileInfoObj' object.

        operation:        Has to be either ngams.NGAMS_DB_CH_FILE_INSERT or
                          ngams.NGAMS_DB_CH_FILE_DELETE (string).

        fileInfoObj:      List of instances of NG/AMS File Info Object
                          containing the information about the file
                          (list/ngamsFileInfo).

        diskInfoObjList:  It is possible to give the information about the
                          disk(s) in question via a list of ngamsDiskInfo
                          objects (list/ngamsDiskInfo).

        Returns:          Void.
        """
        # TODO: Implementation concern: This class is suppose to be
        # at a lower level in the hierarchie than the ngamsFileInfo,
        # ngamsFileList, ngamsDiskInfo and ngamsStatus classes and as
        # such these should not be used from within this class. All usage
        # of these classes in the ngamsDbBase class should be analyzed.
        # Probably these classes should be made base classes for this class.

        # TODO: Potential memory bottleneck.

        timeStamp = toiso8601()

        # Sort the File Info Objects according to disks.
        fileInfoObjDic = {}
        for fileInfo in fileInfoObjList:
            if fileInfo.getDiskId() not in fileInfoObjDic:
                fileInfoObjDic[fileInfo.getDiskId()] = []
            fileInfoObjDic[fileInfo.getDiskId()].append(fileInfo)

        # Get the mount points for the various disks concerned.
        mtPtDic = {}
        if (diskInfoObjList == []):
            diskIdMtPtList = self.getDiskIdsMtPtsMountedDisks(hostId)
            for diskId, mtPt in diskIdMtPtList:
                mtPtDic[diskId] = mtPt
        else:
            for diskInfoObj in diskInfoObjList:
                mtPtDic[diskInfoObj.getDiskId()] = diskInfoObj.getMountPoint()

        # Create on each disk the relevant DB Change Status Document.
        tmpFileList = None
        for diskId in fileInfoObjDic.keys():

            if ((len(fileInfoObjList) == 1) and (diskInfoObjList == [])):
                tmpStatObj = fileInfoObjList[0].setTag(operation)
            else:
                # Apparently the dbId is used only as the ID of the file list,
                # which is totally irrelevant (this object seems to be read on
                # ngamsJanitorThread#checkDbChangeCache)
                dbId = diskId + "." + timeStamp
                tmpFileObjList = fileInfoObjDic[diskId]
                tmpFileList = ngamsFileList.ngamsFileList(dbId, operation)
                for fileObj in tmpFileObjList:
                    tmpFileList.addFileInfoObj(fileObj)
                tmpStatObj = ngamsStatus.ngamsStatus().\
                             setDate(timeStamp).\
                             setVersion(getNgamsVersion()).\
                             setHostId(hostId).\
                             setMessage(dbId).\
                             addFileList(tmpFileList)

            two_stage_pickle(mtPtDic[diskId], tmpStatObj)


    def createDbRemFileChangeStatusDoc(self,
                                       diskInfoObj,
                                       fileInfoObj):
        """
        The function creates a File Removal Status Document with the
        information about a file, which has been removed from the DB and
        which should be removed from the DB Snapshot for the disk concerned.

        diskInfoObj:      Disk Info Object with info for disk concerned
                          (ngamsDiskInfo).

        fileInfoObj:      Instance of NG/AMS File Info Object
                          containing the information about the file
                          (ngamsFileInfo).

        Returns:          Void.
        """
        fo = fileInfoObj
        fileinfo_list = [fo.getDiskId(), fo.getFileId(), fo.getFileVersion()]
        two_stage_pickle(diskInfoObj.getMountPoint(), fileinfo_list)


    def getFileChecksum(self, diskId, fileId, fileVersion):
        """
        Get the checksum for the file.

        diskId:         ID of disk hosting the file (string).

        fileId:         ID of file to be deleted. No wildcards accepted
                        (string).

        fileVersion:    Version of file to delete (integer)

        Returns:        checksum (string | None).
        """
        sql = "SELECT checksum FROM ngas_files WHERE file_id={0} AND file_version={1} AND disk_id={2}"
        res = self.query2(sql, args=(fileId, fileVersion, diskId)) # throw exception if an empty record
        if res:
            return res[0][0]
        return None

    def getFileChecksumValueAndVariant(self, diskId, fileId, fileVersion):
        """
        Get the checksum value and variant for the file.

        diskId:         ID of disk hosting the file (string).

        fileId:         ID of file to be deleted. No wildcards accepted
                        (string).

        fileVersion:    Version of file to delete (integer)

        Returns:        checksum (string | None).
        """
        sql = "SELECT checksum, checksum_plugin FROM ngas_files WHERE file_id={0} AND file_version={1} AND disk_id={2}"
        res = self.query2(sql, args=(fileId, fileVersion, diskId)) # throw exception if an empty record
        if res:
            return res[0]
        return None, None


    def getIngDate(self,
                   diskId,
                   fileId,
                   fileVersion):
        """
        Get the ingestion date for the file.

        diskId:         ID of disk hosting the file (string).

        fileId:         ID of file to be deleted. No wildcards accepted
                        (string).

        fileVersion:    Version of file to delete (integer)

        Returns:        Ingestion date for file or None if file not found
                        (string/ISO 8601 | None).
        """
        sql = "SELECT ingestion_date FROM ngas_files WHERE disk_id={0} AND file_id={1} AND file_version={2}"
        res = self.query2(sql, args=(diskId, fileId, fileVersion))
        if res:
            if (res[0][0] == None):
                return None
            return fromiso8601(res[0][0], local=True)
        return None

    def getFileSize(self,
                   fileId,
                   fileVersion):
        """
        Get the ingestion date for the file.

        diskId:         ID of disk hosting the file (string).

        fileId:         ID of file to be deleted. No wildcards accepted
                        (string).

        fileVersion:    Version of file to delete (integer)

        Returns:        Ingestion date for file or None if file not found
                        (string/ISO 8601 | None).
        """
        sql = "SELECT file_size FROM ngas_files WHERE file_id={0} AND file_version={1}"
        res = self.query2(sql, args=(fileId, fileVersion))
        if res:
            if (res[0][0] == None):
                return None
            return res[0][0]
        return None

    def addFileToContainer(self, containerId, fileId, force):
        """
        Adds the file pointed by fileId to the container
        pointed by containerId. If the file doesn't exist an
        error will be raised. If the file is currently associated
        with a container and the force flag is not True an
        error will be raised also.

        This method returns the uncompressed size of the file just
        added to the container. This can then be used to update the total
        size of the container

        :param str containerId: the id of the container where the file will be added
        :param str fileId: the id of the file to add to the container
        :param bool force: force the operation
        :return: the uncompressed file size of the file denoted by `fileId`
        """
        # Check if the file exists, and if
        # it already is contained in another container
        # We take into account only the latest version of the file for this
        sql = "SELECT container_id, uncompressed_file_size FROM ngas_files WHERE file_id = {0} ORDER BY file_version DESC"
        res = self.query2(sql, args=(fileId,))
        if not res:
            msg = "No file with fileId '%s' found, cannot append it to container" % (fileId,)
            raise Exception(msg)

        prevConatinerId = res[0][0]
        fileSize = res[0][1]
        if prevConatinerId:
            if prevConatinerId == containerId:
                logger.debug('File %s already belongs to container %s, skipping it', fileId, containerId)
                return 0

            if not force:
                msg = "File '%s' is already associated to container '%s'. To override the 'force' parameter must be given" % (fileId, prevConatinerId)
                raise Exception(msg)

        # Update all versions and copies of the file, since the grouping by container
        # is at fileId level
        sql = "UPDATE ngas_files SET container_id = {0} WHERE file_id = {1}"
        self.query2(sql, args=(containerId,fileId))
        logger.debug('File %s added to container %s', fileId,containerId)

        return fileSize

    def removeFileFromContainer(self, fileId, containerId):
        """
        Removes the file pointed by fileId from the container
        pointed by containerId. If the file doesn't exist an
        error will be raised. If the file is currently not associated
        with the indicated container and error will be raised also.

        This method returns the uncompressed size of the file just
        removed from the container. This can then be used to update the total
        size of the container

        :param str fileId: the id to remove from the container
        :param str containerId: the container from which the file needs to be removed
        :return: the uncompressed size of the file just removed from the container
        :rtype: integer
        """

        sql = "SELECT container_id, uncompressed_file_size FROM ngas_files WHERE file_id = {0} ORDER BY file_version DESC"
        res = self.query2(sql, args=(fileId,))
        if not res:
            msg = "No file with fileId '%s' found, cannot append it to container" % (fileId,)
            raise Exception(msg)

        currentContainerId = res[0][0]
        fileSize = res[0][1]
        if not currentContainerId:
            logger.debug("File with fileId '%s' is part of no container, skipping it", fileId)
            return 0
        elif currentContainerId != containerId:
            msg = "File with fileId '%s' is associated with a different container: %s" % (fileId,currentContainerId)
            raise Exception(msg)

        # Update all versions and copies of the file, since the grouping by container
        # is at fileId level
        sql = "UPDATE ngas_files SET container_id = null WHERE file_id = {0}"
        self.query2(sql, args=(fileId,))
        logger.debug('File %s was removed from container %s', fileId,containerId)

        return fileSize

    def isLastVersion(self, fileId, version):
        sql = "SELECT MAX(file_version) FROM ngas_files WHERE file_id = {0}"
        res = self.query2(sql, args=(fileId,))
        if not res:
            return True
        return version == int(res[0][0])

    def _modify_status_bits(self, file_id, file_version, disk_id, bits, on):

        select_status = 'SELECT file_status FROM ngas_files WHERE file_id={0} AND file_version={1} AND disk_id={2}'
        update = 'UPDATE ngas_files SET file_status={0} WHERE file_id={1} AND file_version={2} AND disk_id={3}'

        with self.transaction() as t:

            # select
            res = t.execute(select_status, args=(file_id, file_version, disk_id))[0][0]
            if not res:
                logger.error("No file found for id/version/disk = %s/%d/%s, not updating status",
                             file_id, file_version, disk_id)
                return

            # str to int, apply bits on/off, and back to str
            # If the bits have the desired value already we don't need to update
            status = int(res[0][0], 2)
            if on:
                if (status & bits) == bits:
                    return
                status |= bits
            else:
                if (status & bits) == 0:
                    return
                status &= ~bits
            new_status = bin(status)[2:]

            # apply
            t.execute(update, args=(new_status, file_id, file_version, disk_id))

    def set_available_for_deletion(self, file_id, file_version, disk_id):
        self._modify_status_bits(file_id, file_version, disk_id, 0x04, True)

    def set_valid_checksum(self, file_id, file_version, disk_id, valid):
        self._modify_status_bits(file_id, file_version, disk_id, 0x80, not valid)

# EOF