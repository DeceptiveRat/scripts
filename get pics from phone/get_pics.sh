#!/bin/bash

# remove previous log files
rm pics.txt
rm errors.txt
rm logs.txt

# get list of pictures
wget http://$1:8000/pics.txt >> log.txt 2>&1

PIC_COUNT=$(cat pics.txt | wc -l)
COUNT=0

# get pics in list
# save errors to file
while read p; do
	wget http://$1:8000/$p >> log.txt 2>&1
	COUNT=$((COUNT+1))
	printf "\r%d/%d" $COUNT $PIC_COUNT
done < pics.txt
echo ""
