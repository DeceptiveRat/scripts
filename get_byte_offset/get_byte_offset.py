#!/bin/python3 

import sys
import io
import getopt

def usage():
	print("usage:", sys.argv[0])
	print("options:")
	print("    -h: display this help screen")
	print("    -f <file>: file to search. If this is not provided, stdin is used")
	print("    -l <int>: search length. Default: 1,000,000 bytes")
	print("    -p <pattern>: [required] pattern to search for. Enter as hex; e.g. 0x3ccf10")
	print("    -s: switch endianness. Default: False")

file_name = ""
search_length=1000000
search_pattern=""
switch_endianness=False

try:
	opts, args = getopt.getopt(sys.argv[1:], "hf:l:p:s")
except getopt.GetoptError as err:
	print(err)
	usage()
	sys.exit(2)

for option, argument in opts:
	if option == "-h":
		usage()
		sys.exit()
	elif option == "-f":
		file_name = argument 
	elif option == "-l":
		search_length=int(argument)
	elif option == "-p":
		search_pattern = argument
	elif option == "-s":
		switch_endianness = True
	else:
		assert False, "unhandled option"

if file_name != "":
	with open(file_name, 'rb') as f:
		data_array = f.read(search_length)
else:
	data_array = sys.stdin.buffer.read(search_length)
pos = 0
if switch_endianness:
	search_pattern = hex(int.from_bytes(bytes.fromhex(search_pattern)))
	search_pattern=search_pattern[2:]
if len(search_pattern)%2 != 0:
	search_pattern = "0" + search_pattern
#print(search_pattern)
#print(type(search_pattern))

while True:
	# search for pattern
	pos=data_array.find(bytes.fromhex(search_pattern), pos)
	if pos == -1:
		break;
	# print offset
	print("offset: %d" %(pos))
	# search starts from next byte
	pos+=1
