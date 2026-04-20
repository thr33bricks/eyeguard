import os
from pathlib import Path
from PIL import Image

def resize_square_images(input_folder, output_folder, size=(90, 90)):
    # Create the output directory if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # Path object for the input directory
    input_path = Path(input_folder)
    
    # Loop through all files ending in .jpg (case-insensitive)
    for img_file in input_path.glob("*.jpg"):
        try:
            with Image.open(img_file) as img:
                # Resize the image using high-quality resampling
                # Since they are square, (90, 90) keeps the aspect ratio perfectly
                resized_img = img.resize(size, Image.Resampling.LANCZOS)
                
                # Define the save path
                save_path = os.path.join(output_folder, img_file.name)
                
                # Save the result
                resized_img.save(save_path, "JPEG", quality=95)
                print(f"Resized: {img_file.name}")
                
        except Exception as e:
            print(f"Could not process {img_file.name}: {e}")

# Usage
if __name__ == "__main__":
    # Change 'my_photos' to your actual folder name
    resize_square_images(input_folder='photos_eyes', output_folder='resized_eyes')
    print("Done! Check the 'resized_eyes' folder.")