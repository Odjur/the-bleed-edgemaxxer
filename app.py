
import os
import sys
import cv2
import numpy as np
from tkinter import Tk, filedialog
from scipy.spatial import cKDTree

OUTPUT_DIR = "output"
IMG_EXT = (".png", ".jpg", ".jpeg")
CARD_DIM = (745, 1040)
EDGE_CROP = 2
CORNER_CROP = 10

def GetImages(input_dir) -> list[str]:
	"""
	Recursively fetch image paths.
	"""
	
	imgs = []
	
	for root, dirs, files in os.walk(input_dir):
		for file in files:
			if file.lower().endswith(IMG_EXT):
				imgs.append(os.path.join(root, file))
	
	return imgs

def FillCorners(img):
	"""
	Fill corners with color.
	"""
	
	# 1. Generate mask
	if (img.shape[2] == 4) and img[0, 0, 3] < 10:
		# 1A. Transparent corners (corner pixel has an alpha value less than 10)
		_, card_mask = cv2.threshold(img[:, :, 3], 0, 255, cv2.THRESH_BINARY)
	else:
		# 1B. Color corners
		bgr = img[:, :, :3]
		bg_color = bgr[0, 0].astype(np.int16)
		
		lower = np.clip(bg_color - 15, 0, 255).astype(np.uint8)
		upper = np.clip(bg_color + 15, 0, 255).astype(np.uint8)
		bg_mask = cv2.inRange(bgr, lower, upper)
		
		height, width = img.shape[:2]
		flood_mask = np.zeros((height + 2, width + 2), np.uint8)
		
		corners = [(0, 0), (width - 1, 0), (0, height - 1), (width - 1, height - 1)]
		
		for x, y in corners:
			if bg_mask[y, x] == 255:
				cv2.floodFill(bg_mask, flood_mask, (x, y), 128)
		
		corner_mask = cv2.inRange(bg_mask, 128, 128)
		card_mask = cv2.bitwise_not(corner_mask)
	
	# 2. Erode card mask
	kernel = np.ones((3, 3), np.uint8)
	card_mask_eroded = cv2.erode(card_mask, kernel, iterations=CORNER_CROP)
	
	# 3. Find border pixels
	y_hole, x_hole = np.where(card_mask_eroded == 0)
	
	contours, _ = cv2.findContours(card_mask_eroded, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
	source_pixel_mask = np.zeros_like(card_mask)
	cv2.drawContours(source_pixel_mask, contours, -1, 255, 1)
	
	y_valid, x_valid = np.where(source_pixel_mask == 255)
	valid_pixels = np.column_stack((x_valid, y_valid))
	pixels_to_fill = np.column_stack((x_hole, y_hole))
	
	# 4. Fill corners
	tree = cKDTree(valid_pixels)
	_, indices = tree.query(pixels_to_fill)
	nearest_coords = valid_pixels[indices]
	
	# 5. Apply colors
	img[y_hole, x_hole] = img[nearest_coords[:, 1], nearest_coords[:, 0]]
	
	return img

def ProcessCard(img_path, output_dir):
	"""
	Modify a card to add bleed edges.
	"""
	
	# 1. Load image
	img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
	
	# 2. Resize image
	interpolation = cv2.INTER_AREA if (img.shape[1] > CARD_DIM[0]) else cv2.INTER_LANCZOS4
	img = cv2.resize(img, CARD_DIM, interpolation=interpolation)
	
	# 3. Crop edges
	height, width = img.shape[:2]
	img = img[EDGE_CROP:height - EDGE_CROP, EDGE_CROP:width - EDGE_CROP]
	
	# 4. Fill corners
	img = FillCorners(img)
	
	# 5. Add mirrored bleed edges
	bleed_length = 36 + EDGE_CROP
	
	img = cv2.copyMakeBorder(
		img,
		bleed_length, bleed_length, bleed_length, bleed_length,
		cv2.BORDER_REFLECT_101
	)
	
	# 6. Save image
	filename = os.path.basename(img_path)
	save_path = os.path.join(output_dir, filename)
	
	cv2.imwrite(save_path, img)

def main():
	root = Tk()
	root.withdraw()
	
	print("Select the input folder")
	input_dir = filedialog.askdirectory(title="Select folder with cards")
	
	os.makedirs(OUTPUT_DIR, exist_ok=True)
	img_paths = GetImages(input_dir)
	
	print(f"Processing {len(img_paths)} images...")
	for _, path in enumerate(img_paths):
		ProcessCard(path, OUTPUT_DIR)
	
	print(f"Finished processing {len(img_paths)} images")

if __name__ == "__main__":
	main()
