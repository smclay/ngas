#!/bin/sh
#
#
# chkconfig: 2345 99 70
# description: Starts and stops the ngamsServer
# processname: ngamsServer
# config: /etc/ngamsServer.conf

# Source function library.
. /etc/rc.d/init.d/functions
# on Ubuntu, these functions can be located at: /lib/lsb/init-functions

RETVAL=0

# replace the following if run under a different user.
NGAS_USER="ngas"

#adjust to where the NGAS installation directory is.
NGAS_ROOT="/home/$NGAS_USER/ngas_rt"

NGAMS_PID_FILE="$NGAS_ROOT/NGAS/.NGAS-"${HOSTNAME}"-7777"

# See how we were called.
case "$0" in
  *ngamsServer)
        NGAMS_DAEMON="ngamsDaemon"
        ;;
  *ngamsCacheServer)
        NGAMS_DAEMON="ngamsCacheDaemon"
        ;;
  *)
        echo "Usage: $0 {start|stop|status|restart}"
        exit 1
esac

case "$1" in
  start)
#       echo -n "Starting ngamsServer: "

        su - $NGAS_USER -c "$NGAS_ROOT/bin/$NGAMS_DAEMON start"

        echo "NG/AMS startup"
        [ $RETVAL -eq 0 ] && touch /var/lock/subsys/ngamsServer
#       RETVAL=$?
        ;;
  stop)
#       echo -n "Stopping ngamsServer: "
#        su - $NGAS_USER -c "$NGAS_ROOT/bin/ngamsDaemon stop" 1>/dev/null 2>&1
        su - $NGAS_USER -c "$NGAS_ROOT/bin/$NGAMS_DAEMON stop"
        if [[ -e ${NGAMS_PID_FILE} ]]
        then
          NGAMS_PID=$(cat ${NGAMS_PID_FILE})
          /bin/kill -9 ${NGAMS_PID}
          echo "NG/AMS PID "${NGAMS_PID}" killed."
          rm -f ${NGAMS_PID_FILE}
          echo "NG/AMS PID FILE "${NGAMS_PID_FILE}" removed."
        fi
        RETVAL=$?
        echo "NG/AMS shutdown"
        ;;
  status)
        echo "Status ngamsServer: "
        su - $NGAS_USER -c "$NGAS_ROOT/bin/$NGAMS_DAEMON status"
        RETVAL=$?
        ;;
  restart)
        echo -n "Restarting ngamsServer: "
        $0 stop
        $0 start
        RETVAL=$?
        ;;
  *)
        echo "Usage: $0 {start|stop|status|restart}"
        exit 1
esac

#exit $RETVAL