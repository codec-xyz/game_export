import bpy
import os.path
import random
import string
import time
from .settings import *
from .export import exportCollection, Settings

def isPathFileWritable(path):
	checkFilePath = ''
	for s in range(6):
		checkFilePath = path + '\\' + ''.join(random.choice(string.ascii_letters) for i in range(16))
		if(not os.path.isfile(checkFilePath)): break
	try:
		with open(checkFilePath, 'w+') as f: ''
		os.remove(checkFilePath)
		return True
	except IOError as x:
		return False

exportInfo = []

class GAME_EXPORT_OT_show_export_info(bpy.types.Operator):
	bl_idname = 'game_export.show_export_info'
	bl_label = 'Game Export Info'

	def draw(self, context):
		global exportInfo
		if(len(exportInfo) == 0):
			self.layout.box().label(text = 'Nothing To Export')
			return

		row = self.layout.box().split(factor = 0.7)
		row.label(text = 'Export Completed Successfully')
		row.label(text = f'{sum([info[1] for info in exportInfo]):0.4f} s')
		row = self.layout.box().split(factor = 0.7)
		c1 = row.column()
		c2 = row.column()
		for info in exportInfo:
			c1.label(text = info[0])
			c2.label(text = f'{info[1]:0.4f} s')

	def execute(self, context):
		return {'FINISHED'}

	def invoke(self, context, event):
		context.window_manager.invoke_props_dialog(self)
		return {'RUNNING_MODAL'}

class GAME_EXPORT_OT_export(bpy.types.Operator):
	'''Game export'''
	bl_idname = 'game_export.export'
	bl_label = 'Game Export'

	def execute(self, context):
		settings = context.scene.gameExportSettings
		fullPath = settings.filePath
		if(fullPath[:2] == '//'): fullPath = '.\\' + fullPath[2:]
		fullPath = os.path.abspath(fullPath) + '\\'
		if(not isPathFileWritable(fullPath)):
			def draw(self, context):
				self.layout.label(text = fullPath)
				self.layout.label(text = 'Likely: Folder does not exist or you cannot write here')
			bpy.context.window_manager.popup_menu(draw, title = 'Invalid folder path', icon = 'EXPORT')
			return { 'FINISHED' }

		global exportInfo
		exportInfo = []
		context.window_manager.progress_begin(0, 1)
		context.window_manager.progress_update(0)
		totalObjs = 0
		currentObjs = 0
		for collectionSettings in settings.collectionList:
			if(collectionSettings.shouldExport): totalObjs += len(collectionSettings.collection.all_objects)
		for collectionSettings in settings.collectionList:
			if(collectionSettings.shouldExport):
				specificSettings = Settings()
				specificSettings.collection = collectionSettings.collection
				specificSettings.includeMeshes = collectionSettings.shouldIncludeMeshes
				specificSettings.includeLights = collectionSettings.shouldIncludeLights
				specificSettings.lightMultiplier = collectionSettings.lightMultiplier
				start = time.perf_counter()
				exportCollection(context, fullPath, specificSettings)
				timeElapsed = time.perf_counter() - start
				exportInfo.append((collectionSettings.exportName, timeElapsed))
				currentObjs += len(collectionSettings.collection.all_objects)
				context.window_manager.progress_update(currentObjs / totalObjs)

		context.window_manager.progress_end()
		bpy.ops.game_export.show_export_info('INVOKE_DEFAULT')
		return { 'FINISHED' }

def availableCollections(scene, context):
	return [(c.name, c.name, '') for c in bpy.data.collections]

class GAME_EXPORT_OT_collection_add(bpy.types.Operator):
	'''Add collection to export'''
	bl_idname = 'game_export.collection_add'
	bl_label = 'Add Collection'
	bl_property = 'collections'
	bl_options = {'REGISTER', 'UNDO'}

	collections: bpy.props.EnumProperty(name = 'Collections', description = '', items = availableCollections)

	def execute(self, context):
		settings = context.scene.gameExportSettings
		collectionSettings = settings.collectionList.add()
		collectionSettings.collection = next(c for c in bpy.data.collections if c.name == self.collections)
		collectionSettings.exportName = collectionSettings.collection.name
		settings.collectionListIndex = len(settings.collectionList) - 1
		context.area.tag_redraw()
		return {'FINISHED'}

	def invoke(self, context, event):
		wm = context.window_manager
		wm.invoke_search_popup(self)
		return {'FINISHED'}

class GAME_EXPORT_OT_collection_remove(bpy.types.Operator):
	'''Remove collection to export'''
	bl_idname = 'game_export.collection_remove'
	bl_label = 'Remove Collection'

	@classmethod
	def poll(cls, context):
		return len(context.scene.gameExportSettings.collectionList) != 0

	def execute(self, context):
		settings = context.scene.gameExportSettings
		settings.collectionList.remove(settings.collectionListIndex)
		if(settings.collectionListIndex > 0): settings.collectionListIndex -= 1
		return {'FINISHED'}

class GAME_EXPORT_OT_collection_move_up(bpy.types.Operator):
	'''Remove collection to export'''
	bl_idname = 'game_export.collection_move_up'
	bl_label = 'Move Collection Up'

	@classmethod
	def poll(cls, context):
		return context.scene.gameExportSettings.collectionListIndex > 0

	def execute(self, context):
		settings = context.scene.gameExportSettings
		index = settings.collectionListIndex
		settings.collectionList.move(index, index - 1)
		settings.collectionListIndex -= 1
		return {'FINISHED'}

class GAME_EXPORT_OT_collection_move_down(bpy.types.Operator):
	'''Remove collection to export'''
	bl_idname = 'game_export.collection_move_down'
	bl_label = 'Move Collection Up'

	@classmethod
	def poll(cls, context):
		return len(context.scene.gameExportSettings.collectionList) - 1 > context.scene.gameExportSettings.collectionListIndex

	def execute(self, context):
		settings = context.scene.gameExportSettings
		index = settings.collectionListIndex
		settings.collectionList.move(index, index + 1)
		settings.collectionListIndex += 1
		return {'FINISHED'}

class GAME_EXPORT_UL_collection_list(bpy.types.UIList):
	bl_idname = 'GAME_EXPORT_UL_collection_list'
	def draw_item(self, context, layout: bpy.types.UILayout, data, item, icon, active_data, active_propname, index):
		useIcon = 'OUTLINER_COLLECTION'
		if(item.collection.color_tag != 'NONE'): useIcon = 'COLLECTION_' + item.collection.color_tag
		layout.label(text = item.exportName, icon = useIcon)
		layout.prop(item, 'shouldExport', text = '', emboss = False, icon = 'CHECKBOX_HLT' if item.shouldExport else 'CHECKBOX_DEHLT')

class GAME_EXPORT_PT_settings(bpy.types.Panel):
	bl_idname = 'GAME_EXPORT_PT_settings'
	bl_label = 'Game Export'
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = 'GameExport'

	def draw(self, context):
		settings = context.scene.gameExportSettings
		self.layout.operator(GAME_EXPORT_OT_export.bl_idname, text = 'Export')
		self.layout.prop(settings, 'filePath', text = '')

		row = self.layout.row()
		col = row.column()
		col.template_list(GAME_EXPORT_UL_collection_list.bl_idname, '', settings, 'collectionList', settings, 'collectionListIndex', item_dyntip_propname = '')
		col = row.column(align=True)
		col.operator(GAME_EXPORT_OT_collection_add.bl_idname, icon='ADD', text='')
		col.operator(GAME_EXPORT_OT_collection_remove.bl_idname, icon='REMOVE', text='')
		col.separator()
		col.operator(GAME_EXPORT_OT_collection_move_up.bl_idname, icon='TRIA_UP', text='')
		col.operator(GAME_EXPORT_OT_collection_move_down.bl_idname, icon='TRIA_DOWN', text='')

		if(len(settings.collectionList) != 0):
			item = settings.collectionList[settings.collectionListIndex]
			useIcon = 'OUTLINER_COLLECTION'
			if(item.collection.color_tag != 'NONE'): useIcon = 'COLLECTION_' + item.collection.color_tag
			self.layout.label(text = item.collection.name, icon = useIcon)
			self.layout.prop(item, 'exportName', text = '')
			column = self.layout.column(align = True)
			column.prop(item, 'shouldIncludeMeshes', toggle = 1, text = 'Meshes')
			column.prop(item, 'shouldIncludeLights', toggle = 1, text = 'Lights')
			self.layout.prop(item, 'shouldJoin')
			self.layout.prop(item, 'lightMultiplier')

classes = (
	GAME_EXPORT_collection_settings,
	GAME_EXPORT_settings,
	GAME_EXPORT_OT_show_export_info,
	GAME_EXPORT_OT_export,
	GAME_EXPORT_OT_collection_add,
	GAME_EXPORT_OT_collection_remove,
	GAME_EXPORT_OT_collection_move_up,
	GAME_EXPORT_OT_collection_move_down,
	GAME_EXPORT_PT_settings,
	GAME_EXPORT_UL_collection_list,
)

objectTypes = [
	('DEFAULT', 'Default', 'Export object normally'),
	('IGNORE', 'Ignore', 'Ignore object when exporting'),
	('BOX_COLLIDER', 'Box Collider', 'Export object as a box collider'),
	('MESH_COLLIDER', 'Mesh Collider', 'Export object as a mesh collider')
]

def register():
	for cls in classes: bpy.utils.register_class(cls)
	bpy.types.Scene.gameExportSettings = bpy.props.PointerProperty(name = 'Game Export Settings', type = GAME_EXPORT_settings)
	bpy.types.Object.gameExportType = bpy.props.EnumProperty(items = objectTypes, name = 'Game Export Type', default = 'DEFAULT')

def unregister():
	for cls in classes: bpy.utils.unregister_class(cls)