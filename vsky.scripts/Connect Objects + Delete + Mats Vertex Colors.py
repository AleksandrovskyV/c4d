import c4d

def main():
    active_obj = doc.GetActiveObject()
    if not active_obj:
        return

    # Системная команда "Connect Objects + Delete"
    doc.StartUndo()
    c4d.CallCommand(12144)
    doc.EndUndo()

    obj = doc.GetActiveObject()
    if not obj or not obj.CheckType(c4d.Opolygon):
        c4d.gui.MessageDialog("Не удалось преобразовать объект в полигональный меш!")
        return

    all_tags = obj.GetTags()
    polyCount = obj.GetPolygonCount()

    # 1. Собираем теги выделения полигонов
    selection_dict = {}
    for tag in all_tags:
        if tag.CheckType(c4d.Tpolygonselection):
            sel_name = tag.GetName()
            base_select = tag.GetBaseSelect()
            poly_ids = [i for i in range(polyCount) if base_select.IsSelected(i)]
            selection_dict[sel_name] = poly_ids

    # 2. Создаем базовые массивы СРАЗУ в формате Vector4d (RGBA)
    default_color = c4d.Vector4d(0.8, 0.8, 0.8, 1.0)
    default_lum = c4d.Vector4d(0.0, 0.0, 0.0, 1.0)

    target_colors = [default_color] * polyCount
    target_luminance = [default_lum] * polyCount

    for tag in all_tags:
        if tag.CheckType(c4d.Ttexture):
            mat = tag[c4d.TEXTURETAG_MATERIAL]
            if not mat:
                continue

            col_v3 = mat[c4d.MATERIAL_COLOR_COLOR] if mat[c4d.MATERIAL_USE_COLOR] else c4d.Vector(0.8)
            col_v4 = c4d.Vector4d(col_v3, 1.0)

            if mat[c4d.MATERIAL_USE_LUMINANCE]:
                lum_color = mat[c4d.MATERIAL_LUMINANCE_COLOR]
                lum_brightness = mat[c4d.MATERIAL_LUMINANCE_BRIGHTNESS]
                lum_v4 = c4d.Vector4d(lum_color * lum_brightness, 1.0)
            else:
                lum_v4 = default_lum

            restrict_selection = tag[c4d.TEXTURETAG_RESTRICTION]
            target_polys = range(polyCount)
            if restrict_selection and restrict_selection in selection_dict:
                target_polys = selection_dict[restrict_selection]

            for poly_id in target_polys:
                target_colors[poly_id] = col_v4
                target_luminance[poly_id] = lum_v4



    # 1. Создаем тег прямо на объекте
    vcolor_tag = obj.MakeTag(c4d.Tvertexcolor)
    vlum_tag = obj.MakeTag(c4d.Tvertexcolor)

    if not vcolor_tag:
        return

    vcolor_tag.SetName("mat_color")
    vcolor_tag.SetPerPointMode(False)

    vlum_tag.SetName("mat_luminance")
    vlum_tag.SetPerPointMode(False)

    data_color = vcolor_tag.GetDataAddressW()
    data_lum = vlum_tag.GetDataAddressW()

    for idx in range(polyCount):
        col = target_colors[idx]
        lum = target_luminance[idx]

        poly_color = {"a": col, "b": col, "c": col, "d": col}
        poly_lum = {"a": lum, "b": lum, "c": lum, "d": lum}

        c4d.VertexColorTag.SetPolygon(data_color, idx, poly_color)
        c4d.VertexColorTag.SetPolygon(data_lum, idx, poly_lum)

    c4d.EventAdd()
    print(f"Bake Complete. Успешно запечено полигонов: {polyCount}")

if __name__ == '__main__':
    main()