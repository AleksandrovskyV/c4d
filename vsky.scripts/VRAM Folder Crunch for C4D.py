"""

VRAM Folder Crunch for C4D

Author: Viktor Aleksandrovsky & Google AI & ChatGPT
Written & Tested for Maxon Cinema 4D R20

Description-US:Experimental button  |

Extend: c4d interface for load standalone .exe

"""

TOOL_NAME = "VRAM Folder Crunch / C4D"
SHORT_NAME = "vram4d_crunch"

import c4d, os, sys
import subprocess
import json
import datetime

if sys.version_info >= (3, 0):
    import urllib.request as urllib_req
else:
    import urllib2 as urllib_req

# Прокси-файлы Arnold и Redshift (TX / RSTEX)
# Эти рендеры генерируют зеркальные файлы .rstex или .tx прямо рядом с основными текстурами. Скрипт их пока игнорирует, 
# Проблема при запуске рендера Redshift увидит старый, тяжелый .rstex файл и не поймет, что оригинальный JPEG уменьшился.


SCRIPT_DIR = os.path.dirname(__file__)
LOCAL_LIBS_DIR = os.path.join(SCRIPT_DIR, "libs") if SCRIPT_DIR else ""
dlg = None

if LOCAL_LIBS_DIR and os.path.exists(LOCAL_LIBS_DIR):
    if LOCAL_LIBS_DIR not in sys.path:
        sys.path.insert(0, LOCAL_LIBS_DIR)

def download_from_web():
    if not SCRIPT_DIR:
        c4d.gui.MessageDialog("Save script on disk!")
        return False

    if not os.path.exists(LOCAL_LIBS_DIR):
        os.makedirs(LOCAL_LIBS_DIR)

    download_link = "https://github.com/AleksandrovskyV/vram_crunch/releases/download/e1/VRAM_Folder_Crunch.exe"
    local_file_path = os.path.join(LOCAL_LIBS_DIR, "VRAM Folder Crunch.exe")
    
    dlg.SetString(ID_EXE_DIR, "Downloads...")

    try:
        req = urllib_req.Request(download_link, headers={'User-Agent': 'Mozilla/5.0'})
        response = urllib_req.urlopen(req)
        try:
            with open(local_file_path, 'wb') as f:
                f.write(response.read())
        finally:
            response.close() 

        if os.path.isfile(local_file_path):
            dlg.U_EXE_PATH = local_file_path
            save_settings_to_json("exe_path", dlg.U_EXE_PATH)
            dlg.SetString(ID_EXE_DIR, local_file_path)
            print("Exe path updated: " + str(local_file_path))
        else:
            old_path = dlg.U_EXE_PATH if dlg.U_EXE_PATH else "Try Mirror..."
            dlg.SetString(ID_EXE_DIR, old_path)
        return True

    except Exception as e:
        old_path = dlg.U_EXE_PATH if dlg.U_EXE_PATH else "Try Mirror..."
        dlg.SetString(ID_EXE_DIR, old_path)
        c4d.gui.MessageDialog("Failed download: {}\nCheck connection, or try Mirror...".format(str(e)))
        return False


def get_json_config_path():
    """Находит путь к конфигу в нашей локальной папке libs"""
    if not SCRIPT_DIR:
        return None

    config_filename = SHORT_NAME + "_config.json"
    return os.path.join(SCRIPT_DIR, config_filename)


def save_settings_to_json(key, data_value):
    """
    Сохраняет данные по конкретному ключу с добавлением даты.
    Пример: save_settings_to_json("exe_path", "C:\\path\\to\\tool.exe")
    """
    path = get_json_config_path()
    if not path:
        return
    
    current_config = {}
    if os.path.exists(path):
        try:
            with open(path, 'r') as f:
                current_config = json.load(f)
                if not isinstance(current_config, dict):
                    current_config = {}
        except Exception:
            current_config = {}


    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    current_config[key] = {
        "value": data_value,
        "date": now_str
    }

    # 4. Записываем обновленный словарь обратно в файл
    try:
        if not os.path.exists(SCRIPT_DIR):
            os.makedirs(SCRIPT_DIR)
            
        with open(path, 'w') as f:
            json.dump(current_config, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print("Ошибка сохранения JSON: {}".format(e))

def load_settings_from_json(key):
    path = get_json_config_path()
    if not path or not os.path.exists(path):
        return None
    try:
        with open(path, 'r') as f:
            config = json.load(f)
            if isinstance(config, dict) and key in config:
                # Возвращаем только само значение из структуры {"value": ..., "date": ...}
                return config[key].get("value")
    except Exception as e:
        print("Ошибка чтения JSON: {}".format(e))
    return None



# Идентификаторы
ID_ABOUT = 1000

ID_PIL_TEXT = 1001
ID_LINK_DOWN = 1002
ID_MIRROR = 1003
ID_EXE_OPEN = 1004

ID_EXE_DIR = 1005
ID_DIR_EXE_OPEN = 1006

ID_LBL_DIR = 1007
ID_TXT_DIR = 1008
ID_BTN_DIR = 1009
ID_LBL_TARGET = 1010
ID_CMB_ALGO = 1011
ID_CMB_UNIT = 1012
ID_EDT_VALUE = 1013
ID_LBL_EXCLUDE = 1014
ID_EDT_EXCLUDE = 1015

ID_OK = 1016

class TextureToolDialog(c4d.gui.GeDialog):
    def __init__(self):
        super(TextureToolDialog, self).__init__()
        self.result = {
            "algo": "VRAM", 
            "value": 512.0, 
            "unit": "MB", 
            "excludes": ('.psd', '.hdr'), 
            "dir": None
        }

        self.U_EXE_PATH = load_settings_from_json("exe_path")
        self.prev_unit = "MB"
        self.is_confirmed = False

    def CreateLayout(self):


        self.SetTitle(TOOL_NAME)
        
        # Главная вертикальная группа на всё окно
        self.GroupBegin(10, c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT, cols=1, rows=0)
        self.GroupSpace(0, 10) 
        self.GroupBorderSpace(14, 14, 14, 14)


        # Описание

        about_text = (
            "Горит...\n\n"
            "Pipeline to reduce tex folder size under user input values\n"
            "Designed as post-action for collected texture folders to\n"
            "resolve 'Out of VRAM' errors in GPU render engines\n\n"
            "Backup 'Source Folder' always included ~\n\n"
            "And need download standalone...\n\n"
        )

        self.GroupBegin(0, c4d.BFH_SCALEFIT, cols=1, rows=0)
        

        if sys.version_info >= (3, 0):
            self.GroupBorderSpace(0, 0, 0, 100) 
            self.AddStaticText(ID_ABOUT, c4d.BFH_SCALEFIT, name=about_text, borderstyle=0, initw=0, inith=40)
        else:
            # Для Python 2 (C4D R20)
            self.GroupBorderSpace(0, 0, 0, 10) 
            for line in about_text.split('\n'):
                # Передаем 0 вместо ID — C4D присвоит уникальный ID автоматически
                self.AddStaticText(0, c4d.BFH_SCALEFIT, name=line, borderstyle=0, initw=0, inith=0)


        self.GroupEnd()
        
        

        self.AddSeparatorH(0, flags=c4d.BFH_SCALEFIT)

        # Строка тянется по ширине (3)

        # --- Блок 4: Кнопка подтверждения ---
        # Создаем горизонтальную группу из 2 колонок, которая тянется по ширине окна

        extends = 1
        self.AddStaticText(221, 0, name="", borderstyle=0, initw=0, inith=extends)

        # cols=4, rows=1 — всё верно
        self.GroupBegin(4000, c4d.BFH_SCALEFIT, cols=4, rows=1)
        self.GroupSpace(0, 0)
        
        # 1. Тексту даем флаг BFH_SCALEFIT — он займет все пустое пространство слева
        self.AddStaticText(ID_PIL_TEXT, c4d.BFH_SCALEFIT, name="Folder with standalone", borderstyle=0, initw=0, inith=0)
        
        # 2. Кнопкам даем флаг BFH_LEFT или BFH_FIT и фиксированную ширину, чтобы они не растягивались
        self.AddButton(ID_LINK_DOWN, c4d.BFH_LEFT, name="Download", initw=100)
        self.AddButton(ID_MIRROR, c4d.BFH_LEFT, name="Mirror", initw=100)
        self.AddButton(ID_EXE_OPEN, c4d.BFH_LEFT, name="Open?", initw=100)
        
        self.GroupEnd() # Конец блока кнопок



        self.GroupBegin(1995, c4d.BFH_SCALEFIT, cols=2, rows=1)
        self.GroupSpace(0, 0)
        self.AddEditText(ID_EXE_DIR, c4d.BFH_SCALEFIT, editflags=1) 
        
        self.SetString(ID_EXE_DIR, self.U_EXE_PATH if self.U_EXE_PATH else "No .exe selected...")

        self.AddButton(ID_DIR_EXE_OPEN, 0, name="...", initw=30)
        self.GroupEnd()

        self.AddStaticText(222, 0, name="", borderstyle=0, initw=0, inith=extends)

        self.AddSeparatorH(0, flags=c4d.BFH_SCALEFIT)

        self.AddStaticText(444, 0, name="", borderstyle=0, initw=0, inith=extends)



        # --- Блок 1: Выбор папки ---
        self.AddStaticText(ID_LBL_DIR, c4d.BFH_SCALEFIT, name="Folder with collected textures:")


        # Строка тянется по ширине (3)
        self.GroupBegin(2000, c4d.BFH_SCALEFIT, cols=2, rows=1)
        self.GroupSpace(5, 0)

        # Инпут тянется (3), кнопка фиксирована (0)
        self.AddEditText(ID_TXT_DIR, c4d.BFH_SCALEFIT, editflags=1) 
        #current_dir = self.result.get("dir", "")
        self.SetString(ID_TXT_DIR, "No folder selected...")

        self.AddButton(ID_BTN_DIR, 0, name="...", initw=30)
        self.GroupEnd()

        # --- Блок 2: Целевой размер ---
        self.AddStaticText(ID_LBL_TARGET, c4d.BFH_SCALEFIT, name="Target VRAM size:")
        
        # Строка тянется по ширине (3)
        self.GroupBegin(3000, c4d.BFH_SCALEFIT, cols=3, rows=1)
        self.GroupSpace(5, 0)
        # Инпут тянется (3), комбобоксы фиксированы (0)
        self.AddEditText(ID_EDT_VALUE, c4d.BFH_SCALEFIT)
        self.SetString(ID_EDT_VALUE, "512")
        
        
        self.AddComboBox(ID_CMB_UNIT, 0, initw=55)
        self.AddChild(ID_CMB_UNIT, 0, "MB")
        self.AddChild(ID_CMB_UNIT, 1, "GB")
        
        self.AddComboBox(ID_CMB_ALGO, 0, initw=70)
        self.AddChild(ID_CMB_ALGO, 0, "VRAM")
        self.AddChild(ID_CMB_ALGO, 1, "DRIVE")

        self.GroupEnd()

        # --- Блок 3: Исключения ---
        self.AddStaticText(ID_LBL_EXCLUDE, c4d.BFH_SCALEFIT, name="Exclude formats:")
        
        # Инпут тянется на всю ширину (3)
        self.AddEditText(ID_EDT_EXCLUDE, c4d.BFH_SCALEFIT)
        self.SetString(ID_EDT_EXCLUDE, "psd hdr")

  

        self.AddStaticText(445, 0, name="", borderstyle=0, initw=0, inith=0)

        self.AddButton(ID_OK, 0, name="PROCESSION", initw=120)

        self.AddStaticText(446, 0, name="", borderstyle=0, initw=0, inith=0)

        self.GroupEnd() 
        return True

    def Command(self, id, msg):
        if id == ID_LINK_DOWN:
            download_from_web()
            return True
        elif id == ID_MIRROR:
            c4d.storage.GeExecuteFile("https://github.com/AleksandrovskyV/python")
            return True
        
        elif id==ID_DIR_EXE_OPEN:

            filepath = c4d.storage.LoadDialog(
                type=c4d.FILESELECTTYPE_ANYTHING,
                title="Select standalone .exe", 
                flags=c4d.FILESELECT_LOAD
            )

            if filepath:
                self.SetString(ID_EXE_DIR, filepath)
                save_settings_to_json("exe_path", filepath)
                
                self.U_EXE_PATH = filepath
            
            return True

        elif id == ID_EXE_DIR:
            # 1. Читаем текст и сразу очищаем его от кавычек по краям
            user_entered_path = self.GetString(ID_EXE_DIR).strip('"')

            if os.path.isfile(user_entered_path):
                self.U_EXE_PATH = user_entered_path
                save_settings_to_json("exe_path", self.U_EXE_PATH)
                self.SetString(ID_EXE_DIR, user_entered_path)
                print("Exe path updated:", user_entered_path)
            else:
                c4d.gui.MessageDialog("Only Copy-Paste or click button!")
                old_path = self.U_EXE_PATH if self.U_EXE_PATH else "Not Corrected Path, Try again..."
                self.SetString(ID_EXE_DIR, old_path)

            return True

        elif id==ID_EXE_OPEN:
            if self.U_EXE_PATH:
                os.startfile(self.U_EXE_PATH)
            return True

        elif id == ID_BTN_DIR:
            folder = c4d.storage.LoadDialog(title="Select Texture Folder", flags=2)
            if folder:
                self.SetString(ID_TXT_DIR, folder)
                self.result["dir"] = folder
            
            return True

        
        elif id == ID_CMB_ALGO:
            algo_idx = self.GetInt32(ID_CMB_ALGO)
            if algo_idx == 0:
                self.SetString(ID_LBL_TARGET, "Target VRAM size:")
                self.result["algo"] = "VRAM"
            else:
                self.SetString(ID_LBL_TARGET, "Target Folder size:")
                self.result["algo"] = "DRIVE"
            return True

        
        elif id == ID_CMB_UNIT:
            try:
                raw_text = self.GetString(ID_EDT_VALUE).replace(',', '.')
                current_val = float(raw_text)
                unit_idx = self.GetInt32(ID_CMB_UNIT)
                current_unit = "MB" if unit_idx == 0 else "GB"

                if current_unit == self.prev_unit:
                    return True

                if current_unit == "GB" and self.prev_unit == "MB":
                    new_val = current_val / 1024.0

                    new_text = "%.3f" % new_val
                    new_text = new_text.rstrip('0').rstrip('.')

                elif current_unit == "MB" and self.prev_unit == "GB":
                    new_val = int(current_val * 1024)
                    new_text = str(new_val)
                else:
                    return True

                self.SetString(ID_EDT_VALUE, new_text)
                self.prev_unit = current_unit
            except ValueError:
                unit_idx = 0 if self.prev_unit == "MB" else 1
                self.SetInt32(ID_CMB_UNIT, unit_idx)
            return True


        elif id == ID_OK:
            if not self.result["dir"]:
                c4d.gui.MessageDialog("Please select a folder first!")
                return True
            try:
                raw_val = self.GetString(ID_EDT_VALUE).replace(',', '.')
                self.result["value"] = float(raw_val)
                self.result["algo"] = "VRAM" if self.GetInt32(ID_CMB_ALGO) == 0 else "DRIVE"
                self.result["unit"] = "MB" if self.GetInt32(ID_CMB_UNIT) == 0 else "GB"

                raw_input = self.GetString(ID_EDT_EXCLUDE).strip().split()
                cleaned_excludes = []
                for ext in raw_input:
                    ext = ext.strip().lower()
                    if not ext.startswith('.'):
                        ext = '.' + ext
                    cleaned_excludes.append(ext)
                
                self.result["excludes"] = tuple(cleaned_excludes)
                self.is_confirmed = True

                #self.Close() # Сначала закрываем окно
                start_texture_optimization(self.result) 
                return True

            except ValueError:
                c4d.gui.MessageDialog("Please enter a valid target size number!")
            return True

        return True




def start_texture_optimization(data):
    exe_path = load_settings_from_json("exe_path")

    if not exe_path:
        c4d.gui.MessageDialog("Please select VRAM Folder Crunch.exe first!")
        return False

    if not os.path.isfile(exe_path):
        c4d.gui.MessageDialog(".exe not found: " + str(exe_path))
        return False

    config = {
        "algo": data["algo"],
        "raw_val": data["value"],
        "unit": data["unit"],
        "exclude": list(data["excludes"]),
        "input_dir": data["dir"],
    }

    config_json = json.dumps(config, ensure_ascii=False)
    command = [exe_path, "--mode", "silent", "--config", config_json]

    try:
        import sys
        
        if sys.version_info >= (3, 0):
            # Для Python 3: запускаем процесс полностью независимо
            # Окно плагина C4D не замерзает, консоль живет своей жизнью
            subprocess.Popen(command, creationflags=subprocess.CREATE_NEW_CONSOLE)
        else:
            # Для Python 2 (Cinema 4D R20)
            # Точно так же отправляем процесс в систему асинхронно
            subprocess.Popen(command, creationflags=0x00000010)

        # Мы больше НЕ вызываем .wait() и НЕ вызываем subprocess.run().
        # Cinema 4D просто успешно запустила задачу и сразу готова к работе дальше.
        return True

    except Exception as e:
        c4d.gui.MessageDialog("Failed to start optimizer:\n{}".format(e))
        return False


def user_window_gui():
    global dlg
    dlg = TextureToolDialog()
    dlg.Open(dlgtype=c4d.DLG_TYPE_ASYNC, defaultw=400, defaulth=280)

if __name__ == '__main__':
    user_window_gui()