#!/usr/bin/env bash
#############################################################################
# Defines ADS environment
# written by Kaisa Ryynänen, 03/24/2021
#############################################################################
##Function to display help with -h argument and to control
##The configuration from the commnad line
help_f()
{
cat << EOF
DESCRIPTION
    Links OA designs to ADS

OPTIONS"
  -l
      Open access source library 
  -t
      Technology substrate definition file 
  -w
      ADS workspace. Should contain lib.defs file.
  -h
      Show this help.
EOF
}

WORKDIR="$(pwd)"
while getopts l:t:w:h opt
do
  case "$opt" in
    l) SOURCELIB="$(readlink -f ${OPTARG})";;
    t) TECHFILE="$(readlink -f ${OPTARG})";;
    w) WORKDIR="$(readlink -f ${OPTARG})";;
    h) help_f; exit 0;;
    \?) help_f;;
  esac
done

TECH_FILE_NAME=""

if [ ! -f "${SOURCELIB}/$TECH_FILE_NAME" ]; then
    echo "Copying ${TECHFILE} to ${SOURCELIB}/${TECH_FILE_NAME}"
    cd "${SOURCELIB}" && cp "${TECHFILE}" ./${TECH_FILE_NAME}
fi

if [ ! -f "${WORKDIR}/lib.defs" ]; then
    echo "Creating lib.defs file"
    echo "INCLUDE $HPEESOF_DIR/oalibs/analog_rf.defs" >> ${WORKDIR}/lib.defs
fi

if [ -z "$(sed -n "/^DEFINE $(basename ${SOURCELIB}) /p" ${WORKDIR}/lib.defs)" ]; then
    echo "DEFINE $(basename ${SOURCELIB}) ${SOURCELIB}" >> ${WORKDIR}/lib.defs 
    echo "ASSIGN $(basename ${SOURCELIB}) libMode shared" >> ${WORKDIR}/lib.defs 
fi
exit 0
