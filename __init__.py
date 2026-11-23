import json
import os
import bpy
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import PropertyGroup, Panel, Operator


# ──────────────────────────────────────────────
# 1. SLOT CONFIGURATION (CHARACTER & PROPS)
# ──────────────────────────────────────────────
# True  = preserves Location + Rotation (hands, feet, and torso).
# False = removes Location only (joints).
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
BUILTIN_BONE_PRESETS = {
    "RIGIFY_CTRL": {
        "label": "Rigify (Controls)",
        "bones": {
            "left_hand": ["hand_ik.L", "hand_fk.L", "hand.L"],
            "right_hand": ["hand_ik.R", "hand_fk.R", "hand.R"],
            "left_foot": ["foot_ik.L", "foot_fk.L", "foot.L"],
            "right_foot": ["foot_ik.R", "foot_fk.R", "foot.R"],
            "torso": ["torso", "hips"],
            "chest": ["chest", "spine_fk.003", "spine_fk.002"],
            "head": ["head"],
            "left_elbow": ["upper_arm_fk.L", "forearm_fk.L", "elbow_target.L"],
            "right_elbow": ["upper_arm_fk.R", "forearm_fk.R", "elbow_target.R"],
            "left_knee": ["thigh_fk.L", "shin_fk.L", "knee_target.L"],
            "right_knee": ["thigh_fk.R", "shin_fk.R", "knee_target.R"],
            "root_bone": ["root"],
        },
    },
    "METARIG_DEF": {
        "label": "Metarig / Deform",
        "bones": {
            "left_hand": ["hand.L", "DEF-hand.L"],
            "right_hand": ["hand.R", "DEF-hand.R"],
            "left_foot": ["foot.L", "DEF-foot.L"],
            "right_foot": ["foot.R", "DEF-foot.R"],
            "torso": ["spine", "DEF-spine"],
            "chest": ["spine.003", "chest", "DEF-spine.003", "DEF-chest"],
            "head": ["spine.006", "head", "DEF-spine.006", "DEF-head"],
            "left_elbow": ["forearm.L", "DEF-forearm.L"],
            "right_elbow": ["forearm.R", "DEF-forearm.R"],
            "left_knee": ["shin.L", "DEF-shin.L"],
            "right_knee": ["shin.R", "DEF-shin.R"],
            "root_bone": ["root"],
        },
    },
    "AUTO_RIG_PRO": {
        "label": "Auto-Rig Pro",
        "bones": {
            "left_hand": ["c_hand_ik.l", "c_hand_fk.l", "hand.l"],
            "right_hand": ["c_hand_ik.r", "c_hand_fk.r", "hand.r"],
            "left_foot": ["c_foot_ik.l", "c_foot_fk.l", "foot.l"],
            "right_foot": ["c_foot_ik.r", "c_foot_fk.r", "foot.r"],
            "torso": ["c_root_master.x", "c_hips.x", "hips.x"],
            "chest": ["c_chest.x", "chest.x", "c_spine_02.x"],
            "head": ["c_head.x", "head.x"],
            "left_elbow": ["c_arm_fk.l", "c_forearm_fk.l", "c_arms_pole.l"],
            "right_elbow": ["c_arm_fk.r", "c_forearm_fk.r", "c_arms_pole.r"],
            "left_knee": ["c_leg_fk.l", "c_shin_fk.l", "c_legs_pole.l"],
            "right_knee": ["c_leg_fk.r", "c_shin_fk.r", "c_legs_pole.r"],
            "root_bone": ["root.x", "c_pos.x", "root"],
        },
    },
    "MIXAMO": {
        "label": "Mixamo",
        "bones": {
            "left_hand": ["mixamorig:LeftHand", "LeftHand"],
            "right_hand": ["mixamorig:RightHand", "RightHand"],
            "left_foot": ["mixamorig:LeftFoot", "LeftFoot"],
            "right_foot": ["mixamorig:RightFoot", "RightFoot"],
            "torso": ["mixamorig:Hips", "Hips"],
            "chest": ["mixamorig:Spine2", "Spine2", "mixamorig:Chest", "Chest"],
            "head": ["mixamorig:Head", "Head"],
            "left_elbow": ["mixamorig:LeftForeArm", "LeftForeArm"],
            "right_elbow": ["mixamorig:RightForeArm", "RightForeArm"],
            "left_knee": ["mixamorig:LeftLeg", "LeftLeg"],
            "right_knee": ["mixamorig:RightLeg", "RightLeg"],
            "root_bone": ["mixamorig:Hips", "root", "Hips"],
        },
    },
    "UE_MANNEQUIN": {
        "label": "UE Mannequin",
        "bones": {
            "left_hand": ["hand_l", "ik_hand_l"],
            "right_hand": ["hand_r", "ik_hand_r"],
            "left_foot": ["foot_l", "ik_foot_l"],
            "right_foot": ["foot_r", "ik_foot_r"],
            "torso": ["pelvis"],
            "chest": ["spine_03", "spine_05"],
            "head": ["head"],
            "left_elbow": ["lowerarm_l"],
            "right_elbow": ["lowerarm_r"],
            "left_knee": ["calf_l"],
            "right_knee": ["calf_r"],
            "root_bone": ["root"],
        },
    },
}

_CUSTOM_PRESETS_CACHE = None


def _get_custom_presets_filepath():
    config_dir = bpy.utils.user_resource('CONFIG', create=True)
    return os.path.join(config_dir, "retarget_empties_presets.json")


def _load_custom_presets(force_reload=False):
    global _CUSTOM_PRESETS_CACHE
    if _CUSTOM_PRESETS_CACHE is not None and not force_reload:
        return _CUSTOM_PRESETS_CACHE

    filepath = _get_custom_presets_filepath()
    if not os.path.exists(filepath):
        _CUSTOM_PRESETS_CACHE = {}
        return _CUSTOM_PRESETS_CACHE

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            _CUSTOM_PRESETS_CACHE = data
        else:
            _CUSTOM_PRESETS_CACHE = {}
    except Exception:
        _CUSTOM_PRESETS_CACHE = {}

    return _CUSTOM_PRESETS_CACHE


def _save_custom_presets(presets_dict):
    global _CUSTOM_PRESETS_CACHE
    _CUSTOM_PRESETS_CACHE = presets_dict
    filepath = _get_custom_presets_filepath()
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(presets_dict, f, indent=2, ensure_ascii=False)


def _get_all_presets():
    merged = {}
    for key, val in BUILTIN_BONE_PRESETS.items():
        merged[key] = {
            "label": val["label"],
            "bones": dict(val["bones"]),
            "builtin": True,
        }
    custom = _load_custom_presets()
    for key, val in custom.items():
        if isinstance(val, dict) and "bones" in val:
            merged[key] = {
                "label": val.get("label", key),
                "bones": dict(val["bones"]),
                "builtin": False,
            }
    return merged


def _preset_enum_items(self, context):
    items = [
        ('AUTO', "Auto-Detect (Best Match)", "Automatically detects the best-matching rig preset"),
    ]
    all_presets = _get_all_presets()
    for key, info in all_presets.items():
        tag = "" if info.get("builtin") else " [Custom]"
        items.append((key, f"{info['label']}{tag}", f"Apply preset {info['label']}"))
    return items


def _score_preset_for_armature(armature, preset_bones):
    if armature is None or armature.type != 'ARMATURE' or not armature.data:
        return 0
    score = 0
    for slot_key, candidates in preset_bones.items():
        if isinstance(candidates, str):
            candidates = [candidates]
        for cand in candidates:
            if _get_bone(armature, cand) is not None:
                score += 1
                break
    return score


def _heuristic_find_bone(armature, slot_key):
    """Heuristic fallback search by keywords and side."""
    if armature is None or armature.type != 'ARMATURE' or not armature.data:
        return None

    side_tokens = {
        "left": ("left", ".l", "_l", "-l", "l_"),
        "right": ("right", ".r", "_r", "-r", "r_"),
    }

    want_side = None
    if slot_key.startswith("left_"):
        want_side = "left"
    elif slot_key.startswith("right_"):
        want_side = "right"

    keywords_map = {
        "left_hand": ("hand", "wrist"),
        "right_hand": ("hand", "wrist"),
        "left_foot": ("foot", "ankle"),
        "right_foot": ("foot", "ankle"),
        "torso": ("torso", "hips", "pelvis", "cog"),
        "chest": ("chest", "thorax", "spine_03", "spine_02", "spine2"),
        "head": ("head",),
        "left_elbow": ("forearm", "lowerarm", "elbow"),
        "right_elbow": ("forearm", "lowerarm", "elbow"),
        "left_knee": ("shin", "calf", "lowerleg", "knee"),
        "right_knee": ("shin", "calf", "lowerleg", "knee"),
        "root_bone": ("root",),
    }

    keywords = keywords_map.get(slot_key, ())
    if not keywords:
        return None

    for bone in armature.data.bones:
        b_low = bone.name.lower()
        if any(skip in b_low for skip in ("twist", "adj", "corrective", "finger", "toe", "eye", "jaw")):
            continue

        if want_side == "left":
            has_left = any(tok in b_low for tok in side_tokens["left"]) or b_low.endswith("l")
            has_right = any(tok in b_low for tok in side_tokens["right"])
            if not has_left or has_right:
                continue
        elif want_side == "right":
            has_right = any(tok in b_low for tok in side_tokens["right"]) or b_low.endswith("r")
            has_left = any(tok in b_low for tok in side_tokens["left"])
            if not has_right or has_left:
                continue

        if any(kw in b_low for kw in keywords):
            return bone.name

    return None


def _apply_preset_to_armature(context, armature, preset_key, overwrite=False, use_heuristic_fallback=True):
    """Applies a preset (or Auto-Detect) to the active armature slots."""
    scene = context.scene
    all_presets = _get_all_presets()

    chosen_key = preset_key
    chosen_label = ""
    preset_bones = {}

    if preset_key == 'AUTO':
        best_key = None
        best_score = 0
        for key, info in all_presets.items():
            sc = _score_preset_for_armature(armature, info["bones"])
            if sc > best_score:
                best_score = sc
                best_key = key
        if best_key is not None and best_score > 0:
            chosen_key = best_key
            chosen_label = all_presets[best_key]["label"]
            preset_bones = all_presets[best_key]["bones"]
        else:
            chosen_label = "Heuristic Auto-Search"
    else:
        info = all_presets.get(preset_key)
        if not info:
            return 0, "Unknown"
        chosen_label = info["label"]
        preset_bones = info["bones"]

    assigned = 0

    for slot_key in _all_character_slot_keys():
        slot_prop = _slot_property(scene, slot_key)
        if slot_prop is None:
            continue
        if slot_prop.bone_name and not overwrite:
            continue

        candidates = preset_bones.get(slot_key, [])
        if isinstance(candidates, str):
            candidates = [candidates]

        matched_name = None
        for cand in candidates:
            bone = _get_bone(armature, cand)
            if bone is not None:
                matched_name = bone.name
                break

        if matched_name is None and use_heuristic_fallback:
            matched_name = _heuristic_find_bone(armature, slot_key)

        if matched_name:
            slot_prop.bone_name = matched_name
            if not slot_prop.empty_name:
                if slot_key == "root_bone":
                    slot_prop.empty_name = "RET_Root_Motion"
                else:
                    slot_prop.empty_name = f"RET_{slot_key.replace('_', ' ').title()}"
            assigned += 1

    # Complete symmetry if any pair remained incomplete
    for left_key, right_key in SYMMETRY_PAIRS:
        left_slot = _slot_property(scene, left_key)
        right_slot = _slot_property(scene, right_key)
        if left_slot.bone_name and not right_slot.bone_name:
            sym = _find_symmetric_bone_name(armature, left_slot.bone_name)
            if sym:
                right_slot.bone_name = sym
                if not right_slot.empty_name:
                    right_slot.empty_name = f"RET_{right_key.replace('_', ' ').title()}"
                assigned += 1
        elif right_slot.bone_name and not left_slot.bone_name:
            sym = _find_symmetric_bone_name(armature, right_slot.bone_name)
            if sym:
                left_slot.bone_name = sym
                if not left_slot.empty_name:
                    left_slot.empty_name = f"RET_{left_key.replace('_', ' ').title()}"
                assigned += 1

    return assigned, chosen_label


BONE_MAP_PROP = "_retarget_bone_map"
_SYNCING_BONE_MAP = False


def _all_character_slot_keys():
    keys = [key for key, _, _ in SLOTS_CONFIG]
    keys.append("root_bone")
    return keys


def _get_armature_bone_map_dict(armature):
    if armature is None or armature.type != 'ARMATURE':
        return {}
    raw = armature.get(BONE_MAP_PROP)
    if raw is None:
        return {}
    try:
        return dict(raw)
    except Exception:
        return {}


def _save_slot_bone_to_armature(armature, slot_key, bone_name):
    if armature is None or armature.type != 'ARMATURE':
        return
    if slot_key not in _all_character_slot_keys():
        return
    mapping = _get_armature_bone_map_dict(armature)
    if bone_name:
        mapping[slot_key] = bone_name
    else:
        mapping.pop(slot_key, None)
    armature[BONE_MAP_PROP] = mapping


def _sync_scene_bones_from_armature(scene, armature):
    """Loads saved bone names for this Armature into the scene slots."""
    global _SYNCING_BONE_MAP
    _SYNCING_BONE_MAP = True
    try:
        mapping = _get_armature_bone_map_dict(armature)
        for key in _all_character_slot_keys():
            slot_prop = _slot_property(scene, key)
            if slot_prop is None:
                continue
            saved_bone = mapping.get(key, "") if armature is not None else ""
            if slot_prop.bone_name != saved_bone:
                slot_prop.bone_name = saved_bone
    finally:
        _SYNCING_BONE_MAP = False


def _on_slot_bone_name_updated(self, context):
    if _SYNCING_BONE_MAP or context is None or context.scene is None:
        return
    armature = context.scene.retarget_armature
    if armature is None or armature.type != 'ARMATURE':
        return
    for key in _all_character_slot_keys():
        if _slot_property(context.scene, key) == self:
            _save_slot_bone_to_armature(armature, key, self.bone_name)
            break


def _on_source_armature_updated(self, context):
    if context is None:
        return
    _sync_scene_bones_from_armature(self, self.retarget_armature)


# ──────────────────────────────────────────────
# 2. PROPERTY GROUPS & SCENE PROPERTIES
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
        description="Name of the bone assigned to this slot",
        default="",
        update=_on_slot_bone_name_updated,
    )
    empty_name: StringProperty(
        name="Empty Name",
        description="Empty exclusively associated with this slot",
        default="",
    )
    created: BoolProperty(name="Created", default=False)
    expanded: BoolProperty(
        name="Expanded",
        description="Show/Hide section",
        default=False,
    )


class RETargetPropSlot(PropertyGroup):
    prop_label: StringProperty(
        name="Label",
        description="Custom prop name (e.g., Door, Sword, Rifle)",
        default="",
    )
    source_type: EnumProperty(
        name="Source Type",
        description="Animated source type for the prop",
        items=[
            ('OBJECT', "Object / Mesh", "Directly animated object (door, weapon, unrigged accessory)"),
            ('BONE', "Armature Bone", "Specific bone inside a Rig/Armature"),
        ],
        default='OBJECT',
    )
    prop_object: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Prop Object",
        description="Source Object or Armature for the prop",
        poll=poll_prop_source_object,
    )
    prop_bone_name: StringProperty(
        name="Prop Bone",
        description="Source bone for the prop (when Source is Armature Bone)",
        default="",
    )
    target_type: EnumProperty(
        name="Target Type",
        description="Target type to receive the motion in Step 2",
        items=[
            ('OBJECT', "Object / Mesh", "Transfer motion directly to an Object"),
            ('BONE', "Armature Bone", "Transfer motion to an Armature bone"),
        ],
        default='BONE',
    )
    target_object: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Target Object",
        description="Target Object or Armature for Step 2",
        poll=poll_prop_target_object,
    )
    target_bone_name: StringProperty(
        name="Target Bone",
        description="Target bone inside Target Object (when Target is Armature Bone)",
        default="",
    )
    empty_name: StringProperty(
        name="Empty Name",
        description="Intermediate Empty for this prop",
        default="",
    )
    created: BoolProperty(name="Created", default=False)
    expanded: BoolProperty(
        name="Expanded",
        description="Show/Hide prop section",
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

    # Master list dropdowns (expanded by default)
    scene.retarget_slots_expanded = BoolProperty(
        name="Bone Slots",
        description="Show/Hide bone slots list",
        default=True,
    )
    scene.retarget_prop_slots_expanded = BoolProperty(
        name="Prop Slots",
        description="Show/Hide prop slots list",
        default=True,
    )

    # Module 1: Retarget <-> Empties (Steps 1 & 2)
    scene.retarget_m1_step1_expanded = BoolProperty(
        name="Step 1: Rig → Empties",
        description="Show/Hide Module 1 Step 1 (Rig → Empties)",
        default=False,
    )
    scene.retarget_m1_step2_expanded = BoolProperty(
        name="Step 2: Empties → Rig",
        description="Show/Hide Module 1 Step 2 (Empties → Rig)",
        default=False,
    )

    # Module 2: Torso -> Root Motion (Steps 1 & 2)
    scene.retarget_m2_expanded = BoolProperty(
        name="Module 2: Torso → Root Motion",
        description="Show/Hide Module 2 (Torso → Root Motion)",
        default=False,
    )
    scene.retarget_m2_step1_expanded = BoolProperty(
        name="Step 1: Torso → Empty",
        description="Show/Hide Module 2 Step 1 (Torso → Empty)",
        default=False,
    )
    scene.retarget_m2_step2_expanded = BoolProperty(
        name="Step 2: Empty → Root Bone",
        description="Show/Hide Module 2 Step 2 (Empty → Root Bone)",
        default=False,
    )

    # Module 3: Prop -> Empties (Steps 1 & 2)
    scene.retarget_m3_step1_expanded = BoolProperty(
        name="Step 1: Prop → Empties",
        description="Show/Hide Module 3 Step 1 (Prop → Empties)",
        default=False,
    )
    scene.retarget_m3_step2_expanded = BoolProperty(
        name="Step 2: Empties → Prop",
        description="Show/Hide Module 3 Step 2 (Empties → Prop)",
        default=False,
    )

    scene.retarget_armature = bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Source Armature",
        description="Source armature used by Module 1 and Module 2",
        poll=poll_armature,
        update=_on_source_armature_updated,
    )

    scene.retarget_preset = EnumProperty(
        name="Rig Preset",
        description="Bone preset or auto-detection for Source Armature",
        items=_preset_enum_items,
    )
    scene.retarget_preset_overwrite = BoolProperty(
        name="Overwrite",
        description="Overwrite slots that already have a bone assigned",
        default=False,
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
        "retarget_m1_step1_expanded",
        "retarget_m1_step2_expanded",
        "retarget_m2_expanded",
        "retarget_m2_step1_expanded",
        "retarget_m2_step2_expanded",
        "retarget_m3_step1_expanded",
        "retarget_m3_step2_expanded",
        "retarget_armature",
        "retarget_preset",
        "retarget_preset_overwrite",
    )
    for prop_name in extra_props:
        if hasattr(scene, prop_name):
            delattr(scene, prop_name)

    for key, _ in PROP_SLOTS_CONFIG:
        prop_name = f"retarget_{key}"
        if hasattr(scene, prop_name):
            delattr(scene, prop_name)


# ──────────────────────────────────────────────
# 3. HELPER FUNCTIONS (MODULE 1 & MODULE 2)
# ──────────────────────────────────────────────
def _get_armature(context):
    """Returns the Source Armature for Module 1 and Module 2."""
    armature = context.scene.retarget_armature

    if armature is None or armature.type != 'ARMATURE':
        return None

    return armature


def _validate_armature(context, operator):
    armature = _get_armature(context)

    if armature is None:
        operator.report(
            {'ERROR'},
            "Assign a valid Source Armature before using this operator.",
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
    """Finds the symmetric bone name using Blender flip_name and common naming conventions."""
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
    """Activates the designated armature and switches it to Pose Mode."""
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


def _remove_slot_empty_any_armature(context, armature, slot_key):
    """Removes the slot's registered Empty even if it belongs to another source armature."""
    empty = _get_slot_empty(
        context,
        armature,
        slot_key,
        adopt_legacy=True,
        allow_cross_armature=True,
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
# 3.5. HELPER FUNCTIONS (MODULE 3: PROPS)
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
# 4. OPERATORS (MODULE 1: RETARGET <-> EMPTIES)
# ──────────────────────────────────────────────
class RETARGET_OT_apply_bone_preset(Operator):
    """Applies the selected preset (or Auto-Detect) to populate Source Armature bones."""
    bl_idname = "retarget.apply_bone_preset"
    bl_label = "Auto-Fill / Apply Preset"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        armature = _validate_armature(context, self)
        if not armature:
            return {'CANCELLED'}

        scene = context.scene
        preset_key = scene.retarget_preset
        overwrite = scene.retarget_preset_overwrite

        assigned, label = _apply_preset_to_armature(
            context,
            armature,
            preset_key,
            overwrite=overwrite,
            use_heuristic_fallback=(preset_key == 'AUTO'),
        )

        if assigned == 0:
            self.report(
                {'WARNING'},
                f"No new bones were assigned using '{label}' (enable Overwrite to replace existing assignments).",
            )
            return {'CANCELLED'}

        self.report(
            {'INFO'},
            f"Preset '{label}': {assigned} bone(s) assigned in '{armature.name}'.",
        )
        return {'FINISHED'}


class RETARGET_OT_save_custom_preset(Operator):
    """Saves the current Source Armature bone configuration as a reusable preset."""
    bl_idname = "retarget.save_custom_preset"
    bl_label = "Save Bone Preset"
    bl_options = {'REGISTER', 'UNDO'}

    preset_name: StringProperty(
        name="Preset Name",
        description="Name used to identify this bone preset",
        default="My Custom Rig",
    )

    def invoke(self, context, event):
        armature = _validate_armature(context, self)
        if not armature:
            return {'CANCELLED'}
        self.preset_name = f"{armature.name}_Preset"
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        scene = context.scene
        clean_label = self.preset_name.strip()
        if not clean_label:
            self.report({'ERROR'}, "Enter a valid name for the preset.")
            return {'CANCELLED'}

        bones_dict = {}
        for slot_key in _all_character_slot_keys():
            slot_prop = _slot_property(scene, slot_key)
            if slot_prop and slot_prop.bone_name:
                bones_dict[slot_key] = [slot_prop.bone_name]

        if not bones_dict:
            self.report({'ERROR'}, "Assign at least one bone before saving a preset.")
            return {'CANCELLED'}

        safe_key = "CUSTOM_" + "".join(
            ch if ch.isalnum() else "_" for ch in clean_label.upper()
        ).strip("_")
        if not safe_key or safe_key == "CUSTOM_":
            safe_key = "CUSTOM_USER_PRESET"

        custom_presets = dict(_load_custom_presets())
        custom_presets[safe_key] = {
            "label": clean_label,
            "bones": bones_dict,
        }
        _save_custom_presets(custom_presets)

        try:
            scene.retarget_preset = safe_key
        except Exception:
            pass

        self.report(
            {'INFO'},
            f"Preset '{clean_label}' saved with {len(bones_dict)} bone(s).",
        )
        return {'FINISHED'}


class RETARGET_OT_delete_custom_preset(Operator):
    """Deletes the currently selected custom preset."""
    bl_idname = "retarget.delete_custom_preset"
    bl_label = "Delete Custom Preset"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        preset_key = scene.retarget_preset
        if preset_key == 'AUTO' or preset_key in BUILTIN_BONE_PRESETS:
            self.report({'WARNING'}, "Only custom presets ([Custom]) can be deleted.")
            return {'CANCELLED'}

        custom_presets = dict(_load_custom_presets())
        if preset_key not in custom_presets:
            self.report({'WARNING'}, "The selected preset does not exist in custom presets.")
            return {'CANCELLED'}

        removed_label = custom_presets[preset_key].get("label", preset_key)
        del custom_presets[preset_key]
        _save_custom_presets(custom_presets)

        scene.retarget_preset = 'AUTO'
        self.report({'INFO'}, f"Custom preset '{removed_label}' deleted.")
        return {'FINISHED'}


class RETARGET_OT_symmetrize_bones(Operator):
    """Automatically finds and assigns symmetric bones for Hands, Feet, Elbows, and Knees."""
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
                "Assign at least one side (Left or Right) in Hands, Feet, Elbows, or Knees to symmetrize.",
            )
            return {'CANCELLED'}

        if not_found:
            self.report(
                {'INFO'},
                f"Symmetrized: {filled} bone(s). No match found for: {', '.join(not_found)}.",
            )
        else:
            self.report({'INFO'}, f"Symmetrized: {filled} bone(s) completed.")

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
            self.report({'ERROR'}, "Invalid slot.")
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
                "Select a bone on Source Armature in Pose Mode.",
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

        self.report({'INFO'}, f"Bone captured: {bone_name}")
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
            self.report({'ERROR'}, "This slot has no bone assigned.")
            return {'CANCELLED'}

        bone = _get_bone(armature, slot_prop.bone_name)
        if bone is None:
            self.report(
                {'ERROR'},
                f"Bone '{slot_prop.bone_name}' not found in Source Armature.",
            )
            return {'CANCELLED'}

        try:
            _activate_armature_pose(context, armature)
        except Exception as exc:
            self.report({'ERROR'}, f"Could not activate Source Armature: {exc}")
            return {'CANCELLED'}

        for pose_bone in armature.pose.bones:
            pose_bone.select = False

        pose_bone = armature.pose.bones.get(bone.name)
        if pose_bone:
            pose_bone.select = True
            armature.data.bones.active = bone

        self.report({'INFO'}, f"Bone selected: {bone.name}")
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
            self.report({'ERROR'}, "Invalid slot.")
            return {'CANCELLED'}

        removed = _remove_empty_if_owned(context, armature, self.slot)

        slot_prop.bone_name = ""
        slot_prop.empty_name = ""
        slot_prop.created = False

        _remove_empty_collection_if_unused()

        self.report(
            {'INFO'},
            "Slot cleared. " + (
                "Associated Empty deleted." if removed
                else "No Empty belonging to another armature was deleted."
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
            self.report({'ERROR'}, "No valid bone is assigned to this slot.")
            return {'CANCELLED'}

        bone = _get_bone(armature, slot_prop.bone_name)
        if bone is None:
            self.report(
                {'ERROR'},
                f"Bone '{slot_prop.bone_name}' not found in Source Armature.",
            )
            return {'CANCELLED'}

        existing = _get_slot_empty(
            context, armature, self.slot, adopt_legacy=True, allow_cross_armature=False
        )
        if existing:
            self.report({'WARNING'}, f"This slot already has the Empty '{existing.name}'.")
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
            self.report({'ERROR'}, "Corresponding Pose Bone not found.")
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

        self.report({'INFO'}, f"Empty created: {empty.name}")
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
                f"No Empties were created. Skipped: {skipped}; failed: {failed}.",
            )
            return {'CANCELLED'}

        self.report(
            {'INFO'},
            f"Empties created: {created}; skipped: {skipped}; failed: {failed}.",
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
            f"Constraints removed from {cleared} Empty(s).",
        )
        return {'FINISHED'}


class RETARGET_OT_select_and_open_bake(Operator):
    """Selects registered Empties and opens the Bake dialog."""
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
                "No valid Empties are assigned to Source Armature slots.",
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
                f"Selected {len(empties)} Empty(s) from '{armature.name}'.",
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
            self.report({'ERROR'}, f"Could not prepare Bake: {exc}")
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
                "No valid bone/Empty pairs found for this Source Armature.",
            )
            return {'CANCELLED'}

        try:
            _activate_armature_pose(context, armature)
        except Exception as exc:
            self.report({'ERROR'}, f"Could not activate Source Armature: {exc}")
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
            f"Retarget constraints applied to {applied} bone(s) in '{armature.name}'.",
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
            self.report({'ERROR'}, f"Could not activate Source Armature: {exc}")
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
                "No active bones with a valid Empty were found to select in Pose Mode.",
            )
            return {'CANCELLED'}

        self.report(
            {'INFO'},
            f"'{armature.name}' is in Pose Mode with {selected_bones} bone(s) selected and ready to Bake.",
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
                self.report({'ERROR'}, f"Could not open the Bake menu: {exc}")
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
            self.report({'ERROR'}, f"Could not activate Source Armature: {exc}")
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
            f"Removed {cleared} constraint(s) from '{armature.name}'.",
        )
        return {'FINISHED'}


# ──────────────────────────────────────────────
# 4.5. MODULE 2 OPERATORS: TORSO -> ROOT MOTION
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
            self.report({'ERROR'}, "Assign the Root Bone in Module 2 first.")
            return {'CANCELLED'}

        if not torso_slot or not torso_slot.bone_name:
            self.report({'ERROR'}, "Assign the Torso bone in Bone Slots first.")
            return {'CANCELLED'}

        root_bone = _get_bone(armature, root_slot.bone_name)
        torso_bone = _get_bone(armature, torso_slot.bone_name)

        if not root_bone:
            self.report({'ERROR'}, f"Root bone '{root_slot.bone_name}' not found in Source Armature.")
            return {'CANCELLED'}

        if not torso_bone:
            self.report({'ERROR'}, f"Torso bone '{torso_slot.bone_name}' not found in Source Armature.")
            return {'CANCELLED'}

        existing = _get_slot_empty(context, armature, "root_bone", adopt_legacy=False)
        if existing:
            self.report({'WARNING'}, f"Root Motion Empty already exists: '{existing.name}'.")
            return {'CANCELLED'}

        pose_root = armature.pose.bones.get(root_bone.name)
        if not pose_root:
            self.report({'ERROR'}, "Root Pose Bone not found.")
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

        self.report({'INFO'}, f"Root Motion Empty created: '{empty.name}' copying XY (Offset) from '{torso_bone.name}'.")
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
            f"Root constraints cleared (Empty: {empty_cleared}, Bone: {bone_cleared}).",
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
            self.report({'WARNING'}, "No Root Motion Empty has been created for this armature.")
            return {'CANCELLED'}

        try:
            _ensure_object_mode(context)
            bpy.ops.object.select_all(action='DESELECT')
            empty.select_set(True)
            context.view_layer.objects.active = empty

            self.report({'INFO'}, f"Empty '{empty.name}' selected for Bake.")
            try:
                bpy.ops.nla.bake('INVOKE_DEFAULT', visual_keying=True, clear_constraints=False)
            except Exception:
                bpy.ops.object.bake_action('INVOKE_DEFAULT')
        except Exception as exc:
            self.report({'ERROR'}, f"Could not prepare Bake: {exc}")
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
            self.report({'ERROR'}, "Assign a Root Bone first.")
            return {'CANCELLED'}

        empty = _get_slot_empty(context, armature, "root_bone", adopt_legacy=False, allow_cross_armature=True)
        if not empty:
            self.report({'ERROR'}, "Root Motion Empty not found.")
            return {'CANCELLED'}

        pose_root = armature.pose.bones.get(root_slot.bone_name)
        if not pose_root:
            self.report({'ERROR'}, f"Pose Bone '{root_slot.bone_name}' not found.")
            return {'CANCELLED'}

        try:
            _activate_armature_pose(context, armature)
        except Exception as exc:
            self.report({'ERROR'}, f"Could not activate Source Armature: {exc}")
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

        self.report({'INFO'}, f"Root motion constraint applied to Root Bone '{pose_root.name}'.")
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
            self.report({'ERROR'}, "Assign a Root Bone first.")
            return {'CANCELLED'}

        pose_root = armature.pose.bones.get(root_slot.bone_name)
        bone_data = armature.data.bones.get(root_slot.bone_name)
        if not pose_root or not bone_data:
            self.report({'ERROR'}, f"Root Bone '{root_slot.bone_name}' not found.")
            return {'CANCELLED'}

        try:
            _activate_armature_pose(context, armature)
        except Exception as exc:
            self.report({'ERROR'}, f"Could not activate Source Armature: {exc}")
            return {'CANCELLED'}

        for pb in armature.pose.bones:
            pb.select = False

        pose_root.select = True
        armature.data.bones.active = bone_data

        self.report({'INFO'}, f"Root Bone '{pose_root.name}' selected in Pose Mode for Bake.")

        try:
            bpy.ops.nla.bake('INVOKE_DEFAULT', visual_keying=True, clear_constraints=False)
        except Exception:
            try:
                bpy.ops.object.bake_action('INVOKE_DEFAULT')
            except Exception as exc:
                self.report({'ERROR'}, f"Could not open the Bake menu: {exc}")
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
            f"Root Motion cleaned: {constraints_removed} constraint(s) and {int(empty_removed)} Empty(s) deleted.",
        )
        return {'FINISHED'}


# ──────────────────────────────────────────────
# 4.6. CURVE CLEANUP (MODULE 1 STEP 2) & SETUP CLEANUP
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
            self.report({'ERROR'}, f"Could not activate Source Armature: {exc}")
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
                "The Action has no active Action Slot; no curves were modified.",
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
            f"Cleaned '{armature.name}': "
            f"{constraints_removed} constraint(s), "
            f"{curves_removed} Location curve(s), and "
            f"{empties_removed} owned Empty/Empties removed.",
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
            self.report({'ERROR'}, f"Could not clear Rig constraints: {exc}")
            return {'CANCELLED'}

        empties_removed = 0
        for key, _, _ in SLOTS_CONFIG:
            if _remove_slot_empty_any_armature(context, armature, key):
                empties_removed += 1
                slot_prop = _slot_property(context.scene, key)
                slot_prop.empty_name = ""
                slot_prop.created = False

        if _remove_slot_empty_any_armature(context, armature, "root_bone"):
            empties_removed += 1
            root_slot = _slot_property(context.scene, "root_bone")
            if root_slot:
                root_slot.empty_name = ""
                root_slot.created = False

        _remove_empty_collection_if_unused()

        self.report(
            {'INFO'},
            f"Setup cleaned on '{armature.name}': "
            f"{constraints_removed} constraint(s) and {empties_removed} Empty/Empties deleted (animation curves preserved).",
        )
        return {'FINISHED'}


class RETARGET_OT_clear_all_bone_names(Operator):
    """Clears assigned bone names (including Root Bone) without deleting Empties or affecting Props."""
    bl_idname = "retarget.clear_all_bone_names"
    bl_label = "Clear Bone Names"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        cleared_count = 0

        for key, _, _ in SLOTS_CONFIG:
            slot_prop = _slot_property(scene, key)
            if slot_prop and slot_prop.bone_name:
                slot_prop.bone_name = ""
                cleared_count += 1

        root_slot = _slot_property(scene, "root_bone")
        if root_slot and root_slot.bone_name:
            root_slot.bone_name = ""
            cleared_count += 1

        armature = _get_armature(context)
        if armature is not None and BONE_MAP_PROP in armature:
            del armature[BONE_MAP_PROP]

        self.report(
            {'INFO'},
            f"Bone names cleared in {cleared_count} slot(s) (Empties and Props preserved).",
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
            f"{removed} Empty/Empties from '{armature.name}' deleted.",
        )
        return {'FINISHED'}


# ──────────────────────────────────────────────
# 4.7. MODULE 3 OPERATORS: PROP -> EMPTIES (INDEPENDENT OF SOURCE ARMATURE)
# ──────────────────────────────────────────────
class RETARGET_OT_prop_pick_source_bone(Operator):
    """Captures the selected bone from Prop Obj (Armature) in Pose Mode."""
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
            self.report({'ERROR'}, "Assign an Armature in Prop Obj first.")
            return {'CANCELLED'}

        selected_bone = next((pb for pb in prop_arm.pose.bones if pb.select), None)
        if selected_bone:
            bone_name = selected_bone.name
        elif prop_arm.data.bones.active:
            bone_name = prop_arm.data.bones.active.name
        else:
            self.report({'ERROR'}, f"Select a bone in '{prop_arm.name}' (Pose Mode).")
            return {'CANCELLED'}

        prop_slot.prop_bone_name = bone_name
        if not prop_slot.empty_name:
            label = prop_slot.prop_label.strip() or self.slot.replace('_', ' ').title()
            prop_slot.empty_name = f"RET_Prop_{label.replace(' ', '_')}"

        self.report({'INFO'}, f"Prop Bone captured: {bone_name}")
        return {'FINISHED'}


class RETARGET_OT_prop_select_source_bone(Operator):
    """Selects the Prop Bone in the viewport (Pose Mode)."""
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
            self.report({'ERROR'}, "Assign an Armature in Prop Obj.")
            return {'CANCELLED'}

        if not prop_slot.prop_bone_name:
            self.report({'ERROR'}, "No Prop Bone is assigned.")
            return {'CANCELLED'}

        bone = _get_bone(prop_arm, prop_slot.prop_bone_name)
        if not bone:
            self.report({'ERROR'}, f"Bone '{prop_slot.prop_bone_name}' not found in '{prop_arm.name}'.")
            return {'CANCELLED'}

        _activate_armature_pose(context, prop_arm)
        for pb in prop_arm.pose.bones:
            pb.select = False
        pb = prop_arm.pose.bones.get(bone.name)
        if pb:
            pb.select = True
            prop_arm.data.bones.active = bone

        self.report({'INFO'}, f"Prop Bone selected: {bone.name}")
        return {'FINISHED'}


class RETARGET_OT_prop_pick_target_bone(Operator):
    """Captures the selected bone from Target Obj (Armature) in Pose Mode."""
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
            self.report({'ERROR'}, "Assign an Armature in Target Obj first.")
            return {'CANCELLED'}

        selected_bone = next((pb for pb in target_arm.pose.bones if pb.select), None)
        if selected_bone:
            bone_name = selected_bone.name
        elif target_arm.data.bones.active:
            bone_name = target_arm.data.bones.active.name
        else:
            self.report({'ERROR'}, f"Select a bone in '{target_arm.name}' (Pose Mode).")
            return {'CANCELLED'}

        prop_slot.target_bone_name = bone_name
        self.report({'INFO'}, f"Target Bone captured: {bone_name}")
        return {'FINISHED'}


class RETARGET_OT_prop_select_target_bone(Operator):
    """Selects the Target Bone in the viewport (Pose Mode)."""
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
            self.report({'ERROR'}, "Assign an Armature in Target Obj.")
            return {'CANCELLED'}

        if not prop_slot.target_bone_name:
            self.report({'ERROR'}, "No Target Bone is assigned.")
            return {'CANCELLED'}

        bone = _get_bone(target_arm, prop_slot.target_bone_name)
        if not bone:
            self.report({'ERROR'}, f"Bone '{prop_slot.target_bone_name}' not found in '{target_arm.name}'.")
            return {'CANCELLED'}

        _activate_armature_pose(context, target_arm)
        for pb in target_arm.pose.bones:
            pb.select = False
        pb = target_arm.pose.bones.get(bone.name)
        if pb:
            pb.select = True
            target_arm.data.bones.active = bone

        self.report({'INFO'}, f"Target Bone selected: {bone.name}")
        return {'FINISHED'}


class RETARGET_OT_prop_clear_slot(Operator):
    """Clears the prop slot and removes its associated Empty."""
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

        self.report({'INFO'}, "Prop slot cleared.")
        return {'FINISHED'}


class RETARGET_OT_prop_create_empty(Operator):
    """Creates an Empty that tracks the location/rotation of the Prop (Object or Bone)."""
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
            self.report({'ERROR'}, "Assign a Prop Object or Armature first.")
            return {'CANCELLED'}

        if prop_slot.source_type == 'BONE':
            if prop_obj.type != 'ARMATURE':
                self.report({'ERROR'}, "The assigned object must be an Armature for Armature Bone mode.")
                return {'CANCELLED'}
            if not prop_slot.prop_bone_name or not _get_bone(prop_obj, prop_slot.prop_bone_name):
                self.report({'ERROR'}, "Assign a valid bone in Prop Bone.")
                return {'CANCELLED'}

        existing = _get_prop_slot_empty(context, self.slot)
        if existing:
            self.report({'WARNING'}, f"This Prop already has the Empty '{existing.name}'.")
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

        self.report({'INFO'}, f"Prop Empty created: '{empty.name}'.")
        return {'FINISHED'}


class RETARGET_OT_prop_create_all(Operator):
    """Creates Empties for all configured Props."""
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
            self.report({'WARNING'}, "No Prop Empties were created (check configured slots).")
            return {'CANCELLED'}

        self.report({'INFO'}, f"Created {created} Prop Empty/Empties.")
        return {'FINISHED'}


class RETARGET_OT_prop_clear_all(Operator):
    """Removes all Prop Empties created by the Props module."""
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

        self.report({'INFO'}, f"{removed} Prop Empty/Empties deleted.")
        return {'FINISHED'}


class RETARGET_OT_prop_clear_empties_constraints(Operator):
    """Removes constraints from Prop Empties after baking."""
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

        self.report({'INFO'}, f"Constraints removed from {cleared} Prop Empty/Empties.")
        return {'FINISHED'}


class RETARGET_OT_prop_bake_empties(Operator):
    """Selects active Prop Empties and opens the Bake dialog."""
    bl_idname = "retarget.prop_bake_empties"
    bl_label = "Select Prop Empties & Bake"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        empties = _get_registered_prop_empties(context)
        if not empties:
            self.report({'WARNING'}, "No active Prop Empties to bake.")
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
    """Step 2: Applies Prop Empty animation to the Target (Object or Bone)."""
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
            self.report({'WARNING'}, "No valid pairs found (Prop Empty + configured Target).")
            return {'CANCELLED'}

        self.report({'INFO'}, f"Prop retarget constraints applied to {applied} target(s).")
        return {'FINISHED'}


class RETARGET_OT_prop_clear_target_constraints(Operator):
    """Removes retarget constraints applied to Prop Targets."""
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

        self.report({'INFO'}, f"Removed {cleared} constraint(s) from Prop Targets.")
        return {'FINISHED'}


class RETARGET_OT_prop_select_target_and_bake(Operator):
    """Selects Targets linked to Prop Empties (Object or Pose Bone) and opens the Bake dialog."""
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
            self.report({'WARNING'}, "No valid Targets linked to Prop Empties were found.")
            return {'CANCELLED'}

        if bone_entries and object_entries:
            self.report(
                {'WARNING'},
                "Mixed Targets detected (Objects and Bones). Bake one type first or temporarily clear the other.",
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
    """Clears prop constraints on Targets and deletes Prop Empties (preserves animation curves)."""
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
            f"Prop Setup cleaned: {constraints_removed} constraint(s) and {empties_removed} Prop Empty/Empties deleted.",
        )
        return {'FINISHED'}


def _draw_step2_transition_reminder(layout, step_label="Step 2"):
    reminder_box = layout.box()
    col_rem = reminder_box.column(align=True)
    col_rem.scale_y = 0.8
    col_rem.label(
        text=f"Before {step_label}: clear constraints and",
        icon='INFO',
    )
    col_rem.label(
        text="mute/disable animation actions or NLA strips.",
        icon='BLANK1',
    )


# ──────────────────────────────────────────────
# 5. PANELS (N SIDEBAR - RETARGET TAB)
# ──────────────────────────────────────────────
class RETARGET_PT_module1_panel(Panel):
    bl_label = "Module 1 & 2: Retarget → Empties"
    bl_idname = "RETARGET_PT_module1_panel"
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
                text="Assign a Source Armature for Module 1 and Module 2.",
                icon='ERROR',
            )

        layout.separator()

        # --- MASTER BONE SLOTS DROPDOWN + SYMMETRIZE ---
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
        slots_header.operator(
            "retarget.clear_all_bone_names",
            text="",
            icon='LOOP_BACK',
        )

        if scene.retarget_slots_expanded:
            preset_box = slots_container.box()
            row_preset = preset_box.row(align=True)
            row_preset.prop(scene, "retarget_preset", text="")
            row_preset.operator(
                "retarget.save_custom_preset",
                text="",
                icon='FILE_TICK',
            )
            if (
                scene.retarget_preset != 'AUTO'
                and scene.retarget_preset not in BUILTIN_BONE_PRESETS
            ):
                row_preset.operator(
                    "retarget.delete_custom_preset",
                    text="",
                    icon='TRASH',
                )

            row_apply_preset = preset_box.row(align=True)
            row_apply_preset.operator(
                "retarget.apply_bone_preset",
                text="Auto-Fill Bones",
                icon='VIEWZOOM',
            )
            row_apply_preset.prop(
                scene,
                "retarget_preset_overwrite",
                text="Overwrite",
                toggle=True,
            )

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

        # --- MODULE 1 / STEP 1: RIG -> EMPTIES ---
        m1_step1 = layout.box()
        m1s1_head = m1_step1.row(align=True)
        m1s1_tri = 'TRIA_DOWN' if scene.retarget_m1_step1_expanded else 'TRIA_RIGHT'
        m1s1_head.prop(
            scene,
            "retarget_m1_step1_expanded",
            text="Step 1: Rig → Empties",
            icon=m1s1_tri,
            emboss=False,
        )
        m1s1_head.label(text="", icon='OUTLINER_OB_EMPTY')

        if scene.retarget_m1_step1_expanded:
            row = m1_step1.row(align=True)
            row.operator("retarget.create_all", icon='ADD')
            row.operator("retarget.clear_all", icon='REMOVE')
            m1_step1.operator(
                "retarget.clear_constraints_empties",
                icon='CONSTRAINT_BONE',
            )
            m1_step1.operator(
                "retarget.select_and_open_bake",
                icon='RENDER_ANIMATION',
            )

        layout.separator()
        _draw_step2_transition_reminder(layout, step_label="Step 2")
        layout.separator()

        # --- MODULE 1 / STEP 2: EMPTIES -> RIG ---
        m1_step2 = layout.box()
        m1s2_head = m1_step2.row(align=True)
        m1s2_tri = 'TRIA_DOWN' if scene.retarget_m1_step2_expanded else 'TRIA_RIGHT'
        m1s2_head.prop(
            scene,
            "retarget_m1_step2_expanded",
            text="Step 2: Empties → Rig",
            icon=m1s2_tri,
            emboss=False,
        )
        m1s2_head.label(text="", icon='ARMATURE_DATA')

        if scene.retarget_m1_step2_expanded:
            m1_step2.operator(
                "retarget.apply_to_rig",
                icon='CON_LOCLIKE',
            )
            m1_step2.operator(
                "retarget.clear_rig_constraints",
                icon='X',
            )
            m1_step2.operator(
                "retarget.select_rig_and_open_bake",
                icon='RENDER_ANIMATION',
            )

            m1_step2.separator()
            m1_step2.operator(
                "retarget.clean_curves_and_empties",
                icon='TRASH',
            )
            warn_col = m1_step2.column(align=True)
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

        # --- MODULE 2: TORSO -> ROOT MOTION (IN SAME PANEL, SHARES SOURCE ARMATURE) ---
        m2_container = layout.box()
        m2_head = m2_container.row(align=True)
        m2_tri = 'TRIA_DOWN' if scene.retarget_m2_expanded else 'TRIA_RIGHT'
        m2_head.prop(
            scene,
            "retarget_m2_expanded",
            text="Module 2: Torso → Root Motion",
            icon=m2_tri,
            emboss=False,
        )
        m2_head.label(text="", icon='ORIENTATION_GLOBAL')

        if scene.retarget_m2_expanded:
            root_slot = _slot_property(scene, "root_bone")

            root_box = m2_container.box()
            root_box.label(text="Root Bone Target", icon='BONE_DATA')
            row_root = root_box.row(align=True)
            if armature and armature.data:
                row_root.prop_search(
                    root_slot,
                    "bone_name",
                    armature.data,
                    "bones",
                    text="",
                )
            else:
                row_root.prop(root_slot, "bone_name", text="")

            pick_root = row_root.operator("retarget.pick_bone", icon='BONE_DATA', text="")
            pick_root.slot = "root_bone"

            sel_root = row_root.operator("retarget.select_bone_in_viewport", icon='ZOOM_ALL', text="")
            sel_root.slot = "root_bone"

            clr_root = row_root.operator("retarget.clear_slot", icon='X', text="")
            clr_root.slot = "root_bone"

            m2_container.separator()

            # --- MODULE 2 / STEP 1: TORSO -> EMPTY ---
            m2_step1 = m2_container.box()
            m2s1_head = m2_step1.row(align=True)
            m2s1_tri = 'TRIA_DOWN' if scene.retarget_m2_step1_expanded else 'TRIA_RIGHT'
            m2s1_head.prop(
                scene,
                "retarget_m2_step1_expanded",
                text="Step 1: Torso → Empty",
                icon=m2s1_tri,
                emboss=False,
            )
            m2s1_head.label(text="", icon='EMPTY_ARROWS')

            if scene.retarget_m2_step1_expanded:
                row_rm_create = m2_step1.row(align=True)
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

                m2_step1.operator(
                    "retarget.clear_root_constraints",
                    icon='CONSTRAINT_BONE',
                )
                m2_step1.operator("retarget.bake_root_empty", icon='RENDER_ANIMATION')

            m2_container.separator()
            _draw_step2_transition_reminder(m2_container, step_label="Step 2")
            m2_container.separator()

            # --- MODULE 2 / STEP 2: EMPTY -> ROOT BONE ---
            m2_step2 = m2_container.box()
            m2s2_head = m2_step2.row(align=True)
            m2s2_tri = 'TRIA_DOWN' if scene.retarget_m2_step2_expanded else 'TRIA_RIGHT'
            m2s2_head.prop(
                scene,
                "retarget_m2_step2_expanded",
                text="Step 2: Empty → Root Bone",
                icon=m2s2_tri,
                emboss=False,
            )
            m2s2_head.label(text="", icon='ORIENTATION_GLOBAL')

            if scene.retarget_m2_step2_expanded:
                m2_step2.operator("retarget.apply_root_to_bone", icon='CON_LOCLIKE')
                m2_step2.operator(
                    "retarget.clear_root_constraints",
                    text="Clear Root Constraints",
                    icon='X',
                )
                m2_step2.operator("retarget.select_root_and_bake", icon='RENDER_ANIMATION')

            m2_container.separator()

            clean_rm_box = m2_container.box()
            clean_rm_box.operator("retarget.clean_root_motion", icon='TRASH')
            info_rm = clean_rm_box.column(align=True)
            info_rm.scale_y = 0.8
            info_rm.label(
                text="Deletes Root Empty & root RET_ constraints.",
                icon='INFO',
            )
            info_rm.label(
                text="Animation curves are preserved.",
                icon='BLANK1',
            )

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


class RETARGET_PT_module3_props_panel(Panel):
    bl_label = "Module 3: Prop → Empties"
    bl_idname = "RETARGET_PT_module3_props_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Retarget"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # --- MASTER PROP SLOTS DROPDOWN (EXPANDED BY DEFAULT) ---
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

                    # --- SOURCE ---
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

                    # --- TARGET (FOR STEP 2) ---
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

        # --- MODULE 3 / STEP 1: PROP -> EMPTIES ---
        m3_step1 = layout.box()
        m3s1_head = m3_step1.row(align=True)
        m3s1_tri = 'TRIA_DOWN' if scene.retarget_m3_step1_expanded else 'TRIA_RIGHT'
        m3s1_head.prop(
            scene,
            "retarget_m3_step1_expanded",
            text="Step 1: Prop → Empties",
            icon=m3s1_tri,
            emboss=False,
        )
        m3s1_head.label(text="", icon='OUTLINER_OB_EMPTY')

        if scene.retarget_m3_step1_expanded:
            row_p_btns = m3_step1.row(align=True)
            row_p_btns.operator("retarget.prop_create_all", icon='ADD')
            row_p_btns.operator("retarget.prop_clear_all", icon='REMOVE')
            m3_step1.operator("retarget.prop_clear_empties_constraints", icon='CONSTRAINT_BONE')
            m3_step1.operator("retarget.prop_bake_empties", icon='RENDER_ANIMATION')

        layout.separator()
        _draw_step2_transition_reminder(layout, step_label="Step 2")
        layout.separator()

        # --- MODULE 3 / STEP 2: EMPTIES -> PROP / TARGET ---
        m3_step2 = layout.box()
        m3s2_head = m3_step2.row(align=True)
        m3s2_tri = 'TRIA_DOWN' if scene.retarget_m3_step2_expanded else 'TRIA_RIGHT'
        m3s2_head.prop(
            scene,
            "retarget_m3_step2_expanded",
            text="Step 2: Empties → Prop",
            icon=m3s2_tri,
            emboss=False,
        )
        m3s2_head.label(text="", icon='ARMATURE_DATA')

        if scene.retarget_m3_step2_expanded:
            m3_step2.operator("retarget.prop_apply_to_target", icon='CON_LOCLIKE')
            m3_step2.operator("retarget.prop_clear_target_constraints", icon='X')
            m3_step2.operator("retarget.prop_select_target_and_bake", icon='RENDER_ANIMATION')

        layout.separator()

        # --- FINAL PROP CLEANUP ---
        clean_p_box = layout.box()
        clean_p_box.operator("retarget.prop_clean_all", icon='TRASH')
        info_p = clean_p_box.column(align=True)
        info_p.scale_y = 0.8
        info_p.label(text="Removes Prop Empties & RET_Prop constraints.", icon='INFO')
        info_p.label(text="Preserves baked animation curves.", icon='BLANK1')


# ──────────────────────────────────────────────
# 6. REGISTRATION
# ──────────────────────────────────────────────
classes = (
    RETargetSlot,
    RETargetPropSlot,
    RETARGET_OT_apply_bone_preset,
    RETARGET_OT_save_custom_preset,
    RETARGET_OT_delete_custom_preset,
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
    RETARGET_OT_clear_all_bone_names,
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
    RETARGET_PT_module1_panel,
    RETARGET_PT_module3_props_panel,
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