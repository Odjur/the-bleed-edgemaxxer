
import os
import sys
from enum import Enum
from PIL import Image
import numpy as np
from tkinter import Tk, filedialog

# Constants for output directories and image dimensions
OUTPUT_DIR = 'output'  # Directory where processed images will be saved
CARD_DIM = (745, 1040)	# Target dimensions for card images
IMG_EXT = ('.png', '.jpg', '.jpeg')	 # Supported image file extensions
CROP = 2 # Pixels to crop each edge
BLEED_LENGTH = 36 + CROP # Bleed length in pixels for adding bleed edges

# Initialize INPUT_DIR only when running as main script, not when imported
INPUT_DIR = None

if __name__ == '__main__':
	root = Tk()
	root.withdraw()
	INPUT_DIR = filedialog.askdirectory(title="Select Folder with Cards")
	
	if not INPUT_DIR:
		sys.exit()

# Ensure the output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

def getImgs(input_dir=INPUT_DIR) -> list[str]:
	"""
	Recursively fetches all image file paths from the specified directory.
	"""
	imgs = []
	
	for file in os.listdir(input_dir):
		path = os.path.join(input_dir, file)
		
		if os.path.isdir(path):
			imgs += getImgs(path)  # Recursively get images from subdirectories
		elif path.endswith(IMG_EXT):  # Check if the file has a valid extension
			imgs.append(path)
	return imgs

def resizeImg(img_path, output_dir=OUTPUT_DIR) -> str:
	"""
	Resizes an image to the specified dimensions and saves it.
	Returns the path to the resized image.
	"""
	with Image.open(img_path) as img:
		output_path = img_path	# Default to the original path
		
		if img.size != CARD_DIM:
			# Resize image if it does not match the target dimensions
			img = img.resize(CARD_DIM, Image.Resampling.LANCZOS)
		
		# 2 pixel crop
		img = img.crop((CROP, CROP, img.width - CROP, img.height - CROP))
		
		output_path = os.path.join(output_dir, os.path.basename(img_path))
		img.save(output_path, quality=95)  # Save resized image
	return output_path
	
def addBleedEdge(img_path, output_dir=OUTPUT_DIR) -> str:
	"""
	Adds a bleed edge to an image using either a simple black border 
	or replicated edges, depending on the image perimeter properties.
	"""
	output_path = os.path.join(output_dir, os.path.basename(img_path))
	
	with Image.open(img_path) as img:
		# Calculate new dimensions including the bleed area
		total_width = img.width + 2 * BLEED_LENGTH
		total_height = img.height + 2 * BLEED_LENGTH
		new_dim = (total_width, total_height)
		
		# Add replicated edges as the border
		bleed_img = Image.new("RGB", new_dim)
		x, y = BLEED_LENGTH, BLEED_LENGTH
		bleed_img.paste(img, (x, y))
		
		# Replicate and flip top, left, right, and bottom edges
		top = img.crop((0, 0, img.width, BLEED_LENGTH))
		new_top = top.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
		
		left = img.crop((0, 0, BLEED_LENGTH, img.height))
		new_left = left.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
		
		right = img.crop((img.width - BLEED_LENGTH, 0, img.width, img.height))
		new_right = right.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
		
		bottom = img.crop((0, img.height - BLEED_LENGTH, img.width, img.height))
		new_bottom = bottom.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
		
		# Replicate and flip corners
		new_left_corner = new_left.crop((0, 0, BLEED_LENGTH, BLEED_LENGTH)).transpose(Image.Transpose.FLIP_TOP_BOTTOM)
		new_right_corner = new_right.crop((0, 0, BLEED_LENGTH, BLEED_LENGTH)).transpose(Image.Transpose.FLIP_TOP_BOTTOM)
		new_left_bottom_corner = new_left.crop((0, img.height - BLEED_LENGTH, BLEED_LENGTH, img.height)).transpose(Image.Transpose.FLIP_TOP_BOTTOM)
		new_right_bottom_corner = new_right.crop((0, img.height - BLEED_LENGTH, BLEED_LENGTH, img.height)).transpose(Image.Transpose.FLIP_TOP_BOTTOM)
		
		# Paste replicated edges and corners onto the image
		bleed_img.paste(new_top, (BLEED_LENGTH, 0))
		bleed_img.paste(new_left, (0, BLEED_LENGTH))
		bleed_img.paste(new_right, (img.width + BLEED_LENGTH, BLEED_LENGTH))
		bleed_img.paste(new_bottom, (BLEED_LENGTH, img.height + BLEED_LENGTH))
		bleed_img.paste(new_left_corner, (0, 0))
		bleed_img.paste(new_right_corner, (img.width + BLEED_LENGTH, 0))
		bleed_img.paste(new_left_bottom_corner, (0, img.height + BLEED_LENGTH))
		bleed_img.paste(new_right_bottom_corner, (img.width + BLEED_LENGTH, img.height + BLEED_LENGTH))
		
		bleed_img.save(output_path, quality=95, dpi=(300,300))
	return output_path

def getPerimeter(img_path) -> np.array:
	"""
	Extracts the perimeter pixels of an image as a flattened array.
	"""
	with Image.open(img_path) as img:
		img = img.convert('RGB')
		pixels = np.array(img)
		
		# Extract top, left, right, and bottom edges of the image
		top = pixels[0, :]
		left = pixels[1:-1, 0]
		right = pixels[1:-1, -1]
		bottom = pixels[-1, :]
		
		# Combine perimeter pixels into a single array
		perimeter = np.concatenate((top, left, right, bottom), axis=0)
	return perimeter

def main():
	"""
	Main function to process images by resizing them and adding bleed edges.
	"""
	print("Processing Images...")
	
	img_paths = getImgs()  # Get list of input images
	if not img_paths:
		print("No images")	# Exit if no images are found
		exit()
	
	rz_paths = []  # List to store paths of resized images
	for path in img_paths:
		rz_paths.append(resizeImg(path))
	
	bleeds = []	 # List to store paths of images with bleed edges
	for path in rz_paths:
		bleeds.append(addBleedEdge(path))
	
	print(f"Successfully Created {len(bleeds)} Bleed Edge Images")

if __name__ == '__main__':
	main()
