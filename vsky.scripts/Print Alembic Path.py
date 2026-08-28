import c4d
from c4d.modules import mograph


SHAPE_ONLY = True 

# Глобальный плоский список для учета занятых базовых имен во всей сцене
global_alembic_registry = set()

def clean_alembic_name(name):
    """Очищает имя объекта по правилам Alembic."""
    clean = name.replace(" ", "_").replace(".", "_").replace("-", "_")
    return clean

def get_global_unique_name(raw_name):
    """
    Эмулирует глобальный реестр коллизий Alembic при обходе снизу вверх.
    """
    base_name = clean_alembic_name(raw_name)
    
    if base_name not in global_alembic_registry:
        global_alembic_registry.add(base_name)
        return base_name
    else:
        suffix = 1
        new_name = f"{base_name}_{suffix}"
        while new_name in global_alembic_registry:
            suffix += 1
            new_name = f"{base_name}_{suffix}"
        global_alembic_registry.add(new_name)
        return new_name

def parse_scene_bottom_up(obj, current_path):
    """
    Честный обход сцены снизу вверх (Post-order).
    Жестко изолирует внутренности Extrude и вешает Shape на все конечные меши.
    """
    while obj:
        # Фильтр деформационного мусора после ExecutePasses
        if obj.GetDocument() != doc:
            obj = obj.GetNext()
            continue

        is_instance = obj.CheckType(c4d.Oinstance)
        is_cloner = obj.GetType() == 1018544
        is_polygon = obj.CheckType(c4d.Opolygon) or obj.GetRealType() == c4d.Opolygon
        
        is_extrude_or_generator = (
            obj.CheckType(c4d.Oextrude) or 
            obj.CheckType(c4d.Osweep) or 
            obj.CheckType(c4d.Olathe) or 
            obj.CheckType(c4d.Oloft)
        )

        has_no_children = obj.GetDown() == None

        # 1. СНАЧАЛА ИДЕМ НА САМОЕ ДНО ИЕРАРХИИ
        if not is_polygon and not is_instance and not is_cloner and not is_extrude_or_generator and not has_no_children:
            if obj.GetDown(): 
                parse_scene_bottom_up(obj.GetDown(), current_path)

        # Правило "снизу вверх": дочерние объекты клонера первыми забивают базовые имена
        if is_cloner:
            children = obj.GetChildren()
            if children:
                for child in children:
                    get_global_unique_name(child.GetName())

        # 2. ТЕПЕРЬ ОБРАБАТЫВАЕМ ТЕКУЩИЙ ОБЪЕКТ ПРИ ПОДЪЕМЕ
        unique_name = get_global_unique_name(obj.GetName())
        node_path = f"{current_path}/{unique_name}"

        if is_cloner:
            if not SHAPE_ONLY:
                print(f"[Clone]  {obj.GetName():<25} | {node_path}")
            
            children = obj.GetChildren()
            md = mograph.GeGetMoData(obj)
            
            if children and md:
                clone_count = md.GetCount()
                for i in range(clone_count):
                    for child in children:
                        child_clean_name = clean_alembic_name(child.GetName())
                        clone_node_name = f"{child_clean_name}_{i}"
                        child_path = f"{current_path}/{unique_name}/{clone_node_name}"
                        
                        if not SHAPE_ONLY:
                            # Безопасно формируем имя для колонки
                            mesh_display_name = f"[Cloner Object]:{i}"
                            print(f"[Mesh]   {mesh_display_name:<25} | {child_path}")
                        
                        # Безопасно формируем имя для колонки
                        shape_display_name = f"[Cloner Shape]:{i}"
                        print(f"[Shape]  {shape_display_name:<25} | {child_path}/{child_clean_name}Shape")


        # ЖЕЛЕЗНЫЙ КРИТЕРИЙ ГЕОМЕТРИИ ДЛЯ ALEMBIC
        elif is_polygon or is_instance or is_extrude_or_generator or has_no_children:
            if not SHAPE_ONLY:
                print(f"[Mesh]   {obj.GetName():<25} | {node_path}")
            
            # Shape-поджопник выводится всегда
            print(f"[Shape]  {obj.GetName() + 'Shape':<25} | {node_path}/{unique_name}Shape")
        else:
            if not SHAPE_ONLY:
                print(f"[Null]   {obj.GetName():<25} | {node_path}")

        # 3. ПЕРЕХОДИМ К СОСЕДЯМ НА ТЕКУЩЕМ УРОВНЕ
        obj = obj.GetNext()

def main():
    global global_alembic_registry
    global_alembic_registry.clear()
    
    c4d.CallCommand(12305) # Открываем консоль C4D
    
    active_obj = doc.GetActiveObject()
    if not active_obj:
        print("SelectRoot!")
        return

    print("\n" + "="*100)
    print(f"Alembic Hierarchy Path | ShapeOnly: {SHAPE_ONLY}\n")
    print("Extrude, Sweep, Lather, Loft objects print without subgroup path")
    print("\n")
    print(f"{'TYPE':<9} {'SOURCE NAME':<25} | {'ALEMBIC GEOMETRY PATH'}")
    print("="*100)

    doc.ExecutePasses(None, True, True, True, c4d.BUILDFLAGS_INTERNALRENDERER)

    root_name = clean_alembic_name(active_obj.GetName())
    root_path = f"/{root_name}"
    

    is_root_generator = (
        active_obj.CheckType(c4d.Oextrude) or 
        active_obj.CheckType(c4d.Osweep) or 
        active_obj.CheckType(c4d.Olathe) or 
        active_obj.CheckType(c4d.Oloft)
    )

    # Если у объекта есть дети и это НЕ генератор — идем вниз по вашей логике
    if active_obj.GetDown() and not is_root_generator:
        if not SHAPE_ONLY:
            print(f"[Root]   {active_obj.GetName():<25} | {root_path}")

        parse_scene_bottom_up(active_obj.GetDown(), root_path)
    
    elif is_root_generator:
        unique_name = get_global_unique_name(active_obj.GetName())
        print(f"[Shape]  {active_obj.GetName() + 'Shape':<25} | {root_path}/{unique_name}Shape")



if __name__ == '__main__':
    main()