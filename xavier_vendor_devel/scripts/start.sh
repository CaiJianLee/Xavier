#!/bin/sh
#
#
# start the user program
#
#
#
# set timezone as Shanghai
cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime

LOCAL_FILE=$(cd "$(dirname "$0")";pwd)

function reset_eth0_phy(){
    # pull up the reset mio, reset the ethernet phy
    echo 919 > /sys/class/gpio/export
    echo out > /sys/class/gpio/gpio919/direction
    sleep 0.02
    echo 1 > /sys/class/gpio/gpio919/value
}

function reset_usb_phy(){
    # pull up the reset mio, reset the ethernet phy
    # echo 906 > /sys/class/gpio/export
    # echo out > /sys/class/gpio/gpio906/direction
    sleep 0.02
    # echo 1 > /sys/class/gpio/gpio906/value
}

echo "-------------------- $0 --------------------"
[ "$1" != "network_no_reset" ] && reset_eth0_phy && [ -f /opt/seeing/config/network.sh ] && /opt/seeing/config/network.sh PowerOn && reset_usb_phy
[ ! -f /opt/seeing/config/network.sh ] && /opt/seeing/app/scripts/network.sh PowerOn
[ ! -d /opt/seeing/dut_firmware ] &&  mkdir -p /opt/seeing/dut_firmware

[ -f /opt/seeing/app/kernel_modules/insmod.sh ] && sh /opt/seeing/app/kernel_modules/insmod.sh 2>/dev/null

[ -f /opt/seeing/app/amp/amp.sh ] && /opt/seeing/app/amp/amp.sh
[ -f /opt/seeing/app/pru/pru.sh ] && /opt/seeing/app/pru/pru.sh

cd $LOCAL_FILE
source $LOCAL_FILE/env.sh

function check_run(){
    ProcNumber=`ps -ef | awk '{print $8}' | grep -w $1 | grep -v grep | wc -l`
    if [ "$ProcNumber" -le 0 ];then
        #echo "$1 not running"
        if [ $1 == "cmd" ];then
            python2.7 /opt/seeing/app/command/main.py tcp:7600
        elif [[ $1 == "ee" ]]; then
            #statements
            python2.7 $PYTHON_HOME/ee/embedded_engine.py
        elif [[ $1 == "daq" ]]; then
            #statements
            python2.7 $PYTHON_HOME/daq/daq.py
        elif [[ $1 == "monitor" ]]; then
            #statements
            python2.7 $PYTHON_HOME/monitor/monitor.py
        fi
        echo "start $1"
    else
        echo "$1 is running"
    fi
}

insmod $PYTHON_HOME/lib/axi4lite.ko 2>/dev/null
insmod $PYTHON_HOME/lib/axi4stream.ko 2>/dev/null

if [ "$#" -lt 2 ];then
    check_run monitor
else
    if [ "$2" == "monitor" ];then
        check_run $2
    else
        echo "start $2"
    fi
fi

[ -f $LOCAL_FILE/app.sh ] && sh $LOCAL_FILE/app.sh
sync
echo "-------------------- $0 end --------------------"

