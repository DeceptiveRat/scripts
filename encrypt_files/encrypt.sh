#!/bin/bash

MODE="c"
PASSKEY=""
SERVER="127.0.0.1:8000"
FILENAME="default"
PASSKEYFILE=""
OUTPUT="default_output"
TAR_MODE="False"

while getopts "hp:f:m:i:o:t" opt; do
    case $opt in
		h) cat usage; exit 1 ;;
		p)
			if [ "${OPTARG%:*}" = "file" ]; then
				PASSKEYFILE="${OPTARG#*:}"
				PASSKEY=$(cat "$PASSKEYFILE")
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
		t) TAR_MODE="True" ;;
    esac
done

if [ "$TAR_MODE" = "True" ] && [ "$MODE" = "c" ]; then
	echo "Archiving files in \"encrypt\" directory..."
	tar -cf "$FILENAME" encrypt
fi

if [ "$OUTPUT" = "" ]; then
	OUTPUT = "$FILENAME.gpg"
fi

if [ "$PASSKEY" = "" ]; then
	echo "getting passkey..."
	wget http://$SERVER/$PASSKEYFILE >>/dev/null 2>&1
	PASSKEY="$(cat "$PASSKEYFILE")"
	rm $PASSKEYFILE
fi

if [ "$MODE" = "c" ]; then
	echo "encrypting..."
elif [ "$MODE" = "d" ]; then
	echo "decrypting..."
fi
gpg -$MODE --no-symkey-cache --batch --passphrase "$PASSKEY" -o "$OUTPUT" "$FILENAME" 2>>/dev/null

if [ "$TAR_MODE" = "True" ] && [ "$MODE" = "d" ]; then
	echo "Extracting files to \"decrypt\" directory..."
	tar -xf "$OUTPUT" -C decrypt --strip-components=1 encrypt
	rm "$OUTPUT"
fi

if [ "$TAR_MODE" = "True" ] && [ "$MODE" = "c" ]; then
	rm "$FILENAME"
fi
