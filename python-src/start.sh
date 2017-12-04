#!/bin/bash

cd /home/ec2-user/rbot/python-src

PIDFILE=PIDFILE

if [ -e $PIDFILE ]; then
  printf "pidfile exists $PIDFILE\n"
else
  printf "%-50s\n" "Starting..."
  while true; do python trader.py >> log.txt 2>&1; sleep 2; done &
  echo $! > PIDFILE
  PID=`cat $PIDFILE`
  if [ -z $PID ]; then
    printf "%s\n" "Fail"
  else
    printf "%s %s\n" "Ok" $PID
  fi
fi
