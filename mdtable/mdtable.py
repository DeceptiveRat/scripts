#!/bin/python3

import tkinter as tk
import re

# button press function
def button_pressed():
	text = input_text.get("1.0", tk.END)
	processed_text=""
	horizontal_mark = False

	# preprocess text
	text = re.sub(r" (\(.*?\))", r"\1", text)

	lines = text.split("\n")
	for line in lines:
		if line=="":
			break
		words = line.split()
		processed_text+="| "
		for word in words:
			processed_text+=word
			processed_text+=" | "
		processed_text+="\n"

		if horizontal_mark == False:
			processed_text+="| "
			for word in words:
				processed_text+="---"
				processed_text+=" | "
			processed_text+="\n"
			horizontal_mark=True


	output_text.delete("1.0", tk.END)
	output_text.insert("1.0", processed_text)

# Create a function that copies the output text to the clipboard
def copy_output_to_clipboard():
	text = output_text.get("1.0", tk.END)

	root.clipboard_clear()
	root.clipboard_append(text)

	# Ensure the clipboard data persists after the program exits
	root.update()

def clear_input_text():
	input_text.delete("1.0", tk.END)

root = tk.Tk()
root.title("text to MD table")
root.geometry("500x400")

# Input Text Box
input_label = tk.Label(root, text="Text")
input_label.pack(pady=(10, 0))

# Create a multi-line text widget for input
input_text = tk.Text(root, height=5, width=60)
input_text.pack(pady=5)

button = tk.Button(root, text="Process", command=button_pressed)
button.pack(pady=10)
copy_button = tk.Button(root, text="Copy Output", command=copy_output_to_clipboard)
copy_button.pack(pady=5)
clear_button=tk.Button(root, text="clear input", command=clear_input_text)
clear_button.pack(pady=5)

# Output Text Box
output_label = tk.Label(root, text="MD table")
output_label.pack(pady=(10, 0))

# Create a multi-line text widget for output
output_text = tk.Text(root, height=5, width=60)
output_text.pack(pady=5)

root.mainloop()
