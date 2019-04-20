#!/bin/bash

DIR_PATH=`dirname $0`
URL="https://github.com/aktionskarten/AktionskartenMarker/raw/gh-pages/AktionskartenMarker.png"
INPUT="${DIR_PATH}/INPUT.png"
SIZE=150
COLORS=(e04f9e fe0000 ee9c00 ffff00 00e13c 00a54c 00adf0 7e55fc 1f4199 7d3411)
NAMES=(train megaphone tent speaker reheat cooking-pot police nuclear empty point information exclamation-mark star star-megaphone arrow bang)
NAMES_ALT=(flag megaphone empty point exclamation-mark thor-steinar arrow)

wget -O ${INPUT} ${URL}

for (( i=0; i<${#COLORS[@]}; i++ )); do
  color=\#${COLORS[i]}
  mkdir -p ${DIR_PATH}/${color}
  echo $color

  names=("${NAMES[@]}")
  if [[ "i" -ge "$((${#COLORS[@]}-1))" ]]; then
    names=("${NAMES_ALT[@]}")
  fi

  for (( j=0; j<${#names[@]}; j++ )); do
    filename=${DIR_PATH}/${color}/${names[j]}.png
    offset="$(($j*$SIZE))+$(($i*$SIZE))"
    convert ${INPUT} -crop ${SIZE}x${SIZE}+${offset} ${filename}
    echo -e "\t* ${color}/${names[j]}.png"
  done
done

rm ${INPUT}
