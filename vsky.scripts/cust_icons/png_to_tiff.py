import os, re
from PIL import Image

OUTPUT_SIZE = 64
REMOVE_START_TEXT = True  # True — удалять всё до "_", False — оставлять как есть

def process_images():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    for filename in os.listdir(current_dir):
        if filename.lower().endswith('.png'):
            source_path = os.path.join(current_dir, filename)
            name_without_ext, _ = os.path.splitext(filename)
            
            # REMOVE_START_TEXT
            if REMOVE_START_TEXT and "_" in name_without_ext:
                new_name = name_without_ext.split("_", 1)[1]
            else:
                new_name = name_without_ext
            
            new_name = re.sub(r'-\d+$', '', new_name)
            
            new_filename = f"{new_name}.tif"
            destination_path = os.path.join(current_dir, new_filename)
            
            try:
                with Image.open(source_path) as img:
                    resized_img = img.resize((OUTPUT_SIZE, OUTPUT_SIZE), Image.Resampling.LANCZOS)
                    resized_img.save(destination_path, format='TIFF')
                    
                print(f"Succes: {filename} -> {new_filename} ({OUTPUT_SIZE}x{OUTPUT_SIZE})")
            except Exception as e:
                print(f"Error {filename}: {e}")

if __name__ == "__main__":
    process_images()
