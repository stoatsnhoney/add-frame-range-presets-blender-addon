# BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# END GPL LICENSE BLOCK #####

import bpy
from bpy.types import Operator, Menu, Panel, PropertyGroup, AddonPreferences


# Define a property group to store frame range preset data
class FrameRangePreset(PropertyGroup):
    name: bpy.props.StringProperty(name="Preset Name")
    start: bpy.props.IntProperty(name="Start Frame")
    end: bpy.props.IntProperty(name="End Frame")


class MyAddonPreferences(AddonPreferences):
    # Define the bl_idname for the add-on preferences
    bl_idname = __name__

    # Create a property for the default length of the last marker
    last_marker_frame_length: bpy.props.IntProperty(
        name="Last Marker Frame Length",
        default=100,
        min=1,
        description="Set default length of the last marker's preset range"
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "last_marker_frame_length")


def update_selected_preset(self, context):
    """ Update the selected preset when the value changes. """
    if self.selected_preset:
        for preset in context.scene.frame_range_presets:
            if preset.name == self.selected_preset:
                context.scene.frame_start = preset.start
                context.scene.frame_end = preset.end


class OUTPUT_MT_frame_range_presets(Menu):
    bl_label = "Frame Range Presets"

    def draw(self, context):
        layout = self.layout
        for preset in context.scene.frame_range_presets:
            layout.operator("output.set_frame_range_from_preset", text=preset.name).preset_index = preset.index


class AddPresetFrameRange(Operator):
    """Add a Frame Range Preset"""
    bl_idname = "output.frame_range_preset_add"
    bl_label = "Add Frame Range Preset"

    def execute(self, context):
        start = context.scene.frame_start
        end = context.scene.frame_end
        preset_name = context.scene.new_preset_name.strip()

        if preset_name:
            # Check if preset name already exists
            for preset in context.scene.frame_range_presets:
                if preset.name == preset_name:
                    self.report({'WARNING'}, f"Preset '{preset_name}' already exists.")
                    return {'CANCELLED'}

            # Add new preset
            preset = context.scene.frame_range_presets.add()
            preset.name = preset_name
            preset.start = start
            preset.end = end
            
            # Automatically select the new preset
            context.scene.selected_preset = preset.name
            
            context.scene.new_preset_name = ""  # Clear input field
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "Preset name cannot be empty.")
            return {'CANCELLED'}


class OUTPUT_PT_frame_range_presets_panel(Panel):
    bl_label = "Frame Range Presets"
    bl_idname = "OUTPUT_PT_frame_range_presets"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "output"

    def draw(self, context):
        layout = self.layout

        # Dropdown for selecting presets
        layout.prop(context.scene, "selected_preset", text="Select Preset")
        layout.prop(context.scene, "new_preset_name", text="Preset Name")

        # Add and markers to frame range
        layout.operator("output.frame_range_preset_add", text="Save Current Frame Range", icon='ZOOM_IN')
        layout.operator("output.markers_to_frame_range", text="Markers to Frame Range")

        layout.separator()

        # Reordered buttons: Edit Selected Preset first, then Delete Selected Preset
        layout.operator("output.edit_selected_preset", text="Edit Selected Preset")
        layout.operator("output.delete_frame_range_preset", text="Delete Selected Preset")


class SetFrameRangeFromPreset(Operator):
    bl_idname = "output.set_frame_range_from_preset"
    bl_label = "Set Frame Range from Preset"

    preset_index: bpy.props.IntProperty()

    def execute(self, context):
        preset = context.scene.frame_range_presets[self.preset_index]
        context.scene.frame_start = preset.start
        context.scene.frame_end = preset.end
        return {'FINISHED'}


class EditSelectedPreset(Operator):
    """Edit the selected preset"""
    bl_idname = "output.edit_selected_preset"
    bl_label = "Edit Selected Preset"
    bl_options = {'REGISTER', 'UNDO'}

    # Properties for editing the selected preset
    selected_preset_name: bpy.props.StringProperty()  # Holds the name of the currently selected preset
    new_name: bpy.props.StringProperty(name="Preset Name")
    start_frame: bpy.props.IntProperty(name="Start Frame", default=1)
    end_frame: bpy.props.IntProperty(name="End Frame", default=1)

    def invoke(self, context, event):
        self.selected_preset_name = context.scene.selected_preset
        preset = next((p for p in context.scene.frame_range_presets if p.name == self.selected_preset_name), None)

        if preset:
            self.new_name = preset.name
            self.start_frame = preset.start
            self.end_frame = preset.end
            return context.window_manager.invoke_props_dialog(self)

        return {'CANCELLED'}

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "new_name", text="Preset Name")
        layout.prop(self, "start_frame", text="Start Frame")
        layout.prop(self, "end_frame", text="End Frame")

    def execute(self, context):
        preset = next((p for p in context.scene.frame_range_presets if p.name == self.selected_preset_name), None)

        if preset:
            preset.name = self.new_name
            preset.start = self.start_frame
            preset.end = self.end_frame
            
            context.scene.selected_preset = self.new_name  # Update selected preset name
            return {'FINISHED'}
        return {'CANCELLED'}


class DeleteFrameRangePreset(Operator):
    """Delete the active preset"""
    bl_idname = "output.delete_frame_range_preset"
    bl_label = "Delete Frame Range Preset"

    def execute(self, context):
        selected_name = context.scene.selected_preset
        presets = context.scene.frame_range_presets

        # Find and remove the selected preset by name
        for index, preset in enumerate(presets):
            if preset.name == selected_name:
                presets.remove(index)  # Remove the preset from the collection by index
                break
        else:
            self.report({'WARNING'}, "No preset selected to delete.")
            return {'CANCELLED'}

        # If any presets remain, update selected preset; otherwise, leave current frame range unchanged
        if presets:
            context.scene.selected_preset = presets[0].name  # Select the first preset
        else:
            # Leave the selected_preset unchanged if no presets are left
            pass

        return {'FINISHED'}


class MarkersToFrameRange(Operator):
    """Create presets from timeline markers"""
    bl_idname = "output.markers_to_frame_range"
    bl_label = "Markers to Frame Range"

    def execute(self, context):
        markers = context.scene.timeline_markers

        # Get the user-defined length for the last marker from preferences
        frame_length = context.preferences.addons[__name__].preferences.last_marker_frame_length

        # Ensure that we process the markers if at least one exists
        if not markers:
            self.report({'WARNING'}, "No markers found in the timeline.")
            return {'CANCELLED'}

        # Iterate through the markers and create presets
        for i, marker in enumerate(markers):
            start_frame = marker.frame
            
            # Check if the marker is camera bound
            camera_name = ""
            if marker.camera:
                camera_name = marker.camera.name  # Get the name of the linked camera
            else:
                camera_name = marker.name  # Fall back to the marker's name if no camera is linked
            
            # Use the camera's name as the preset's name if available
            preset_name = camera_name
            
            # Check if this is the last marker
            if i + 1 < len(markers):
                end_frame = markers[i + 1].frame - 1  # Set end frame before the next marker
            else:
                end_frame = start_frame + frame_length  # Use user-defined length of the last marker

            # Add a new preset with the marker information
            preset = context.scene.frame_range_presets.add()
            preset.name = preset_name  # Set preset name based on linked camera or marker name
            preset.start = start_frame
            preset.end = end_frame

        return {'FINISHED'}


def get_frame_range_presets_items(self, context):
    """ Dynamic property to get presets for the EnumProperty """
    items = [(preset.name, preset.name, "") for preset in context.scene.frame_range_presets]
    return items


def register():
    bpy.utils.register_class(FrameRangePreset)
    bpy.utils.register_class(MyAddonPreferences)
    bpy.utils.register_class(AddPresetFrameRange)
    bpy.utils.register_class(SetFrameRangeFromPreset)
    bpy.utils.register_class(EditSelectedPreset)
    bpy.utils.register_class(DeleteFrameRangePreset)
    bpy.utils.register_class(OUTPUT_MT_frame_range_presets)
    bpy.utils.register_class(OUTPUT_PT_frame_range_presets_panel)
    bpy.utils.register_class(MarkersToFrameRange)

    bpy.types.Scene.frame_range_presets = bpy.props.CollectionProperty(type=FrameRangePreset)
    bpy.types.Scene.new_preset_name = bpy.props.StringProperty(name="New Preset Name")
    bpy.types.Scene.selected_preset = bpy.props.EnumProperty(name="Selected Preset", items=get_frame_range_presets_items, update=update_selected_preset)


def unregister():
    bpy.utils.unregister_class(OUTPUT_PT_frame_range_presets_panel)
    bpy.utils.unregister_class(DeleteFrameRangePreset)
    bpy.utils.unregister_class(EditSelectedPreset)
    bpy.utils.unregister_class(SetFrameRangeFromPreset)
    bpy.utils.unregister_class(AddPresetFrameRange)
    bpy.utils.unregister_class(OUTPUT_MT_frame_range_presets)
    bpy.utils.unregister_class(MarkersToFrameRange)

    del bpy.types.Scene.frame_range_presets
    del bpy.types.Scene.new_preset_name
    del bpy.types.Scene.selected_preset


if __name__ == "__main__":
    register()
