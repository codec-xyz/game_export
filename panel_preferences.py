import bpy
from .install import *

class GAME_EXPORT_preferences(bpy.types.AddonPreferences):
	bl_idname = __package__

	def draw(self, context):
		box = self.layout.box()
		GAME_EXPORT_OT_install_modules.drawTable(box)

		box = self.layout.box()
		if not GAME_EXPORT_OT_delete_data.poll(context=context):
			box.label(text='Data deleted')
			box.label(text='Turn the addon off and on to use again')
		box.operator(GAME_EXPORT_OT_delete_data.bl_idname)

classes = (
	GAME_EXPORT_preferences,
)

def register():
	for cls in classes: bpy.utils.register_class(cls)

def unregister():
	for cls in reversed(classes): bpy.utils.unregister_class(cls)