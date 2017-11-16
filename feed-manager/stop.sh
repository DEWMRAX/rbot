#!/bin/bash -x

GID=$(ps x -o  "%p %r %y %x %c " | grep $(cat PIDFILE) | awk '{print $2}')

kill -- -$GID

rm PIDFILE
