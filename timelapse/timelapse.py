#!/bin/python3

import subprocess
import sys
import getopt
import time
import glob

def usage():
	print("usage:", sys.argv[0])
	print("options:")
	print("-h: display this help screen")
	print("-f: set fps. Default: 5")
	print("-l: set screenshot save location. Default: . Use with -d option")
	print("-b: set bitrate. Default: 10 Mbps")
	print("-c: set capture fps. Default: 5. Recommended to be less than fps")
	print("-o: set output file name. Default: timelapse.mp4")
	print("-d: do not delete screenshots")

fps=5
capture_fps=5
bitrate=10
save_location="."
count=1
output_file="timelapse.mp4"
delete_screenshots=True

try:
	opts, args = getopt.getopt(sys.argv[1:], "hf:l:b:c:o:d")
except getopt.GetoptError as err:
	print(err)
	usage()
	sys.exit(2)

for option, argument in opts:
	if option == "-h":
		usage()
		sys.exit()
	elif option == "-f":
		fps = int(argument)
	elif option == "-l":
		save_location = argument
	elif option == "-b":
		bitrate = int(argument)
	elif option == "-c":
		capture_fps = int(argument)
	elif option == "-o":
		output_file = argument
	elif option == "-d":
		delete_screenshots=False
	else:
		assert False, "unhandled option"

try:
	while True:
		time.sleep(1/capture_fps)
		file_name = save_location+'/'+f"frame{count:06d}.png"
		subprocess.run(['flameshot', 'full', '-p', file_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
		print("saved")
		count+=1
except KeyboardInterrupt:
	print()
	print("Keyboard interrupt detected. Exiting capture.")
	
print("Creating video from images...")
file_name = save_location+'/frame%06d.png'
subprocess.call(['ffmpeg', '-framerate', str(fps), '-i', file_name, '-c:v', 'libx264', '-pix_fmt', 'yuv420p', output_file])
print()
if delete_screenshots:
	print("Deleting images...")
	files = glob.glob(save_location+'/frame*.png')
	if files:
		subprocess.call(['rm', *files])
print("Terminating...")
