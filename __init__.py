import bpy
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import PropertyGroup, Panel, Operator


# ──────────────────────────────────────────────
# 1. CONFIGURACIÓN DE SLOTS (CHARACTER & PROPS)
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

SYMMETRY_PAIRS = [
    ("left_hand",  "right_hand"),
    ("left_foot",  "right_foot"),
    ("left_elbow", "right_elbow"),
    ("left_knee",  "right_knee"),
]

PROP_SLOTS_CONFIG = [
    ("prop_1", "Prop 1"),
    ("prop_2", "Prop 2"),
    ("prop_3", "Prop 3"),
    ("prop_4", "Prop 4"),
    ("prop_5", "Prop 5"),
]

OWNER_PROP = "_retarget_owner_armature"
SLOT_PROP = "_retarget_slot"
PROP_SLOT_PROP = "_retarget_prop_slot"


# ──────────────────────────────────────────────
# 2. PROPERTY GROUP Y PROPIEDADES DE ESCENA
# ──────────────────────────────────────────────
def poll_armature(self, obj):
    return obj is not None and obj.type == 'ARMATURE'


def poll_prop_source_object(self, obj):
    if obj is None:
        return False
    if self.source_type == 'BONE':
        return obj.type == 'ARMATURE'
    return True


def poll_prop_target_object(self, obj):
    if obj is None:
        return False
    if self.target_type == 'BONE':
        return obj.type == 'ARMATURE'
    return True


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


class RETargetPropSlot(PropertyGroup):
    prop_label: StringProperty(
        name="Label",
        description="Nombre personalizado del prop (ej. Door, Sword, Rifle)",
        default="",
    )
    source_type: EnumProperty(
        name="Source Type",
        description="Tipo de origen animado del prop",
        items=[
            ('OBJECT', "Object / Mesh", "Objeto animado directamente (puerta, arma, accesorio sin rig)"),
            ('BONE', "Armature Bone", "Hueso específico dentro de un Rig/Armature"),
        ],
        default='OBJECT',
    )
    prop_object: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Prop Object",
        description="Objeto o Armature de origen del prop",
        poll=poll_prop_source_object,
    )
    prop_bone_name: StringProperty(
        name="Prop Bone",
        description="Hueso de origen del prop (si Source es Armature Bone)",
        default="",
    )
    target_type: EnumProperty(
        name="Target Type",
        description="Tipo de destino al que se transferirá el movimiento en Step 2",
        items=[
            ('OBJECT', "Object / Mesh", "Transferir movimiento a un Objeto directamente"),
            ('BONE', "Armature Bone", "Transferir movimiento a un hueso de una Armature"),
        ],
        default='BONE',
    )
    target_object: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Target Object",
        description="Objeto o Armature destino para Step 2",
        poll=poll_prop_target_object,
    )
    target_bone_name: StringProperty(
        name="Target Bone",
        description="Hueso destino dentro de Target Object (si Target es Armature Bone)",
        default="",
    )
    empty_name: StringProperty(
        name="Empty Name",
        description="Empty intermediario para este prop",
        default="",
    )
    created: BoolProperty(name="Created", default=False)
    expanded: BoolProperty(
        name="Expanded",
        description="Mostrar/Ocultar sección del prop",
        default=False,
    )


def register_scene_props():
    scene = bpy.types.Scene

    for key, _, _ in SLOTS_CONFIG:
        setattr(
            scene,
            f"retarget_{key}",
            bpy.props.PointerProperty(type=RETargetSlot),
        )

    scene.retarget_root_bone = bpy.props.PointerProperty(type=RETargetSlot)

    # Desplegables maestros de listas (abiertos por defecto)
    scene.retarget_slots_expanded = BoolProperty(
        name="Bone Slots",
        description="Mostrar/Ocultar lista de slots de huesos",
        default=True,
    )
    scene.retarget_prop_slots_expanded = BoolProperty(
        name="Prop Slots",
        description="Mostrar/Ocultar lista de slots de props",
        default=True,
    )

    # Desplegables de etapas/secciones (cerrados por defecto)
    scene.retarget_part1_expanded = BoolProperty(
        name="Part 1: Rig → Empties",
        description="Mostrar/Ocultar Part 1",
        default=False,
    )
    scene.retarget_part2_expanded = BoolProperty(
        name="Part 2: Empties → Rig",
        description="Mostrar/Ocultar Part 2",
        default=False,
    )
    scene.retarget_part3_expanded = BoolProperty(
        name="Part 3: Torso → Root Motion",
        description="Mostrar/Ocultar Part 3",
        default=False,
    )
    scene.retarget_prop_step1_expanded = BoolProperty(
        name="Step 1: Prop → Empties",
        description="Mostrar/Ocultar Step 1 de Props",
        default=False,
    )
    scene.retarget_prop_step2_expanded = BoolProperty(
        name="Step 2: Empties → Prop",
        description="Mostrar/Ocultar Step 2 de Props",
        default=False,
    )

    scene.retarget_armature = bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Source Armature",
        description="Única armature sobre la que trabajará el módulo principal",
        poll=poll_armature,
    )

    for key, _ in PROP_SLOTS_CONFIG:
        setattr(
            scene,
            f"retarget_{key}",
            bpy.props.PointerProperty(type=RETargetPropSlot),
        )


def unregister_scene_props():
    scene = bpy.types.Scene

    for key, _, _ in SLOTS_CONFIG:
        prop_name = f"retarget_{key}"
        if hasattr(scene, prop_name):
            delattr(scene, prop_name)

    extra_props = (
        "retarget_root_bone",
        "retarget_slots_expanded",
        "retarget_prop_slots_expanded",
        "retarget_part1_expanded",
        "retarget_part2_expanded",
        "retarget_part3_expanded",
        "retarget_prop_step1_expanded",
        "retarget_prop_step2_expanded",
        "retarget_armature",
    )
    for prop_name in extra_props:
        if hasattr(scene, prop_name):
            delattr(scene, prop_name)

    for key, _ in PROP_SLOTS_CONFIG:
        prop_name = f"retarget_{key}"
        if hasattr(scene, prop_name):
            delattr(scene, prop_name)


# ──────────────────────────────────────────────
# 3. FUNCIONES AUXILIARES (CHARACTER)
# ──────────────────────────────────────────────
def _get_armature(context):
    """Devuelve exclusivamente Source Armature del módulo principal."""
    armature = context.scene.retarget_armature

    if armature is None or armature.type != 'ARMATURE':
        return None

    return armature


def _validate_armature(context, operator):
    armature = _get_armature(context)

    if armature is None:
        operator.report(
            {'ERROR'},
            "Asigna una Source Armature válida antes de usar este operador.",
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


def _find_symmetric_bone_name(armature, bone_name):
    """Busca el nombre simétrico de un hueso usando Blender flip_name y convenciones comunes."""
    if not armature or not armature.data or not bone_name:
        return None

    candidates = []

    try:
        flipped = bpy.utils.flip_name(bone_name)
        if flipped and flipped != bone_name:
            candidates.append(flipped)
    except Exception:
        pass

    replacements = [
        (".L", ".R"), (".R", ".L"),
        ("_L", "_R"), ("_R", "_L"),
        (".l", ".r"), (".r", ".l"),
        ("_l", "_r"), ("_r", "_l"),
        ("-L", "-R"), ("-R", "-L"),
        ("-l", "-r"), ("-r", "-l"),
        ("Left", "Right"), ("Right", "Left"),
        ("LEFT", "RIGHT"), ("RIGHT", "LEFT"),
        ("left", "right"), ("right", "left"),
    ]

    for old, new in replacements:
        if old in bone_name:
            cand = bone_name.replace(old, new)
            if cand != bone_name and cand not in candidates:
                candidates.append(cand)

    for cand in candidates:
        bone = _get_bone(armature, cand)
        if bone and bone.name != bone_name:
            return bone.name

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

    if collection.name not in context.scene.collection.children:
        context.scene.collection.children.link(collection)

    return collection


def _slot_property(scene, slot_key):
    if slot_key == "root_bone":
        return getattr(scene, "retarget_root_bone", None)
    valid_keys = {key for key, _, _ in SLOTS_CONFIG}
    if slot_key not in valid_keys:
        return None
    return getattr(scene, f"retarget_{slot_key}")


def _get_slot_empty(context, armature, slot_key, adopt_legacy=False, allow_cross_armature=False):
    slot_prop = _slot_property(context.scene, slot_key)
    if slot_prop is None or not slot_prop.empty_name:
        return None

    empty = bpy.data.objects.get(slot_prop.empty_name)
    if empty is None or empty.type != 'EMPTY':
        return None

    owner_name = empty.get(OWNER_PROP)
    stored_slot = empty.get(SLOT_PROP)

    if owner_name is not None:
        if stored_slot is not None and stored_slot != slot_key:
            return None
        if owner_name == armature.name or allow_cross_armature:
            return empty
        return None

    if not adopt_legacy:
        return None

    expected_bone = slot_prop.bone_name
    if not expected_bone:
        return None

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


def _get_registered_empties(context, armature, adopt_legacy=False, allow_cross_armature=False):
    result = []
    seen = set()

    for key, _, _ in SLOTS_CONFIG:
        empty = _get_slot_empty(
            context,
            armature,
            key,
            adopt_legacy=adopt_legacy,
            allow_cross_armature=allow_cross_armature,
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
        allow_cross_armature=False,
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
# 3.5. FUNCIONES AUXILIARES (PROPS)
# ──────────────────────────────────────────────
def _get_or_create_props_collection(context):
    col_name = "RETARGET_Prop_Empties"
    collection = bpy.data.collections.get(col_name)

    if collection is None:
        collection = bpy.data.collections.new(col_name)

    if collection.name not in context.scene.collection.children:
        context.scene.collection.children.link(collection)

    return collection


def _remove_props_collection_if_unused():
    collection = bpy.data.collections.get("RETARGET_Prop_Empties")
    if collection and not collection.objects and not collection.children:
        bpy.data.collections.remove(collection)


def _prop_slot_property(scene, prop_key):
    valid_keys = {key for key, _ in PROP_SLOTS_CONFIG}
    if prop_key not in valid_keys:
        return None
    return getattr(scene, f"retarget_{prop_key}", None)


def _get_prop_slot_empty(context, prop_key):
    prop_slot = _prop_slot_property(context.scene, prop_key)
    if prop_slot is None or not prop_slot.empty_name:
        return None

    empty = bpy.data.objects.get(prop_slot.empty_name)
    if empty is None or empty.type != 'EMPTY':
        return None

    if empty.get(PROP_SLOT_PROP) != prop_key:
        return None

    return empty


def _get_registered_prop_empties(context):
    result = []
    seen = set()
    for key, _ in PROP_SLOTS_CONFIG:
        empty = _get_prop_slot_empty(context, key)
        if empty and empty.name not in seen:
            result.append(empty)
            seen.add(empty.name)
    return result


def _remove_prop_empty_if_owned(context, prop_key):
    empty = _get_prop_slot_empty(context, prop_key)
    if empty is None:
        return False
    bpy.data.objects.remove(empty, do_unlink=True)
    return True


# ──────────────────────────────────────────────
# 4. OPERADORES (CHARACTER RETARGET)
# ──────────────────────────────────────────────
class RETARGET_OT_symmetrize_bones(Operator):
    """Busca y asigna automáticamente los huesos simétricos en Hands, Feet, Elbows y Knees."""
    bl_idname = "retarget.symmetrize_bones"
    bl_label = "Symmetrize"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        armature = _validate_armature(context, self)
        if not armature:
            return {'CANCELLED'}

        scene = context.scene
        filled = 0
        not_found = []

        for left_key, right_key in SYMMETRY_PAIRS:
            left_slot = _slot_property(scene, left_key)
            right_slot = _slot_property(scene, right_key)

            if left_slot.bone_name and not right_slot.bone_name:
                sym_name = _find_symmetric_bone_name(armature, left_slot.bone_name)
                if sym_name:
                    right_slot.bone_name = sym_name
                    if not right_slot.empty_name:
                        right_slot.empty_name = f"RET_{right_key.replace('_', ' ').title()}"
                    filled += 1
                else:
                    not_found.append(right_key)

            elif right_slot.bone_name and not left_slot.bone_name:
                sym_name = _find_symmetric_bone_name(armature, right_slot.bone_name)
                if sym_name:
                    left_slot.bone_name = sym_name
                    if not left_slot.empty_name:
                        left_slot.empty_name = f"RET_{left_key.replace('_', ' ').title()}"
                    filled += 1
                else:
                    not_found.append(left_key)

        if filled == 0 and not not_found:
            self.report(
                {'WARNING'},
                "Asigna al menos un lado (Left o Right) en Hands, Feet, Elbows o Knees para simetrizar.",
            )
            return {'CANCELLED'}

        if not_found:
            self.report(
                {'INFO'},
                f"Simetrizados: {filled} hueso(s). Sin coincidencia en: {', '.join(not_found)}.",
            )
        else:
            self.report({'INFO'}, f"Simetrizados: {filled} hueso(s) completado(s).")

        return {'FINISHED'}


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
            if self.slot == "root_bone":
                slot_prop.empty_name = "RET_Root_Motion"
            else:
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
            context, armature, self.slot, adopt_legacy=True, allow_cross_armature=False
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
        empty.show_in_front = True

        empty[OWNER_PROP] = armature.name
        empty[SLOT_PROP] = self.slot

        slot_prop.empty_name = empty.name
        slot_prop.created = True

        copy_location = empty.constraints.new('COPY_LOCATION')
        copy_location.name = "RET_Copy Location"
        copy_location.target = armature
        copy_location.subtarget = bone.name

        copy_rotation = empty.constraints.new('COPY_ROTATION')
        copy_rotation.name = "RET_Copy Rotation"
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
                context, armature, key, adopt_legacy=True, allow_cross_armature=False
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
            context, armature, adopt_legacy=True, allow_cross_armature=True
        )

        for empty in empties:
            if empty.constraints:
                empty.constraints.clear()
                cleared += 1

        self.report(
            {'INFO'},
            f"Restricciones eliminadas en {cleared} Empty(s).",
        )
        return {'FINISHED'}


class RETARGET_OT_select_and_open_bake(Operator):
    """Selecciona los Empties registrados y abre Bake."""
    bl_idname = "retarget.select_and_open_bake"
    bl_label = "Auto-Select Empties & Bake"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        armature = _validate_armature(context, self)
        if not armature:
            return {'CANCELLED'}

        empties = _get_registered_empties(
            context, armature, adopt_legacy=True, allow_cross_armature=False
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
                context, armature, key, adopt_legacy=True, allow_cross_armature=True
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
            for constraint in list(pose_bone.constraints):
                if (
                    constraint.type in {'COPY_LOCATION', 'COPY_ROTATION'}
                    and constraint.target == empty
                ):
                    pose_bone.constraints.remove(constraint)

            copy_location = pose_bone.constraints.new('COPY_LOCATION')
            copy_location.name = "RET_Copy Location"
            copy_location.target = empty
            copy_location.owner_space = 'WORLD'
            copy_location.target_space = 'WORLD'

            copy_rotation = pose_bone.constraints.new('COPY_ROTATION')
            copy_rotation.name = "RET_Copy Rotation"
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

        for pb in armature.pose.bones:
            pb.select = False

        selected_bones = 0
        last_bone = None
        for key, _, _ in SLOTS_CONFIG:
            slot_prop = _slot_property(context.scene, key)
            if not slot_prop.bone_name:
                continue

            empty = _get_slot_empty(
                context, armature, key, adopt_legacy=True, allow_cross_armature=True
            )
            if empty is None:
                continue

            pose_bone = armature.pose.bones.get(slot_prop.bone_name)
            bone_data = armature.data.bones.get(slot_prop.bone_name)
            if pose_bone and bone_data:
                pose_bone.select = True
                last_bone = bone_data
                selected_bones += 1

        if last_bone:
            armature.data.bones.active = last_bone

        if selected_bones == 0:
            self.report(
                {'WARNING'},
                "No se encontraron huesos activos con Empty válido para seleccionar en Pose Mode.",
            )
            return {'CANCELLED'}

        self.report(
            {'INFO'},
            f"'{armature.name}' en Pose Mode con {selected_bones} hueso(s) seleccionado(s) listo para Bake.",
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
                context, armature, adopt_legacy=True, allow_cross_armature=True
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
                    and (
                        (constraint.target is not None and constraint.target.name in registered_empty_names)
                        or constraint.name.startswith("RET_")
                    )
                ):
                    pose_bone.constraints.remove(constraint)
                    cleared += 1

        self.report(
            {'INFO'},
            f"Eliminadas {cleared} restricciones de '{armature.name}'.",
        )
        return {'FINISHED'}


# ──────────────────────────────────────────────
# 4.5. OPERADORES PARTE 3: TORSO -> ROOT MOTION
# ──────────────────────────────────────────────
class RETARGET_OT_create_root_empty(Operator):
    bl_idname = "retarget.create_root_empty"
    bl_label = "Create Root Motion Empty"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        armature = _validate_armature(context, self)
        if not armature:
            return {'CANCELLED'}

        root_slot = _slot_property(context.scene, "root_bone")
        torso_slot = _slot_property(context.scene, "torso")

        if not root_slot or not root_slot.bone_name:
            self.report({'ERROR'}, "Asigna primero el hueso Root en la sección Root Motion.")
            return {'CANCELLED'}

        if not torso_slot or not torso_slot.bone_name:
            self.report({'ERROR'}, "Asigna primero el hueso Torso en la lista principal.")
            return {'CANCELLED'}

        root_bone = _get_bone(armature, root_slot.bone_name)
        torso_bone = _get_bone(armature, torso_slot.bone_name)

        if not root_bone:
            self.report({'ERROR'}, f"Hueso Root '{root_slot.bone_name}' no encontrado en Source Armature.")
            return {'CANCELLED'}

        if not torso_bone:
            self.report({'ERROR'}, f"Hueso Torso '{torso_slot.bone_name}' no encontrado en Source Armature.")
            return {'CANCELLED'}

        existing = _get_slot_empty(context, armature, "root_bone", adopt_legacy=False)
        if existing:
            self.report({'WARNING'}, f"Ya existe el Empty de Root Motion: '{existing.name}'.")
            return {'CANCELLED'}

        pose_root = armature.pose.bones.get(root_bone.name)
        if not pose_root:
            self.report({'ERROR'}, "No se encontró el Pose Bone del Root.")
            return {'CANCELLED'}

        base_name = root_slot.empty_name or "RET_Root_Motion"
        empty_name = base_name
        suffix = 1
        while empty_name in bpy.data.objects:
            empty_name = f"{base_name}_{suffix:02d}"
            suffix += 1

        empty = bpy.data.objects.new(empty_name, None)
        collection = _get_or_create_retarget_collection(context)
        collection.objects.link(empty)

        empty.location = armature.matrix_world @ pose_root.head
        empty.empty_display_type = 'ARROWS'
        empty.empty_display_size = 0.4
        empty.show_in_front = True

        empty[OWNER_PROP] = armature.name
        empty[SLOT_PROP] = "root_bone"

        root_slot.empty_name = empty.name
        root_slot.created = True

        cl = empty.constraints.new('COPY_LOCATION')
        cl.name = "RET_Copy Location"
        cl.target = armature
        cl.subtarget = torso_bone.name
        cl.use_x = True
        cl.use_y = True
        cl.use_z = False
        cl.use_offset = True
        cl.owner_space = 'WORLD'
        cl.target_space = 'WORLD'

        self.report({'INFO'}, f"Root Motion Empty creado: '{empty.name}' copiando XY (Offset) de '{torso_bone.name}'.")
        return {'FINISHED'}


class RETARGET_OT_clear_root_constraints(Operator):
    bl_idname = "retarget.clear_root_constraints"
    bl_label = "Clear Root Constraints"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        armature = _validate_armature(context, self)
        if not armature:
            return {'CANCELLED'}

        root_slot = _slot_property(context.scene, "root_bone")
        empty = _get_slot_empty(context, armature, "root_bone", adopt_legacy=False, allow_cross_armature=True)

        empty_cleared = 0
        bone_cleared = 0

        if empty and empty.constraints:
            empty.constraints.clear()
            empty_cleared = 1

        if root_slot and root_slot.bone_name:
            try:
                _activate_armature_pose(context, armature)
                pose_root = armature.pose.bones.get(root_slot.bone_name)
                if pose_root:
                    for c in list(pose_root.constraints):
                        if (
                            c.type in {'COPY_LOCATION', 'COPY_ROTATION'}
                            and (
                                (empty is not None and c.target == empty)
                                or c.name.startswith("RET_")
                            )
                        ):
                            pose_root.constraints.remove(c)
                            bone_cleared += 1
            except Exception:
                pass

        self.report(
            {'INFO'},
            f"Constraints de Root limpiados (Empty: {empty_cleared}, Bone: {bone_cleared}).",
        )
        return {'FINISHED'}


class RETARGET_OT_bake_root_empty(Operator):
    bl_idname = "retarget.bake_root_empty"
    bl_label = "Select Root Empty & Bake"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        armature = _validate_armature(context, self)
        if not armature:
            return {'CANCELLED'}

        empty = _get_slot_empty(context, armature, "root_bone", adopt_legacy=False)
        if not empty:
            self.report({'WARNING'}, "No hay un Empty de Root Motion creado para esta armature.")
            return {'CANCELLED'}

        try:
            _ensure_object_mode(context)
            bpy.ops.object.select_all(action='DESELECT')
            empty.select_set(True)
            context.view_layer.objects.active = empty

            self.report({'INFO'}, f"Empty '{empty.name}' seleccionado para Bake.")
            try:
                bpy.ops.nla.bake('INVOKE_DEFAULT', visual_keying=True, clear_constraints=False)
            except Exception:
                bpy.ops.object.bake_action('INVOKE_DEFAULT')
        except Exception as exc:
            self.report({'ERROR'}, f"No se pudo preparar el Bake: {exc}")
            return {'CANCELLED'}

        return {'FINISHED'}


class RETARGET_OT_apply_root_to_bone(Operator):
    bl_idname = "retarget.apply_root_to_bone"
    bl_label = "Empty → Root Bone (Apply)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        armature = _validate_armature(context, self)
        if not armature:
            return {'CANCELLED'}

        root_slot = _slot_property(context.scene, "root_bone")
        if not root_slot or not root_slot.bone_name:
            self.report({'ERROR'}, "Asigna un Root Bone primero.")
            return {'CANCELLED'}

        empty = _get_slot_empty(context, armature, "root_bone", adopt_legacy=False, allow_cross_armature=True)
        if not empty:
            self.report({'ERROR'}, "No se encontró el Empty de Root Motion.")
            return {'CANCELLED'}

        pose_root = armature.pose.bones.get(root_slot.bone_name)
        if not pose_root:
            self.report({'ERROR'}, f"Pose Bone '{root_slot.bone_name}' no encontrado.")
            return {'CANCELLED'}

        try:
            _activate_armature_pose(context, armature)
        except Exception as exc:
            self.report({'ERROR'}, f"No se pudo activar Source Armature: {exc}")
            return {'CANCELLED'}

        for c in list(pose_root.constraints):
            if c.type == 'COPY_LOCATION' and c.target == empty:
                pose_root.constraints.remove(c)

        cl = pose_root.constraints.new('COPY_LOCATION')
        cl.name = "RET_Copy Location"
        cl.target = empty
        cl.use_x = True
        cl.use_y = True
        cl.use_z = False
        cl.owner_space = 'WORLD'
        cl.target_space = 'WORLD'

        self.report({'INFO'}, f"Constraint aplicada al Root Bone '{pose_root.name}'.")
        return {'FINISHED'}


class RETARGET_OT_select_root_and_bake(Operator):
    bl_idname = "retarget.select_root_and_bake"
    bl_label = "Select Root Bone & Bake"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        armature = _validate_armature(context, self)
        if not armature:
            return {'CANCELLED'}

        root_slot = _slot_property(context.scene, "root_bone")
        if not root_slot or not root_slot.bone_name:
            self.report({'ERROR'}, "Asigna un Root Bone primero.")
            return {'CANCELLED'}

        pose_root = armature.pose.bones.get(root_slot.bone_name)
        bone_data = armature.data.bones.get(root_slot.bone_name)
        if not pose_root or not bone_data:
            self.report({'ERROR'}, f"Root Bone '{root_slot.bone_name}' no encontrado.")
            return {'CANCELLED'}

        try:
            _activate_armature_pose(context, armature)
        except Exception as exc:
            self.report({'ERROR'}, f"No se pudo activar Source Armature: {exc}")
            return {'CANCELLED'}

        for pb in armature.pose.bones:
            pb.select = False

        pose_root.select = True
        armature.data.bones.active = bone_data

        self.report({'INFO'}, f"Root Bone '{pose_root.name}' seleccionado en Pose Mode para Bake.")

        try:
            bpy.ops.nla.bake('INVOKE_DEFAULT', visual_keying=True, clear_constraints=False)
        except Exception:
            try:
                bpy.ops.object.bake_action('INVOKE_DEFAULT')
            except Exception as exc:
                self.report({'ERROR'}, f"No se pudo abrir el menú de Bake: {exc}")
                return {'CANCELLED'}

        return {'FINISHED'}


class RETARGET_OT_clean_root_motion(Operator):
    bl_idname = "retarget.clean_root_motion"
    bl_label = "Clean Root Motion Setup"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        armature = _validate_armature(context, self)
        if not armature:
            return {'CANCELLED'}

        root_slot = _slot_property(context.scene, "root_bone")
        empty = _get_slot_empty(context, armature, "root_bone", adopt_legacy=False, allow_cross_armature=True)

        constraints_removed = 0
        if root_slot and root_slot.bone_name:
            try:
                _activate_armature_pose(context, armature)
                pose_root = armature.pose.bones.get(root_slot.bone_name)
                if pose_root:
                    for c in list(pose_root.constraints):
                        if (
                            c.type in {'COPY_LOCATION', 'COPY_ROTATION'}
                            and (
                                (empty is not None and c.target == empty)
                                or c.name.startswith("RET_")
                            )
                        ):
                            pose_root.constraints.remove(c)
                            constraints_removed += 1
            except Exception:
                pass

        empty_removed = _remove_empty_if_owned(context, armature, "root_bone")
        if root_slot and empty_removed:
            root_slot.empty_name = ""
            root_slot.created = False

        _remove_empty_collection_if_unused()

        self.report(
            {'INFO'},
            f"Root Motion limpiado: {constraints_removed} restricción(es) y {int(empty_removed)} Empty eliminado(s).",
        )
        return {'FINISHED'}


# ──────────────────────────────────────────────
# 4.6. LIMPIEZA DE CURVAS (PARTE 2) Y LIMPIEZA FINAL DEL SETUP
# ──────────────────────────────────────────────
class RETARGET_OT_clean_curves_and_empties(Operator):
    bl_idname = "retarget.clean_curves_and_empties"
    bl_label = "Clean Curves and Empties"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        armature = _validate_armature(context, self)
        if not armature:
            return {'CANCELLED'}

        registered_empties = _get_registered_empties(
            context, armature, adopt_legacy=True, allow_cross_armature=True
        )
        registered_empty_names = {empty.name for empty in registered_empties}

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
                    and (
                        (constraint.target is not None and constraint.target.name in registered_empty_names)
                        or constraint.name.startswith("RET_")
                    )
                ):
                    pose_bone.constraints.remove(constraint)
                    constraints_removed += 1

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
            f"{empties_removed} Empties propios eliminados.",
        )
        return {'FINISHED'}


class RETARGET_OT_clean_all_setup(Operator):
    bl_idname = "retarget.clean_all_setup"
    bl_label = "Clean Setup (Empties & Constraints)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        armature = _validate_armature(context, self)
        if not armature:
            return {'CANCELLED'}

        registered_empties = _get_registered_empties(
            context, armature, adopt_legacy=True, allow_cross_armature=True
        )
        registered_empty_names = {empty.name for empty in registered_empties}

        root_empty = _get_slot_empty(
            context, armature, "root_bone", adopt_legacy=False, allow_cross_armature=True
        )
        if root_empty:
            registered_empty_names.add(root_empty.name)

        constraints_removed = 0
        try:
            _activate_armature_pose(context, armature)
            for pose_bone in armature.pose.bones:
                for constraint in list(pose_bone.constraints):
                    if (
                        constraint.type in {'COPY_LOCATION', 'COPY_ROTATION'}
                        and (
                            (constraint.target is not None and constraint.target.name in registered_empty_names)
                            or constraint.name.startswith("RET_")
                        )
                    ):
                        pose_bone.constraints.remove(constraint)
                        constraints_removed += 1
        except Exception as exc:
            self.report({'ERROR'}, f"No se pudo limpiar constraints del Rig: {exc}")
            return {'CANCELLED'}

        empties_removed = 0
        for key, _, _ in SLOTS_CONFIG:
            if _remove_empty_if_owned(context, armature, key):
                empties_removed += 1
                slot_prop = _slot_property(context.scene, key)
                slot_prop.empty_name = ""
                slot_prop.created = False

        if _remove_empty_if_owned(context, armature, "root_bone"):
            empties_removed += 1
            root_slot = _slot_property(context.scene, "root_bone")
            if root_slot:
                root_slot.empty_name = ""
                root_slot.created = False

        _remove_empty_collection_if_unused()

        self.report(
            {'INFO'},
            f"Setup limpiado en '{armature.name}': "
            f"{constraints_removed} constraints y {empties_removed} Empties propios eliminados (curvas conservadas).",
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
# 4.7. OPERADORES MÓDULO PROP -> EMPTIES (100% LIBRE DE SOURCE ARMATURE)
# ──────────────────────────────────────────────
class RETARGET_OT_prop_pick_source_bone(Operator):
    """Captura el hueso seleccionado de Prop Obj (Armature) en Pose Mode."""
    bl_idname = "retarget.prop_pick_source_bone"
    bl_label = "Pick Prop Bone"
    bl_options = {'REGISTER', 'UNDO'}

    slot: StringProperty()

    def execute(self, context):
        prop_slot = _prop_slot_property(context.scene, self.slot)
        if not prop_slot:
            return {'CANCELLED'}

        prop_arm = prop_slot.prop_object
        if prop_arm is None or prop_arm.type != 'ARMATURE':
            self.report({'ERROR'}, "Asigna primero una Armature en Prop Obj.")
            return {'CANCELLED'}

        selected_bone = next((pb for pb in prop_arm.pose.bones if pb.select), None)
        if selected_bone:
            bone_name = selected_bone.name
        elif prop_arm.data.bones.active:
            bone_name = prop_arm.data.bones.active.name
        else:
            self.report({'ERROR'}, f"Selecciona un hueso en '{prop_arm.name}' (Pose Mode).")
            return {'CANCELLED'}

        prop_slot.prop_bone_name = bone_name
        if not prop_slot.empty_name:
            label = prop_slot.prop_label.strip() or self.slot.replace('_', ' ').title()
            prop_slot.empty_name = f"RET_Prop_{label.replace(' ', '_')}"

        self.report({'INFO'}, f"Prop Bone capturado: {bone_name}")
        return {'FINISHED'}


class RETARGET_OT_prop_select_source_bone(Operator):
    """Selecciona el Prop Bone en el viewport (Pose Mode)."""
    bl_idname = "retarget.prop_select_source_bone"
    bl_label = "Select Prop Bone in Viewport"
    bl_options = {'REGISTER', 'UNDO'}

    slot: StringProperty()

    def execute(self, context):
        prop_slot = _prop_slot_property(context.scene, self.slot)
        if not prop_slot:
            return {'CANCELLED'}

        prop_arm = prop_slot.prop_object
        if prop_arm is None or prop_arm.type != 'ARMATURE':
            self.report({'ERROR'}, "Asigna una Armature en Prop Obj.")
            return {'CANCELLED'}

        if not prop_slot.prop_bone_name:
            self.report({'ERROR'}, "No hay Prop Bone asignado.")
            return {'CANCELLED'}

        bone = _get_bone(prop_arm, prop_slot.prop_bone_name)
        if not bone:
            self.report({'ERROR'}, f"Hueso '{prop_slot.prop_bone_name}' no encontrado en '{prop_arm.name}'.")
            return {'CANCELLED'}

        _activate_armature_pose(context, prop_arm)
        for pb in prop_arm.pose.bones:
            pb.select = False
        pb = prop_arm.pose.bones.get(bone.name)
        if pb:
            pb.select = True
            prop_arm.data.bones.active = bone

        self.report({'INFO'}, f"Prop Bone seleccionado: {bone.name}")
        return {'FINISHED'}


class RETARGET_OT_prop_pick_target_bone(Operator):
    """Captura el hueso seleccionado de Target Obj (Armature) en Pose Mode."""
    bl_idname = "retarget.prop_pick_target_bone"
    bl_label = "Pick Target Bone"
    bl_options = {'REGISTER', 'UNDO'}

    slot: StringProperty()

    def execute(self, context):
        prop_slot = _prop_slot_property(context.scene, self.slot)
        if not prop_slot:
            return {'CANCELLED'}

        target_arm = prop_slot.target_object
        if target_arm is None or target_arm.type != 'ARMATURE':
            self.report({'ERROR'}, "Asigna primero una Armature en Target Obj.")
            return {'CANCELLED'}

        selected_bone = next((pb for pb in target_arm.pose.bones if pb.select), None)
        if selected_bone:
            bone_name = selected_bone.name
        elif target_arm.data.bones.active:
            bone_name = target_arm.data.bones.active.name
        else:
            self.report({'ERROR'}, f"Selecciona un hueso en '{target_arm.name}' (Pose Mode).")
            return {'CANCELLED'}

        prop_slot.target_bone_name = bone_name
        self.report({'INFO'}, f"Target Bone capturado: {bone_name}")
        return {'FINISHED'}


class RETARGET_OT_prop_select_target_bone(Operator):
    """Selecciona el Target Bone en el viewport (Pose Mode)."""
    bl_idname = "retarget.prop_select_target_bone"
    bl_label = "Select Target Bone in Viewport"
    bl_options = {'REGISTER', 'UNDO'}

    slot: StringProperty()

    def execute(self, context):
        prop_slot = _prop_slot_property(context.scene, self.slot)
        if not prop_slot:
            return {'CANCELLED'}

        target_arm = prop_slot.target_object
        if target_arm is None or target_arm.type != 'ARMATURE':
            self.report({'ERROR'}, "Asigna una Armature en Target Obj.")
            return {'CANCELLED'}

        if not prop_slot.target_bone_name:
            self.report({'ERROR'}, "No hay Target Bone asignado.")
            return {'CANCELLED'}

        bone = _get_bone(target_arm, prop_slot.target_bone_name)
        if not bone:
            self.report({'ERROR'}, f"Hueso '{prop_slot.target_bone_name}' no encontrado en '{target_arm.name}'.")
            return {'CANCELLED'}

        _activate_armature_pose(context, target_arm)
        for pb in target_arm.pose.bones:
            pb.select = False
        pb = target_arm.pose.bones.get(bone.name)
        if pb:
            pb.select = True
            target_arm.data.bones.active = bone

        self.report({'INFO'}, f"Target Bone seleccionado: {bone.name}")
        return {'FINISHED'}


class RETARGET_OT_prop_clear_slot(Operator):
    """Limpia el slot de prop y elimina su Empty asociado."""
    bl_idname = "retarget.prop_clear_slot"
    bl_label = "Clear Prop Slot"
    bl_options = {'REGISTER', 'UNDO'}

    slot: StringProperty()

    def execute(self, context):
        prop_slot = _prop_slot_property(context.scene, self.slot)
        if not prop_slot:
            return {'CANCELLED'}

        _remove_prop_empty_if_owned(context, self.slot)
        prop_slot.prop_label = ""
        prop_slot.prop_object = None
        prop_slot.prop_bone_name = ""
        prop_slot.target_object = None
        prop_slot.target_bone_name = ""
        prop_slot.empty_name = ""
        prop_slot.created = False
        _remove_props_collection_if_unused()

        self.report({'INFO'}, "Slot de Prop limpiado.")
        return {'FINISHED'}


class RETARGET_OT_prop_create_empty(Operator):
    """Crea un Empty que sigue el movimiento/rotación del Prop (Objeto o Hueso)."""
    bl_idname = "retarget.prop_create_empty"
    bl_label = "Create Prop Empty"
    bl_options = {'REGISTER', 'UNDO'}

    slot: StringProperty()

    def execute(self, context):
        prop_slot = _prop_slot_property(context.scene, self.slot)
        if not prop_slot:
            return {'CANCELLED'}

        prop_obj = prop_slot.prop_object
        if prop_obj is None:
            self.report({'ERROR'}, "Asigna un Prop Object o Armature primero.")
            return {'CANCELLED'}

        if prop_slot.source_type == 'BONE':
            if prop_obj.type != 'ARMATURE':
                self.report({'ERROR'}, "El objeto asignado debe ser una Armature para modo Armature Bone.")
                return {'CANCELLED'}
            if not prop_slot.prop_bone_name or not _get_bone(prop_obj, prop_slot.prop_bone_name):
                self.report({'ERROR'}, "Asigna un hueso válido en Prop Bone.")
                return {'CANCELLED'}

        existing = _get_prop_slot_empty(context, self.slot)
        if existing:
            self.report({'WARNING'}, f"Este Prop ya tiene el Empty '{existing.name}'.")
            return {'CANCELLED'}

        label = prop_slot.prop_label.strip() or self.slot.replace('_', ' ').title()
        base_name = prop_slot.empty_name or f"RET_Prop_{label.replace(' ', '_')}"
        empty_name = base_name
        suffix = 1
        while empty_name in bpy.data.objects:
            empty_name = f"{base_name}_{suffix:02d}"
            suffix += 1

        empty = bpy.data.objects.new(empty_name, None)
        col = _get_or_create_props_collection(context)
        col.objects.link(empty)

        if prop_slot.source_type == 'BONE':
            pb = prop_obj.pose.bones.get(prop_slot.prop_bone_name)
            empty.location = prop_obj.matrix_world @ pb.head
            empty.empty_display_type = 'CONE'
            empty.empty_display_size = 0.25
        else:
            empty.location = prop_obj.matrix_world.translation
            empty.empty_display_type = 'SINGLE_ARROW'
            empty.empty_display_size = 0.8

        empty.show_in_front = True
        empty[PROP_SLOT_PROP] = self.slot

        prop_slot.empty_name = empty.name
        prop_slot.created = True

        cl = empty.constraints.new('COPY_LOCATION')
        cl.name = "RET_Prop Copy Location"
        cl.target = prop_obj
        if prop_slot.source_type == 'BONE':
            cl.subtarget = prop_slot.prop_bone_name
        cl.owner_space = 'WORLD'
        cl.target_space = 'WORLD'

        cr = empty.constraints.new('COPY_ROTATION')
        cr.name = "RET_Prop Copy Rotation"
        cr.target = prop_obj
        if prop_slot.source_type == 'BONE':
            cr.subtarget = prop_slot.prop_bone_name
        cr.owner_space = 'WORLD'
        cr.target_space = 'WORLD'

        self.report({'INFO'}, f"Prop Empty creado: '{empty.name}'.")
        return {'FINISHED'}


class RETARGET_OT_prop_create_all(Operator):
    """Crea Empties para todos los Props configurados."""
    bl_idname = "retarget.prop_create_all"
    bl_label = "Create All Prop Empties"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        created = 0
        for key, _ in PROP_SLOTS_CONFIG:
            prop_slot = _prop_slot_property(context.scene, key)
            if prop_slot and prop_slot.prop_object and not _get_prop_slot_empty(context, key):
                res = bpy.ops.retarget.prop_create_empty(slot=key)
                if 'FINISHED' in res:
                    created += 1

        if created == 0:
            self.report({'WARNING'}, "No se crearon Prop Empties (revisa los slots configurados).")
            return {'CANCELLED'}

        self.report({'INFO'}, f"Creados {created} Prop Empty(s).")
        return {'FINISHED'}


class RETARGET_OT_prop_clear_all(Operator):
    """Elimina todos los Prop Empties creados por el módulo de Props."""
    bl_idname = "retarget.prop_clear_all"
    bl_label = "Delete All Empties"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        removed = 0
        for key, _ in PROP_SLOTS_CONFIG:
            if _remove_prop_empty_if_owned(context, key):
                removed += 1

            prop_slot = _prop_slot_property(context.scene, key)
            if prop_slot:
                prop_slot.empty_name = ""
                prop_slot.created = False

        _remove_props_collection_if_unused()

        self.report({'INFO'}, f"{removed} Prop Empty(s) eliminados.")
        return {'FINISHED'}


class RETARGET_OT_prop_clear_empties_constraints(Operator):
    """Elimina las restricciones de los Prop Empties después de hacer Bake."""
    bl_idname = "retarget.prop_clear_empties_constraints"
    bl_label = "Clear Prop Empties Constraints"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        empties = _get_registered_prop_empties(context)
        cleared = 0
        for emp in empties:
            if emp.constraints:
                emp.constraints.clear()
                cleared += 1

        self.report({'INFO'}, f"Constraints eliminados en {cleared} Prop Empty(s).")
        return {'FINISHED'}


class RETARGET_OT_prop_bake_empties(Operator):
    """Selecciona los Prop Empties activos y abre Bake."""
    bl_idname = "retarget.prop_bake_empties"
    bl_label = "Select Prop Empties & Bake"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        empties = _get_registered_prop_empties(context)
        if not empties:
            self.report({'WARNING'}, "No hay Prop Empties activos para hornear.")
            return {'CANCELLED'}

        _ensure_object_mode(context)
        bpy.ops.object.select_all(action='DESELECT')
        for emp in empties:
            emp.select_set(True)
        context.view_layer.objects.active = empties[0]

        try:
            bpy.ops.nla.bake('INVOKE_DEFAULT', visual_keying=True, clear_constraints=False)
        except Exception:
            bpy.ops.object.bake_action('INVOKE_DEFAULT')

        return {'FINISHED'}


class RETARGET_OT_prop_apply_to_target(Operator):
    """Step 2: Aplica la animación de los Prop Empties al Target (Objeto o Hueso)."""
    bl_idname = "retarget.prop_apply_to_target"
    bl_label = "Empties → Prop (Apply)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        applied = 0

        for key, _ in PROP_SLOTS_CONFIG:
            prop_slot = _prop_slot_property(context.scene, key)
            if not prop_slot or not prop_slot.target_object:
                continue

            empty = _get_prop_slot_empty(context, key)
            if not empty:
                continue

            target_obj = prop_slot.target_object

            if prop_slot.target_type == 'BONE':
                if target_obj.type != 'ARMATURE' or not prop_slot.target_bone_name:
                    continue
                pose_bone = target_obj.pose.bones.get(prop_slot.target_bone_name)
                if not pose_bone:
                    continue

                _activate_armature_pose(context, target_obj)
                for c in list(pose_bone.constraints):
                    if c.type in {'COPY_LOCATION', 'COPY_ROTATION'} and c.target == empty:
                        pose_bone.constraints.remove(c)

                cl = pose_bone.constraints.new('COPY_LOCATION')
                cl.name = "RET_Prop Copy Location"
                cl.target = empty
                cl.owner_space = 'WORLD'
                cl.target_space = 'WORLD'

                cr = pose_bone.constraints.new('COPY_ROTATION')
                cr.name = "RET_Prop Copy Rotation"
                cr.target = empty
                cr.owner_space = 'WORLD'
                cr.target_space = 'WORLD'
                applied += 1
            else:
                _ensure_object_mode(context)
                for c in list(target_obj.constraints):
                    if c.type in {'COPY_LOCATION', 'COPY_ROTATION'} and c.target == empty:
                        target_obj.constraints.remove(c)

                cl = target_obj.constraints.new('COPY_LOCATION')
                cl.name = "RET_Prop Copy Location"
                cl.target = empty
                cl.owner_space = 'WORLD'
                cl.target_space = 'WORLD'

                cr = target_obj.constraints.new('COPY_ROTATION')
                cr.name = "RET_Prop Copy Rotation"
                cr.target = empty
                cr.owner_space = 'WORLD'
                cr.target_space = 'WORLD'
                applied += 1

        if applied == 0:
            self.report({'WARNING'}, "No hay pares válidos (Prop Empty + Target configurado).")
            return {'CANCELLED'}

        self.report({'INFO'}, f"Prop retarget aplicado a {applied} destino(s).")
        return {'FINISHED'}


class RETARGET_OT_prop_clear_target_constraints(Operator):
    """Elimina las restricciones de retarget aplicadas en los Targets de Props."""
    bl_idname = "retarget.prop_clear_target_constraints"
    bl_label = "Clear Target Constraints"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        prop_empty_names = {emp.name for emp in _get_registered_prop_empties(context)}
        cleared = 0

        for key, _ in PROP_SLOTS_CONFIG:
            prop_slot = _prop_slot_property(context.scene, key)
            if not prop_slot or not prop_slot.target_object:
                continue

            target_obj = prop_slot.target_object
            if prop_slot.target_type == 'BONE' and target_obj.type == 'ARMATURE':
                pose_bone = target_obj.pose.bones.get(prop_slot.target_bone_name)
                if pose_bone:
                    for c in list(pose_bone.constraints):
                        if (
                            c.type in {'COPY_LOCATION', 'COPY_ROTATION'}
                            and (
                                (c.target is not None and c.target.name in prop_empty_names)
                                or c.name.startswith("RET_Prop")
                            )
                        ):
                            pose_bone.constraints.remove(c)
                            cleared += 1
            else:
                for c in list(target_obj.constraints):
                    if (
                        c.type in {'COPY_LOCATION', 'COPY_ROTATION'}
                        and (
                            (c.target is not None and c.target.name in prop_empty_names)
                            or c.name.startswith("RET_Prop")
                        )
                    ):
                        target_obj.constraints.remove(c)
                        cleared += 1

        self.report({'INFO'}, f"Eliminadas {cleared} restricciones en los Targets de Prop.")
        return {'FINISHED'}


class RETARGET_OT_prop_select_target_and_bake(Operator):
    """Selecciona los Targets vinculados a Prop Empties (Objeto o Pose Bone) y abre Bake."""
    bl_idname = "retarget.prop_select_target_and_bake"
    bl_label = "Select Targets & Bake"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bone_entries = []
        object_entries = []

        for key, _ in PROP_SLOTS_CONFIG:
            prop_slot = _prop_slot_property(context.scene, key)
            if not prop_slot or not prop_slot.target_object:
                continue
            empty = _get_prop_slot_empty(context, key)
            if not empty:
                continue

            target_obj = prop_slot.target_object
            if prop_slot.target_type == 'BONE' and target_obj.type == 'ARMATURE':
                pb = target_obj.pose.bones.get(prop_slot.target_bone_name)
                b_data = target_obj.data.bones.get(prop_slot.target_bone_name)
                if pb and b_data:
                    bone_entries.append((target_obj, pb, b_data))
            else:
                object_entries.append(target_obj)

        if not bone_entries and not object_entries:
            self.report({'WARNING'}, "No se encontraron Targets válidos vinculados a Prop Empties.")
            return {'CANCELLED'}

        if bone_entries and object_entries:
            self.report(
                {'WARNING'},
                "Hay Targets mixtos (Objetos y Huesos). Hornea primero un tipo o desactiva temporalmente uno.",
            )
            return {'CANCELLED'}

        _ensure_object_mode(context)
        bpy.ops.object.select_all(action='DESELECT')

        if bone_entries:
            armatures = []
            for target_arm, _, _ in bone_entries:
                target_arm.select_set(True)
                if target_arm not in armatures:
                    armatures.append(target_arm)

            context.view_layer.objects.active = armatures[0]
            bpy.ops.object.mode_set(mode='POSE')

            for arm in armatures:
                for pb in arm.pose.bones:
                    pb.select = False

            for target_arm, pb, b_data in bone_entries:
                pb.select = True
                target_arm.data.bones.active = b_data
        else:
            for obj in object_entries:
                obj.select_set(True)
            context.view_layer.objects.active = object_entries[0]

        try:
            bpy.ops.nla.bake('INVOKE_DEFAULT', visual_keying=True, clear_constraints=False)
        except Exception:
            bpy.ops.object.bake_action('INVOKE_DEFAULT')

        return {'FINISHED'}


class RETARGET_OT_prop_clean_all(Operator):
    """Limpia constraints de props en Targets y borra los Prop Empties (conserva curvas)."""
    bl_idname = "retarget.prop_clean_all"
    bl_label = "Clean Prop Setup"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        prop_empties = _get_registered_prop_empties(context)
        prop_empty_names = {e.name for e in prop_empties}

        constraints_removed = 0
        for key, _ in PROP_SLOTS_CONFIG:
            prop_slot = _prop_slot_property(context.scene, key)
            if not prop_slot or not prop_slot.target_object:
                continue
            target_obj = prop_slot.target_object
            if target_obj.type == 'ARMATURE':
                for pb in target_obj.pose.bones:
                    for c in list(pb.constraints):
                        if (
                            c.type in {'COPY_LOCATION', 'COPY_ROTATION'}
                            and (
                                (c.target is not None and c.target.name in prop_empty_names)
                                or c.name.startswith("RET_Prop")
                            )
                        ):
                            pb.constraints.remove(c)
                            constraints_removed += 1
            for c in list(target_obj.constraints):
                if (
                    c.type in {'COPY_LOCATION', 'COPY_ROTATION'}
                    and (
                        (c.target is not None and c.target.name in prop_empty_names)
                        or c.name.startswith("RET_Prop")
                    )
                ):
                    target_obj.constraints.remove(c)
                    constraints_removed += 1

        empties_removed = 0
        for key, _ in PROP_SLOTS_CONFIG:
            if _remove_prop_empty_if_owned(context, key):
                empties_removed += 1
            prop_slot = _prop_slot_property(context.scene, key)
            if prop_slot:
                prop_slot.empty_name = ""
                prop_slot.created = False

        _remove_props_collection_if_unused()

        self.report(
            {'INFO'},
            f"Prop Setup limpiado: {constraints_removed} constraints y {empties_removed} Prop Empty(s) eliminados.",
        )
        return {'FINISHED'}


# ──────────────────────────────────────────────
# 5. PANELES (N SIDEBAR - MISMA PESTAÑA RETARGET)
# ──────────────────────────────────────────────
class RETARGET_PT_panel(Panel):
    bl_label = "Retarget → Empties"
    bl_idname = "RETARGET_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Retarget"
    bl_options = {'DEFAULT_CLOSED'}

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
                text="Asigna una Source Armature para el módulo principal.",
                icon='ERROR',
            )

        layout.separator()

        # --- DESPLEGABLE MAESTRO DE BONE SLOTS + SYMMETRIZE ---
        slots_container = layout.box()
        slots_header = slots_container.row(align=True)
        slots_tri = 'TRIA_DOWN' if scene.retarget_slots_expanded else 'TRIA_RIGHT'
        assigned_count = sum(
            1 for key, _, _ in SLOTS_CONFIG if _slot_property(scene, key).bone_name
        )
        slots_header.prop(
            scene,
            "retarget_slots_expanded",
            text=f"Bone Slots ({assigned_count}/{len(SLOTS_CONFIG)})",
            icon=slots_tri,
            emboss=False,
        )
        slots_header.operator(
            "retarget.symmetrize_bones",
            text="Symmetrize",
            icon='ARROW_LEFTRIGHT',
        )

        if scene.retarget_slots_expanded:
            for key, label, _ in SLOTS_CONFIG:
                slot_prop = _slot_property(scene, key)
                box = slots_container.box()

                row_head = box.row(align=True)
                icon_tri = 'TRIA_DOWN' if slot_prop.expanded else 'TRIA_RIGHT'
                row_head.prop(
                    slot_prop,
                    "expanded",
                    text=label,
                    icon=icon_tri,
                    emboss=False,
                )

                if slot_prop.bone_name:
                    row_head.label(text="", icon='CHECKMARK')

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
                        _get_slot_empty(
                            context,
                            armature,
                            key,
                            adopt_legacy=True,
                            allow_cross_armature=True,
                        )
                        if armature else None
                    )
                    create_row.label(
                        text="",
                        icon='CHECKMARK' if valid_empty else 'BLANK1',
                    )

        layout.separator()

        # --- PART 1: RIG -> EMPTIES ---
        part_one = layout.box()
        p1_head = part_one.row(align=True)
        p1_tri = 'TRIA_DOWN' if scene.retarget_part1_expanded else 'TRIA_RIGHT'
        p1_head.prop(
            scene,
            "retarget_part1_expanded",
            text="Part 1: Rig → Empties",
            icon=p1_tri,
            emboss=False,
        )
        p1_head.label(text="", icon='OUTLINER_OB_EMPTY')

        if scene.retarget_part1_expanded:
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

        reminder_box = layout.box()
        col_rem = reminder_box.column(align=True)
        col_rem.scale_y = 0.8
        col_rem.label(
            text="Remember to mute original animation",
            icon='INFO',
        )
        col_rem.label(
            text="strips/actions before starting Part 2.",
            icon='BLANK1',
        )

        layout.separator()

        # --- PART 2: EMPTIES -> RIG ---
        part_two = layout.box()
        p2_head = part_two.row(align=True)
        p2_tri = 'TRIA_DOWN' if scene.retarget_part2_expanded else 'TRIA_RIGHT'
        p2_head.prop(
            scene,
            "retarget_part2_expanded",
            text="Part 2: Empties → Rig",
            icon=p2_tri,
            emboss=False,
        )
        p2_head.label(text="", icon='ARMATURE_DATA')

        if scene.retarget_part2_expanded:
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

            part_two.separator()
            part_two.operator(
                "retarget.clean_curves_and_empties",
                icon='TRASH',
            )
            warn_col = part_two.column(align=True)
            warn_col.scale_y = 0.8
            warn_col.label(
                text="Warning: Location curves of joints",
                icon='ERROR',
            )
            warn_col.label(
                text="(Chest, Head, Elbows, Knees) will be deleted.",
                icon='BLANK1',
            )

        layout.separator()

        # --- PART 3: TORSO -> ROOT MOTION ---
        part_three = layout.box()
        p3_head = part_three.row(align=True)
        p3_tri = 'TRIA_DOWN' if scene.retarget_part3_expanded else 'TRIA_RIGHT'
        p3_head.prop(
            scene,
            "retarget_part3_expanded",
            text="Part 3: Torso → Root Motion",
            icon=p3_tri,
            emboss=False,
        )
        p3_head.label(text="", icon='ORIENTATION_GLOBAL')

        if scene.retarget_part3_expanded:
            root_slot = _slot_property(scene, "root_bone")
            row_root = part_three.row(align=True)
            if armature and armature.data:
                row_root.prop_search(
                    root_slot,
                    "bone_name",
                    armature.data,
                    "bones",
                    text="Root Bone",
                )
            else:
                row_root.prop(root_slot, "bone_name", text="Root Bone")

            pick_root = row_root.operator("retarget.pick_bone", icon='BONE_DATA', text="")
            pick_root.slot = "root_bone"

            sel_root = row_root.operator("retarget.select_bone_in_viewport", icon='ZOOM_ALL', text="")
            sel_root.slot = "root_bone"

            clr_root = row_root.operator("retarget.clear_slot", icon='X', text="")
            clr_root.slot = "root_bone"

            row_rm_create = part_three.row(align=True)
            row_rm_create.operator("retarget.create_root_empty", icon='EMPTY_ARROWS')
            valid_root_empty = (
                _get_slot_empty(
                    context,
                    armature,
                    "root_bone",
                    adopt_legacy=False,
                    allow_cross_armature=True,
                )
                if armature else None
            )
            row_rm_create.label(
                text="",
                icon='CHECKMARK' if valid_root_empty else 'BLANK1',
            )

            part_three.operator(
                "retarget.clear_root_constraints",
                icon='CONSTRAINT_BONE',
            )
            part_three.operator("retarget.bake_root_empty", icon='RENDER_ANIMATION')

            part_three.separator()
            rm_step_col = part_three.column(align=True)
            rm_step_col.scale_y = 0.8
            rm_step_col.label(
                text="Step 2 of 2: Clear Root Constraints",
                icon='INFO',
            )
            rm_step_col.label(
                text="before applying to Root Bone.",
                icon='BLANK1',
            )

            part_three.operator("retarget.apply_root_to_bone", icon='CON_LOCLIKE')
            part_three.operator("retarget.select_root_and_bake", icon='BONE_DATA')
            part_three.operator("retarget.clean_root_motion", icon='TRASH')

        layout.separator()

        clean_box = layout.box()
        clean_box.operator(
            "retarget.clean_all_setup",
            icon='TRASH',
        )
        info_col = clean_box.column(align=True)
        info_col.scale_y = 0.8
        info_col.label(
            text="Deletes all addon Empties & RET_ constraints.",
            icon='INFO',
        )
        info_col.label(
            text="Animation curves are preserved.",
            icon='BLANK1',
        )


class RETARGET_PT_props_subpanel(Panel):
    bl_label = "Prop → Empties"
    bl_idname = "RETARGET_PT_props_subpanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Retarget"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # --- DESPLEGABLE MAESTRO DE PROP SLOTS (ABIERTO POR DEFECTO) ---
        props_container = layout.box()
        props_header = props_container.row(align=True)
        props_tri = 'TRIA_DOWN' if scene.retarget_prop_slots_expanded else 'TRIA_RIGHT'
        assigned_props = sum(
            1 for key, _ in PROP_SLOTS_CONFIG if _prop_slot_property(scene, key).prop_object is not None
        )
        props_header.prop(
            scene,
            "retarget_prop_slots_expanded",
            text=f"Prop Slots ({assigned_props}/{len(PROP_SLOTS_CONFIG)})",
            icon=props_tri,
            emboss=False,
        )

        if scene.retarget_prop_slots_expanded:
            for key, default_label in PROP_SLOTS_CONFIG:
                prop_slot = _prop_slot_property(scene, key)
                box = props_container.box()

                display_title = (
                    f"{default_label}: {prop_slot.prop_label}"
                    if prop_slot.prop_label.strip()
                    else default_label
                )

                row_head = box.row(align=True)
                icon_tri = 'TRIA_DOWN' if prop_slot.expanded else 'TRIA_RIGHT'
                row_head.prop(
                    prop_slot,
                    "expanded",
                    text=display_title,
                    icon=icon_tri,
                    emboss=False,
                )

                valid_empty = _get_prop_slot_empty(context, key)
                if valid_empty:
                    row_head.label(text="", icon='CHECKMARK')

                clr_op = row_head.operator("retarget.prop_clear_slot", icon='X', text="")
                clr_op.slot = key

                if prop_slot.expanded:
                    box.prop(prop_slot, "prop_label", text="Name")

                    # --- ORIGEN (SOURCE) ---
                    box.prop(prop_slot, "source_type", text="Source")
                    box.prop(prop_slot, "prop_object", text="Prop Obj")

                    if prop_slot.source_type == 'BONE':
                        row_pbone = box.row(align=True)
                        if prop_slot.prop_object and prop_slot.prop_object.type == 'ARMATURE':
                            row_pbone.prop_search(
                                prop_slot,
                                "prop_bone_name",
                                prop_slot.prop_object.data,
                                "bones",
                                text="Prop Bone",
                            )
                        else:
                            row_pbone.prop(prop_slot, "prop_bone_name", text="Prop Bone")

                        pick_src_op = row_pbone.operator("retarget.prop_pick_source_bone", icon='BONE_DATA', text="")
                        pick_src_op.slot = key

                        sel_src_op = row_pbone.operator("retarget.prop_select_source_bone", icon='ZOOM_ALL', text="")
                        sel_src_op.slot = key

                    box.prop(prop_slot, "empty_name", text="Empty")

                    row_create = box.row()
                    c_op = row_create.operator("retarget.prop_create_empty", text="Create Prop Empty", icon='CUBE')
                    c_op.slot = key

                    box.separator()

                    # --- DESTINO (TARGET PARA STEP 2) ---
                    box.prop(prop_slot, "target_type", text="Target")
                    box.prop(prop_slot, "target_object", text="Target Obj")

                    if prop_slot.target_type == 'BONE':
                        row_tbone = box.row(align=True)
                        if prop_slot.target_object and prop_slot.target_object.type == 'ARMATURE':
                            row_tbone.prop_search(
                                prop_slot,
                                "target_bone_name",
                                prop_slot.target_object.data,
                                "bones",
                                text="Target Bone",
                            )
                        else:
                            row_tbone.prop(prop_slot, "target_bone_name", text="Target Bone")

                        pick_tgt_op = row_tbone.operator("retarget.prop_pick_target_bone", icon='BONE_DATA', text="")
                        pick_tgt_op.slot = key

                        sel_tgt_op = row_tbone.operator("retarget.prop_select_target_bone", icon='ZOOM_ALL', text="")
                        sel_tgt_op.slot = key

        layout.separator()

        # --- STEP 1: PROP -> EMPTIES (DESPLEGABLE, CERRADO POR DEFECTO) ---
        p1_box = layout.box()
        ps1_head = p1_box.row(align=True)
        ps1_tri = 'TRIA_DOWN' if scene.retarget_prop_step1_expanded else 'TRIA_RIGHT'
        ps1_head.prop(
            scene,
            "retarget_prop_step1_expanded",
            text="Step 1: Prop → Empties",
            icon=ps1_tri,
            emboss=False,
        )
        ps1_head.label(text="", icon='OUTLINER_OB_EMPTY')

        if scene.retarget_prop_step1_expanded:
            row_p_btns = p1_box.row(align=True)
            row_p_btns.operator("retarget.prop_create_all", icon='ADD')
            row_p_btns.operator("retarget.prop_clear_all", icon='REMOVE')
            p1_box.operator("retarget.prop_clear_empties_constraints", icon='CONSTRAINT_BONE')
            p1_box.operator("retarget.prop_bake_empties", icon='RENDER_ANIMATION')

        layout.separator()

        # --- ADVERTENCIA INTERMEDIA (MUTE ORIGINAL STRIPS/ACTIONS) ---
        prop_reminder_box = layout.box()
        col_prem = prop_reminder_box.column(align=True)
        col_prem.scale_y = 0.8
        col_prem.label(
            text="Remember to mute original prop animation",
            icon='INFO',
        )
        col_prem.label(
            text="strips/actions before starting Step 2.",
            icon='BLANK1',
        )

        layout.separator()

        # --- STEP 2: EMPTIES -> PROP / TARGET (DESPLEGABLE, CERRADO POR DEFECTO) ---
        p2_box = layout.box()
        ps2_head = p2_box.row(align=True)
        ps2_tri = 'TRIA_DOWN' if scene.retarget_prop_step2_expanded else 'TRIA_RIGHT'
        ps2_head.prop(
            scene,
            "retarget_prop_step2_expanded",
            text="Step 2: Empties → Prop",
            icon=ps2_tri,
            emboss=False,
        )
        ps2_head.label(text="", icon='ARMATURE_DATA')

        if scene.retarget_prop_step2_expanded:
            p2_box.operator("retarget.prop_apply_to_target", icon='CON_LOCLIKE')
            p2_box.operator("retarget.prop_clear_target_constraints", icon='X')
            p2_box.operator("retarget.prop_select_target_and_bake", icon='RENDER_ANIMATION')

        layout.separator()

        # --- LIMPIEZA FINAL PROPS ---
        clean_p_box = layout.box()
        clean_p_box.operator("retarget.prop_clean_all", icon='TRASH')
        info_p = clean_p_box.column(align=True)
        info_p.scale_y = 0.8
        info_p.label(text="Removes Prop Empties & RET_Prop constraints.", icon='INFO')
        info_p.label(text="Preserves baked animation curves.", icon='BLANK1')


# ──────────────────────────────────────────────
# 6. REGISTRO
# ──────────────────────────────────────────────
classes = (
    RETargetSlot,
    RETargetPropSlot,
    RETARGET_OT_symmetrize_bones,
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
    RETARGET_OT_create_root_empty,
    RETARGET_OT_clear_root_constraints,
    RETARGET_OT_bake_root_empty,
    RETARGET_OT_apply_root_to_bone,
    RETARGET_OT_select_root_and_bake,
    RETARGET_OT_clean_root_motion,
    RETARGET_OT_clean_curves_and_empties,
    RETARGET_OT_clean_all_setup,
    RETARGET_OT_clear_all,
    RETARGET_OT_prop_pick_source_bone,
    RETARGET_OT_prop_select_source_bone,
    RETARGET_OT_prop_pick_target_bone,
    RETARGET_OT_prop_select_target_bone,
    RETARGET_OT_prop_clear_slot,
    RETARGET_OT_prop_create_empty,
    RETARGET_OT_prop_create_all,
    RETARGET_OT_prop_clear_all,
    RETARGET_OT_prop_clear_empties_constraints,
    RETARGET_OT_prop_bake_empties,
    RETARGET_OT_prop_apply_to_target,
    RETARGET_OT_prop_clear_target_constraints,
    RETARGET_OT_prop_select_target_and_bake,
    RETARGET_OT_prop_clean_all,
    RETARGET_PT_panel,
    RETARGET_PT_props_subpanel,
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