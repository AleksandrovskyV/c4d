"""
Convert Object Color to Vertex Color

Author: Viktor Aleksandrovsky & Google
Written & Tested for Maxon Cinema 4D R23
"""

import c4d

def main():
    active_objects = doc.GetActiveObjects(c4d.GETACTIVEOBJECTFLAGS_NONE)

    if not active_objects:
        c4d.gui.MessageDialog("Please select at least one object!")
        return

    success_count = 0
    skipped_objects = []

    doc.StartUndo()

    for obj in active_objects:
        if not isinstance(obj, c4d.PolygonObject):
            skipped_objects.append(obj.GetName())
            continue

        point_count = obj.GetPointCount()
        if point_count == 0:
            print(f"Skipped: '{obj.GetName()}' has no vertices to create a map.")
            continue

        color_vector = obj[c4d.ID_BASEOBJECT_COLOR]

        vc_tag = c4d.VertexColorTag(point_count)
        if vc_tag is None:
            print(f"Error: Failed to create a tag for '{obj.GetName()}'.")
            continue

        data_handle = vc_tag.GetDataAddressW()
        
        for i in range(point_count):
            c4d.VertexColorTag.SetColor(data_handle, None, None, i, color_vector)

        obj.InsertTag(vc_tag)
        doc.AddUndo(c4d.UNDOTYPE_NEW, vc_tag)
        obj.Message(c4d.MSG_UPDATE)

        success_count += 1
        print(f"Successfully created Vertex Color Tag for '{obj.GetName()}'.")

    doc.EndUndo()

    if success_count > 0:
        c4d.EventAdd()
        print(f">> Script completed. Processed objects: {success_count}.")

    if skipped_objects:
        total_skipped = len(skipped_objects)
        
        if total_skipped > 4:
            visible_skipped = skipped_objects[:4]
            skipped_str = "\n- ".join(visible_skipped)
            remaining_count = total_skipped - 4
            skipped_str += f"\n- ... and {remaining_count} more object(s)"
        else:
            skipped_str = "\n- ".join(skipped_objects)

        c4d.gui.MessageDialog(
            f"Process finished with warnings.\n\n"
            f"The following objects were skipped because they are not editable meshes:\n"
            f"- {skipped_str}\n\n"
            f"Please convert them to Editable (press 'C') and try again."
        )

if __name__ == '__main__':
    main()
