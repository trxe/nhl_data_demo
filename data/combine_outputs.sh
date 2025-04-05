set -e

ARGC=$#                          # number of command line args

if [[ $ARGC -lt 5 ]];
then
    echo "Not enough variables, check script at" $(pwd)/$(basename $0)};
    exit 1;
fi

OUTNAME_BASE=$1
TOOLS_DIR=$2
INPUT_DIR=$3
OUTPUT_DIR=$4
DELETE=$5
OUTNAME=${OUTPUT_DIR}/${OUTNAME_BASE}.csv
PATTERN=${OUTPUT_DIR}/${OUTNAME_BASE}_*.csv
PATCNT=$(find ${OUTPUT_DIR} -name ${OUTNAME_BASE}_*.csv -printf '.' | wc -m)

if [[ -z $VIRTUAL_ENV ]];
then
    echo "Activate venv first";
    exit 1;
fi

if [[ $DELETE -eq del ]]
then
    echo "Deleting after complete";
fi

echo "Found $PATCNT files"

if [[ $PATCNT -eq 0 ]]
then
    python ${TOOLS_DIR}/transform.py -c ${TOOLS_DIR}/config.yml -i ${INPUT_DIR} -o ${OUTPUT_DIR} -t ${OUTNAME_BASE}
fi

cat ${PATTERN} | head -n1 > ${OUTNAME};

for f in $PATTERN;
do
    echo $f to $OUTNAME;
    cat "`pwd`/$f" | tail -n +2 >> ${OUTNAME}; 
    if [[ $DELETE -eq del ]];
    then
        rm $f;
    fi
done

# echo "Written to ${OUTNAME}"