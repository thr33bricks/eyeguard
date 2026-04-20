import os
import shutil
import random

def move_percentage_of_files(source_dir, dest_dir, percentage=0.05):
    # Ensure the destination directory exists
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)
        print(f"Created destination directory: {dest_dir}")

    # Get a list of all files in the source directory (excluding folders)
    all_items = os.listdir(source_dir)
    files = [f for f in all_items if os.path.isfile(os.path.join(source_dir, f))]
    
    total_files = len(files)
    
    if total_files == 0:
        print("No files found in the source directory.")
        return

    # Calculate the number of files to move
    num_to_move = int(total_files * percentage)
    print(f"Total files found: {total_files}")
    print(f"Moving {num_to_move} files ({int(percentage * 100)}%)...")

    # Select a random sample of files
    files_to_move = random.sample(files, num_to_move)

    # Move the files
    for file_name in files_to_move:
        src_path = os.path.join(source_dir, file_name)
        dest_path = os.path.join(dest_dir, file_name)
        
        try:
            shutil.move(src_path, dest_path)
        except Exception as e:
            print(f"Error moving {file_name}: {e}")

    print("Task completed successfully.")

# --- Configuration ---
# Use absolute paths or relative paths here
source_folder = '/home/dan/Programming/Uni/Pavia/Tests/Eyes_model/Eyes_dataset/train/open'
destination_folder = '/home/dan/Programming/Uni/Pavia/Tests/Eyes_model/Eyes_dataset/open_moved'

move_percentage_of_files(source_folder, destination_folder)