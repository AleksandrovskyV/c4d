"""
Swap Mats

Author: Viktor Aleksandrovsky & Google
Written & Tested for Maxon Cinema 4D R23
"""

import c4d

def find_target_texture_tag(obj):
    tags = obj.GetTags()
    texture_tags = [t for t in tags if t.CheckType(c4d.Ttexture)]

    if texture_tags:
        return texture_tags[-1]

    children = obj.GetChildren()
    for child in children:
        found_tag = find_target_texture_tag(child)
        if found_tag:
            return found_tag

    return None

def main():
    doc = c4d.documents.GetActiveDocument()

    selected_tags = doc.GetActiveTags()
    texture_tags = [tag for tag in selected_tags if tag.CheckType(c4d.Ttexture)]

    tag_a = None
    tag_b = None

    if len(texture_tags) == 2:
        tag_a = texture_tags[0]
        tag_b = texture_tags[1]
        print("[Swap Mats] Mode 1: Swapping by two selected tags.")
    else:
        selected_objects = doc.GetActiveObjects(c4d.GETACTIVEOBJECTFLAGS_NONE)

        if len(selected_objects) == 2:
            obj_a = selected_objects[0]
            obj_b = selected_objects[1]

            tag_a = find_target_texture_tag(obj_a)
            tag_b = find_target_texture_tag(obj_b)

            if not tag_a or not tag_b:
                missing = []
                if not tag_a: missing.append(obj_a.GetName())
                if not tag_b: missing.append(obj_b.GetName())
                c4d.gui.MessageDialog(f"[Swap Mats] - Error 1!")
                return

            print(f"[Swap Mats] Mode 2: Swapping by objects")
        else:
            return

    mat_a = tag_a[c4d.TEXTURETAG_MATERIAL]
    mat_b = tag_b[c4d.TEXTURETAG_MATERIAL]

    if not mat_a or not mat_b:
        c4d.gui.MessageDialog("[Swap Mats] - Error 2")
        return


    doc.StartUndo()
    doc.AddUndo(c4d.UNDOTYPE_CHANGE, tag_a)
    doc.AddUndo(c4d.UNDOTYPE_CHANGE, tag_b)
    tag_a[c4d.TEXTURETAG_MATERIAL] = mat_b
    tag_b[c4d.TEXTURETAG_MATERIAL] = mat_a
    doc.EndUndo()
    c4d.EventAdd()

    print(f"[Swap Mats] complete")

if __name__=='__main__':
    main()