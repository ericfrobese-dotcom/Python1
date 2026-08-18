#!/bin/bash

# Configuration
SOURCE_DIR="/home/eric/Music"
DEST_DIR="/mnt/music_share"

# Ensure destination exists
mkdir -p "$DEST_DIR"

echo "Starting sync from $SOURCE_DIR to $DEST_DIR..."

# 1. Handle Collisions in Root Destination
# Find all files currently in the root of the destination
find "$DEST_DIR" -maxdepth 1 -type f | while read -r dest_file; do
    filename=$(basename "$dest_file")
    
    # Check if a file with the same name exists in the SOURCE (any subdirectory)
    # We look for the file in the source to determine its "appropriate" subdirectory
    match=$(find "$SOURCE_DIR" -type f -name "$filename" | head -n 1)
    
    if [ -n "$match" ]; then
        # Determine the subdirectory path relative to SOURCE
        subdir_path=$(dirname "$match")
        relative_subdir=${subdir_path#$SOURCE_DIR}
        
        # Create the corresponding subdirectory in DESTINATION if it doesn't exist
        if [ -n "$relative_subdir" ] && [ "$relative_subdir" != "." ]; then
            target_subdir="$DEST_DIR$relative_subdir"
            mkdir -p "$target_subdir"
            
            echo "Collision detected: '$filename'. Moving existing root file to '$target_subdir'."
            mv "$dest_file" "$target_subdir/"
        fi
    fi
done

# 2. Copy Content from Source to Destination
# Using rsync for efficient copying. 
# --ignore-existing ensures we don't overwrite the files we just moved or any other existing files 
# if you prefer to overwrite, remove --ignore-existing
echo "Copying new files..."
rsync -av --ignore-existing "$SOURCE_DIR/" "$DEST_DIR/"

# Alternative using cp if rsync is not available:
# find "$SOURCE_DIR" -type f | while read -r src_file; do
#     relative_path=${src_file#$SOURCE_DIR/}
#     dest_file="$DEST_DIR/$relative_path"
#     dest_dir=$(dirname "$dest_file")
#     
#     if [ ! -f "$dest_file" ]; then
#         mkdir -p "$dest_dir"
#         cp "$src_file" "$dest_file"
#     fi
# done

# 3. Delete Empty Subdirectories in Destination
# -depth ensures we process children before parents, allowing nested empty dirs to be removed
echo "Cleaning up empty directories..."
find "$DEST_DIR" -depth -type d -empty -delete

echo "Sync complete."   