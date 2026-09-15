"""

Checker

Author: Viktor Aleksandrovsky & Google AI
Written & Tested for Maxon Cinema 4D R20+ and R26

Description-US:Custom GeDialog with methods & helpers|for spamming development

Might be moved to a module later if cleaned from trash...

"""

import c4d       # .py api cinema4d
import sys       # модуль самого python (version check)
import os        # работа с OS, пути \ поиск-чтение файлов
import inspect   # анализ и дебаг кода 
import importlib # динамическая подгрузка .py модулей
import tempfile  # создание временных файлов (лог,cache)

import time      # таймеры\паузы
import math      # математика\вычисления 
import json      # чтения\запись json
import re        # работа со строками (string)

import datetime  # генерация текущего времени

# =========== IDs ===================

PANEL = None
TOOL_NAME  = "Checkers"
SHORT_NAME = "chkrs"
SCRIPT_DIR = os.path.dirname(__file__)
IS_PY3 = sys.version_info >= (3, 0)

NULL_ID         = 0  # TRICK
MAIN_ID         = 1 
MAIN_COMBO_ID   = 2
MAIN_TOP_GRP_ID = 3  # Vertical Main Group
MAIN_ABT_GRP_ID = 4  # Abouts groups from Combobox 
MAIN_FNC_GRP_ID = 5  # Horizontal Columns [Quest, Main, Inputs\Version]

DESC_HEADER_ID  = 6  # Header Description
DESC_GRP_ID     = 7  # Text rewrite lines group

# need rewrite
COMBO_SUB_ID        = 5000   # Combobox Elem Offset
INPUT_QST_ID_OFFSET = 10000  # Question Offset 
INPUT_STR_ID_OFFSET = 20000  # Input String Value Offset


GROUP_MAP = {
    501:{
      "name": "Console Loggers", 
      "desc": "Script Family around 'Console' printings",  
    },
    502:{
      "name": "Calculators", 
      "desc": "Script Family around 'math' calculations",  
    },
    503:{
      "name": "Getters", 
      "desc": "Script Family around... heh, i dont know",  
    },
    504:{
      "name": "Breaking News", 
      "desc": "Script Family...",  
    },
}

FUNCTIONS_MAP = {
    1001: { "label": "Print Versions.. ",
            "desc" : "check version Cinema 4D and Python... or return",
            "group": "Console Loggers",
            "func" : "version",
    },
    1002: { "label": "Print Hierarchy!", # seq: sequence heh
            "desc" : "print hierarchy 'object manager' in different styles",
            "group": "Console Loggers",
            "func" : "run_print_hierarchy",# loader ⌵
            "btns" :{#"core"    :"print_core_hierarchy",    # for debug "copy-paste" in other scripts
                     #"user"    :"print_user_hierarchy",    # default "checker" version call
                      1003:{"ndjson"  :"print_ndjson_hierarchy"},
                      1004:{"alembic" :"print_abc_hierarchy"},     # alembic houdini style 
                      1005:{"seq?"    :"print_seq_hierarchy_gpt"}, # extend template "print_seq_hierarchy" 
                    },
            "input": "btns",
    },
    1006:{  "label": "Print Z-Order... ",
            "group": "Console Loggers",
            "desc" : "print object z-order from current view",
            "func" : "print_z_orderer",
    },
    1007: { "label": "Print IDs value  ",
            "desc" : "checked ID in system variables",
            "group": "Console Loggers",
            "func" : "check_c4d_py_module_variable",
            "input": ("string","OBJECT_GENERATOR")
    },
    1008: { "label": "Scan WindowID",
            "desc" : "scan c4d windows by name or index to find params IDs",
            "group": "Console Loggers",
            "func" : "scan_window_params",
            "input": ("string","alembic")
    },

    1009: { "label" : "Extend Cam Res..",
            "desc"  : "return \"camera data\" from extend resolution value *in pixels",
            "group" : "Calculators",
            "func"  : "calc_camdata_by_extend",
            "input" : ("values", "row", 100),
            "values": {
                "row_labels": {
                    1010: ("AddStaticText", "width  (px)"),
                    1011: ("AddStaticText", "height (px)"),
                    1012: ("AddStaticText", "sensor (mm)"),
                    1013: ("AddStaticText", "extend (px)"),
                },
                "row_inputs": {
                    1014: ("AddEditNumber", 1920, "w"),
                    1015: ("AddEditNumber", 1080, "h"),
                    1016: ("AddEditNumber", 36.0, "s"),
                    1017: ("AddEditNumber", 25, "extend"),
                }
            },     
    },
    1040: { "label": "Call Window",
            "desc" : "call window by ID",
            "group": "Getters",
            "func" : "call_window",
            "input": ("string","12305"),
    },
    1041: { "label": "Get...",
            "desc" : "get something",
            "group": "Getters",
            "func" : "get_something",
            "input": ("string","?"),
    },
    1042: { "label": "append...",
            "desc" : "global status check",
            "group": "Breaking News",
            "func" : "append_user",
            "input": ("web","VONC","https://g..."),
    },
}


"""
       0    1    2
name   2000 2001 2002
pos    2003 2004 2005
date   2006 2007 2008
check  2009 2010 2011
"""

USER_INIT = {
    2000: { "name"      : "aturtur",
            "link"      : "https://github.com/aturtur/cinema4d-scripts",
            "type"      : "github",
            "lastdate"  : "?",
            "checkdate" : "always", # fix spaming
    },
    2001: { "name"      : "vvdwarf",
            "link"      : "https://github.com/AleksandrovskyV/c4d",
            "type"      : "github",
            "lastdate"  : "2026:09:15",
            "checkdate" : "always",
    },
    2002: { "name"      : "boghma",
            "link"      : "https://github.com/DunHouGo",
            "type"      : "github",
            "lastdate"  : "?",
            "checkdate" : "always",
    },
    2003: { "name"      : "zomax",
            "link"      : "https://github.com/corneliusdammrich",
            "type"      : "github",
            "lastdate"  : "?",
            "checkdate" : "always",
    },
    2004: { "name"      : "udin",
            "link"      : "https://mikeudin.net/",
            "type"      : "custom_web",
            "lastdate"  : "?",
            "checkdate" : "always",
    },
}

"""
    1044: {
            "label": "Scan MenuIds?",
            "group": "Console Loggers",
            "func" : "search_menu_command",
            "desc" : "Scanning top mehu bar?",
            "input": "string",
    }
"""


# ===== Specific Cases ===============

import ssl # 2\3
import codecs #cyrillic safe

# urllib запросы в интернет

if IS_PY3:
    import urllib.request as urllib_req
    from urllib.parse import urlparse
else:
    import urllib2 as urllib_req
    from urlparse import urlparse


def get_dict_values(d):
    return d.values() if IS_PY3 else d.itervalues()

def get_dict_items(d):
    return d.items() if IS_PY3 else d.iteritems()

def get_first_item(d):
    if IS_PY3:
        return next(iter(d.items()))
    else:
        return d.iteritems().next()

def get_dict_keys(d):
    return d.keys() if IS_PY3 else d.iterkeys()


# json safe

def safe_open_json(path, mode='r'):
    #cyrillic safe and python 2\3
    if IS_PY3:
        return open(path, mode, encoding='utf-8')
    else: 
        return codecs.open(path, mode, encoding='utf-8')

def safe_json_dump(data, f):
    #cyrillic safe and python 2\3
    if IS_PY3:
        json.dump(data, f, ensure_ascii=False, indent=4)
    else:
        json.dump(data, f, indent=4)

def get_sys_date_string(format_str="%Y:%m:%d"):
    #  python 2\3
    safe_format = str(format_str).replace('%D', '%d')
    return datetime.datetime.now().strftime(safe_format)

def decode_net_response(response):
    #  python 2\3
    raw_data = response.read()
    if IS_PY3:
        return json.loads(raw_data.decode('utf-8'))
    else:
        return json.loads(raw_data)

def safe_print(msg_format, *args):
    #cyrillic safe and python 2\3
    if IS_PY3:
        print(msg_format.format(*args))
    else:
        safe_args = tuple(
            a.encode('utf-8') if isinstance(a, unicode) else a for a in args
        )
        safe_format = msg_format.encode('utf-8') if isinstance(msg_format, unicode) else msg_format
        print(safe_format.format(*safe_args))



# database

def get_json_config_path():
    if not SCRIPT_DIR:
        return None

    config_filename = SHORT_NAME + "_config.json"
    return os.path.join(SCRIPT_DIR, config_filename)


def init_users_database():
    global USER_INIT
    path = get_json_config_path()
    if not path:
        return False

    # 1: first run
    if not os.path.exists(path):
        try:
            if not os.path.exists(SCRIPT_DIR):
                os.makedirs(SCRIPT_DIR)

            config = {str(k): v for k, v in USER_INIT.items()}

            with safe_open_json(path, 'w') as f:
                safe_json_dump(config, f)

            #print("Database successful init (First run)")
            return True
        except Exception as e:
            print("Error database init: {}".format(e))
            return False

    # 2: update USER_INIT 
    try:
        with safe_open_json(path, 'r') as f:
            disk_config = json.load(f)
            if not isinstance(disk_config, dict):
                disk_config = {}
                
        for disk_key, disk_value in disk_config.items():
            try:
                int_key = int(disk_key)
            except ValueError:
                continue 

            if int_key == 2000 and not disk_value.get("lastdate"):
                continue

            USER_INIT[int_key] = disk_value

        #print("Database successfully synchronized with disk data.")
        return True

    except Exception as e:
        print("Error reading/syncing database from disk: {}".format(e))
        return False


def append_user(name, url):
    global USER_INIT

    # checking git\not git and get mark
    # check name in json
    # if not name > add

    path = get_json_config_path()
    if not path or not name or not url:
        return False

    stored_name = str(name).strip().lower()
    clean_url = str(url).strip()

    if not IS_PY3 and isinstance(stored_name, str):
        stored_name = stored_name.decode('utf-8')

    if stored_name == "arturtur":
        print("Append Error: ARTURTUR is immutable!")
        return False

    current_config = {}
    if os.path.exists(path):
        try:
            with safe_open_json(path, 'r') as f:
                disk_data = json.load(f)
                if isinstance(disk_data, dict):
                    current_config = {str(k): v for k, v in disk_data.items()}
        except Exception:
            current_config = {}

    existing_key = None
    for k, v in current_config.items():
        if v.get("name", "").lower() == stored_name:
            existing_key = k
            break

    detected_type = "github" if "github.com" in clean_url.lower() else "custom_web"

    if existing_key is not None:
        current_config[existing_key]["link"] = clean_url
        current_config[existing_key]["type"] = detected_type
        current_config[existing_key]["lastdate"] = "?" 
        safe_print("User '{}' updated under existing ID {}.".format(stored_name.upper(), existing_key))
    else:
        existing_ids = [int(k) for k in current_config.keys()]
        next_id = max(existing_ids) + 1 if existing_ids else 2001

        current_config[str(next_id)] = {
            "name"      : stored_name,
            "link"      : clean_url,
            "type"      : detected_type,
            "lastdate"  : "?",
            "checkdate" : "never"
        }
        safe_print("Appended new user '{}' with ID {}.", stored_name.upper(), next_id)

    try:
        if not os.path.exists(SCRIPT_DIR):
            os.makedirs(SCRIPT_DIR)

        with safe_open_json(path, 'w') as f:
            safe_json_dump(current_config, f)
        
        USER_INIT = current_config
        return True
        
    except Exception as e:
        print("error append_database JSON: {}".format(e))
        return False


def check_user_update(a_id):
    global USER_INIT
    path = get_json_config_path()
    if not path: return False

    key = int(a_id)
    if key not in USER_INIT:
        if str(a_id) in USER_INIT:
            key = str(a_id)
        else:
            print("check_user_update false: key not found in USER_INIT")
            return False

    user_data = USER_INIT[key]
    gitlink = user_data.get("link", "")
    success, last_github_date = check_github(gitlink)
    if not success or not last_github_date:
        print("check_user_update false: network error")
        return False

    if "T" in last_github_date:
        new_clean_date = last_github_date.split('T')[0].replace('-', ':')
    else:
        new_clean_date = last_github_date

    USER_INIT[key]["lastdate"] = str(new_clean_date)
    USER_INIT[key]["checkdate"] = get_sys_date_string("%Y:%m:%d")

    disk_config = {}

    if os.path.exists(path):
        try:
            with safe_open_json(path, 'r') as f:
                disk_data = json.load(f)
                if isinstance(disk_data, dict):
                    disk_config = {str(k): v for k, v in disk_data.items()}
        except Exception:
            disk_config = {}

    str_key = str(a_id)
    today_check_date = get_sys_date_string("%Y:%m:%d")

    if str_key in disk_config:
        disk_config[str_key]["lastdate"] = str(new_clean_date)
        disk_config[str_key]["checkdate"] = today_check_date
    else:
        disk_config[str_key] = {param_k: param_v for param_k, param_v in user_data.items() if param_k != "ui_status"}
        disk_config[str_key]["lastdate"] = str(new_clean_date)
        disk_config[str_key]["checkdate"] = today_check_date

    try:
        with safe_open_json(path, 'w') as f:
            safe_json_dump(disk_config, f)
        
        return True
    except Exception as e:
        print("error saving updated date to JSON: {}".format(e))
        return False


def check_github(gitlink, lastdate=None): 
    if gitlink is None: 
        return False, None
    
    try:
        clean_link = gitlink.strip().rstrip('/')
        parsed_url = urlparse(clean_link)
        path_parts = [p for p in parsed_url.path.split('/') if p]

        if len(path_parts) < 1:
            return False, None

        user = path_parts[0]
        repo = path_parts[1] if len(path_parts) > 1 else None
        root = "https://api.github.com"

        if repo:
            api_url = "{}/repos/{}/{}".format(root, user, repo)
            target_key = "pushed_at"
        else:
            api_url = "{}/users/{}/events".format(root, user)
            target_key = "created_at"

        req = urllib_req.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
        #response = urllib_req.urlopen(req, timeout=5)

        context = ssl._create_unverified_context() if hasattr(ssl, '_create_unverified_context') else None
        if context:
            response = urllib_req.urlopen(req, timeout=5, context=context)
        else:
            response = urllib_req.urlopen(req, timeout=5)

        data = decode_net_response(response)
        #print(data)

        if repo:
            # for repo = dict
            last_github_date = data.get(target_key) if isinstance(data, dict) else None
        else:
            # for profile =  list get [0]
            if isinstance(data, list) and len(data) > 0:
                first_event = data[0]
                last_github_date = first_event.get(target_key) if isinstance(first_event, dict) else None
            else:
                last_github_date = None

        if not last_github_date:
            return False, None

        if lastdate:
            if last_github_date > lastdate:
                return True, last_github_date
            else:
                return False, last_github_date 

        return True, last_github_date

    except Exception as e:
        #print("case_error",e)
        return False, None


def open_web(link=None): 
    if link is None:
        return False
        
    import webbrowser 
    
    safe_link = str(link).strip()
    
    try:
        webbrowser.open(safe_link)
        safe_print("go to: {}", safe_link)
        return True
    except Exception as e:
        safe_print("Web Error: {}", str(e))
        c4d.storage.GeExecuteFile(safe_link)
        return False


"""
# trash backup
import threading
class BackgroundHtmlChecker(threading.Thread):
    def __init__(self, url, dialog_instance, target_group_id):
        threading.Thread.__init__(self)
        self.url = url
        self.dialog = dialog_instance
        self.group_id = target_group_id

    def run(self):
        try:
            req = urllib_req.Request(self.url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib_req.urlopen(req, timeout=5) as response:
                # Качаем на полную в фоне — синема этого НЕ ЗАМЕТИТ
                full_html = response.read()
                size = len(full_html)
                say = "Готово! Вес страницы: {} байт.".format(size)
        except Exception:
            say = "Не удалось достучаться до сервера."

        # Когда поток закончил работу, он безопасно обновляет интерфейс диалога
        self.dialog.LayoutFlushGroup(self.group_id)
        self.dialog.AddStaticText(0, 1, name=say) # c4d.BFH_SCALEFIT = 1
        self.dialog.LayoutChanged(self.group_id)
        
        c4d.EventAdd()



def get_raw_html_bytes(url):
    if not url: 
        return b""
        
    try:
        req = urllib_req.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib_req.urlopen(req, timeout=4) as response:
            full_html = response.read()#max_bytes
            size = len(full_html)
            return size
    except Exception:
        return b""


"""



# =========== HELPERS ===================

# get name current call function
def fname(): 
    return inspect.currentframe().f_back.f_code.co_name

# console print with === a =====
def logline(text="", espace=3, offset=-5, clamp=60 ):
    # Универсальное приведение к тексту
    if IS_PY3:
        text_unicode = str(text) if not isinstance(text, str) else text
    else:
        # В Python 2 бережно декодируем байты в unicode
        if not isinstance(text, unicode):
            try:
                text_unicode = str(text).decode('utf-8')
            except Exception:
                text_unicode = unicode(text)
        else:
            text_unicode = text

    text_len = len(text_unicode) + (espace * 2)

    total_fillers = clamp - text_len
    if total_fillers < 0:
        total_fillers = 0

    base_half = total_fillers // 2
    odd_remainder = total_fillers % 2
    left_count = base_half + offset
    right_count = base_half - offset + odd_remainder

    if left_count < 0:
        right_count += left_count
        left_count = 0
    if right_count < 0:
        left_count += right_count
        right_count = 0

    filler_left = left_count * u"="
    filler_right = right_count * u"="
    space = espace * u" "

    centered_line = filler_left + space + text_unicode + space + filler_right
    print("\n" + centered_line + "\n")


def version(target="console", full=False):
    import c4d, sys

    target = str(target).lower()

    cinemaNames = ["c4d","cinema","maxon"]
    pyNames = ["py","python"]
    debugNames = ["console","cmd", "print", "log"]

    cinemaVersion = c4d.GetC4DVersion()
    cinemaMajor = cinemaVersion // 1000
    cinemaNumber = cinemaVersion % 1000

    pythonVersion = sys.version_info
    p = pythonVersion

    if target in cinemaNames:
        return cinemaVersion if full else cinemaMajor

    if target in pyNames:
        return pythonVersion if full else p[0], p[1]

    if target in debugNames:
        logline = globals().get('logline', lambda *a, **kw: None)

        logline(fname())

        print("Cinema4D:  R{}.{}".format(cinemaMajor, cinemaNumber))
        print("Python: {}.{}.{}".format(p[0], p[1], p[2]))

        logline("вот так вот")

        return cinemaVersion, pythonVersion


# be default > open "Console Window"
# "Console Window" not "variable" to fast open Python Tab? Why?
# GePrint() out to "Console: default" and 1 str arg...
# WriteConsole() out to "Console: default" and...
# 2 methods? 
def call_window(target=12305, name="console", ctx="python"):
    import c4d
    search_query = str(target).strip()

    if search_query == "" or not search_query.isdigit():
        cmd_id = 12305 # open Console
    else:
        cmd_id = int(search_query)

    # close > open
    if c4d.IsCommandChecked(cmd_id):
        c4d.CallCommand(cmd_id)

    c4d.CallCommand(cmd_id)

    #if str(ctx).lower() == "python":
        #c4d.WriteConsole(str="a net ego")


# срань от ии...
def search_menu_command(search_query=""):
    """
    Рекурсивно сканирует главное меню Cinema 4D R20.
    Работает на "сырых" внутренних ID типов (3 и 4) в обход багов SDK Максона.
    """
    logline = globals().get('logline', lambda *a, **kw: None)

    query_str = str(search_query).strip()
    if query_str == "":
        logline(fname())
        print("Enter name or ID for search!")
        logline("вот так вот")
        return

    logline(fname())

    main_menu = c4d.gui.GetMenuResource("M_EDITOR")
    if not main_menu:
        print("Failed to read menu container M_EDITOR!")
        logline("вот так вот")
        return

    if query_str.isdigit():
        search_value = int(query_str)
        is_numeric = True
    else:
        search_value = query_str.upper()
        is_numeric = False

    found_items = []

    def parse_container(bc, path=""):
        if bc is None:
            return

        for menu_type, value in bc:

            if menu_type == 3:
                sub_name = bc.GetString(value)
                sub_bc = bc.GetContainer(value)

                new_path = "{} -> {}".format(path, sub_name) if path else sub_name
                parse_container(sub_bc, new_path)

            elif menu_type == 4:
                cmd_id = bc.GetInt32(value)
                cmd_name = bc.GetString(value)

                if is_numeric:
                    if cmd_id == search_value:
                        found_items.append({"path": path, "name": cmd_name, "id": cmd_id})
                else:
                    if search_value in cmd_name.upper():
                        found_items.append({"path": path, "name": cmd_name, "id": cmd_id})


    parse_container(main_menu)

    if found_items:
        print("'{}' find in mainmenu struct:".format(search_query))
        for item in found_items:
            print(" -> [ {} ] {} (ID: {})".format(item["path"], item["name"], item["id"]))
    else:
        print("'{}' not find in mainmenu struct.".format(search_query))

    logline("вот так вот")


# срань от меня
def get_something(intext=""):
    call_window(12305)
    c4d.CallCommand(13957) # Clear Console
    call_window(12305)
    if intext=="?":
        print("Maybe u read...")
    else:
        print("I dont knwo!")
    pass


# В интерфейсе cinema4d есть числовые значения\переменные для 
# обозначения части своих элементов (окон, объектов, и т.д) 
# Часть этих значений имеют текстовое представление. Пример: 
# test = c4d.OBJECT_GENERATOR 
# print(test) # выдаст значение 16384 
# Это число я использовал как флаг для регистрации
# плагин-генератора-геометрии, чтобы c4d знала к какому типу
# шаблона он относится и как его обновлять в интерфейсе
#      
# ..Да эти значения могут прыгать от версий к версиям?

def check_c4d_py_module_variable(variable=""):

    search_query = str(variable).strip()
    if search_query == "":
        logline(fname())
        print("Enter something, at least!")
        logline("вот так вот")
        return

    logline(fname())
    found_flags = []


    if search_query.isdigit():
        search_value = int(search_query)
        is_numeric_search = True
    else:
        search_value = search_query.upper()
        is_numeric_search = False

    for attr_name in dir(c4d):
        try:
            attr_value = getattr(c4d, attr_name)

            if is_numeric_search:
                if attr_value == search_value:
                    found_flags.append("c4d.{}".format(attr_name))
            else:
                if search_value in attr_name.upper():
                    found_flags.append("c4d.{} (values: {})".format(attr_name, attr_value))
        except Exception:
            pass

    if hasattr(c4d, "plugins"):
        for attr_name in dir(c4d.plugins):
            try:
                attr_value = getattr(c4d.plugins, attr_name)

                if is_numeric_search:
                    if attr_value == search_value:
                        found_flags.append("c4d.plugins.{}".format(attr_name))
                else:
                    if search_value in attr_name.upper():
                        found_flags.append("c4d.plugins.{} (values: {})".format(attr_name, attr_value))
            except Exception:
                pass

    if found_flags:
        print ("'{}' found in system variables:".format(search_query))
        for flag in found_flags:
            print( " -> {}".format(flag))
    else:

        cd_ver = version("c4d")
        py_ver, py_sub = version("py", full=True)[:2] # берем major и minor

        print( "'{}' not found as a variable in API C4D R{} / Python {}.{}".format(search_query, cd_ver, py_ver, py_sub))

    logline("вот так вот")



# Чтобы найти переменные окна и их индексы
# Как пример Alembic Export

def scan_window_params(variable="alembic", debug=True):
    logline = globals().get('logline', lambda *a, **kw: None)
    fname = globals().get('fname', lambda: "")

    search_query = str(variable).strip()
    if not search_query:
        logline(fname())
        print("Введи хоть что-нибудь!")
        logline("вот так вот")
        return

    logline(fname())
    
    doc = c4d.documents.GetActiveDocument()

    if search_query.isdigit():
        search_id = int(search_query)
        is_numeric_search = True
    else:
        search_name_upper = search_query.upper()
        is_numeric_search = False

    plugin_types = [
        (c4d.PLUGINTYPE_SCENESAVER, "EXPORT"),
        (c4d.PLUGINTYPE_SCENELOADER, "IMPORT"),
        (c4d.PLUGINTYPE_TOOL, "MODELING/TOOL"),      
        (c4d.PLUGINTYPE_COMMAND, "COMMAND/WINDOW"),   
        (c4d.PLUGINTYPE_OBJECT, "OBJECT/GENERATOR"), 
        (c4d.PLUGINTYPE_TAG, "TAG")                  
    ]

    plugins_to_check = []

    # 2. ТОТАЛЬНЫЙ СБОР ПЛАГИНОВ
    if is_numeric_search:
        for p_type, label in plugin_types:
            plug = c4d.plugins.FindPlugin(search_id, p_type)
            if plug:
                plugins_to_check.append((plug, label))
    else:
        plug = c4d.plugins.GetFirstPlugin()
        while plug:
            plug_name = plug.GetName()
            if plug_name and search_name_upper in plug_name.upper():
                plugin_id = plug.GetID()
                for p_type, label in plugin_types:
                    p_found = c4d.plugins.FindPlugin(plugin_id, p_type)
                    if p_found and not any(p == p_found for p, _ in plugins_to_check):
                        plugins_to_check.append((p_found, label))
            plug = plug.GetNext()

    if not plugins_to_check:
        print("check_window_descr: No active UI windows found for '{}'.".format(search_query))
        logline("вот так вот")
        return

    # 3. УНИВЕРСАЛЬНЫЙ ДАМП ДАННЫХ С ЗАЩИТОЙ ОТ НЕИЗВЕСТНЫХ ОБЪЕКТОВ C++
    for target_plugin, direction in plugins_to_check:
        plugin_id = target_plugin.GetID()
        plug_saver = None
        bc = None

        # ШАГ А: Проверяем приватные данные (Alembic / FBX)
        op = {}
        res = target_plugin.Message(c4d.MSG_RETRIEVEPRIVATEDATA, op)
        if res and op:
            plug_saver = op.get("imexporter") or op.get("op") or op.get("options") or op.get("component") or op.get("node")

        # ШАГ Б: Проверяем World Container (Preferences, Timeline)
        world_bc = c4d.GetWorldContainerInstance()
        if world_bc:
            try:
                bc_instance = world_bc.GetContainerInstance(plugin_id)
                # Безопасно проверяем, что контейнер вообще существует
                if bc_instance:
                    bc = bc_instance
            except Exception:
                pass

        # ШАГ В: Если это инструмент моделирования в контексте документа
        if not bc and doc:
            try: bc = c4d.plugins.GetToolData(doc, plugin_id)
            except Exception: pass

        # ШАГ Г: Фолбэк на стандартный GetDataInstance плагина
        if not plug_saver and not bc:
            plug_saver = target_plugin

        if plug_saver and not bc:
            try: bc = plug_saver.GetDataInstance()
            except Exception: pass

        # Получаем описание параметров окна (Description)
        description = None
        if plug_saver:
            try: description = plug_saver.GetDescription(c4d.DESCFLAGS_DESC_0)
            except Exception: pass
        if not description:
            try: description = target_plugin.GetDescription(c4d.DESCFLAGS_DESC_0)
            except Exception: pass

        # ВЫВОД РЕЗУЛЬТАТОВ
        print( "DUMP FOR [{}] PLUGIN: {} (ID: {})".format(direction, target_plugin.GetName(), plugin_id))
        print( "=========================================================")

        # ИСПРАВЛЕНИЕ: Безопасный пошаговый перебор контейнера
        has_content = False
        if bc:
            try:
                # Безопасный способ итерации по контейнеру в Python без list()
                for key, value in bc:
                    has_content = True
                    param_name = "UNKNOWN"
                    if description:
                        try:
                            param_desc = description.GetParameterI(c4d.DescID(c4d.DescLevel(key)))
                            if param_desc:
                                param_name = param_desc[c4d.DESC_NAME]
                        except Exception:
                            pass
                                
                    print( "ID: {:<6} | Name: {:<25} === Value: {}".format(key, param_name, value))
            except Exception:
                # Если наткнулись на Weight Manager или неподдерживаемые типы данных C++
                print( "Container contains internal C++ structures unreadable by Python API.")
                has_content = True

        if not bc or not has_content:
            print("Container BaseContainer is empty or hidden for this context.")
            
        print("=========================================================\n")

    logline("вот так вот")




# ========= OBJECT MANAGER  ===========


def getDocWrap(targetDoc=None, debug=False): # wrapper
    # Если документ передан явно, используем его
    if targetDoc:
        if debug:
            print("[gd][target]: targetDoc: {}".format(targetDoc.GetName()))
        return targetDoc
        
    # Если не передан, берем активный и ВСЕГДА пишем в консоль
    activeDoc = c4d.documents.GetActiveDocument()
    if activeDoc:
        print("[gd][auto]: activeDoc: {}".format(activeDoc.GetName()))
        return activeDoc
        
    return None


def walk_hierarchy(first_obj): # by yield
    """
    Итеративный обход ЛЮБОЙ иерархии (вниз и вбок от стартового объекта).
    """
    if not first_obj:
        return

    stack = [(first_obj, True)]
    while stack:
        obj, allow_next = stack.pop()
        yield obj
        
        if obj.GetDown():
            stack.append((obj.GetDown(), True))
        if obj.GetNext() and allow_next:
            stack.append((obj.GetNext(), True))


def walk_selected_hierarchy(selected_objects):  # by yield
    """
    Чистый итеративный обход ТОЛЬКО выделенных корней и их дочерней иерархии.
    Проверка GUID для защиты от дубликатов.
    """
    if not selected_objects:
        return
        
    allowed_roots_guids = set(obj.GetGUID() for obj in selected_objects)
    stack = [(obj, False) for obj in reversed(selected_objects)]
    
    while stack:
        obj, allow_next = stack.pop()
        yield obj
        
        if obj.GetDown():
            stack.append((obj.GetDown(), True))
                
        if obj.GetNext() and allow_next:
            next_guid = obj.GetNext().GetGUID()
            if next_guid not in allowed_roots_guids:
                stack.append((obj.GetNext(), True))


def rename_obj(obj, counter, suffix="_UI"):
    clean_name = obj.GetName()
    uuid = "{}{}".format(suffix, counter + 1)
    obj.SetName(clean_name + uuid)
    return


def run_batcher():

    # pre
    doc = getDocWrap()
    renameSelected=True
    selectAll=False

    if selectAll: 
        doc.SetActiveObject(None, c4d.SELECTION_NEW)

    # start
    first_obj = doc.GetFirstObject()
    counter = 0

    for obj in walk_hierarchy(first_obj):
        if renameSelected:
            rename_obj(obj, counter)
        if selectAll:
            doc.SetActiveObject(obj, c4d.SELECTION_ADD)

        counter += 1


def get_obj_list(targetDoc=None, zsort=False, debug=False):
    """
    Возвращает список объектов сцены, 
    опционально отсортированный по Z-глубине камеры
    """
    
    if debug: 
        fname = globals().get('fname', lambda: "")
        logline = globals().get('logline', lambda *a, **kw: None)
        logtext = fname() + "  |  zsort: " + str(zsort)
        logline(logtext)


    doc = getDocWrap(targetDoc, debug)
    if not doc:
        return []

    selected = doc.GetActiveObjects(0)
    
    if selected:
        raw_objects = list(walk_selected_hierarchy(selected))
    else:
        first_obj = doc.GetFirstObject()
        if not first_obj and debug:
            print("[get_obj_list]: empty scene!")
        raw_objects = list(walk_hierarchy(first_obj))
            
    if not zsort:
        return raw_objects


    bd = doc.GetActiveBaseDraw()
    if not bd: return raw_objects
    
    camera = (
        bd.GetSceneCamera(doc) 
        if bd.GetSceneCamera(doc) 
        else bd.GetEditorCamera()
    )

    if not camera: 
        return raw_objects

    if debug: 
        print("From: {}\n".format(camera.GetName())) 

    cam_mg_inv = ~camera.GetMg() 
    object_depths = []
    
    for obj in raw_objects:
        # исключаем объект камеры, 
        # из которой рассчитываем дистанцию
        if obj == camera: 
            continue

        # filter on only geom obj
        if not obj.IsInstanceOf(c4d.Obase):
            continue

        case = 1
        # 3. calc z-order

        if case==0:
            
            obj_world_pos = obj.GetMg().off
            obj_cam_pos = cam_mg_inv * obj_world_pos
            z_depth = obj_cam_pos.z
        else:
            # --- НАДЕЖНЫЙ РАСЧЕТ МИРОВЫХ КООРДИНАТ ---
            
            # GetMp() возвращает локальный центр геометрии объекта.
            # У сдвинутых или скопированных объектов он покажет истинный центр меша.
            obj_mg = obj.GetMg()
            local_center = obj.GetMp()
            obj_world_pos = obj_mg * local_center
            obj_cam_pos = cam_mg_inv * obj_world_pos
            z_depth = obj_cam_pos.z
        
        object_depths.append((z_depth, obj))

    # Сортируем от ближних к дальним
    object_depths.sort(key=lambda x: x[0])

    if debug:
        for index, (depth, obj) in enumerate(object_depths, start=1):
            behind_cam = " (Behind Cam)" if depth < 0 else ""
            print("{0}: {1} -> Z-depth: {2:.2f}{3}".format(
                index, obj.GetName(), depth, behind_cam
            ))

        print("\nSorted: " + str(len(object_depths)))

    return object_depths


def print_z_orderer():
    get_obj_list(zsort=True, debug=True)





# ======= PRINT HIERARHY =============


from collections import defaultdict
from textwrap import dedent

def run_print_hierarchy(func=None):
    #print(func)
    if func=="":
        print_user_hierarchy()
    else:
        print_user_hierarchy()


def print_core_hierarchy(target=None, indent="", _is_child=False):
    """
    Basic for copy-paste
    Если дать doc — принтит всю сцену.
    Если дать op — принтит СТРОГО этот объект и его детей (без чужих соседей).
    """
    import c4d
    if target is None:
        target = c4d.documents.GetActiveDocument()
    if not target: return

    if isinstance(target, c4d.documents.BaseDocument):
        op = target.GetFirstObject()
        is_isolated_op = False 
    else:
        op = target
        is_isolated_op = not _is_child 

    while op:
        print("{}└{}".format(indent, op.GetName()))

        if op.GetDown():
            print_core_hierarchy(op.GetDown(), indent + "    ", _is_child=True)
            
        if is_isolated_op:
            break
            
        op = op.GetNext()


def print_ndjson_hierarchy(target=None, debug=False):
    """
    Вариант на set + GUID (в R20).
    """
    
    logline = globals().get('logline', lambda *a, **kw: None)
    fname = globals().get('fname', lambda: "")
    logline(fname())


    doc = getDocWrap(targetDoc=None, debug=debug)
    if not doc:
        return

    roots = []
    is_isolated = False
    allowed_guids = None # Множество строк-GUID для моментального поиска O(1)

    if target is not None:
        if isinstance(target, c4d.documents.BaseDocument):
            roots = [target.GetFirstObject()] if target.GetFirstObject() else []
        else:
            roots = [target]
            is_isolated = True
    else:
        selected = doc.GetActiveObjects(0)
        if selected:
            # Собираем ТОЛЬКО GUID строк. Это супер-быстро и хэшируется без ошибок!
            allowed_guids = set(obj.GetGUID() for obj in walk_selected_hierarchy(selected))
            roots = selected
            is_isolated = False 
        else:
            first = doc.GetFirstObject()
            roots = [first] if first else []

    if not roots:
        if debug: print( "print_ndjson_hierarchy: empty roots")
        return

    #local_store = {} # УДАЛЯЕМ эту строку (больше не нужна)
    if debug: print("print_ndjson_hierarchy, start")

    stack = [(r, not is_isolated) for r in reversed(roots)]
    
    while stack:
        obj, allow_next = stack.pop()
        if not obj:
            continue
            
        child = obj.GetDown()
        if child:
            children_names = []
            current_child = child
            while current_child:
                # Быстрая проверка O(1) по хэшируемой строке GUID
                if allowed_guids is None or current_child.GetGUID() in allowed_guids:
                    children_names.append(current_child.GetName())
                current_child = current_child.GetNext()
            
            if children_names:
                # ИСПРАВЛЕНО: Печатаем строку NDJSON сразу по месту действия!
                # Теперь плевать на одинаковые имена — выведутся ВСЕ родительские объекты
                print('{"' + obj.GetName() + '":' + json.dumps(children_names) + '}')
            
            stack.append((child, True))
            
        if obj.GetNext() and allow_next:
            stack.append((obj.GetNext(), True))

    # Весь финальный цикл for parent, children in local_store.items(): — ПОЛНОСТЬЮ УДАЛЯЕМ
    
    logline("вот так вот")



def print_user_hierarchy(targetDoc=None, op=None, indent="", _internal=False, debug=True):


    doc = getDocWrap(targetDoc=targetDoc)
    if not doc:
        print("print_user_hierarchy: No document available.")
        return

    logline = globals().get('logline', lambda *a, **kw: None)
    fname = globals().get('fname', lambda: "")
    
    flag_none = getattr(c4d, "GETACTIVEOBJECTFLAGS_NONE", 0)

    # Точка входа (самый верхний вызов)
    if not _internal:
        logline(fname())
        
        # Определяем стартовые объекты
        if op is not None:
            ops = op if isinstance(op, (list, tuple)) else [op]
        else:
            # Используем GetActiveObjects для поддержки множественного выделения
            #ops = doc.GetActiveObjects(globals().get('c4d').GETACTIVEOBJECTFLAGS_NONE if globals().get('c4d') else 0)
            ops = doc.GetActiveObjects(flag_none)
            if not ops: # берем первый
                first_obj = doc.GetFirstObject()
                ops = [first_obj] if first_obj else []

        # Обходим все стартовые объекты верхнего уровня
        for current_op in ops:
            if current_op:
                print("{}└{}".format(indent, current_op.GetName()))
                # Спускаемся к детям. Передаем _internal=True, чтобы включилась правильная логика рекурсии
                print_user_hierarchy(doc, current_op.GetDown(), indent + "  ", _internal=True)
                
                # ЕСЛИ ВЫДЕЛЕНИЯ НЕ БЫЛО: мы должны пройтись по всему корню сцены (соседям первого объекта)
                #if op is None and not doc.GetActiveObjects(globals().get('c4d').GETACTIVEOBJECTFLAGS_NONE if globals().get('c4d') else 0):
                if op is None and not doc.GetActiveObjects(flag_none):
                    next_op = current_op.GetNext()
                    while next_op:
                        print("{}└{}".format(indent, next_op.GetName()))
                        print_user_hierarchy(doc, next_op.GetDown(), indent + "  ", _internal=True)
                        next_op = next_op.GetNext()

        logline("вот так вот")
        return

    # Логика для рекурсивного обхода (внутренние уровни / дети)
    if op is None:
        return

    # Печатаем текущего ребенка
    print("{}└{}".format(indent, op.GetName()))
    
    # Рекурсивно уходим в его детей (вглубь)
    print_user_hierarchy(doc, op.GetDown(), indent + "  ", _internal=True)
    
    # Переходим к следующему ребенку на этом же уровне (вбок)
    print_user_hierarchy(doc, op.GetNext(), indent, _internal=True)


def get_child_structure_signature(op):
    """Собирает имена и структуру всех детей в одну строку."""
    if not op: return ""
    signatures = []
    child = op.GetDown()
    while child:
        signatures.append(child.GetName())
        if child.GetDown():
            signatures.append("(" + get_child_structure_signature(child) + ")")
        child = child.GetNext()
    return ",".join(signatures)


def print_seq_hierarchy(doc=None, op=None, indent=0, _internal=False):
    """
    Интеллектуальный дебаггер по твоему кастомному паттерну символов.
    Зона Статуса (слева) и Зона Иерархии (справа) разделены линией '|'.
    """
    func_about = dedent("""\
        Sequence hierarchy merging in logs, marks:
        # Broken Sequence - logging warnings...
        * Problem object
    """)

    # =====================================================================
    if not _internal and doc is None:
        case_a = globals().get('doc')
        case_b = globals().get('c4d').documents.GetActiveDocument() if globals().get('c4d') else None
        doc = case_a or case_b
        
    if not doc: print("Error: doc not found"); return

    logline = globals().get('logline', lambda *a, **kw: None)
    fname = globals().get('fname', lambda: "")

    space = 2    # offset levels (count " ")
    
    # column separator
    col_divider = "|"      
    col_offset = 4
    column = col_divider + (col_offset * " ")

    # =====================================================================
    def print_level_core(start_op, level_depth):
        if not start_op: return
        
        # calc offsets current level
        level_spaces = " " * (level_depth * space)
        
        siblings = []
        curr = start_op
        while curr:
            siblings.append(curr)
            curr = curr.GetNext()
        
        pattern = re.compile(r'^(.*?)([\-_.\s]?)(?:\.|\b)?(\d+)$')
        groups = defaultdict(list)
        single_objects = []
        
        # Get object on current level
        for obj in siblings:
            name = obj.GetName()
            match = pattern.match(name)
            if match:
                base, separator, digits = match.groups()
                groups[(base, separator)].append((int(digits), obj, len(digits)))
            else:
                single_objects.append((name, [obj], "single", ""))

        # Scanning Sequences
        # Scanning Sequences
        level_has_any_broken = False # Флаг: сломано ли что-то на этом уровне или ниже
        
        for (base, separator), items in groups.items():
            if len(items) > 7:
                items.sort(key=lambda x: x)
                
                reference_obj = items[0][1]
                reference_signature = get_child_structure_signature(reference_obj)
                digits_len = items[0][2]
                
                analyzed_sequence = []
                has_warnings = False
                
                for digits, obj, _ in items:
                    current_sig = get_child_structure_signature(obj)
                    is_broken = (current_sig != reference_signature)
                    if is_broken:
                        has_warnings = True
                        level_has_any_broken = True # Помечаем весь уровень как проблемный
                    analyzed_sequence.append({"frame_num": digits, "obj": obj, "is_broken": is_broken})
                
                if not has_warnings:
                    all_objs = [data[1] for data in items]
                    hidden_start = str(items[1][0]).zfill(digits_len)
                    hidden_end = str(items[-2][0]).zfill(digits_len)
                    range_str = "{}-{}".format(hidden_start, hidden_end)
                    single_objects.append((base, all_objs, "sequence_clean", range_str))
                else:                    
                    temp_clean_range = []
                    temp_clean_objs = []
                    
                    for i, node in enumerate(analyzed_sequence):
                        if i == 0 or i == len(analyzed_sequence) - 1:
                            if temp_clean_range:
                                range_str = "{}-{}".format(temp_clean_range[0], temp_clean_range[-1])
                                single_objects.append(("*", temp_clean_objs, "sequence_star", range_str))
                                temp_clean_range, temp_clean_objs = [], []
                            single_objects.append((node["obj"].GetName(), [node["obj"]], "single", ""))
                            continue
                        
                        if node["is_broken"]:
                            if temp_clean_range:
                                range_str = "{}-{}".format(temp_clean_range[0], temp_clean_range[-1])
                                single_objects.append(("*", temp_clean_objs, "sequence_star", range_str))
                                temp_clean_range, temp_clean_objs = [], []
                            
                            single_objects.append((node["obj"].GetName(), [node["obj"]], "single_broken", ""))
                        else:
                            formatted_num = str(node["frame_num"]).zfill(digits_len)
                            temp_clean_range.append(formatted_num)
                            temp_clean_objs.append(node["obj"])
            else:
                for digits, obj, _ in items:
                    single_objects.append((obj.GetName(), [obj], "single", ""))
        
        # Sort by Cinema 4D index
        single_objects.sort(key=lambda x: min(siblings.index(o) for o in x[1]))
        
        # Printing
        for display_name, objs, item_type, range_str in single_objects:
            if item_type == "sequence_clean":
                first_obj, last_obj = objs[0], objs[-1]
                print(" {}└ {}".format(column + level_spaces, first_obj.GetName()))
                if first_obj.GetDown(): 
                    print_level_core(first_obj.GetDown(), level_depth + 1)
                
                print(" {}...".format(column + level_spaces))
                
                print(" {}└ {}".format(column + level_spaces, last_obj.GetName()))
                if last_obj.GetDown(): 
                    print_level_core(last_obj.GetDown(), level_depth + 1)
                    
            elif item_type == "sequence_star":
                print(" {}...".format(column + level_spaces))
                
            elif item_type == "single":
                obj = objs[0]
                
                # Запускаем дочерний уровень БЕЗ ПРИНТА заранее, чтобы узнать, есть ли там ошибки!
                # Если дети вернут True — значит внутри этой папки сидит битый кадр!
                child_has_error = False
                if obj.GetDown():
                    # Мы временно перехватываем результат рекурсии
                    child_has_error = print_level_core(obj.GetDown(), level_depth + 1)
                
                if child_has_error:
                    # 1. ТВОЁ ПРАВИЛО: Шапка папки, внутри которой есть поломка, получает '#'
                    print("#{}└ {}".format(column + level_spaces, display_name))
                else:
                    # Обычный целый объект или чистый родитель
                    print(" {}└ {}".format(column + level_spaces, display_name))

                    if obj.GetDown() and not child_has_error:
                        pass # Дети уже напечатаны в логике выше, если они были. 
                             # Чтобы не дублировать вызовы, мы просто вызываем принт дерева, только если child_has_error был False:
                        print_level_core(obj.GetDown(), level_depth + 1)
                    
            elif item_type == "single_broken":
                # 2.  Битый кадр получает '*' перед линией и суффикс
                obj = objs[0]
                display_with_warning = "{} < Warning!".format(obj.GetName())
                print("*{}└ {}".format(column + level_spaces, display_with_warning))
                
                if obj.GetDown():
                    print_level_core(obj.GetDown(), level_depth + 1)
                    
        # Возвращаем наверх статус: были ли поломки на этом этаже
        return level_has_any_broken


    # =====================================================================
    # Start Point
    # =====================================================================
    if not _internal:
        logline(fname())
        print(func_about)
        print( "=== hierarchy log\n")
        
        if op is not None:
            ops = op if isinstance(op, (list, tuple)) else [op]
        else:
            #ops = doc.GetActiveObjects(globals().get('c4d').GETACTIVEOBJECTFLAGS_NONE if globals().get('c4d') else 0)
            flag_none = getattr(c4d, "GETACTIVEOBJECTFLAGS_NONE", 0)
            ops = doc.GetActiveObjects(flag_none)
            if not ops:
                ops = [doc.GetFirstObject()] if doc.GetFirstObject() else []

        for current_op in ops:
            if current_op:
                print(" {}└ {}".format(column, current_op.GetName()))
                if current_op.GetDown():
                    print_level_core(current_op.GetDown(), level_depth=1)
                
                if op is None and not doc.GetActiveObjects(0):
                    next_op = current_op.GetNext()
                    while next_op:
                        print(" {}└ {}".format(column, next_op.GetName()))
                        if next_op.GetDown():
                            print_level_core(next_op.GetDown(), level_depth=1)
                        next_op = next_op.GetNext()

        logline("вот так вот")
        return

    if op is not None:
        print_level_core(op, level_depth=int(indent))


def print_seq_hierarchy_gpt(doc=None, op=None, indent=0, _internal=False):
    func_about = dedent("""\
        Sequence hierarchy merging in logs, marks:
        # - Broken Sequence - logging warnings...
        * - Problem struct
    """)

    # =====================================================================

    logline = globals().get('logline', lambda *a, **kw: None)
    fname = globals().get('fname', lambda: "")

    if not _internal and doc is None:
        case_a = globals().get('doc')
        case_b = globals().get('c4d').documents.GetActiveDocument() if globals().get('c4d') else None
        doc = case_a or case_b
        
    if not doc: print("Error: doc not found"); return



    space = 2    # offset levels (count " ")
    
    # column separator
    col_divider = "|"      
    col_offset = 4
    column = col_divider + (col_offset * " ")

    # =====================================================================
    # Build hierarchy in memory first.
    #
    # This is intentional: Cinema 4D console output is not treated as
    # something that can be "patched" after print().  We first analyze and
    # build the lines, then print them in the final order.
    # =====================================================================
    def build_level_core(start_op, level_depth):
        if not start_op:
            return [], False

        level_spaces = " " * (level_depth * space)

        siblings = []
        curr = start_op
        while curr:
            siblings.append(curr)
            curr = curr.GetNext()

        pattern = re.compile(r'^(.*?)([\-_.\s]?)(?:\.|\b)?(\d+)$')
        groups = defaultdict(list)
        single_objects = []

        # Get objects on current level
        for obj in siblings:
            name = obj.GetName()
            match = pattern.match(name)
            if match:
                base, separator, digits = match.groups()
                groups[(base, separator)].append(
                    (int(digits), obj, len(digits))
                )
            else:
                single_objects.append((name, [obj], "single", ""))

        # Scanning sequences
        level_has_any_broken = False

        for (base, separator), items in groups.items():
            if len(items) > 7:
                items.sort(key=lambda x: x)

                reference_obj = items[0][1]
                reference_signature = get_child_structure_signature(
                    reference_obj
                )
                digits_len = items[0][2]

                analyzed_sequence = []
                has_warnings = False

                for digits, obj, _ in items:
                    current_sig = get_child_structure_signature(obj)
                    is_broken = (current_sig != reference_signature)

                    if is_broken:
                        has_warnings = True
                        level_has_any_broken = True

                    analyzed_sequence.append({
                        "frame_num": digits,
                        "obj": obj,
                        "is_broken": is_broken
                    })

                if not has_warnings:
                    all_objs = [data[1] for data in items]
                    hidden_start = str(items[1][0]).zfill(digits_len)
                    hidden_end = str(items[-2][0]).zfill(digits_len)
                    range_str = "{}-{}".format(
                        hidden_start, hidden_end
                    )
                    single_objects.append(
                        (base, all_objs, "sequence_clean", range_str)
                    )

                else:
                    temp_clean_range = []
                    temp_clean_objs = []

                    for i, node in enumerate(analyzed_sequence):
                        if i == 0 or i == len(analyzed_sequence) - 1:
                            if temp_clean_range:
                                range_str = "{}-{}".format(
                                    temp_clean_range[0],
                                    temp_clean_range[-1]
                                )
                                single_objects.append(
                                    (
                                        "*",
                                        temp_clean_objs,
                                        "sequence_star",
                                        range_str
                                    )
                                )
                                temp_clean_range = []
                                temp_clean_objs = []

                            single_objects.append(
                                (
                                    node["obj"].GetName(),
                                    [node["obj"]],
                                    "single",
                                    ""
                                )
                            )
                            continue

                        if node["is_broken"]:
                            if temp_clean_range:
                                range_str = "{}-{}".format(
                                    temp_clean_range[0],
                                    temp_clean_range[-1]
                                )
                                single_objects.append(
                                    (
                                        "*",
                                        temp_clean_objs,
                                        "sequence_star",
                                        range_str
                                    )
                                )
                                temp_clean_range = []
                                temp_clean_objs = []

                            single_objects.append(
                                (
                                    node["obj"].GetName(),
                                    [node["obj"]],
                                    "single_broken",
                                    ""
                                )
                            )
                        else:
                            formatted_num = str(
                                node["frame_num"]
                            ).zfill(digits_len)
                            temp_clean_range.append(formatted_num)
                            temp_clean_objs.append(node["obj"])

                    if temp_clean_range:
                        range_str = "{}-{}".format(
                            temp_clean_range[0],
                            temp_clean_range[-1]
                        )
                        single_objects.append(
                            (
                                "*",
                                temp_clean_objs,
                                "sequence_star",
                                range_str
                            )
                        )

            else:
                for digits, obj, _ in items:
                    single_objects.append(
                        (obj.GetName(), [obj], "single", "")
                    )

        # Sort by Cinema 4D index
        single_objects.sort(
            key=lambda x: min(siblings.index(o) for o in x[1])
        )

        # Build output lines, but DO NOT print yet.
        lines = []

        for display_name, objs, item_type, range_str in single_objects:

            if item_type == "sequence_clean":
                first_obj, last_obj = objs[0], objs[-1]

                first_children = []
                first_has_error = False
                if first_obj.GetDown():
                    first_children, first_has_error = build_level_core(
                        first_obj.GetDown(),
                        level_depth + 1
                    )

                first_prefix = "#" if first_has_error else " "
                lines.append(
                    "{}{}└ {}".format(
                        first_prefix,
                        column + level_spaces,
                        first_obj.GetName()
                    )
                )
                lines.extend(first_children)
                level_has_any_broken = (
                    level_has_any_broken or first_has_error
                )

                lines.append(
                    " {}...".format(column + level_spaces)
                )

                last_children = []
                last_has_error = False
                if last_obj.GetDown():
                    last_children, last_has_error = build_level_core(
                        last_obj.GetDown(),
                        level_depth + 1
                    )

                last_prefix = "#" if last_has_error else " "
                lines.append(
                    "{}{}└ {}".format(
                        last_prefix,
                        column + level_spaces,
                        last_obj.GetName()
                    )
                )
                lines.extend(last_children)
                level_has_any_broken = (
                    level_has_any_broken or last_has_error
                )

            elif item_type == "sequence_star":
                lines.append(
                    " {}...".format(column + level_spaces)
                )

            elif item_type == "single":
                obj = objs[0]

                child_lines = []
                child_has_error = False
                if obj.GetDown():
                    child_lines, child_has_error = build_level_core(
                        obj.GetDown(),
                        level_depth + 1
                    )

                marker = "#" if child_has_error else " "
                lines.append(
                    "{}{}└ {}".format(
                        marker,
                        column + level_spaces,
                        display_name
                    )
                )
                lines.extend(child_lines)

                level_has_any_broken = (
                    level_has_any_broken or child_has_error
                )

            elif item_type == "single_broken":
                obj = objs[0]
                display_with_warning = "{} < Warning!".format(
                    obj.GetName()
                )

                lines.append(
                    "*{}└ {}".format(
                        column + level_spaces,
                        display_with_warning
                    )
                )

                child_lines = []
                child_has_error = False
                if obj.GetDown():
                    child_lines, child_has_error = build_level_core(
                        obj.GetDown(),
                        level_depth + 1
                    )

                lines.extend(child_lines)

                # This node is broken by definition.  Keep the status true
                # even if its own children happen to be clean.
                level_has_any_broken = True

        return lines, level_has_any_broken

    def build_object_line(obj, level_depth):
        """Build one object header plus its children, without printing."""
        if not obj:
            return [], False

        child_lines = []
        child_has_error = False
        if obj.GetDown():
            child_lines, child_has_error = build_level_core(
                obj.GetDown(),
                level_depth + 1
            )

        marker = "#" if child_has_error else " "
        lines = [
            "{}{}└ {}".format(
                marker,
                column + (" " * (level_depth * space)),
                obj.GetName()
            )
        ]
        lines.extend(child_lines)
        return lines, child_has_error

    # =====================================================================
    # Start Point
    # =====================================================================
    if not _internal:
        logline(fname())
        print(func_about)
        print( "=== hierarchy log\n")

        if op is not None:
            ops = op if isinstance(op, (list, tuple)) else [op]
        else:
            flag_none = getattr(c4d, "GETACTIVEOBJECTFLAGS_NONE", 0)
            ops = doc.GetActiveObjects(flag_none)
            #ops = doc.GetActiveObjects(globals().get('c4d').GETACTIVEOBJECTFLAGS_NONEif globals().get('c4d') else 0)
            if not ops:
                ops = [doc.GetFirstObject()] if doc.GetFirstObject() else []

        for current_op in ops:
            if current_op:
                root_lines, _ = build_object_line(current_op, 0)
                for line in root_lines:
                    print(line)

                if op is None and not doc.GetActiveObjects(0):
                    next_op = current_op.GetNext()
                    while next_op:
                        root_lines, _ = build_object_line(next_op, 0)
                        for line in root_lines:
                            print(line)
                        next_op = next_op.GetNext()

        logline("вот так вот")
        return

    if op is not None:
        lines, _ = build_level_core(op, level_depth=int(indent))
        for line in lines:
            print(line)




"""
C4D экспортируя .abc файл, меняет имена дублирующих объектов без учёта 
их порядка в иерархии и индексов в конце имени. Коллизия имён
у разработчиков вроде решается на уровне движка и указателей памяти C++ 
Так скопированная иерархия из одного проекта в другой будет иметь 
корректные порядковые индексы идущие друг за другом

Данный скрипт отображает иерархию, !только! текущего документа 
и последнего экспорта из него

В теории при переоткрытии проекта, индексы могут смещаться и значит 
последующий экспорт может иметь уже другие значения...
"""

def print_abc_hierarchy(targetDoc=None, debug=False): #r20 Save
    print("abc_hierarchy: r20save")
    import uuid  # Добавляем стандартный модуль Python

    logline = globals().get('logline', lambda *a, **kw: None)
    fname = globals().get('fname', lambda: "")

    # 1. Получаем документ через наш враппер
    doc = getDocWrap(targetDoc=targetDoc, debug=debug)
    if not doc:
        print("abc_hierarchy: No document available.")
        return

    houdini_path = True
    mesh_only = False
    selection_only = True if doc.GetActiveObject() else False

    func_about = dedent("""\
        * read temp .abc and print path attr
        * tempfile generated with \"Selection Only\" option

        When exporting an .abc file, C4D changes the names of duplicate objects without
        considering their order in the hierarchy or the indices at the end of their names.
        Name collisions are resolved at the level of the C++ engine and memory pointers.
        Thus, a hierarchy copied from one project to another will have correct indices
        running sequentially one after another

        Displays below hierarchy based !only! on the current tempfile
        snapshot from this doc
    """)
    mode_about = "Houdini Path View: {}  | Mesh Only Mode: {}".format(houdini_path, mesh_only)


    # 3. Безопасный путь к файлу через UUID
    temp_dir = tempfile.gettempdir()
    temp_name = "c4ds_temp_" + str(uuid.uuid4())[:8]
    temp_name_f = temp_name + ".abc"
    temp_abc_file = os.path.join(temp_dir, temp_name_f)
    
    # 4. Plug Settings
    abc_export_id = 1028082     
    plug = c4d.plugins.FindPlugin(abc_export_id, c4d.PLUGINTYPE_SCENESAVER)

    if not plug: print("abc_hierarchy: Failed"); return
        
    op = {}
    res = plug.Message(c4d.MSG_RETRIEVEPRIVATEDATA, op)
    if res:
        abc_saver = op.get("imexporter") or op.get("op")
        if abc_saver:            
            fps = doc.GetFps()
            current_frame = doc.GetTime().GetFrame(fps)
            # Set params by ID from up dump (R20)
            # params get help check_window_descr()
            abc_saver[1001] = current_frame  # Start Frame
            abc_saver[1002] = current_frame  # End Frame
            abc_saver[1006] = True           # Selection Only
            abc_saver[1019] = False          # Merge All

    if not c4d.documents.SaveDocument(doc, temp_abc_file, c4d.SAVEDOCUMENTFLAGS_DONTADDTORECENTLIST, abc_export_id):
        print("Failed to save temporary Alembic file.")
        return

    abc_doc = c4d.documents.LoadDocument(temp_abc_file, c4d.SCENEFILTER_OBJECTS)
    if not abc_doc:
        print("Cannot read file")
        if os.path.exists(temp_abc_file): os.remove(temp_abc_file)
        return

    first_obj = abc_doc.GetFirstObject()
    
    if first_obj:
        logline(fname())
        print(func_about)
        print(mode_about)
        print("")

        # 4. ИСПРАВЛЕНИЕ ДЛЯ R20: Кэшируем пути по GUID, а не по объектам
        paths_cache = {}

        for obj in walk_hierarchy(first_obj):
            clean_name = obj.GetName().replace(" ", "_").replace(".", "_").replace("-", "_")
            
            # Проверяем родителя по его GUID
            parent = obj.GetUp()
            parent_guid = parent.GetGUID() if parent else None
            
            if parent_guid and parent_guid in paths_cache:
                node_path = paths_cache[parent_guid] + "/" + clean_name
            else:
                node_path = "/" + clean_name
            
            # Записываем текущий путь, используя GUID объекта как хэшируемый ключ
            paths_cache[obj.GetGUID()] = node_path

            is_mesh = not obj.GetDown()
            if is_mesh:
                houdini_path_text = node_path + "/" + clean_name + "Shape"
                final_path = houdini_path_text if houdini_path else node_path
                print(final_path)
            elif not mesh_only:
                print(node_path)
                
        paths_cache.clear()
    else:
        print("File is Empty")

    c4d.documents.KillDocument(abc_doc)
    
    if os.path.exists(temp_abc_file):
        os.remove(temp_abc_file)
        time.sleep(0.1)
        if not os.path.exists(temp_abc_file):
            logline("temp file deleted")
        else:
            print("\nTemp File Not Delete\n{}\n".format(temp_abc_file))
            logline("вот так вот")


def print_abc_preprod_r23_hierarchy(target=None, debug=True):
    logline = globals().get('logline', lambda *a, **kw: None)
    fname = globals().get('fname', lambda: "")

    houdini_path = True
    mesh_only = False
    debug = False

    func_about = dedent("""\
        * read temp .abc and print path attr
        * tempfile generated with \"Selection Only\" option

        When exporting an .abc file, C4D changes the names of duplicate objects without
        considering their order in the hierarchy or the indices at the end of their names.
        Name collisions are resolved at the level of the C++ engine and memory pointers.
        Thus, a hierarchy copied from one project to another will have correct indices
        running sequentially one after another

        Displays below hierarchy based !only! on the current tempfile
        snapshot from this doc
    """)
    mode_about = "Houdini Path View: {}  | Mesh Only Mode: {}".format(houdini_path, mesh_only)

    """
        C4D экспортируя .abc файл, меняет имена дублирующих объектов без учёта их порядка в иерархии 
        и индексов в конце имени. Коллизия имён у разработчиков вроде решается на уровне движка
        и указателей памяти C++. Так скопированная иерархия из одного проекта в другой будет иметь 
        корректные порядковые индексы идущие друг за другом
        Данный скрипт отображает иерархию, !только! текущего документа и последнего экспорта из него
        
        В теории при переоткрытии проекта, индексы могут смещаться и значит последующий экспорт может
        иметь уже другие значения...
    """

    active_obj = doc.GetActiveObject()
    if not active_obj:
        print("abc_hierarchy: Not Select Object")
        return

    temp_dir = tempfile.gettempdir()
    temp_name = "c4ds_temp_" + str(active_obj.GetGUID())
    temp_name_f = temp_name+".abc"
    temp_abc_file = os.path.join(temp_dir, temp_name_f)
    
    abc_export_id = 1028082     
    plug = c4d.plugins.FindPlugin(abc_export_id, c4d.PLUGINTYPE_SCENESAVER)

    if not plug: print("abc_hierarchy: Failed"); return
        
    op = {}
    res = plug.Message(c4d.MSG_RETRIEVEPRIVATEDATA, op)
    if res:
        abc_saver = op.get("imexporter") or op.get("op")
        if abc_saver:            
            fps = doc.GetFps()
            current_frame = doc.GetTime().GetFrame(fps)
            # Set params by ID from up dump (R20)
            abc_saver[1001] = current_frame  # Start Frame
            abc_saver[1002] = current_frame  # End Frame
            abc_saver[1006] = True           # Selection Only
            abc_saver[1019] = False          # Merge All

    if not c4d.documents.SaveDocument(doc, temp_abc_file, c4d.SAVEDOCUMENTFLAGS_DONTADDTORECENTLIST, abc_export_id):
        print("Failed")
        return

    abc_doc = c4d.documents.LoadDocument(temp_abc_file, c4d.SCENEFILTER_OBJECTS)
    if not abc_doc:
        print("Cannot read file")
        if os.path.exists(temp_abc_file): os.remove(temp_abc_file)
        return

    def walk_and_print(obj, current_path=""):
        while obj:
            name = obj.GetName().replace(" ", "_").replace(".", "_").replace("-", "_")
            node_path = current_path+"/"+name
            is_mesh = not obj.GetDown()

            if is_mesh:
                houdini_path_text = node_path+"/"+name+"Shape"
                final_path = houdini_path_text if houdini_path else node_path
                print(final_path)
            elif not mesh_only:
                print(node_path)

            if obj.GetDown():
                walk_and_print(obj.GetDown(), node_path)

            obj = obj.GetNext()

    first_obj = abc_doc.GetFirstObject()
    
    if first_obj:

        logline(fname())

        print(func_about)
        print(mode_about)
        print("")

        walk_and_print(first_obj)

    else:
        print("File is Empty")

    c4d.documents.KillDocument(abc_doc)
    
    if os.path.exists(temp_abc_file):
        os.remove(temp_abc_file)
        time.sleep(0.1)
        if not os.path.exists(temp_abc_file):
            logline("temp file deleted")
        else:
            print("")
            print("Temp File Not Delete")
            print(temp_abc_file)
            print("")
            logline("вот так вот")


# =========

# Все аргументы после * можно передать ТОЛЬКО по имени: func(w=1920)
# Но работает только после третьего питона
def calc_camdata_by_extend(extend, camera=None, w=1280, h=720, s=36):
    #print("debug_func")
    if isinstance(extend, str) and extend.isdigit():
        extend = int(extend)
    elif isinstance(extend, str):
        print("camdata_by_extend: extend value only int")
        return 0

    c = 1 # c = clip values, w=width, h=height, s=sensor_size
    if not camera and (w<=c or h<=c or s<=c or extend<=0):
        print("camdata_by_extend: values need > 0")
        return 0

    if camera:
        pass # logic apply camdata
    
    new_h = h + extend
    new_w = round(new_h * w / h)
    d0 = math.hypot(w, h)
    d1 = math.hypot(new_w, new_h)
    new_s = s * (d1 / d0)

    clip_s=round(new_s, 4)
    resdata=[new_w,new_h,clip_s]

    printOut = True
    if printOut:
        print("calc_camdata_by_extend")
        print("input : [{},{},{}]".format(w,h,s))
        print("extend: {}px".format(extend))
        print("result: {}".format(resdata))

    return new_w, new_h, new_s



# ======= GUI SCIPT DIALOG =============




class CheckerDialog(c4d.gui.GeDialog):
    def __init__(self):
        self.initize = False
        self.debug = False

        self.unique_groups = []
        self.BTN_ID_MAP = {}

    def CreateLayout(self):
        self.SetTitle("Checker")
        init_users_database()
        # Base Window Group [1/2]

        self.GroupBegin(MAIN_ID, c4d.BFH_SCALEFIT, cols=1, rows=0)
        self.GroupSpace(0, 10)
        self.GroupBorderSpace(14, 14, 14, 0) # left top right bot

        # - 1. Combobox for thematic groups
        self.AddComboBox(MAIN_COMBO_ID, c4d.BFH_SCALEFIT, initw=70)

        #self.unique_groups = sorted(list(set(info["group"] for info in FUNCTIONS_MAP.itervalues())))
        self.unique_groups = sorted(list(set(info["group"] for info in get_dict_values(FUNCTIONS_MAP))))

        #--- set "Console Loggers" to first
        default_group = "Console Loggers"
        if default_group in self.unique_groups:
            self.unique_groups.remove(default_group)
            self.unique_groups.insert(0, default_group)

        #--- push content to combobox
        for index, group_name in enumerate(self.unique_groups, start=COMBO_SUB_ID):
            self.AddChild(MAIN_COMBO_ID, index, group_name)

        self.SetLong(MAIN_COMBO_ID, COMBO_SUB_ID) # Set on start

        # - 2. Main Vertical - start 
        self.GroupBegin(MAIN_TOP_GRP_ID, c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT, cols=1, rows=0)

        self.GroupBegin(MAIN_ABT_GRP_ID, c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT, cols=1, rows=0)
        self.GroupEnd()
        self.GroupBegin(MAIN_FNC_GRP_ID,  c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT, cols=3, rows=0)
        self.GroupEnd()

        self.GroupEnd()
        # - 2. Main Vertical - end

        # - 3. Push thematical btns
        if self.unique_groups:
            self._update_interface(self.unique_groups[0])

        self.GroupEnd()


        # Second Window Group [2/2]
        #    Bottom group for out information about main func 
        #    push to boundary top content)

        self.GroupBegin(NULL_ID, c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT, cols=1, rows=0)
        self.GroupSpace(0, 10)
        #self.GroupBorder(c4d.BORDER_ACTIVE_1)
        self.GroupBorderSpace(14, 14, 14, 14)

        self.AddStaticText(DESC_HEADER_ID, c4d.BFH_LEFT, name="Description")
        
        # Group for refill
        self.GroupBegin(DESC_GRP_ID, c4d.BFH_SCALEFIT, cols=1, rows=0)
        self.AddStaticText(NULL_ID, c4d.BFH_LEFT, name="[ ? ] click > return [ ! ]")
        self.GroupEnd()

        self.GroupEnd()

        # pack all IDs func from struct fo fast check in Command Call
        self.BTN_ID_MAP = {}
        #for parent_id, parent_info in FUNCTIONS_MAP.iteritems():
        for parent_id, parent_info in get_dict_items(FUNCTIONS_MAP):
            self.BTN_ID_MAP[parent_id] = parent_info.get("func")
            
            btns_dict = parent_info.get("btns", {})
            #for btn_id, btn_data in btns_dict.iteritems():
            for btn_id, btn_data in get_dict_items(btns_dict):

                #func_name = btn_data.values()[0] if btn_data else None
                func_name = next(iter(btn_data.values())) if btn_data else None
                self.BTN_ID_MAP[btn_id] = func_name


        if self.debug: print("debug", self.BTN_ID_MAP)

        return True



    def _update_interface(self, filter_group_name):

        # 2. update about "combobox groups" text
        self.LayoutFlushGroup(MAIN_ABT_GRP_ID) 
        
        #for grp_id, info in GROUP_MAP.iteritems():  
        for grp_id, info in get_dict_items(GROUP_MAP):
            if info["name"] == filter_group_name:
                
                text = info["desc"]
                self.AddStaticText(NULL_ID, c4d.BFH_SCALEFIT, name=text, inith=20)                
                

        self.LayoutChanged(MAIN_ABT_GRP_ID)

        # 2. update scripts content
        hor = 6    # space between [ ? | MAIN | INPUTS ]
        ver = 4    # space between row lines
        hs  = 18   # default height button \ row line
        btw = 140  # default width  button 

        self.LayoutFlushGroup(MAIN_FNC_GRP_ID) 

        #for btn_id, info in sorted(FUNCTIONS_MAP.iteritems(), key=lambda x: x[0]):
        for btn_id, info in sorted(get_dict_items(FUNCTIONS_MAP), key=lambda x: x[0]):
            if info["group"] == filter_group_name:
                
                # 0 column = about
                quest_id = btn_id + INPUT_QST_ID_OFFSET
                self.AddButton(quest_id, c4d.BFV_TOP, initw=20, inith=hs, name="?")

                # 1 column = main func
                self.AddButton(btn_id, c4d.BFV_TOP, initw=btw, inith=hs, name=info["label"])

                # 2 colum = settings
                input_val = info.get("input", False)

                if input_val:
                    input_type = ""

                    if isinstance(input_val, (tuple, list)):
                        input_type = input_val[0] # example ("string", "alembic"))
                    else:
                        input_type = input_val 

                    
                    if input_type == "string" or input_type == "web":

                        if input_type == "string": # horizont
                            input_id = btn_id + INPUT_STR_ID_OFFSET
                            self.AddEditText(input_id, c4d.BFH_SCALEFIT | c4d.BFV_CENTER, inith=hs-4)
                            if isinstance(input_val, (tuple, list)) and len(input_val) > 1:
                                self.SetString(input_id, input_val[1])

                        elif input_type == "web": 

                            total_authors = len(USER_INIT)
                            self.GroupBegin(NULL_ID, c4d.BFH_SCALEFIT, cols=1, rows=0)

                            self.GroupBegin(NULL_ID, c4d.BFH_SCALEFIT, cols=2, rows=1)

                            # name paste
                            input_id = btn_id + INPUT_STR_ID_OFFSET
                            self.AddEditText(input_id, c4d.BFH_LEFT, initw=100, inith=hs-4)                                

                            # link paste
                            self.AddEditText(333, c4d.BFH_SCALEFIT, inith=hs-4)

                            rule = isinstance(input_val, (tuple, list)) and len(input_val) > 1
                            if rule:
                                self.SetString(input_id, input_val[1])
                                self.SetString(333, input_val[2])

                            self.GroupEnd()

                            # Static Space between lines
                            self.AddStaticText(NULL_ID, c4d.BFH_SCALEFIT | c4d.BFV_CENTER, inith=hs-4) 

                            self.GroupBegin(NULL_ID, c4d.BFH_SCALEFIT, cols=4, rows=total_authors)
                            self.GroupSpace(4, 12) 
                            
                            # Cascade:
                            # 1. x[1].get("type") == "github" -> separate two groups:


                            # Cascade:
                            leader_pair = next(((k, v) for k, v in get_dict_items(USER_INIT) if int(k) == 2000), None)
                            others = [(k, v) for k, v in get_dict_items(USER_INIT) if int(k) != 2000]
                            
                            def get_sort_key(item):
                                a_id = item[0]
                                a_data = item[1]
                                
                                # 1. Проверяем тип (GitHub выше обычных сайтов, хотя у тебя сейчас все github)
                                is_github = 1 if a_data.get("type") == "github" else 0
                                raw_date = a_data.get("lastdate", "?")
                                if raw_date == "?":
                                    sort_date = "0000:00:00"
                                    has_date = 0
                                else:
                                    sort_date = raw_date
                                    has_date = 1
                                
                                sort_id = int(a_id) if has_date == 1 else -int(a_id)
                                
                                return (is_github, has_date, sort_date, sort_id)

                            # Сортируем с разворотом (от большего к меньшему)
                            sorted_others = sorted(others, key=get_sort_key, reverse=True)
                            
                            sorted_authors = []
                            if leader_pair: 
                                sorted_authors.append(leader_pair)
                            sorted_authors.extend(sorted_others)

                            for display_idx, (a_id, a_data) in enumerate(sorted_authors):
                                author_name = a_data["name"].upper()
                                position = str(display_idx)
                                safe = "    "
                                int_author_id = int(a_id)
                                
                                total_authors = len(USER_INIT)
                                name_btn_id  = int_author_id + (0 * total_authors)
                                pos_text_id  = int_author_id + (1 * total_authors)
                                date_text_id = int_author_id + (2 * total_authors)
                                check_btn_id = int_author_id + (3 * total_authors)

                                self.BTN_ID_MAP[name_btn_id]  = "open_web"
                                self.BTN_ID_MAP[check_btn_id] = "check_user_update"
                                if "btns" not in FUNCTIONS_MAP[btn_id]:
                                    FUNCTIONS_MAP[btn_id]["btns"] = {}
                                FUNCTIONS_MAP[btn_id]["btns"][name_btn_id]  = "open_web"
                                FUNCTIONS_MAP[btn_id]["btns"][check_btn_id] = "check_user_update"
                                
                                if int_author_id == 2000:
                                    clean_date = get_sys_date_string("%Y:%m:%d")
                                else:
                                    ui_status = a_data.get("ui_status")

                                    if ui_status in ["updated!", "net not sup","Not updated.."]:
                                        clean_date = ui_status
                                    else:
                                        raw_date = a_data.get("lastdate", "?")
                                        if "T" in raw_date:
                                            clean_date = raw_date.split('T')[0].replace('-', ':')
                                        else:
                                            clean_date = raw_date if raw_date else "?"


                                # Create Elems (0, 1, 2, 3)
                                self.AddStaticText(pos_text_id, c4d.BFH_LEFT | c4d.BFV_CENTER, inith=hs-2, name=position+"_  ")
                                self.AddButton(name_btn_id, c4d.BFV_CENTER, initw=btw, inith=hs-2, name=author_name) 
                                self.AddStaticText(date_text_id, c4d.BFH_SCALEFIT | c4d.BFV_CENTER, name=safe + "update: " + clean_date + safe)
                                self.AddButton(check_btn_id, c4d.BFV_CENTER, initw=80, inith=hs-2, name="Check")
                                #print("debug",name_btn_id,  pos_text_id, date_text_id,check_btn_id)

                            #print("after all", FUNCTIONS_MAP)

                            self.GroupEnd()
                            self.GroupEnd() 

                    

                    elif input_val == "btns":
                        btns_dict = info.get("btns", {})
                        total = len(btns_dict)
                        #sorted_btns = sorted(btns_dict.iteritems(), key=lambda x: x)
                        sorted_btns = sorted(get_dict_items(btns_dict), key=lambda x: x)

                        self.GroupBegin(NULL_ID, c4d.BFH_SCALEFIT, cols=total, rows=1)

                        for sub_btn_id, btn_data in sorted_btns:
                            #btn_label, btn_func = btn_data.items()[0] #python 2
                            btn_label, btn_func = next(iter(btn_data.items()))
                            self.AddButton(sub_btn_id, c4d.BFH_CENTER, initw=80, inith=hs, name=btn_label)

                        self.GroupEnd()

                    elif input_type == "values":
                        values_data = info.get("values", {})
                        layout_style = input_val[1] if len(input_val) > 1 else "row"
                        elem_width = int(input_val[2]) if len(input_val) > 2 else 80

                        if layout_style == "row":
                            labels_dict = values_data.get("row_labels", {})
                            inputs_dict = values_data.get("row_inputs", {})
                            
                            #sorted_labels = sorted(labels_dict.iteritems(), key=lambda x: x[0])
                            #sorted_inputs = sorted(inputs_dict.iteritems(), key=lambda x: x[0])
                            sorted_labels = sorted(get_dict_items(labels_dict), key=lambda x: x[0])
                            sorted_inputs = sorted(get_dict_items(inputs_dict), key=lambda x: x[0])
                            
                            cols_count = len(sorted_labels)
                            
                            # Create One table:
                            self.GroupBegin(NULL_ID, c4d.BFH_LEFT, cols=cols_count, rows=2)
                            self.GroupSpace(hor, ver) 

                            # --- 1: Filled first line---
                            for element_id, element_data in sorted_labels:
                                if element_data[0] == "AddStaticText":
                                    self.AddStaticText(element_id, c4d.BFH_SCALEFIT, name=element_data[1], borderstyle=0, initw=elem_width, inith=hs)
                            
                            # --- 2: Filled second line ---
                            for element_id, element_data in sorted_inputs:
                                if element_data[0] == "AddEditNumber":
                                    self.AddEditNumber(element_id, c4d.BFH_SCALEFIT, initw=elem_width, inith=hs)
                                    
                                    element_val = element_data[1]
                                    if isinstance(element_val, float):
                                        self.SetFloat(element_id, float(element_val))
                                    else:
                                        self.SetInt32(element_id, int(element_val))

                            self.GroupEnd() 

                else:
                    # заглушка 
                    self.AddStaticText(NULL_ID, c4d.BFH_SCALEFIT, name="", borderstyle=0, initw=0, inith=hs)


        self.LayoutChanged(MAIN_FNC_GRP_ID)


    def Command(self, id, msg):

        # == listen combobox click
        
        if id == MAIN_COMBO_ID:
            selected_id = self.GetLong(MAIN_COMBO_ID)
            group_index = selected_id - COMBO_SUB_ID

            if 0 <= group_index < len(self.unique_groups):
                target_group_name = self.unique_groups[group_index]
                self._update_interface(target_group_name)

            self.LayoutFlushGroup(DESC_GRP_ID)
            self.AddStaticText(NULL_ID, c4d.BFH_SCALEFIT, name="[ ? ] click > return [ ! ]")
            self.LayoutChanged(DESC_GRP_ID)

            print("============= swap scroll ==============") # just smile scroll

            return True

        if INPUT_QST_ID_OFFSET <= id < INPUT_STR_ID_OFFSET:
            parent_id = id - INPUT_QST_ID_OFFSET
            if parent_id in FUNCTIONS_MAP:
                
                desc_text = FUNCTIONS_MAP[parent_id].get("desc", "No description available.")

                self.LayoutFlushGroup(DESC_GRP_ID)
                for line in desc_text.split('\n'):
                    self.AddStaticText(0, c4d.BFH_SCALEFIT, name=line)
                
                self.LayoutChanged(DESC_GRP_ID)

                return True


        # == listen buttons

        #print("dddd", id)
        if id in self.BTN_ID_MAP:

            func_name = self.BTN_ID_MAP[id]
            is_sub_btn = id not in FUNCTIONS_MAP 

            # if not web
            if is_sub_btn: # Search Parents
                #parent_id = next(pid for pid, pinfo in FUNCTIONS_MAP.iteritems() if id in pinfo.get("btns", {}))
                parent_id = next(pid for pid, pinfo in get_dict_items(FUNCTIONS_MAP) if id in pinfo.get("btns", {}))
                info = FUNCTIONS_MAP[parent_id]
            else:
                info = FUNCTIONS_MAP[id]


            if func_name is not None:
                func_to_run = globals().get(func_name, None)

                if func_to_run:
                    group = info.get("group", None)
                    input_type = info.get("input", False)
                    #if self.debug: print("press",input_type)
                    
                    firstConsole =  False if group == "Breaking News" else True  
                    callConsole = True if group == "Console Loggers" else False

                    if not self.initize and firstConsole:
                        call_window(12305) # call Console
                        c4d.CallCommand(13957) # Clear Console
                        self.initize =True
                        if self.debug: print("Command: first press", self.initize)


                    if input_type:
                        if input_type == "string" or (isinstance(input_type, (tuple, list)) and input_type[0] == "string"):
                            user_text = self.GetString(id + INPUT_STR_ID_OFFSET)

                            func_to_run(user_text)

                        elif input_type == "web" or (isinstance(input_type, (tuple, list)) and input_type[0] == "web"):
                            
                            if id == 1042: # case append
                                username = self.GetString(id + INPUT_STR_ID_OFFSET).lower()
                                weblink = self.GetString(333)
                                print("t", username, weblink) 
                                if func_to_run(username, weblink):
                                    self._update_interface("Breaking News")
                            
                            else: # other func btn
                                
                                safe = "    "
                                total_authors = len(USER_INIT)
                                start_id = 2000

                                # Case 1: Click on Name [2000 ... 2003)
                                if id >= start_id and id < start_id + total_authors:
                                    print("turn name", id) 
                                    real_author_id = id
                                    
                                    # HARD FIX R20
                                    if real_author_id not in USER_INIT and str(real_author_id) in USER_INIT:
                                        real_author_id = str(real_author_id)
                                        
                                    weblink = USER_INIT[real_author_id]["link"]
                                    
                                    # Вызываем твою именную обертку открытия браузера
                                    func_to_run(weblink)
                                    return True

                                # Case 2: Click on Check [2009, 2010, 2011]

                                if id >= (start_id + (3 * total_authors)):
                                    target_text_id = id - total_authors
                                    real_author_id = id - (3 * total_authors)
                                    
                                    self.SetString(target_text_id, safe + "update: Checking..." + safe)
                                    
                                    if real_author_id not in USER_INIT and str(real_author_id) in USER_INIT:
                                        real_author_id = str(real_author_id)

                                    author_info = USER_INIT.get(real_author_id, {})
                                    is_github = author_info.get("type") == "github"

                                    # --- github update ---
                                    if is_github:
                                        last_check = author_info.get("checkdate", "never")
                                        today_date = get_sys_date_string("%Y:%m:%d")

                                        if last_check == today_date:
                                            print("Not updated..")
                                            USER_INIT[real_author_id]["ui_status"] = "Not updated.."
                                            self._update_interface("Breaking News")
                                            return True

                                        if func_to_run(real_author_id):
                                            USER_INIT[real_author_id]["ui_status"] = "updated!"
                                            self._update_interface("Breaking News")
                                        else:
                                            self.SetString(target_text_id, safe + "update: Offline" + safe)


                                    # --- web update ---
                                    else:
                                        USER_INIT[real_author_id]["ui_status"] = "net not sup"
                                        self._update_interface("Breaking News")

                                    print("turn check", id, "Target text field:", target_text_id) 
                                    return True


                                return False


                        elif input_type == "values" or (isinstance(input_type, (tuple, list)) and input_type[0] == "values"):

                            values_data = info.get("values", {})
                            inputs_dict = values_data.get("row_inputs", {})
                            kwargs = {}
                            
                            #for element_id, element_data in inputs_dict.iteritems():
                            for element_id, element_data in get_dict_items(inputs_dict):
                                if element_data[0] == "AddEditNumber":
                                    arg_name = element_data[2] # args func ('s', 'w', 'h', 'extend')
                                    element_val = element_data[1]
                                    
                                    if isinstance(element_val, float):
                                        kwargs[arg_name] = self.GetFloat(element_id)
                                    else:
                                        kwargs[arg_name] = self.GetInt32(element_id)


                            func_to_run(**kwargs)
                            

                        elif input_type == "btns":
                            if not is_sub_btn:
                                if self.debug: print("MAIN_FUNC")
                                func_to_run()
                            else:
                                if self.debug: print("SUB_FUNC")
                                func_to_run()
                    else:

                        func_to_run()

                    if callConsole:
                        call_window(12305)

                else:
                    print("Error: func {} not found!".format(func_name))
            else:
                print("Warning: FUNCTIONS_MAP, on ID {} not set 'func'!".format(id))

            return True

        if self.debug: print("OUT CLICK!")
        return True




def main():
    global PANEL
    PANEL = CheckerDialog()
    PANEL.Open(dlgtype=c4d.DLG_TYPE_ASYNC, defaultw=400, defaulth=280)


if __name__=='__main__':
    main()