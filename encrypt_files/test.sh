#!/bin/bash

echo "TEST MESSAGE" > testing.txt
echo "PASSPHRASE" > passphrase.txt

echo "Testing passphrase as string"
./encrypt.sh -f testing.txt -m E -o encrypted.txt -p PASSPHRASE
./encrypt.sh -f encrypted.txt -m D -o decrypted.txt -p PASSPHRASE
if [ $(sha256sum testing.txt | awk '{print $1}') != $(sha256sum decrypted.txt | awk '{print $1}') ]; then
	echo "Text does not match"
	rm testing.txt
	rm passphrase.txt
	rm encrypted.txt
	rm decrypted.txt
	exit 1
else
	echo "Text matches!"
fi

rm encrypted.txt
rm decrypted.txt

echo "Testing passphrase from file name"
./encrypt.sh -f testing.txt -m E -o encrypted.txt -p file:passphrase.txt
./encrypt.sh -f encrypted.txt -m D -o decrypted.txt -p file:passphrase.txt
if [ $(sha256sum testing.txt | awk '{print $1}') != $(sha256sum decrypted.txt | awk '{print $1}') ]; then
	echo "Text does not match"
	rm testing.txt
	rm passphrase.txt
	rm encrypted.txt
	rm decrypted.txt
	exit 1
else
	echo "Text matches!"
fi

rm testing.txt
rm passphrase.txt
rm encrypted.txt
rm decrypted.txt
