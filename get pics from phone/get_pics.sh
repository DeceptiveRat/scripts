#!/bin/bash

# remove previous log files
rm pics.txt
rm errors.txt
rm logs.txt

# get list of pictures
wget http://$1:8000/pics.txt >> log.txt 2>&1

PIC_COUNT=$(cat pics.txt | wc -l)
COUNT=0

cleanup() {
	echo "interrupted. Removing incomplete file..."
	if [ -n "$tmp" ]; then
		rm "$tmp"
	fi
	exit 130
}

trap cleanup SIGINT

# get pics in list
# save errors to file
while read -r p; do
	if [ -f "$p" ]; then
		echo "skipping existing file $p..."
	else
		printf "\r%d/%d" $COUNT $PIC_COUNT
		tmp="$p.tmp"
		wget -O "$tmp" "http://$1:8000/$p" >> log.txt 2>&1 &&
		mv "$tmp" "$p"
	fi
	COUNT=$((COUNT+1))
done < pics.txt
printf "\r%d/%d" $COUNT $PIC_COUNT
echo ""
