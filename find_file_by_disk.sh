#!/usr/bin/env bash

# Read a list of simtel files and a disk name
# Print the first simtel file with a replica found on that disk

file_list=$1  # which list of simtel files to scan
disk_user=$2  # which disk to filter for

for simtel in $(cat $file_list)
do
  replicate_output=$(dirac-dms-lfn-replicas $simtel)
  disk=$(echo $replicate_output | cut -d ' ' -f6)
  if [[ "$disk" == "$disk_user" ]]
  then
    echo "You can use $simtel"
    break
  fi
done
