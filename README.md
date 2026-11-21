Retarget to Empties (Blender Extension)

A production add-on for Blender designed to support animation workflows through bi-directional retargeting using Empty objects.

Its primary goal is to isolate movement channels (location and rotation), extract clean Root Motion, retarget props or weapons, and clean up unnecessary curves before transferring animation back to a rig. It is well suited for blending incompatible animations in the Non-Linear Animation (NLA) Editor and preparing animations for game engines (Unreal Engine, Unity, Godot, and others).

⚠️ Scope and Compatibility

Built for IK chains and global pivots: This workflow transfers transforms in World Space. It is intended for IK controllers, limbs, Root Bones, and props/weapons. It is not designed for pure hierarchical FK chains.

Blender Version: Built for Blender 5.0+ and its modern animation architecture (Action Layers / Channelbags and the official Blender Extensions format).

✨ Key Features

Strict Isolation (Source Armature): Requires explicitly assigning the source rig. Each generated Empty stores owner metadata to avoid interfering with or breaking other rigs in complex scenes.

Automatic Collection Organization:

RETARGET_Empties: Groups character and Root Motion proxy empties.

RETARGET_Prop_Empties: Groups independent proxy empties created for weapons, shields, or accessories.

Selective Curve Cleanup:

Limbs (Hands, Feet, Torso): Preserve both Location and Rotation curves.

Joints / Pole Targets (Chest, Head, Elbows, Knees): Optionally remove residual Location curves while keeping rotation intact.

Root Motion Extraction (Torso → Root): Projects horizontal movement (X / Y with Offset, with Z disabled) from the torso bone to the Root Bone.

Prop and Weapon Retargeting (5 Slots): Captures motion from directly animated objects (Object / Mesh, displayed as a single arrow 'SINGLE_ARROW') or bones inside an external rig (Armature Bone, displayed as a cone 'CONE') and transfers it to a target character bone or socket.

🔄 Workflow

The main panel and the prop subpanel live in the 3D Viewport sidebar: N Sidebar > Retarget.

Setup

Pick your rig in the Source Armature (Required) field.

Expand the limb and joint slots you need (use the bone picker icon to capture the active bone in Pose Mode or search by name).

Part 1: Rig → Empties (Extraction and Isolation)

Click Create All Empties to generate world-space proxy empties.

Click Auto-Select Empties & Bake to select all proxies and open the Bake dialog (enable Visual Keying).

Click Clear Empties Constraints to detach the Empties from the original rig constraints.

(Important) Mute or disable the original Action Strips / Actions on the rig before starting Part 2 to avoid evaluation conflicts.

Part 2: Empties → Rig (Retargeting and Cleanup)

Click Empties → Rig (Apply Retarget) to link your rig controllers to the Empties.

Click Select Rig & Bake (the add-on switches the rig to Pose Mode, selects the target bones, and opens the Bake dialog).

Choose your cleanup step:

Clean Curves and Empties: Removes temporary rig constraints, deletes Location F-Curves on joints (Chest, Head, Elbows, Knees), and deletes the Empties.

Clean Setup (Empties & Constraints): Removes only the Empties and RET_ constraints created by the add-on while keeping all baked animation curves.

Part 3: Torso → Root Motion

Assign your character's root bone in Root Bone (make sure the Torso slot is also assigned).

Click Create Root Motion Empty to create the proxy at the Root Bone position copying X and Y from the Torso with Offset.

Use Select Root Empty & Bake to bake the root movement and Clear Root Constraints to release the proxy.

Click Empty → Root Bone (Apply), then Select Root Bone & Bake to transfer the root motion to the rig.

Finish with Clean Root Motion Setup to remove the constraint and proxy empty.

Additional Module: Prop → Empties

Expand the Prop → Empties subpanel to retarget weapons or external props across up to 5 slots:

Configure each slot by choosing the source type (Object / Mesh or Armature Bone), the prop object/rig, and the target bone on the character (Char Bone, such as an IK Hand or Weapon Socket bone).

Step 1 (Prop → Empties): Use Create All Prop Empties (or create them per slot), bake with Select Prop Empties & Bake, and release constraints with Clear Prop Empties Constraints.

(Important) Mute the original prop strips/actions before moving on.

Step 2 (Empties → Character): Click Prop Empties → Character, bake with Select Prop Bones & Bake, and clean up with Clean Prop Setup (preserving baked animation curves on the character).

📦 Installation

Download the extension .zip archive from Blender Extensions or from Releases.

Open Blender and go to Edit > Preferences > Get Extensions (or Add-ons).

Open the top-right menu (v) and select Install from Disk....

Select the downloaded .zip file and make sure Retarget to Empties is enabled.

📄 License

Licensed under the MIT license (SPDX:MIT). See the LICENSE file for full details.