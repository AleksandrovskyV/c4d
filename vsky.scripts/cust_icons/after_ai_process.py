import os, re
from PIL import Image

OUTPUT_SIZE = 64
REMOVE_START_TEXT = True  # True — удалять всё до "_", False — оставлять как есть

def process_images():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Список файлов собираем заранее, так как имена файлов будут меняться в процессе
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
            
            # Пути для новых файлов
            new_png_path = os.path.join(current_dir, f"{new_name}.png")
            new_tif_path = os.path.join(current_dir, f"{new_name}.tif")
            
            try:
                # Открываем оригинал, меняем размер и сохраняем обратно в PNG
                with Image.open(source_path) as img:
                    resized_img = img.resize((OUTPUT_SIZE, OUTPUT_SIZE), Image.Resampling.LANCZOS)
                    resized_img.save(new_png_path, format='PNG')
                    
                    # Из этой же измененной картинки сразу делаем TIFF-копию
                    resized_img.save(new_tif_path, format='TIFF')
                
                # Если имя файла изменилось, удаляем старый оригинальный PNG
                if source_path != new_png_path:
                    os.remove(source_path)
                    
                print(f"Готово: {filename} -> {new_name}.png + {new_name}.tif")
                
            except Exception as e:
                print(f"Ошибка при обработке файла {filename}: {e}")

if __name__ == "__main__":
    process_images()
