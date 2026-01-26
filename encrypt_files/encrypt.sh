#!/bin/bash

MODE="c"
PASSKEY=""
SERVER="127.0.0.1:8000"
FILENAME=""
PASSKEYFILE=""
OUTPUT=""

while getopts "hp:f:m:i:o:" opt; do
    case $opt in
		h) cat usage; exit 1 ;;
		p)
			if [ "${OPTARG%:*}" = "file" ]; then
				PASSKEYFILE="${OPTARG#*:}"
				PASSKEY=$(cat $PASSKEYFILE)
			elif [ "${OPTARG%:*}" = "IP" ]; then
				PASSKEYFILE="${OPTARG#*:}"
			else
				PASSKEY="$OPTARG"
			fi ;;
		f) FILENAME="$OPTARG" ;;
		m) 
			if [ "$OPTARG" = "E" ] || [ "$OPTARG" = "encrypt" ]; then
				MODE="c"
			elif [ "$OPTARG" = "D" ] || [ "$OPTARG" = "decrypt" ]; then
				MODE="d"
			else
				echo "Wrong mode option"
				cat usage
				exit 1
			fi ;;
		i) SERVER="$OPTARG" ;;
		o) OUTPUT="$OPTARG" ;;
    esac
done

if [ "$OUTPUT" = "" ]; then
	OUTPUT = "$FILENAME.gpg"
fi

if [ "$PASSKEY" = "" ]; then
	wget http://$SERVER/$PASSKEYFILE >>/dev/null 2>&1
	PASSKEY="$(cat "$PASSKEYFILE")"
	rm $PASSKEYFILE
fi

gpg -$MODE --no-symkey-cache --batch --passphrase "$PASSKEY" -o "$OUTPUT" "$FILENAME" 2>>/dev/null
