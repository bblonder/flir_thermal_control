#!/bin/sh

export GI_TYPELIB_PATH=$GI_TYPELIB_PATH:/home/odroid/aravis/src
export LD_LIBRARY_PATH=/home/odroid/aravis/src/.libs
export PYTHONPATH=/home/odroid/aravis:/home/odroid/.local/lib/python2.7/site-packages

python /home/odroid/Desktop/control/thermal_control.py 2>&1 >> /home/odroid/Desktop/log.txt &
chown odroid:odroid /home/odroid/Desktop/log.txt
