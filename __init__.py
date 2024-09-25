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

class FrameRangePreset:
    def __init__(self, name, start, end):
        self.name = name
        self.start = start
        self.end = end

frame_range_presets = []

class FrameRangePresetPanel(bpy.types.Panel):
    bl_label = "Frame Range Presets"
    bl_idname = "OUTPUT_PT_frame_range_presets"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "output"

    def draw(self, context):
        layout = self.layout
        
        layout.prop(context.scene, "new_preset_name", text="Preset Name")
        
        layout.operator("output.set_current_frame_range_as_preset", text="Add Preset")
        
        layout.operator("output.markers_to_frame_range", text="Markers to Frame Range")
        
        layout.separator()

        for index, preset in enumerate(frame_range_presets):
            row = layout.row(align=True)
            row.label(text=preset.name)
            row.operator("output.set_frame_range_from_preset", text="Set").preset_index = index
            row.operator("output.edit_frame_range_preset", text="Edit").preset_index = index
            row.operator("output.delete_frame_range_preset", text="Delete").preset_index = index

class SetCurrentFrameRangeAsPreset(bpy.types.Operator):
    bl_idname = "output.set_current_frame_range_as_preset"
    bl_label = "Set Current Frame Range as Preset"
    
    def execute(self, context):
        start = context.scene.frame_start
        end = context.scene.frame_end
        preset_name = context.scene.new_preset_name.strip()
        
        if preset_name:
            if any(preset.name == preset_name for preset in frame_range_presets):
                self.report({'WARNING'}, f"Preset '{preset_name}' already exists.")
                return {'CANCELLED'}
            
            frame_range_presets.append(FrameRangePreset(preset_name, start, end))
            context.scene.new_preset_name = ""  
            self.report({'INFO'}, f"Saved frame range as '{preset_name}'")
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "Preset name cannot be empty.")
            return {'CANCELLED'}

class MarkersToFrameRange(bpy.types.Operator):
    bl_idname = "output.markers_to_frame_range"
    bl_label = "Markers to Frame Range"
    
    def execute(self, context):
        markers = context.scene.timeline_markers
        
        for i, marker in enumerate(markers):
            start_frame = marker.frame
            
            if i + 1 < len(markers):
                end_frame = markers[i + 1].frame - 1  
            else:
                end_frame = start_frame  
            
            if marker.camera:
                preset_name = marker.camera.name
            else:
                preset_name = marker.name
            
            frame_range_presets.append(FrameRangePreset(preset_name, start_frame, end_frame))
        
        self.report({'INFO'}, f"Created {len(markers)} presets from markers.")
        return {'FINISHED'}

class EditFrameRangePreset(bpy.types.Operator):
    bl_idname = "output.edit_frame_range_preset"
    bl_label = "Edit Frame Range Preset"
    
    preset_index: bpy.props.IntProperty()  
    new_name: bpy.props.StringProperty(name="New Name")  
    new_start: bpy.props.IntProperty(name="Start Frame")  
    new_end: bpy.props.IntProperty(name="End Frame")  

    def invoke(self, context, event):
        if 0 <= self.preset_index < len(frame_range_presets):
            preset = frame_range_presets[self.preset_index]
            self.new_name = preset.name
            self.new_start = preset.start
            self.new_end = preset.end
            return context.window_manager.invoke_props_dialog(self)
        return {'CANCELLED'}

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "new_name")
        layout.prop(self, "new_start")
        layout.prop(self, "new_end")

    def execute(self, context):
        if 0 <= self.preset_index < len(frame_range_presets):
            if self.new_name.strip():  
               
                if any(preset.name == self.new_name for preset in frame_range_presets if preset != frame_range_presets[self.preset_index]):
                    self.report({'WARNING'}, f"Preset '{self.new_name}' already exists.")
                    return {'CANCELLED'}
                
                preset = frame_range_presets[self.preset_index]
                preset.name = self.new_name
                preset.start = self.new_start
                preset.end = self.new_end
                
                self.report({'INFO'}, f"Updated preset to '{self.new_name}' with range {self.new_start} - {self.new_end}")
                return {'FINISHED'}
            else:
                self.report({'WARNING'}, "Preset name cannot be empty.")
                return {'CANCELLED'}
        return {'CANCELLED'}

class SetFrameRangeFromPreset(bpy.types.Operator):
    bl_idname = "output.set_frame_range_from_preset"
    bl_label = "Set Frame Range from Preset"
    
    preset_index: bpy.props.IntProperty()  

    def execute(self, context):
        if 0 <= self.preset_index < len(frame_range_presets):
            preset = frame_range_presets[self.preset_index]
            context.scene.frame_start = preset.start
            context.scene.frame_end = preset.end
            self.report({'INFO'}, f"Set frame range to '{preset.name}'")
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "Invalid preset index.")
            return {'CANCELLED'}

class DeleteFrameRangePreset(bpy.types.Operator):
    bl_idname = "output.delete_frame_range_preset"
    bl_label = "Delete Frame Range Preset"
    
    preset_index: bpy.props.IntProperty() 

    def execute(self, context):
        if 0 <= self.preset_index < len(frame_range_presets):
            deleted_preset = frame_range_presets.pop(self.preset_index)
            self.report({'INFO'}, f"Deleted preset '{deleted_preset.name}'")
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "Invalid preset index.")
            return {'CANCELLED'}

def register():
    bpy.utils.register_class(SetCurrentFrameRangeAsPreset)
    bpy.utils.register_class(MarkersToFrameRange)
    bpy.utils.register_class(EditFrameRangePreset)
    bpy.utils.register_class(SetFrameRangeFromPreset)
    bpy.utils.register_class(DeleteFrameRangePreset)
    bpy.utils.register_class(FrameRangePresetPanel)
    
    bpy.types.Scene.new_preset_name = bpy.props.StringProperty(name="New Preset Name")

def unregister():
    bpy.utils.unregister_class(FrameRangePresetPanel)
    bpy.utils.unregister_class(DeleteFrameRangePreset)
    bpy.utils.unregister_class(EditFrameRangePreset)
    bpy.utils.unregister_class(SetFrameRangeFromPreset)
    bpy.utils.unregister_class(SetCurrentFrameRangeAsPreset)
    bpy.utils.unregister_class(MarkersToFrameRange)
    
    del bpy.types.Scene.new_preset_name

if __name__ == "__main__":
    register()
