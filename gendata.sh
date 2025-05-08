#!/bin/bash

pgears () {
  # pgears <G> <tmax> <rpc> ...
  outname=data/$1-$2
  cmdline="./pgears.py -G $1 -tmax=$2"
  shift 2
  for a in "$@"; do
     outname="${outname}-${a}"
     cmdline="${cmdline} --${a}"
  done
  outname="${outname}.out"
  echo "doing ${cmdline} >${outname}"
  $cmdline > $outname
}

for g in SR SRP SRI; do
  for t in 50 60 90 120; do
    for c in "" rpc; do
      for c2 in "" rp2c; do
        pgears $g $t $c $c2
      done
    done
    for f in rnf rn2f "rnf rn2f"; do
      pgears $g $t $f
    done
  done
done
