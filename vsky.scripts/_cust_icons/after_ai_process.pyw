import os
import re
from PIL import Image

OUTPUT_SIZE = 64
REMOVE_START_TEXT = True  # True — удалять всё до "_", False — оставлять как есть

def process_images():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    files = os.listdir(current_dir)
    
    for filename in files:
        if filename.lower().endswith('.png'):
            source_path = os.path.join(current_dir, filename)
            name_without_ext, _ = os.path.splitext(filename)
            
            # 1. Обработка префикса до "_"
            if REMOVE_START_TEXT and "_" in name_without_ext:
                new_name = name_without_ext.split("_", 1)[1]
            else:
                new_name = name_without_ext
            
            # 2. Очистка от дефиса и цифр в конце
            new_name = re.sub(r'-\d+$', '', new_name)
            
            # Путь для нового TIFF файла
            tif_path = os.path.join(current_dir, f"{new_name}.tif")
            
            try:
                with Image.open(source_path) as img:
                    # Преобразуем в RGBA/RGB, если это необходимо для TIFF
                    if img.mode not in ('RGB', 'RGBA'):
                        img = img.convert('RGBA')
                        
                    resized_img = img.resize((OUTPUT_SIZE, OUTPUT_SIZE), Image.Resampling.LANCZOS)
                    resized_img.save(tif_path, format='TIFF')
                
                # Безопасное удаление оригинального PNG после закрытия файла
                os.remove(source_path)
                print(f"Готово: {filename} -> {new_name}.tif")
                
            except Exception as e:
                print(f"Ошибка при обработке файла {filename}: {e}")

if __name__ == "__main__":
    process_images()
