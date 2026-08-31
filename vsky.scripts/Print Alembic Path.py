"""
Print Alembic Paths

Author: Viktor Aleksandrovsky & Google AI
Written & Tested for Maxon Cinema 4D R23
"""

import os, c4d, tempfile

HOUDINI_PATH = True
MESH_ONLY = False

def main():
    active_obj = doc.GetActiveObject()
    if not active_obj:
        print("Not Select Object")
        return

    temp_dir = tempfile.gettempdir()
    temp_name = "c4ds_temp_" + str(active_obj.GetGUID())
    temp_abc_file = os.path.join(temp_dir, f"{temp_name}.abc")
    
    abc_export_id = 1028082     
    plug = c4d.plugins.FindPlugin(abc_export_id, c4d.PLUGINTYPE_SCENESAVER)
    if not plug:
        print("Failed")
        return
        
    op = {}
    if plug.Message(c4d.MSG_RETRIEVEPRIVATEDATA, op):
        abc_saver = op.get("exporter") or op.get("op")
        if abc_saver:
            abc_saver[c4d.ABCEXPORT_SELECTIONONLY] = True

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
            node_path = f"{current_path}/{name}"
            is_mesh = not obj.GetDown()

            if is_mesh:
                final_path = f"{node_path}/{name}Shape" if HOUDINI_PATH else node_path
                print(f"{final_path}")
            elif not MESH_ONLY:
                print(f"{node_path}")

            if obj.GetDown():
                walk_and_print(obj.GetDown(), node_path)

            obj = obj.GetNext()

    first_obj = abc_doc.GetFirstObject()
    if first_obj:
        print(
            f"======== Print Alemic Path ======================================================\n\n"
            f" * read temp .abc and print path attr\n"
            f" * tempfile generated with \"Selection Only\" option\n\n"
            f" When exporting an .abc file, C4D changes the names of duplicate objects without\n"
            f" considering their order in the hierarchy or the indices at the end of their names.\n"
            f" Name collisions are resolved at the level of the C++ engine and memory pointers.\n"
            f" Thus, a hierarchy copied from one project to another will have correct indices\n"
            f" running sequentially one after another\n\n"
            f" Displays below hierarchy based !only! on the current tempfile\n"
            f" snapshot from this doc\n\n"
            f" Houdini Path View: {HOUDINI_PATH}  | Mesh Only Mode: {MESH_ONLY}\n\n"
            f"=========================================\n"
        )

        """
            C4D экспортируя .abc файл, меняет имена дублирующих объектов без учёта их порядка в иерархии 
            и индексов в конце имени. Коллизия имён у разработчиков вроде решается на уровне движка
            и указателей памяти C++. Так скопированная иерархия из одного проекта в другой будет иметь 
            корректные порядковые индексы идущие друг за другом
            Данный скрипт отображает иерархию, !только! текущего документа и последнего экспорта из него
            
            В теории при переоткрытии проекта, индексы могут смещаться и значит последующий экспорт может
            иметь уже другие значения...
        """

        walk_and_print(first_obj)
    else:
        print("File is Empty")

    c4d.documents.KillDocument(abc_doc)
    
    if os.path.exists(temp_abc_file):
        os.remove(temp_abc_file)
        print(
            f"\n\n========= temp file deleted ====================================================\n"
        )

if __name__ == '__main__':
    main()
