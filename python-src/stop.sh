#!/bin/bash -x

PID=$(ps aux | grep "python trader" | grep -v grep | awk '{print $2}')

kill $PID
