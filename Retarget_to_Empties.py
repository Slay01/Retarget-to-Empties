bl_info = {
    "name": "Retarget to Empties",
    "author": "Slay",
    "version": (1, 0, 0),
    "blender": (5, 0, 0),
    "location": "View3D > N Sidebar > Retarget",
    "description": "Bi-directional IK retargeting via Empties to isolate movement channels, clean curves for NLA blending, and extract clean Root Motion for game engines.",
    "category": "Animation",
}

import bpy
from bpy.props import StringProperty, BoolProperty
from bpy.types import PropertyGroup, Panel, Operator


# ──────────────────────────────────────────────
# 1. CONFIGURACIÓN DE SLOTS
# ──────────────────────────────────────────────
# True  = conserva Location + Rotation (manos, pies y torso).
# False = elimina únicamente Location (articulaciones).
SLOTS_CONFIG = [
    ("left_hand",    "Left Hand",    True),
    ("right_hand",   "Right Hand",   True),
    ("left_foot",    "Left Foot",    True),
    ("right_foot",   "Right Foot",   True),
    ("torso",        "Torso",        True),
    ("chest",        "Chest",        False),
    ("head",         "Head",         False),
    ("left_elbow",   "Left Elbow",   False),
    ("right_elbow",  "Right Elbow",  False),
    ("left_knee",    "Left Knee",    False),
    ("right_knee",   "Right Knee",   False),
]

OWNER_PROP = "_retarget_owner_armature"
SLOT_PROP = "_retarget_slot"


# ──────────────────────────────────────────────
# 2. PROPERTY GROUP Y PROPIEDADES DE ESCENA
# ──────────────────────────────────────────────
class RETargetSlot(PropertyGroup):
    bone_name: StringProperty(
        name="Bone",
        description="Nombre del hueso asignado a este slot",
        default="",
    )
    empty_name: StringProperty(
        name="Empty Name",
        description="Empty asociado exclusivamente a este slot",
        default="",
    )
    created: BoolProperty(name="Created", default=False)
    expanded: BoolProperty(
        name="Expanded",
        description="Mostrar/Ocultar sección",
        default=False,
    )


def poll_armature(self, obj):
    return obj is not None and obj.type == 'ARMATURE'


def register_scene_props():
    scene = bpy.types.Scene

    for key, _, _ in SLOTS_CONFIG:
        setattr(
            scene,
            f"retarget_{key}",
            bpy.props.PointerProperty(type=RETargetSlot),
        )

    scene.retarget_armature = bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Source Armature",
        description="Única armature sobre la que trabajará el addon",
        poll=poll_armature,
    )


def unregister_scene_props():
    scene = bpy.types.Scene

    for key, _, _ in SLOTS_CONFIG:
        prop_name = f"retarget_{key}"
        if hasattr(scene, prop_name):
            delattr(scene, prop_name)

    if hasattr(scene, "retarget_armature"):
        delattr(scene, "retarget_armature")


# ──────────────────────────────────────────────
# 3. FUNCIONES AUXILIARES
# ──────────────────────────────────────────────
def _get_armature(context):
    """Devuelve exclusivamente Source Armature. Nunca usa el objeto activo."""
    armature = context.scene.retarget_armature

    if armature is None or armature.type != 'ARMATURE':
        return None

    return armature


def _validate_armature(context, operator):
    armature = _get_armature(context)

    if armature is None:
        operator.report(
            {'ERROR'},
            "Asigna una Source Armature válida antes de usar el addon.",
        )
        return None

    return armature


def _get_bone(armature, bone_name):
    if not armature or not armature.data or not bone_name:
        return None

    bone = armature.data.bones.get(bone_name)
    if bone:
        return bone

    for candidate in armature.data.bones:
        if candidate.name.lower() == bone_name.lower():
            return candidate

    return None


def _activate_armature_pose(context, armature):
    """Activa la armature designada y la coloca en Pose Mode."""
    if context.object and context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')

    for obj in context.selected_objects:
        obj.select_set(False)

    armature.select_set(True)
    context.view_layer.objects.active = armature

    if armature.mode != 'POSE':
        bpy.ops.object.mode_set(mode='POSE')


def _get_or_create_retarget_collection(context):
    col_name = "RETARGET_Empties"
    collection = bpy.data.collections.get(col_name)

    if collection is None:
        collection = bpy.data.collections.new(col_name)

    # Asegura que la colección esté vinculada a la escena actual.
    if collection.name not in context.scene.collection.children:
        context.scene.collection.children.link(collection)

    return collection


def _slot_property(scene, slot_key):
    valid_keys = {key for key, _, _ in SLOTS_CONFIG}
    if slot_key not in valid_keys:
        return None
    return getattr(scene, f"retarget_{slot_key}")


def _get_slot_empty(context, armature, slot_key, adopt_legacy=False):
    """
    Devuelve el Empty de un slot solo si pertenece a la Source Armature.

    Los Empties creados desde 2.9 llevan metadatos de propietario.
    Para compatibilidad con Empties antiguos, puede adoptarlos si todavía
    conservan una restricción cuyo target sea exactamente esta armature
    y cuyo subtarget corresponda al hueso configurado.
    """
    slot_prop = _slot_property(context.scene, slot_key)
    if slot_prop is None or not slot_prop.empty_name:
        return None

    empty = bpy.data.objects.get(slot_prop.empty_name)
    if empty is None or empty.type != 'EMPTY':
        return None

    owner_name = empty.get(OWNER_PROP)
    stored_slot = empty.get(SLOT_PROP)

    if owner_name is not None:
        if owner_name != armature.name or stored_slot != slot_key:
            return None
        return empty

    if not adopt_legacy:
        return None

    expected_bone = slot_prop.bone_name
    if not expected_bone:
        return None

    # Adopción segura de un Empty de versiones anteriores.
    linked_to_source = any(
        constraint.target == armature
        and (not constraint.subtarget or constraint.subtarget == expected_bone)
        for constraint in empty.constraints
    )

    if linked_to_source:
        empty[OWNER_PROP] = armature.name
        empty[SLOT_PROP] = slot_key
        return empty

    return None


def _get_registered_empties(context, armature, adopt_legacy=False):
    """Obtiene únicamente los Empties registrados y validados para esta armature."""
    result = []
    seen = set()

    for key, _, _ in SLOTS_CONFIG:
        empty = _get_slot_empty(
            context,
            armature,
            key,
            adopt_legacy=adopt_legacy,
        )
        if empty and empty.name not in seen:
            result.append(empty)
            seen.add(empty.name)

    return result


def _remove_empty_if_owned(context, armature, slot_key):
    empty = _get_slot_empty(
        context,
        armature,
        slot_key,
        adopt_legacy=True,
    )
    if empty is None:
        return False

    bpy.data.objects.remove(empty, do_unlink=True)
    return True


def _remove_empty_collection_if_unused():
    collection = bpy.data.collections.get("RETARGET_Empties")
    if collection and not collection.objects and not collection.children:
        bpy.data.collections.remove(collection)


def _ensure_object_mode(context):
    if context.object and context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')


# ──────────────────────────────────────────────
# 4. OPERADORES
# ──────────────────────────────────────────────
class RETARGET_OT_pick_bone(Operator):
    bl_idname = "retarget.pick_bone"
    bl_label = "Pick Bone from Selection"
    bl_options = {'REGISTER', 'UNDO'}

    slot: StringProperty()

    def execute(self, context):
        armature = _validate_armature(context, self)
        if not armature:
            return {'CANCELLED'}

        slot_prop = _slot_property(context.scene, self.slot)
        if slot_prop is None:
            self.report({'ERROR'}, "Slot no válido.")
            return {'CANCELLED'}

        selected_bone = next(
            (pb for pb in armature.pose.bones if pb.select),
            None,
        )

        if selected_bone:
            bone_name = selected_bone.name
        elif armature.data.bones.active:
            bone_name = armature.data.bones.active.name
        else:
            self.report(
                {'ERROR'},
                "Selecciona un hueso de Source Armature en Pose Mode.",
            )
            return {'CANCELLED'}

        slot_prop.bone_name = bone_name

        if not slot_prop.empty_name:
            slot_prop.empty_name = (
                f"RET_{self.slot.replace('_', ' ').title()}"
            )

        self.report({'INFO'}, f"Hueso capturado: {bone_name}")
        return {'FINISHED'}


class RETARGET_OT_select_bone_in_viewport(Operator):
    bl_idname = "retarget.select_bone_in_viewport"
    bl_label = "Select Bone in Viewport"
    bl_options = {'REGISTER', 'UNDO'}

    slot: StringProperty()

    def execute(self, context):
        armature = _validate_armature(context, self)
        if not armature:
            return {'CANCELLED'}

        slot_prop = _slot_property(context.scene, self.slot)
        if slot_prop is None or not slot_prop.bone_name:
            self.report({'ERROR'}, "El slot no tiene un hueso asignado.")
            return {'CANCELLED'}

        bone = _get_bone(armature, slot_prop.bone_name)
        if bone is None:
            self.report(
                {'ERROR'},
                f"Hueso '{slot_prop.bone_name}' no encontrado en Source Armature.",
            )
            return {'CANCELLED'}

        try:
            _activate_armature_pose(context, armature)
        except Exception as exc:
            self.report({'ERROR'}, f"No se pudo activar Source Armature: {exc}")
            return {'CANCELLED'}

        for pose_bone in armature.pose.bones:
            pose_bone.select = False

        pose_bone = armature.pose.bones.get(bone.name)
        if pose_bone:
            pose_bone.select = True
            armature.data.bones.active = bone

        self.report({'INFO'}, f"Hueso seleccionado: {bone.name}")
        return {'FINISHED'}


class RETARGET_OT_clear_slot(Operator):
    bl_idname = "retarget.clear_slot"
    bl_label = "Clear Slot"
    bl_options = {'REGISTER', 'UNDO'}

    slot: StringProperty()

    def execute(self, context):
        armature = _validate_armature(context, self)
        if not armature:
            return {'CANCELLED'}

        slot_prop = _slot_property(context.scene, self.slot)
        if slot_prop is None:
            self.report({'ERROR'}, "Slot no válido.")
            return {'CANCELLED'}

        removed = _remove_empty_if_owned(context, armature, self.slot)

        slot_prop.bone_name = ""
        slot_prop.empty_name = ""
        slot_prop.created = False

        _remove_empty_collection_if_unused()

        self.report(
            {'INFO'},
            "Slot limpiado. " + (
                "Empty asociado eliminado." if removed
                else "No se eliminó ningún Empty ajeno a esta armature."
            ),
        )
        return {'FINISHED'}


class RETARGET_OT_create_empty(Operator):
    bl_idname = "retarget.create_empty"
    bl_label = "Create Empty"
    bl_options = {'REGISTER', 'UNDO'}

    slot: StringProperty()

    def execute(self, context):
        armature = _validate_armature(context, self)
        if not armature:
            return {'CANCELLED'}

        slot_prop = _slot_property(context.scene, self.slot)
        if slot_prop is None or not slot_prop.bone_name:
            self.report({'ERROR'}, "No hay un hueso válido asignado al slot.")
            return {'CANCELLED'}

        bone = _get_bone(armature, slot_prop.bone_name)
        if bone is None:
            self.report(
                {'ERROR'},
                f"Hueso '{slot_prop.bone_name}' no encontrado en Source Armature.",
            )
            return {'CANCELLED'}

        existing = _get_slot_empty(
            context, armature, self.slot, adopt_legacy=True
        )
        if existing:
            self.report({'WARNING'}, f"El slot ya tiene el Empty '{existing.name}'.")
            return {'CANCELLED'}

        base_name = (
            slot_prop.empty_name
            or f"RET_{self.slot.replace('_', ' ').title()}"
        )
        empty_name = base_name
        suffix = 1

        # No reutiliza ni sobrescribe objetos que pertenezcan a otro proceso.
        while empty_name in bpy.data.objects:
            empty_name = f"{base_name}_{suffix:02d}"
            suffix += 1

        pose_bone = armature.pose.bones.get(bone.name)
        if pose_bone is None:
            self.report({'ERROR'}, "No se encontró el Pose Bone correspondiente.")
            return {'CANCELLED'}

        empty = bpy.data.objects.new(empty_name, None)
        collection = _get_or_create_retarget_collection(context)
        collection.objects.link(empty)

        empty.location = armature.matrix_world @ pose_bone.head
        empty.empty_display_type = 'PLAIN_AXES'
        empty.empty_display_size = 0.3

        # Metadatos de propiedad: impiden que otro rig use o borre este Empty.
        empty[OWNER_PROP] = armature.name
        empty[SLOT_PROP] = self.slot

        slot_prop.empty_name = empty.name
        slot_prop.created = True

        copy_location = empty.constraints.new('COPY_LOCATION')
        copy_location.target = armature
        copy_location.subtarget = bone.name

        copy_rotation = empty.constraints.new('COPY_ROTATION')
        copy_rotation.target = armature
        copy_rotation.subtarget = bone.name
        copy_rotation.owner_space = 'WORLD'
        copy_rotation.target_space = 'WORLD'

        self.report({'INFO'}, f"Empty creado: {empty.name}")
        return {'FINISHED'}


class RETARGET_OT_create_all(Operator):
    bl_idname = "retarget.create_all"
    bl_label = "Create All Empties"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        armature = _validate_armature(context, self)
        if not armature:
            return {'CANCELLED'}

        created = 0
        skipped = 0
        failed = 0

        for key, _, _ in SLOTS_CONFIG:
            slot_prop = _slot_property(context.scene, key)

            if not slot_prop.bone_name:
                skipped += 1
                continue

            existing = _get_slot_empty(
                context, armature, key, adopt_legacy=True
            )
            if existing:
                skipped += 1
                continue

            result = bpy.ops.retarget.create_empty(slot=key)
            if 'FINISHED' in result:
                created += 1
            else:
                failed += 1

        if created == 0:
            self.report(
                {'WARNING'},
                f"No se crearon Empties. Omitidos: {skipped}; fallidos: {failed}.",
            )
            return {'CANCELLED'}

        self.report(
            {'INFO'},
            f"Empties creados: {created}; omitidos: {skipped}; fallidos: {failed}.",
        )
        return {'FINISHED'}


class RETARGET_OT_clear_constraints_empties(Operator):
    bl_idname = "retarget.clear_constraints_empties"
    bl_label = "Clear Empties Constraints"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        armature = _validate_armature(context, self)
        if not armature:
            return {'CANCELLED'}

        cleared = 0
        empties = _get_registered_empties(
            context, armature, adopt_legacy=True
        )

        for empty in empties:
            if empty.constraints:
                empty.constraints.clear()
                cleared += 1

        self.report(
            {'INFO'},
            f"Restricciones eliminadas en {cleared} Empty(s) de '{armature.name}'.",
        )
        return {'FINISHED'}


class RETARGET_OT_select_and_open_bake(Operator):
    """Selecciona solo los Empties registrados para Source Armature y abre Bake."""
    bl_idname = "retarget.select_and_open_bake"
    bl_label = "Auto-Select Empties & Bake"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        armature = _validate_armature(context, self)
        if not armature:
            return {'CANCELLED'}

        empties = _get_registered_empties(
            context, armature, adopt_legacy=True
        )
        if not empties:
            self.report(
                {'WARNING'},
                "No hay Empties válidos asignados a los slots de Source Armature.",
            )
            return {'CANCELLED'}

        try:
            _ensure_object_mode(context)
            bpy.ops.object.select_all(action='DESELECT')

            for empty in empties:
                empty.select_set(True)

            context.view_layer.objects.active = empties[0]

            self.report(
                {'INFO'},
                f"Seleccionados {len(empties)} Empty(s) de '{armature.name}'.",
            )

            try:
                bpy.ops.nla.bake(
                    'INVOKE_DEFAULT',
                    visual_keying=True,
                    clear_constraints=False,
                )
            except Exception:
                bpy.ops.object.bake_action('INVOKE_DEFAULT')

        except Exception as exc:
            self.report({'ERROR'}, f"No se pudo preparar el Bake: {exc}")
            return {'CANCELLED'}

        return {'FINISHED'}


class RETARGET_OT_apply_to_rig(Operator):
    bl_idname = "retarget.apply_to_rig"
    bl_label = "Empties → Rig (Apply Retarget)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        armature = _validate_armature(context, self)
        if not armature:
            return {'CANCELLED'}

        valid_pairs = []
        for key, _, _ in SLOTS_CONFIG:
            slot_prop = _slot_property(context.scene, key)
            if not slot_prop.bone_name:
                continue

            pose_bone = armature.pose.bones.get(slot_prop.bone_name)
            empty = _get_slot_empty(
                context, armature, key, adopt_legacy=True
            )

            if pose_bone and empty:
                valid_pairs.append((pose_bone, empty))

        if not valid_pairs:
            self.report(
                {'WARNING'},
                "No hay pares hueso/Empty válidos para esta Source Armature.",
            )
            return {'CANCELLED'}

        try:
            _activate_armature_pose(context, armature)
        except Exception as exc:
            self.report({'ERROR'}, f"No se pudo activar Source Armature: {exc}")
            return {'CANCELLED'}

        applied = 0
        for pose_bone, empty in valid_pairs:
            # Evita duplicar las restricciones del mismo Empty al repetir Apply.
            for constraint in list(pose_bone.constraints):
                if (
                    constraint.type in {'COPY_LOCATION', 'COPY_ROTATION'}
                    and constraint.target == empty
                ):
                    pose_bone.constraints.remove(constraint)

            copy_location = pose_bone.constraints.new('COPY_LOCATION')
            copy_location.target = empty
            copy_location.owner_space = 'WORLD'
            copy_location.target_space = 'WORLD'

            copy_rotation = pose_bone.constraints.new('COPY_ROTATION')
            copy_rotation.target = empty
            copy_rotation.owner_space = 'WORLD'
            copy_rotation.target_space = 'WORLD'

            applied += 1

        self.report(
            {'INFO'},
            f"Retarget inverso aplicado a {applied} hueso(s) de '{armature.name}'.",
        )
        return {'FINISHED'}


class RETARGET_OT_select_rig_and_open_bake(Operator):
    """Selecciona Source Armature en Pose Mode y abre el menú de Bake."""
    bl_idname = "retarget.select_rig_and_open_bake"
    bl_label = "Select Rig & Bake"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        armature = _validate_armature(context, self)
        if not armature:
            return {'CANCELLED'}

        try:
            _activate_armature_pose(context, armature)
        except Exception as exc:
            self.report({'ERROR'}, f"No se pudo activar Source Armature: {exc}")
            return {'CANCELLED'}

        self.report(
            {'INFO'},
            f"'{armature.name}' activa en Pose Mode y lista para Bake.",
        )

        try:
            bpy.ops.nla.bake(
                'INVOKE_DEFAULT',
                visual_keying=True,
                clear_constraints=False,
            )
        except Exception:
            try:
                bpy.ops.object.bake_action('INVOKE_DEFAULT')
            except Exception as exc:
                self.report({'ERROR'}, f"No se pudo abrir el menú de Bake: {exc}")
                return {'CANCELLED'}

        return {'FINISHED'}


class RETARGET_OT_clear_rig_constraints(Operator):
    bl_idname = "retarget.clear_rig_constraints"
    bl_label = "Clear Rig Retarget Constraints"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        armature = _validate_armature(context, self)
        if not armature:
            return {'CANCELLED'}

        registered_empty_names = {
            empty.name
            for empty in _get_registered_empties(
                context, armature, adopt_legacy=True
            )
        }

        try:
            _activate_armature_pose(context, armature)
        except Exception as exc:
            self.report({'ERROR'}, f"No se pudo activar Source Armature: {exc}")
            return {'CANCELLED'}

        cleared = 0
        for key, _, _ in SLOTS_CONFIG:
            slot_prop = _slot_property(context.scene, key)
            if not slot_prop.bone_name:
                continue

            pose_bone = armature.pose.bones.get(slot_prop.bone_name)
            if pose_bone is None:
                continue

            for constraint in list(pose_bone.constraints):
                if (
                    constraint.type in {'COPY_LOCATION', 'COPY_ROTATION'}
                    and constraint.target is not None
                    and constraint.target.name in registered_empty_names
                ):
                    pose_bone.constraints.remove(constraint)
                    cleared += 1

        self.report(
            {'INFO'},
            f"Eliminadas {cleared} restricciones de '{armature.name}'.",
        )
        return {'FINISHED'}


class RETARGET_OT_clean_curves_and_empties(Operator):
    """Limpia solo Source Armature, sus curvas configuradas y sus Empties."""
    bl_idname = "retarget.clean_curves_and_empties"
    bl_label = "Clean Curves and Empties"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        armature = _validate_armature(context, self)
        if not armature:
            return {'CANCELLED'}

        registered_empties = _get_registered_empties(
            context, armature, adopt_legacy=True
        )
        registered_empty_names = {empty.name for empty in registered_empties}

        # 1. Eliminar restricciones de retarget solo en los huesos de esta armature
        # y solo si apuntan a Empties registrados para ella.
        constraints_removed = 0

        try:
            _activate_armature_pose(context, armature)
        except Exception as exc:
            self.report({'ERROR'}, f"No se pudo activar Source Armature: {exc}")
            return {'CANCELLED'}

        for key, _, _ in SLOTS_CONFIG:
            slot_prop = _slot_property(context.scene, key)
            if not slot_prop.bone_name:
                continue

            pose_bone = armature.pose.bones.get(slot_prop.bone_name)
            if pose_bone is None:
                continue

            for constraint in list(pose_bone.constraints):
                if (
                    constraint.type in {'COPY_LOCATION', 'COPY_ROTATION'}
                    and constraint.target is not None
                    and constraint.target.name in registered_empty_names
                ):
                    pose_bone.constraints.remove(constraint)
                    constraints_removed += 1

        # 2. Eliminar exclusivamente F-Curves de Location de articulaciones.
        # Blender 5.x organiza las curvas en Action -> Layers -> Strips -> Channelbags.
        curves_removed = 0
        anim_data = armature.animation_data
        action = anim_data.action if anim_data else None
        action_slot = anim_data.action_slot if anim_data else None

        if action and action_slot:
            joint_paths = set()

            for key, _, keep_location in SLOTS_CONFIG:
                if keep_location:
                    continue

                slot_prop = _slot_property(context.scene, key)
                if not slot_prop.bone_name:
                    continue

                pose_bone = armature.pose.bones.get(slot_prop.bone_name)
                if pose_bone:
                    joint_paths.add(pose_bone.path_from_id("location"))

            for layer in action.layers:
                for strip in layer.strips:
                    channelbags = getattr(strip, "channelbags", None)
                    if channelbags is None:
                        continue

                    for channelbag in channelbags:
                        if channelbag.slot_handle != action_slot.handle:
                            continue

                        for fcurve in list(channelbag.fcurves):
                            if fcurve.data_path in joint_paths:
                                channelbag.fcurves.remove(fcurve)
                                curves_removed += 1

        elif action and not action_slot:
            self.report(
                {'WARNING'},
                "La Action no tiene Action Slot activo; no se modificaron curvas.",
            )

        # 3. Eliminar solo los Empties validados para esta Source Armature.
        empties_removed = 0
        for key, _, _ in SLOTS_CONFIG:
            if _remove_empty_if_owned(context, armature, key):
                empties_removed += 1

            slot_prop = _slot_property(context.scene, key)
            slot_prop.empty_name = ""
            slot_prop.created = False

        _remove_empty_collection_if_unused()

        self.report(
            {'INFO'},
            f"Limpieza de '{armature.name}': "
            f"{constraints_removed} restricciones, "
            f"{curves_removed} curvas Location y "
            f"{empties_removed} Empties eliminados.",
        )
        return {'FINISHED'}


class RETARGET_OT_clear_all(Operator):
    bl_idname = "retarget.clear_all"
    bl_label = "Delete All Empties"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        armature = _validate_armature(context, self)
        if not armature:
            return {'CANCELLED'}

        removed = 0
        for key, _, _ in SLOTS_CONFIG:
            if _remove_empty_if_owned(context, armature, key):
                removed += 1

            slot_prop = _slot_property(context.scene, key)
            slot_prop.empty_name = ""
            slot_prop.created = False

        _remove_empty_collection_if_unused()

        self.report(
            {'INFO'},
            f"{removed} Empty(s) de '{armature.name}' eliminados.",
        )
        return {'FINISHED'}


# ──────────────────────────────────────────────
# 5. PANEL (N SIDEBAR)
# ──────────────────────────────────────────────
class RETARGET_PT_panel(Panel):
    bl_label = "Retarget → Empties"
    bl_idname = "RETARGET_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Retarget"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        armature = _get_armature(context)

        box = layout.box()
        box.label(text="Source Armature (Required)", icon='BONE_DATA')
        box.prop(scene, "retarget_armature", text="")

        if armature is None:
            warning = layout.box()
            warning.label(
                text="Asigna una Source Armature para habilitar el addon.",
                icon='ERROR',
            )

        layout.separator()

        for key, label, _ in SLOTS_CONFIG:
            slot_prop = _slot_property(scene, key)
            box = layout.box()

            row_head = box.row(align=True)
            icon_tri = 'TRIA_DOWN' if slot_prop.expanded else 'TRIA_RIGHT'
            row_head.prop(
                slot_prop,
                "expanded",
                text=label,
                icon=icon_tri,
                emboss=False,
            )

            clear_op = row_head.operator("retarget.clear_slot", icon='X', text="")
            clear_op.slot = key

            if slot_prop.expanded:
                row_bone = box.row(align=True)

                if armature and armature.data:
                    row_bone.prop_search(
                        slot_prop,
                        "bone_name",
                        armature.data,
                        "bones",
                        text="Bone",
                    )
                else:
                    row_bone.prop(
                        slot_prop,
                        "bone_name",
                        text="Bone",
                    )

                pick_op = row_bone.operator(
                    "retarget.pick_bone",
                    icon='BONE_DATA',
                    text="",
                )
                pick_op.slot = key

                select_op = row_bone.operator(
                    "retarget.select_bone_in_viewport",
                    icon='ZOOM_ALL',
                    text="",
                )
                select_op.slot = key

                box.prop(slot_prop, "empty_name", text="Empty")

                create_row = box.row()
                create_op = create_row.operator(
                    "retarget.create_empty",
                    text="Create",
                )
                create_op.slot = key

                valid_empty = (
                    _get_slot_empty(context, armature, key, adopt_legacy=False)
                    if armature else None
                )
                create_row.label(
                    text="",
                    icon='CHECKMARK' if valid_empty else 'BLANK1',
                )

        layout.separator()

        part_one = layout.box()
        part_one.label(
            text="Part 1: Rig → Empties",
            icon='OUTLINER_OB_EMPTY',
        )
        row = part_one.row(align=True)
        row.operator("retarget.create_all", icon='ADD')
        row.operator("retarget.clear_all", icon='REMOVE')
        part_one.operator(
            "retarget.clear_constraints_empties",
            icon='CONSTRAINT_BONE',
        )
        part_one.operator(
            "retarget.select_and_open_bake",
            icon='RENDER_ANIMATION',
        )

        layout.separator()

        part_two = layout.box()
        part_two.label(
            text="Part 2: Empties → Rig",
            icon='ARMATURE_DATA',
        )
        part_two.operator(
            "retarget.apply_to_rig",
            icon='CON_LOCLIKE',
        )
        part_two.operator(
            "retarget.clear_rig_constraints",
            icon='X',
        )
        part_two.operator(
            "retarget.select_rig_and_open_bake",
            icon='RENDER_ANIMATION',
        )

        layout.separator()
        layout.operator(
            "retarget.clean_curves_and_empties",
            icon='TRASH',
        )


# ──────────────────────────────────────────────
# 6. REGISTRO
# ──────────────────────────────────────────────
classes = (
    RETargetSlot,
    RETARGET_OT_pick_bone,
    RETARGET_OT_select_bone_in_viewport,
    RETARGET_OT_clear_slot,
    RETARGET_OT_create_empty,
    RETARGET_OT_create_all,
    RETARGET_OT_clear_constraints_empties,
    RETARGET_OT_select_and_open_bake,
    RETARGET_OT_apply_to_rig,
    RETARGET_OT_select_rig_and_open_bake,
    RETARGET_OT_clear_rig_constraints,
    RETARGET_OT_clean_curves_and_empties,
    RETARGET_OT_clear_all,
    RETARGET_PT_panel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    register_scene_props()


def unregister():
    unregister_scene_props()

    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass


if __name__ == "__main__":
    register()
