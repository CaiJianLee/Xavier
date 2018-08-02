#########################################################################
# File Name: deploy.sh:
# Author: zhen
# mail: qingzhen.zhu@gzseeing.com 
# Created Time: 2016年12月23日 星期五 09时32分22秒
# modify Author:weizhenhua
# mail: zhenhua.wei@gzseeing.com
# modify time: 2017年8月31日 星期四 14时07分3秒
#########################################################################
#!/bin/bash

BOARD_NAME=ARM_Board_D3

LOCAL_FILE=$(cd "$(dirname "$0")";pwd)
PROJECT_NAME=""
RENAME=

SOURCE_FILE=$LOCAL_FILE/../
OUTPUT_PATH=$SOURCE_FILE

FLODER=$LOCAL_FILE/../build/deploy/


Usage()
{
	project_name=`ls $SOURCE_FILE/projects/`
	cat <<EOF
	Usage:
	$0 <version num> <project_name> --exclude [file] --include [file] 
	project_name: specific project name: 
$project_name
	version num: project name version
	file: BOOT.bin | devicetree.dtb | fpga.bit | uImage | rootfs.tar.gz | tools
	dir:  the output dir, default is build/deploy
	the package default include BOOT.bin, devicetree.dtb, fpga.bit and uImage
	if want to pack tools in tar,eg: /bin/bash $0 v5.00.01 N131 --include tools
	if want to clean project.eg: /bin/bash $0 clean
	
	eg: /bin/bash $0 v5.00.01 N131"
EOF
}

clean_project()
{
	echo "clean project ..."
	rm -rf $SOURCE_FILE/build 
	rm -rf ARM_Board_D3_*
	echo "clean project ok."
	exit 1
}

if [ "$1" = "clean" ];then
	clean_project
fi

if test $# -lt 2 || test $1 = "?" || test $1 = "h" || test $1 = "help" || test $1 = "-H" || test $1 = "-h" || test $1 = "-help" ;then 
	Usage
	exit 0
fi

version_str=$1
VERSION=${version_str#*v}
VERSION=${VERSION#*V}
echo 'version is :'$VERSION

PROJECT_NAME=$2

[ -d $LOCAL_FILE ]
if [ $? -ne 0 ];then
	echo "[err ] Please check your folder, cannot contain special characters in your folder."
	echo "exit !!!"
	exit 1
fi
[ -d $SOURCE_FILE/projects/$PROJECT_NAME ]
if [ $? -ne 0 ];then
	echo "[err ] Please check your folder, cannot contain special characters in your folder."
	echo "exit !!!"
	exit 1
fi

# get params
param_type='none'
tools_status=0
for arg in "$@"
do
	if [ $arg = '--include' ];then
		param_type='include'
	elif [ $arg = '--exclude' ];then
		param_type='exclude'
	elif [ $arg = '--output' ];then
		param_type='path'
	elif [ $arg = '--rename' ];then
		param_type='rename'
	else
		if [ $param_type = 'include' ];then
			if [ $arg = 'tools' ];then
				tools_status=1
				echo "include tools file "
			else
				INCLUDE_FILE="$INCLUDE_FILE $arg"	
			fi		
		elif [ $param_type = 'exclude' ];then
			EXCLUDE_FILE="$EXCLUDE_FILE $arg"			
		elif [ $param_type = 'path' ];then
			OUTPUT_PATH=$arg
		elif [ $param_type = 'rename' ];then
			RENAME=$arg
		fi
	fi
done
echo $INCLUDE_FILE
echo $EXCLUDE_FILE
echo $OUTPUT_PATH
echo $FLODER

echo 'project name is :'$PROJECT_NAME

if [ ! -d $FLODER ];then
	mkdir -p $FLODER
else
	rm -rf $FLODER/* 
fi


cd $FLODER
/bin/bash $LOCAL_FILE/release.sh 1 $PROJECT_NAME pack 
cp -rf $SOURCE_FILE/projects/$PROJECT_NAME/* ./
rm -rf $FLODER/*.json $FLODER/*.xlsx $FLODER/*.gz
cp $FLODER/../app/seeing.tar.gz $FLODER
if [ $? -ne 0 ];then
	echo "Can not find $SOURCE_FILE/build/app/seeing.tar.gz. package exit !"
	exit 1
fi
[ -f $SOURCE_FILE/projects/$PROJECT_NAME/rootfs*.tar.gz ] \
&& cp -rf $SOURCE_FILE/projects/$PROJECT_NAME/rootfs*.tar.gz $FLODER


if [ -f $SOURCE_FILE/projects/$PROJECT_NAME/kernel_modules_*.tar.gz ];then
    tar zxf $SOURCE_FILE/projects/$PROJECT_NAME/kernel_modules_*.tar.gz -C $FLODER
elif [ -d $SOURCE_FILE/projects/$PROJECT_NAME/amp ];then
    tar zxf $SOURCE_FILE/packages/kernel_modules_zynqamp_*.tar.gz -C $FLODER
elif [ -d $SOURCE_FILE/projects/$PROJECT_NAME/pru ];then
    echo ""
else
    tar zxf $SOURCE_FILE/packages/kernel_modules_zynq_*.tar.gz -C $FLODER
fi

firmware_file=`ls`
if [ -n "$firmware_file" ];then
    for folder_file in $firmware_file
    do
        [ -d $folder_file ] && rm -rf $folder_file
    done
fi

cd $FLODER
echo "first list file:"
ls
echo "------------"

if [ -n "$INCLUDE_FILE" ];then
	cd $SOURCE_FILE/bin/
	cp $INCLUDE_FILE $FLODER
	if [ $? -ne 0 ];then
		echo "ERR: cp \"$INCLUDE_FILE\"  error!"
		exit 1
	fi
	cd $FLODER
fi
if [ -n "$EXCLUDE_FILE" ];then
	cd $FLODER
	rm $EXCLUDE_FILE 
	if [ $? -ne 0 ];then
		echo "ERR: rm \"$EXCLUDE_FILE\" error!"
		exit 1
	fi
fi
if [ $tools_status -eq 1 ];then
	echo "tar tools file"
	cd $SOURCE_FILE
	tar zcvf tools.tar.gz tools
	mv tools.tar.gz  $FLODER
fi

cd $FLODER
echo "second list file:"
ls
echo "------------"

if [ ! -f $SOURCE_FILE/projects/$PROJECT_NAME/version.txt ];then
	echo "warn: not have version.txt !!! "
#	exit 1
else
# change seeing param 
	while read line; do
		eval "$line"
	done < version.txt
fi

string=${seeing#=}
project=${project#=}
time_string=${compile_time#=}
if [ -z $string ];then
	echo "not have \"seeing\" value in \"version.txt\" file"
	echo "now version is "$VERSION
	echo "seeing="$VERSION >> version.txt
else
	echo "old version is "$string
	echo "new version is "$VERSION
	sed -i 's/'$string'/'$VERSION'/g' version.txt
fi

if [ -z $project ];then
	echo "not have \"project\" value in \"version.txt\" file"
	echo "now project is "$PROJECT_NAME
	if [ $RENAME ];then
		echo "project="$RENAME>> version.txt
	else
		echo "project="$PROJECT_NAME>> version.txt
	fi
else
	echo "project name is \""$PROJECT_NAME"\""
	if [ $RENAME ];then
		sed -i 's/'$project'/'$RENAME'/g' version.txt
	else
		sed -i 's/'$project'/'$PROJECT_NAME'/g' version.txt
	fi
fi

COMPILE_TIME=$(date  +"%Y-%m-%d--%H:%M:%S")
if [ -z $time_string ];then
	echo "not have \"compile_time\" value in \"version.txt\" file"
	echo "now compile time is "$COMPILE_TIME
	echo "compile_time="$COMPILE_TIME>> version.txt
else
	echo "now time is "$COMPILE_TIME
	echo "compile time name is \""$COMPILE_TIME"\""
	sed -i 's/'$time_string'/'$COMPILE_TIME'/g' version.txt
fi

sync

md5sum * > md5.txt

if [ $RENAME ];then
    echo "Remane project $PROJECT_NAME to $RENAME" 
    SW="$BOARD_NAME"_"$RENAME"
else
    SW="$BOARD_NAME"_"$PROJECT_NAME"
fi
PACK_NAME="$SW"_V"$VERSION".tar.gz
tar -mzcf $PACK_NAME *
mv $PACK_NAME $OUTPUT_PATH

# mv version.txt $SOURCE_FILE/bin/
mv version.txt $SOURCE_FILE/projects/$PROJECT_NAME/

rm $FLODER/build/app/* -rf

