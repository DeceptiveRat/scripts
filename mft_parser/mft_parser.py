#!/bin/python3 

import sys
import getopt
import struct
import io

def usage():
	print("usage:", sys.argv[0])
	print("options:")
	print("-h: display this help screen")
	print("-f <file>: file to parse. File must contain raw bytes for mft entry. If this is not provided, stdin will be used")

try:
	opts, args = getopt.getopt(sys.argv[1:], "hf:")
except getopt.GetoptError as err:
	print(err)
	usage()
	sys.exit(2)

file_name=""

for option, argument in opts:
	if option == "-h":
		usage()
		sys.exit()
	elif option == "-f":
		file_name = argument 
	else:
		assert False, "unhandled option"

data_array=b''

if file_name != "":
	with open(file_name, 'rb') as f:
		data_array = f.read(1024)
else:
	data_array = sys.stdin.buffer.read()

data_buffer = io.BytesIO(data_array)

# read MFT entry header
signature = data_buffer.read(4)
fixup_array_offset = data_buffer.read(2)
fixup_array_entries = data_buffer.read(2)
logfile_sequence_number = data_buffer.read(8)
sequence_value = data_buffer.read(2)
link_count = data_buffer.read(2)
offset_attribute = data_buffer.read(2)
flags = data_buffer.read(2)
MFT_entry_used_size = data_buffer.read(4)
MFT_entry_allocated_size = data_buffer.read(4)
base_record_file_reference = data_buffer.read(8)
next_attribute_id = data_buffer.read(2)

# parse MFT entry header
if signature != b'FILE':
	print("Signature not FILE", file=sys.stderr)
else:
	print("Signature: FILE")
print("offset to fixup array: %d" %(int.from_bytes(fixup_array_offset, "little")))
print("fixup array entry count: %d" %(int.from_bytes(fixup_array_entries, "little")))
print("$LogFile sequence number: %d" %(int.from_bytes(logfile_sequence_number, "little")))
print("sequence value: %d" %(int.from_bytes(sequence_value, "little")))
print("link count: %d" %(int.from_bytes(link_count, "little")))
print("attribute offset: %d" %(int.from_bytes(offset_attribute, "little")))
if int.from_bytes(flags, "little") & 0x01:
	print("flags: in use flag set")
if int.from_bytes(flags, "little") & 0x02:
	print("flags: directory flag set")
print("MFT entry used size: %d" %(int.from_bytes(MFT_entry_used_size, "little")))
print("MFT entry allocated size: %d" %(int.from_bytes(MFT_entry_allocated_size, "little")))
print("file reference to base record: %d" %(int.from_bytes(base_record_file_reference, "little")))
print("next attribute id: %d" %(int.from_bytes(next_attribute_id, "little")))

# read and parse attribute header/data
