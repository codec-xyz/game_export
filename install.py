import importlib
import bpy
import subprocess
import os
import sys
from .settings import *
from . import *
PYTHON_BINARY = sys.executable if bpy.app.version >= (2,91,0) else bpy.app.binary_path_python
MODULES_PATH = os.path.dirname(os.path.abspath(__file__))

class GAME_EXPORT_OT_install_modules(bpy.types.Operator):
	'''Install missing modules'''
	bl_idname = 'game_export.install_modules'
	bl_label = 'Install missing modules'

	def drawTable(layout: bpy.types.UILayout):
		layout.label(text = 'Required Modules')
		column = layout.column()
		for module in PIP_MODULES:
			row = column.row()
			if f'{__package__}.{module}' in sys.modules: row.label(icon = 'CHECKBOX_HLT')
			else: row.label(icon = 'CHECKBOX_DEHLT')
			row.label(text = module + ' (pip package)')
		layout.operator(GAME_EXPORT_OT_install_modules.bl_idname)

	@classmethod
	def poll(cls, context):
		return not dependenciesAreLoaded()

	def execute(self, context):
		modulesToInstall = []
		for module in PIP_MODULES:
			if f'{__package__}.{module}' in sys.modules: continue
			try:
				importlib.import_module(f'{__package__}.{module}')
			except:
				modulesToInstall.append(module)

		try:
			subprocess.run([PYTHON_BINARY, '-m', 'ensurepip'], check = True, capture_output = True)
			subprocess.run([PYTHON_BINARY, '-m', 'pip', 'install', *modulesToInstall, '-t', MODULES_PATH], check = True, capture_output = True)
		except subprocess.CalledProcessError as e:
			def draw(self, context):
				self.layout.label(text = 'Some modules failed to install...')
				for line in e.stderr.decode().split('\n'):
					self.layout.label(text = line)
			bpy.context.window_manager.popup_menu(draw, title = 'Error installing modules', icon = 'IMPORT')

		loadModules(PIP_MODULES)
		if dependenciesAreLoaded():
			loadModules(MODULES_CORE)
			registerModules(MODULES_CORE)
			bpy.utils.unregister_class(GAME_EXPORT_PT_temp_insall_modules_info)

		return { 'FINISHED' }

class GAME_EXPORT_PT_temp_insall_modules_info(bpy.types.Panel):
	bl_idname = 'GAME_EXPORT_PT_temp_insall_modules_info'
	bl_label = 'Game Export'
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = 'GameExport'

	def draw(self, context):
		column = self.layout.column(align=True)
		column.label(text='Install missing modules')
		column.label(text='More info under...')
		column.label(text='Edit > Preferences > Add-ons > Game Export')
		self.layout.operator(GAME_EXPORT_OT_install_modules.bl_idname)

class GAME_EXPORT_PT_temp_data_delete_info(bpy.types.Panel):
	bl_idname = 'GAME_EXPORT_PT_temp_data_delete_info'
	bl_label = 'Game Export'
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = 'GameExport'

	def draw(self, context):
		column = self.layout.column(align=True)
		column.label(text='Data deleted')
		column.label(text='Turn the addon off and on to use again')

class GAME_EXPORT_OT_delete_data(bpy.types.Operator):
	'''Delete addon data from this blender file'''
	bl_idname = 'game_export.delete_data'
	bl_label = 'Delete Addon Data'

	@classmethod
	def poll(cls, context):
		return doesDataExist()

	def execute(self, context):
		deleteData()
		unregisterModules(MODULES_CORE)
		bpy.utils.register_class(GAME_EXPORT_PT_temp_data_delete_info)
		return { 'FINISHED' }

classes = (
	GAME_EXPORT_OT_install_modules,
	GAME_EXPORT_OT_delete_data,
)

def register():
	for cls in classes: bpy.utils.register_class(cls)
	if not dependenciesAreLoaded(): bpy.utils.register_class(GAME_EXPORT_PT_temp_insall_modules_info)

def unregister():
	for cls in reversed(classes): bpy.utils.unregister_class(cls)
	if not dependenciesAreLoaded(): bpy.utils.unregister_class(GAME_EXPORT_PT_temp_insall_modules_info)
	if not doesDataExist(): bpy.utils.unregister_class(GAME_EXPORT_PT_temp_data_delete_info)