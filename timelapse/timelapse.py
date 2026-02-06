#!/bin/python3

import subprocess
import sys
import getopt
import time
from mss import mss

def usage():
	print("usage:", sys.argv[0])
	print("options:")
	print("\t-h: display this help screen")
	print("\t-f [integer]: set fps. Default: 7")
	print("\t-l [save location]: set screenshot save location. Irrelevant without -s option. Default: .")
	print("\t-b [integer][k/M]: set bitrate. Default: 500k")
	print("\t-c [integer]: set capture fps. Recommended to be less than fps. Default: 2")
	print("\t-o [filename]: set output file name. Default: timelapse.mp4")
	print("\t-s: save screenshots. Runs ffmpeg in static mode")
	print("\t-r [resolution]: set screen resolution. Irrelevant when using -s option. Default 1920x1080")

fps=7
capture_fps=2
bitrate="500k"
save_location="."
count=1
output_file="timelapse.mp4"
delete_screenshots=True
screen_resolution="1920x1080"

try:
	opts, args = getopt.getopt(sys.argv[1:], "hf:l:b:c:o:sr:")
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
		bitrate = argument
	elif option == "-c":
		capture_fps = int(argument)
	elif option == "-o":
		output_file = argument
	elif option == "-s":
		delete_screenshots=False
	elif option == "-r":
		screen_resolution=argument
	else:
		assert False, "unhandled option"

wait_time = 1/capture_fps

if not delete_screenshots:
	try:
		while True:
			print("Recording... Press Ctrl+C to save and exit.")
			time.sleep(wait_time)
			file_name = save_location+'/'+f"frame{count:06d}.png"
			subprocess.run(['flameshot', 'full', '-p', file_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
			print("\rframes captured: %d" %(count), end="")
			count+=1
	except KeyboardInterrupt:
		print()
		print("Keyboard interrupt detected. Exiting capture.")
		
	print("Creating video from images...")
	file_name = save_location+'/frame%06d.png'
	subprocess.call(['ffmpeg', '-framerate', str(fps), '-i', file_name, '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-b:v', bitrate, output_file])
	print()
	print("Terminating...")

else:
	ffmpeg_command = [
		'ffmpeg',
		'-y', # overwrite output file without asking
		'-f', 'rawvideo', # format rawvideo
		'-c:v', 'rawvideo', # input is rawvideo 
		'-s', screen_resolution, # set frame size
		'-pix_fmt', 'bgra', # set pixel format
		'-r', str(fps), # set frame rate
		'-i', '-', # use stdin as input
		'-c:v', 'libx264', # output codec is h.264
		'-pix_fmt', 'yuv420p', # set pixel format
		'-b:v', bitrate,
		output_file
	]

	# open subprocess with pipe to stdin open
	process = subprocess.Popen(ffmpeg_command, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)

	try:
		with mss() as sct:
			# set monitor to main monitor
			monitor = sct.monitors[1]
			print("Recording... Press Ctrl+C to save and exit.")
			
			while True:
				# Capture and write immediately
				img = sct.grab(monitor)
				process.stdin.write(img.raw)

				print("\rframes captured: %d" %(count), end="")
				time.sleep(wait_time)
				count+=1

	except KeyboardInterrupt:
		print()
		print("Keyboard interrupt detected. Exiting capture.")
	finally:
		# properly close subprocess
		process.stdin.close()
		process.wait()
		print("Terminating...")
