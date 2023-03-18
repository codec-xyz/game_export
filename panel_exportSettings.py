import bpy
import os
import random
import string
import time
import math
from .settings import *
from .export import exportCollection

def isPathFileWritable(path):
	checkFilePath = ''
	for _ in range(6):
		checkFilePath = path + '\\' + ''.join(random.choice(string.ascii_letters) for i in range(16))
		if(not os.path.isfile(checkFilePath)): break
	try:
		with open(checkFilePath, 'w+') as _: ''
		os.remove(checkFilePath)
		return True
	except IOError as _:
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
		fullPath = bpy.path.abspath(settings.filePath)
		if(not isPathFileWritable(fullPath)):
			def draw(self, context):
				self.layout.label(text = fullPath)
				self.layout.label(text = 'Likely: Folder does not exist or you cannot write here')
			context.window_manager.popup_menu(draw, title = 'Invalid folder path', icon = 'EXPORT')
			return { 'CANCELLED' }

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
				start = time.perf_counter()
				exportCollection(context, fullPath, collectionSettings)
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
	bl_options = {'UNDO'}

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
	bl_options = {'UNDO'}

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
	bl_options = {'UNDO'}

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
	bl_options = {'UNDO'}

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

class GAME_EXPORT_OT_collection_static(bpy.types.Operator):
	'''Set collection Static type'''
	bl_idname = 'game_export.collection_static'
	bl_label = 'Set static type'
	bl_options = {'UNDO'}

	setTypeOptions = ['NOTHING','EVERYTHING', 'CONTRIBUTE_GI', 'OCCLUDER_STATIC', 'BATCHING_STATIC', 'NAVIGATION_STATIC', 'OCCLUDEE_STATIC', 'OFF_MESH_LINK_GENERATION', 'REFLECTION_PROBE_STATIC']

	setType: bpy.props.EnumProperty(name='Set Type', items=[
		('NOTHING', 'Nothing', ''),
		('EVERYTHING', 'Everything', ''),
		('CONTRIBUTE_GI', 'Contribute GI', ''),
		('OCCLUDER_STATIC', 'Occluder Static', ''),
		('BATCHING_STATIC', 'Batching Static', ''),
		('NAVIGATION_STATIC', 'Navigation Static', ''),
		('OCCLUDEE_STATIC', 'Occludee Static', ''),
		('OFF_MESH_LINK_GENERATION', 'Off Mesh Link Generation', ''),
		('REFLECTION_PROBE_STATIC', 'Reflection Probe Static', ''),
	])

	value: bpy.props.BoolProperty(name='Set Value')

	@classmethod
	def poll(cls, context: bpy.types.Context):
		settings = context.scene.gameExportSettings
		return len(settings.collectionList) != 0

	def execute(self, context):
		settings = context.scene.gameExportSettings
		collectionSettings = settings.collectionList[settings.collectionListIndex]
		if self.setType == 'NOTHING': collectionSettings.static = [not self.value] * 7
		elif self.setType == 'EVERYTHING': collectionSettings.static = [self.value] * 7
		else: collectionSettings.static[GAME_EXPORT_OT_collection_static.setTypeOptions.index(self.setType) - 2] = self.value
		context.area.tag_redraw()
		return {'FINISHED'}

class GAME_EXPORT_PT_collection_static(bpy.types.Panel):
	bl_idname = 'GAME_EXPORT_PT_collection_static'
	bl_label = 'Collection Static'
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'HEADER'
	bl_category = ''

	@classmethod
	def poll(cls, context: bpy.types.Context):
		settings = context.scene.gameExportSettings
		return len(settings.collectionList) != 0

	def drawSummary(context: bpy.types.Context, layout: bpy.types.UILayout):
		settings = context.scene.gameExportSettings
		collectionSettings = settings.collectionList[settings.collectionListIndex]
		isNothingStatic = not any(collectionSettings.static)
		isEverythingStatic = all(collectionSettings.static)

		if isNothingStatic: icon = 'BLANK1'
		elif isEverythingStatic: icon = 'CHECKMARK'
		else: icon = 'REMOVE'

		row = layout.row(align=True)
		row.label(text='Static')

		sub = row.row(align=True)
		g = sub.operator(GAME_EXPORT_OT_collection_static.__name__, text='', icon=icon, depress=isEverythingStatic)
		g.setType = 'EVERYTHING'
		g.value = not isEverythingStatic

		row.popover(panel=GAME_EXPORT_PT_collection_static.__name__, text='', icon='DOWNARROW_HLT')

	def draw(self, context: bpy.types.Context):
		settings = context.scene.gameExportSettings
		collectionSettings = settings.collectionList[settings.collectionListIndex]

		self.layout.label(text='Static')
		column = self.layout.column(align=True)
		for i in [0, 1, 2, 3, 6, 4, 5, 7, 8]:
			if i == 0: isOn = not any(collectionSettings.static)
			elif i == 1: isOn = all(collectionSettings.static)
			else: isOn = collectionSettings.static[i - 2]

			row = column.row(align=True)
			g = row.operator(GAME_EXPORT_OT_collection_static.__name__, text=['Nothing', 'Everything', 'Contribute GI', 'Occluder Static', 'Batching Static', 'Navigation Static', 'Occludee Static', 'Off Mesh Link Generation', 'Reflection Probe'][i], icon='CHECKMARK' if isOn else 'BLANK1', depress=isOn)
			g.setType = GAME_EXPORT_OT_collection_static.setTypeOptions[i]
			g.value = not isOn

def collectionQuickToggleEnumEdit(name: str, codeName: str, enum, propName: str, shortName: 'list[str] | None' = None):
	class GAME_EXPORT_OT_collection_(bpy.types.Operator):
		bl_description = f'Set {name} Type'
		bl_idname = f'game_export.collection_{codeName}'
		bl_label = f'{name} Type'
		bl_options = {'UNDO'}

		value: bpy.props.EnumProperty(name='Set Value', items=enum)

		@classmethod
		def poll(cls, context: bpy.types.Context):
			settings = context.scene.gameExportSettings
			return len(settings.collectionList) != 0

		def execute(self, context):
			settings = context.scene.gameExportSettings
			collectionSettings = settings.collectionList[settings.collectionListIndex]
			setattr(collectionSettings, propName, self.value)
			context.area.tag_redraw()
			return {'FINISHED'}

	class GAME_EXPORT_PT_collection_(bpy.types.Panel):
		bl_idname = f'GAME_EXPORT_PT_collection_{codeName}'
		bl_label = f'Collection {name}'
		bl_space_type = 'VIEW_3D'
		bl_region_type = 'HEADER'
		bl_category = ''

		@classmethod
		def poll(cls, context: bpy.types.Context):
			settings = context.scene.gameExportSettings
			return len(settings.collectionList) != 0

		def drawSummary(context: bpy.types.Context, layout: bpy.types.UILayout):
			settings = context.scene.gameExportSettings
			collectionSettings = settings.collectionList[settings.collectionListIndex]

			isOn = getattr(collectionSettings, propName) != enum[0][0]

			if shortName: value = shortName[[i[0] for i in enum].index(getattr(collectionSettings, propName))]
			else: value = ''

			row = layout.row(align=True)
			row.label(text=name)

			sub = row.row(align=True)
			sub.alignment = 'RIGHT'
			g = sub.operator(f'GAME_EXPORT_OT_collection_{codeName}', text=value, icon='CHECKMARK' if isOn else 'BLANK1', depress=isOn)
			g.value = enum[0][0] if isOn else enum[1][0]

			row.popover(f'GAME_EXPORT_PT_collection_{codeName}', text='', icon='DOWNARROW_HLT')

		def draw(self, context: bpy.types.Context):
			settings = context.scene.gameExportSettings
			collectionSettings = settings.collectionList[settings.collectionListIndex]
			value = getattr(collectionSettings, propName)

			self.layout.label(text=name)
			column = self.layout.column(align=True)
			for enumValue in enum:
				isOn = (value == enumValue[0])

				row = column.row(align=True)
				g = row.operator(f'GAME_EXPORT_OT_collection_{codeName}', text=enumValue[1], icon='CHECKMARK' if isOn else 'BLANK1', depress=isOn)
				g.value = enumValue[0]

	return (GAME_EXPORT_OT_collection_, GAME_EXPORT_PT_collection_)

(GAME_EXPORT_OT_collection_mesh_render, GAME_EXPORT_PT_collection_mesh_render) = collectionQuickToggleEnumEdit('Mesh Render', 'mesh_render', meshRenderEnum[1:], 'meshRender')
(GAME_EXPORT_OT_collection_light_render, GAME_EXPORT_PT_collection_light_render) = collectionQuickToggleEnumEdit('Light Render', 'light_render', lightRenderEnum[1:], 'lightRender')
(GAME_EXPORT_OT_collection_collider, GAME_EXPORT_PT_collection_collider) = collectionQuickToggleEnumEdit('Collider', 'collider', colliderEnum[1:], 'collider', ['', 'Box', 'Mesh'])

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
			collectionSettings = settings.collectionList[settings.collectionListIndex]
			useIcon = 'OUTLINER_COLLECTION'
			if(collectionSettings.collection.color_tag != 'NONE'): useIcon = 'COLLECTION_' + collectionSettings.collection.color_tag
			self.layout.label(text = collectionSettings.collection.name, icon = useIcon)
			self.layout.prop(collectionSettings, 'exportName', text = '')
			self.layout.prop(collectionSettings, 'lightMultiplier')
			self.layout.prop(collectionSettings, 'fixFBXTextureTint')

class GAME_EXPORT_PT_settings_inherit(bpy.types.Panel):
	bl_idname = 'GAME_EXPORT_PT_settings_inherit'
	bl_label = 'Inherit Values'
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_parent_id = 'GAME_EXPORT_PT_settings'

	@classmethod
	def poll(cls, context: bpy.types.Context):
		settings = context.scene.gameExportSettings
		return len(settings.collectionList) != 0

	def draw(self, context):
		GAME_EXPORT_PT_collection_static.drawSummary(context, self.layout)
		GAME_EXPORT_PT_collection_mesh_render.drawSummary(context, self.layout)
		GAME_EXPORT_PT_collection_light_render.drawSummary(context, self.layout)
		GAME_EXPORT_PT_collection_collider.drawSummary(context, self.layout)

class GAME_EXPORT_OT_collection_material_link_search_files(bpy.types.Operator):
	bl_description = 'Search folder for material links'
	bl_idname = 'game_export.collection_material_link_search_files'
	bl_label = 'Search Folder'
	bl_options = {'UNDO'}

	relativeFilePath: bpy.props.BoolProperty(name='Relative Path', default=True)
	replaceLinked: bpy.props.BoolProperty(name='Replace Linked Materials', description='Replace already linked materials if found in folder', default=False)
	filepath: bpy.props.StringProperty(subtype='DIR_PATH')

	@classmethod
	def poll(cls, context: bpy.types.Context):
		settings = context.scene.gameExportSettings
		return len(settings.collectionList) != 0

	def draw(self, context):
		import textwrap
		box = self.layout.box()
		column = box.column(align = True)
		text = 'Save (Ctrl-S) before running. If opened on a large folder this operation could take a while. The only way to stop is to force quit blender.'
		wrapper = textwrap.TextWrapper(max(int(context.region.width / 8), 6))
		textLines = wrapper.wrap(text=text)
		for textLine in textLines:
			column.label(text=textLine)

		self.layout.prop(self, 'relativeFilePath')
		self.layout.prop(self, 'replaceLinked')

	def execute(self, context):
		settings = context.scene.gameExportSettings
		if len(settings.collectionList) == 0:
			def draw(self, context): self.layout.label(text = 'No export collection to edit')
			context.window_manager.popup_menu(draw, title = 'No export collection', icon = 'ERROR')
			return { 'CANCELLED' }
		collectionSettings = settings.collectionList[settings.collectionListIndex]

		searchFolder = os.path.dirname(bpy.path.abspath(self.filepath))

		if not os.path.exists(searchFolder):
			def draw(self, context): self.layout.label(text = 'Likely: Folder does not exist')
			context.window_manager.popup_menu(draw, title = 'Invalid folder path', icon = 'IMPORT')
			return { 'CANCELLED' }
		
		materialFiles: 'dict[str, str]' = {}

		for walkFolder in os.walk(searchFolder):
			for item in walkFolder[2]:
				if os.path.splitext(item)[1] not in ['.mat']: continue
				materialFiles[os.path.splitext(item)[0].lower()] = os.path.join(walkFolder[0], item)

		materialNameSet = materialNameSetGet(collectionSettings.collection)
		materialLinksNameLookup = materialLinksNameLookupGet(collectionSettings)
		
		addCount = 0
		updateCount = 0
		unlinkedCount = 0

		for materialName in materialNameSet:
			materialLink = materialLinksNameLookup.get(materialName)
			if materialLink == None: unlinkedCount += 1
			if materialLink != None and not self.replaceLinked: continue

			file = materialFiles.get(materialName.lower())
			if file == None: continue

			if materialLink == None:
				addCount += 1
				materialLink = collectionSettings.materialLinks.add()
				materialLink.material = bpy.data.materials[materialName]
			else:
				updateCount += 1
			
			if self.relativeFilePath: materialLink.filePath = bpy.path.relpath(file)
			else: materialLink.filePath = file

		unlinkedCount -= addCount

		def draw(self, context):
			self.layout.label(text=f'{addCount} material link{"s" * (addCount != 1)} add')
			self.layout.label(text=f'{updateCount} material link{"s" * (updateCount != 1)} updated')
			self.layout.label(text=f'{unlinkedCount} material{"s" * (unlinkedCount != 1)} still unlinked')
		context.window_manager.popup_menu(draw, title = 'Search Folder Complete', icon = 'VIEWZOOM')

		context.area.tag_redraw()
		return {'FINISHED'}
	
	def invoke(self, context, event):
		context.window_manager.fileselect_add(self)
		return {'RUNNING_MODAL'}

class GAME_EXPORT_OT_collection_material_link_clean(bpy.types.Operator):
	bl_description = 'Checks for linked material files and removes any that no longer exist'
	bl_idname = 'game_export.collection_material_link_clean'
	bl_label = 'Check Material Links'
	bl_options = {'UNDO'}

	@classmethod
	def poll(cls, context: bpy.types.Context):
		settings = context.scene.gameExportSettings
		return len(settings.collectionList) != 0

	def execute(self, context):
		settings = context.scene.gameExportSettings
		collectionSettings = settings.collectionList[settings.collectionListIndex]

		removedCount = 0

		removeIndexes = []
		for i, materialLink in enumerate(collectionSettings.materialLinks):
			if materialLink.material == None:
				removeIndexes.append(i)
				continue

			if not os.path.isfile(bpy.path.abspath(materialLink.filePath)):
				removedCount += 1
				removeIndexes.append(i)
		
		for index in removeIndexes:
			collectionSettings.materialLinks.remove(index)

		def draw(self, context):
			self.layout.label(text=f'{removedCount} material link{"s" * (removedCount != 1)} removed')
		context.window_manager.popup_menu(draw, title = 'Check Material Links', icon = 'VIEWZOOM')

		context.area.tag_redraw()
		return {'FINISHED'}

class GAME_EXPORT_OT_collection_material_link_remove_all(bpy.types.Operator):
	bl_description = 'Remove all material links'
	bl_idname = 'game_export.collection_material_link_remove_all'
	bl_label = 'Remove All'
	bl_options = {'UNDO'}

	@classmethod
	def poll(cls, context: bpy.types.Context):
		settings = context.scene.gameExportSettings
		return len(settings.collectionList) != 0

	def execute(self, context):
		settings = context.scene.gameExportSettings
		collectionSettings = settings.collectionList[settings.collectionListIndex]

		while len(collectionSettings.materialLinks) > 0:
			collectionSettings.materialLinks.remove(0)

		context.area.tag_redraw()
		return {'FINISHED'}

class GAME_EXPORT_OT_collection_material_link_remove(bpy.types.Operator):
	bl_description = 'Remove material link'
	bl_idname = 'game_export.collection_material_link_remove'
	bl_label = 'Remove Material Link'
	bl_options = {'UNDO'}

	materialName: bpy.props.StringProperty()

	@classmethod
	def poll(cls, context: bpy.types.Context):
		settings = context.scene.gameExportSettings
		return len(settings.collectionList) != 0

	def execute(self, context):
		settings = context.scene.gameExportSettings
		collectionSettings = settings.collectionList[settings.collectionListIndex]

		materialLinkIndex = -1
		for i, materialLink in enumerate(collectionSettings.materialLinks):
			if materialLink.material == None: continue
			if materialLink.material.name == self.materialName:
				materialLinkIndex = i
				break

		if materialLinkIndex != -1:
			collectionSettings.materialLinks.remove(materialLinkIndex)
		context.area.tag_redraw()
		return {'FINISHED'}

class GAME_EXPORT_OT_collection_material_link_set(bpy.types.Operator):
	bl_description = 'Set material link'
	bl_idname = 'game_export.collection_material_link_set'
	bl_label = 'Set Material Link'
	bl_options = {'UNDO'}

	relativeFilePath: bpy.props.BoolProperty(name='Relative Path', default=True)
	materialName: bpy.props.StringProperty()
	filepath: bpy.props.StringProperty(subtype='FILE_PATH')

	@classmethod
	def poll(cls, context: bpy.types.Context):
		settings = context.scene.gameExportSettings
		return len(settings.collectionList) != 0

	def draw(self, context):
		self.layout.prop(self, 'relativeFilePath')
		self.layout.label(text='Select Material File For')
		self.layout.label(text=self.materialName)

	def execute(self, context):
		settings = context.scene.gameExportSettings
		if len(settings.collectionList) == 0:
			def draw(self, context): self.layout.label(text = 'No export collection to edit')
			context.window_manager.popup_menu(draw, title = 'No export collection', icon = 'ERROR')
			return { 'CANCELLED' }
		collectionSettings = settings.collectionList[settings.collectionListIndex]

		if bpy.path.basename(self.filepath) == '':
			def draw(self, context): self.layout.label(text = 'Select a file, not a folder')
			context.window_manager.popup_menu(draw, title = 'Not a file', icon = 'IMPORT')
			return { 'CANCELLED' }

		editMaterialLink = None
		for materialLink in collectionSettings.materialLinks:
			if materialLink.material == None: continue
			if materialLink.material.name == self.materialName:
				editMaterialLink = materialLink
				break

		if editMaterialLink == None:
			try: material = bpy.data.materials[self.materialName]
			except: return {'CANCELLED'}
			editMaterialLink = collectionSettings.materialLinks.add()
			editMaterialLink.material = material
		
		if self.relativeFilePath: editMaterialLink.filePath = bpy.path.relpath(self.filepath)
		else: editMaterialLink.filePath = self.filepath
		context.area.tag_redraw()
		return {'FINISHED'}
	
	def invoke(self, context, event):
		context.window_manager.fileselect_add(self)
		return {'RUNNING_MODAL'}

class GAME_EXPORT_PT_settings_material_link(bpy.types.Panel):
	bl_idname = 'GAME_EXPORT_PT_settings_material_link'
	bl_label = 'Material Links'
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_parent_id = 'GAME_EXPORT_PT_settings'
	bl_options = {'DEFAULT_CLOSED'}

	@classmethod
	def poll(cls, context: bpy.types.Context):
		settings = context.scene.gameExportSettings
		return len(settings.collectionList) != 0

	def draw(self, context):
		settings = context.scene.gameExportSettings
		collectionSettings = settings.collectionList[settings.collectionListIndex]
		materialNameSet = materialNameSetGet(collectionSettings.collection)
		materialLinksNameLookup = materialLinksNameLookupGet(collectionSettings)

		linkedCount = 0
		unlinkedCount = 0

		for materialName in materialNameSet:
			if materialLinksNameLookup.get(materialName) == None: unlinkedCount += 1
			else: linkedCount += 1

		self.layout.operator(GAME_EXPORT_OT_collection_material_link_search_files.__name__, icon='VIEWZOOM')
		self.layout.operator(GAME_EXPORT_OT_collection_material_link_clean.__name__, icon='FILE_REFRESH')
		self.layout.operator(GAME_EXPORT_OT_collection_material_link_remove_all.__name__, icon='TRASH')

		infoColumn = self.layout.column(align=True)
		infoColumn.label(text=f'{linkedCount} material{"s" * (linkedCount != 1)} linked')
		infoColumn.label(text=f'{unlinkedCount} material{"s" * (unlinkedCount != 1)} not linked')

class GAME_EXPORT_PT_settings_material_link_manual(bpy.types.Panel):
	bl_idname = 'GAME_EXPORT_PT_settings_material_link_manual'
	bl_label = 'Manually Edit'
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_parent_id = 'GAME_EXPORT_PT_settings_material_link'
	bl_options = {'DEFAULT_CLOSED'}

	@classmethod
	def poll(cls, context: bpy.types.Context):
		settings = context.scene.gameExportSettings
		return len(settings.collectionList) != 0

	def draw(self, context):
		settings = context.scene.gameExportSettings
		collectionSettings = settings.collectionList[settings.collectionListIndex]

		materialNameList = [*materialNameSetGet(collectionSettings.collection)]
		materialNameList.sort(key=str.casefold)
		materialLinksNameLookup = materialLinksNameLookupGet(collectionSettings)

		grid = self.layout.grid_flow(align=True, columns=max(math.floor(context.region.width / 300), 1))

		for materialName in materialNameList:
			row = grid.row()
			row.label(text=materialName)

			materialLink = materialLinksNameLookup.get(materialName)
			haveLink = (materialLink != None)
			if haveLink: text = bpy.path.display_name_from_filepath(materialLink.filePath)
			else: text = 'None'

			buttonGroup = row.row(align=True)
			sub = buttonGroup.row(align=True)
			sub.alignment = 'RIGHT'
			sub.operator(GAME_EXPORT_OT_collection_material_link_remove.__name__, text=text, icon='CHECKMARK' if haveLink else 'NONE', depress=haveLink).materialName = materialName
			sub.enabled = haveLink
			op = buttonGroup.operator(GAME_EXPORT_OT_collection_material_link_set.__name__, text='', icon='FILE_FOLDER')
			op.materialName = materialName
			if haveLink: op.filepath = materialLink.filePath

classes = (
	GAME_EXPORT_OT_show_export_info,
	GAME_EXPORT_OT_export,
	GAME_EXPORT_OT_collection_add,
	GAME_EXPORT_OT_collection_remove,
	GAME_EXPORT_OT_collection_move_up,
	GAME_EXPORT_OT_collection_move_down,
	GAME_EXPORT_UL_collection_list,
	GAME_EXPORT_OT_collection_static,
	GAME_EXPORT_PT_collection_static,
	GAME_EXPORT_OT_collection_mesh_render,
	GAME_EXPORT_PT_collection_mesh_render,
	GAME_EXPORT_OT_collection_light_render,
	GAME_EXPORT_PT_collection_light_render,
	GAME_EXPORT_OT_collection_collider,
	GAME_EXPORT_PT_collection_collider,
	GAME_EXPORT_PT_settings,
	GAME_EXPORT_PT_settings_inherit,
	GAME_EXPORT_OT_collection_material_link_search_files,
	GAME_EXPORT_OT_collection_material_link_clean,
	GAME_EXPORT_OT_collection_material_link_remove_all,
	GAME_EXPORT_OT_collection_material_link_remove,
	GAME_EXPORT_OT_collection_material_link_set,
	GAME_EXPORT_PT_settings_material_link,
	GAME_EXPORT_PT_settings_material_link_manual,
)

def register():
	for cls in classes: bpy.utils.register_class(cls)

def unregister():
	for cls in reversed(classes): bpy.utils.unregister_class(cls)