import bpy
from .settings import *

class GAME_EXPORT_OT_selection_static(bpy.types.Operator):
	'''Set Selection Static type'''
	bl_idname = 'game_export.selection_static'
	bl_label = 'Set static type'
	bl_options = {'UNDO'}

	setTypeOptions = ['INHERIT', 'NOTHING','EVERYTHING', 'CONTRIBUTE_GI', 'OCCLUDER_STATIC', 'BATCHING_STATIC', 'NAVIGATION_STATIC', 'OCCLUDEE_STATIC', 'OFF_MESH_LINK_GENERATION', 'REFLECTION_PROBE_STATIC']

	setType: bpy.props.EnumProperty(name='Set Type', items=[
		('INHERIT', 'Inherit', ''),
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
		return len(context.selected_objects) > 0

	def execute(self, context):
		for object in bpy.context.selected_objects:
			if self.setType == 'INHERIT': object.gameExportSettings.static[0] = self.value
			elif self.setType == 'NOTHING': object.gameExportSettings.static[1:] = [not self.value] * 7
			elif self.setType == 'EVERYTHING': object.gameExportSettings.static[1:] = [self.value] * 7
			else: object.gameExportSettings.static[GAME_EXPORT_OT_selection_static.setTypeOptions.index(self.setType) - 2] = self.value
		context.area.tag_redraw()
		return {'FINISHED'}

class GAME_EXPORT_PT_selection_static(bpy.types.Panel):
	bl_idname = 'GAME_EXPORT_PT_selection_static'
	bl_label = 'Selection Static'
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'HEADER'
	bl_category = ''

	@classmethod
	def poll(cls, context: bpy.types.Context):
		return len(context.selected_objects) > 0

	def getSelectionInfo(context: bpy.types.Context, index: int):
		settings = context.scene.gameExportSettings
		if len(settings.collectionList) != 0: staticInherit = settings.collectionList[settings.collectionListIndex].static
		else: staticInherit = [True] * 7

		def objectStaticInfo(static: 'list[bool]'):
			if index == 0: return static[0]
			static = staticInherit if static[0] else static[1:]
			if index == 1: return not any(static)
			if index == 2: return all(static)
			return static[index - 3]

		value = objectStaticInfo(context.selected_objects[0].gameExportSettings.static)
		for object in context.selected_objects[1:]:
			if value != objectStaticInfo(object.gameExportSettings.static):
				return 1
		if value: return 2
		return 0
	
	def drawSummary(context: bpy.types.Context, layout: bpy.types.UILayout):
		isInherit = GAME_EXPORT_PT_selection_static.getSelectionInfo(context, 0)
		isNothingStatic = GAME_EXPORT_PT_selection_static.getSelectionInfo(context, 1)
		isEverythingStatic = GAME_EXPORT_PT_selection_static.getSelectionInfo(context, 2)

		if isInherit == 2: icon = 'DUPLICATE'
		elif isInherit == 1: icon = 'REMOVE'
		elif isNothingStatic == 2: icon = 'BLANK1'
		elif isEverythingStatic == 2: icon = 'CHECKMARK'
		else: icon = 'REMOVE'

		row = layout.row(align=True)
		row.label(text=f'Static{" (Inherit)" * (isInherit == 2)}')

		sub = row.row(align=True)
		g = sub.operator(GAME_EXPORT_OT_selection_static.__name__, text='', icon=icon, depress=(isEverythingStatic == 2))
		g.setType = 'EVERYTHING'
		g.value = (isEverythingStatic != 2)
		if isInherit != 0: sub.enabled = False

		row.popover(panel=GAME_EXPORT_PT_selection_static.__name__, text='', icon='DOWNARROW_HLT')

	def draw(self, context: bpy.types.Context):
		self.layout.label(text='Static')
		column = self.layout.column(align=True)
		for i in [0, 1, 2, 3, 4, 7, 5, 6, 8, 9]:
			value = GAME_EXPORT_PT_selection_static.getSelectionInfo(context, i)
			if i == 0: isInherit = value

			row = column.row(align=True)
			g = row.operator(GAME_EXPORT_OT_selection_static.__name__, text=['Inherit', 'Nothing', 'Everything', 'Contribute GI', 'Occluder Static', 'Batching Static', 'Navigation Static', 'Occludee Static', 'Off Mesh Link Generation', 'Reflection Probe'][i], icon=['BLANK1', 'REMOVE', 'CHECKMARK'][value], depress=(value == 2))
			g.setType = GAME_EXPORT_OT_selection_static.setTypeOptions[i]
			g.value = (value != 2)
			if i != 0 and isInherit != 0: row.enabled = False

def selectionQuickToggleEnumEdit(name: str, codeName: str, enum, propName: str, shortName: 'list[str] | None' = None):
	class GAME_EXPORT_OT_selection_(bpy.types.Operator):
		bl_description = f'Set Selection {name} Type'
		bl_idname = f'game_export.selection_{codeName}'
		bl_label = f'{name} Type'
		bl_options = {'UNDO'}

		value: bpy.props.EnumProperty(name='Set Value', items=[*enum, ('LAZY_ON', 'Lazy on', '')])

		@classmethod
		def poll(cls, context: bpy.types.Context):
			return len(context.selected_objects) > 0

		def execute(self, context):
			for object in bpy.context.selected_objects:
				if self.value == 'LAZY_ON':
					if getattr(object.gameExportSettings, propName) == enum[1][0]:
						setattr(object.gameExportSettings, propName, enum[2][0])
				else: setattr(object.gameExportSettings, propName, self.value)
			context.area.tag_redraw()
			return {'FINISHED'}

	class GAME_EXPORT_PT_selection_(bpy.types.Panel):
		bl_idname = f'GAME_EXPORT_PT_selection_{codeName}'
		bl_label = f'Selection {name}'
		bl_space_type = 'VIEW_3D'
		bl_region_type = 'HEADER'
		bl_category = ''

		@classmethod
		def poll(cls, context: bpy.types.Context):
			return len(context.selected_objects) > 0

		def getSelectionInfo(context: bpy.types.Context, index: int):
			settings = context.scene.gameExportSettings
			if len(settings.collectionList) != 0: inheritValue = getattr(settings.collectionList[settings.collectionListIndex], propName)
			else: inheritValue = enum[2][0]

			def objectStaticInfo(value: str):
				if index == 0: return value == 'INHERIT'
				value = inheritValue if value == 'INHERIT' else value
				return value == enum[index][0]

			value = objectStaticInfo(getattr(context.selected_objects[0].gameExportSettings, propName))
			for object in context.selected_objects[1:]:
				if value != objectStaticInfo(getattr(object.gameExportSettings, propName)):
					return 1
			if value: return 2
			return 0
		
		def drawSummary(context: bpy.types.Context, layout: bpy.types.UILayout):
			isInherit = GAME_EXPORT_PT_selection_.getSelectionInfo(context, 0)
			isOff = GAME_EXPORT_PT_selection_.getSelectionInfo(context, 1)

			if shortName:
				settings = context.scene.gameExportSettings
				if len(settings.collectionList) != 0: inheritValue = getattr(settings.collectionList[settings.collectionListIndex], propName)
				else: inheritValue = enum[2][0]
				def getValue(value): return inheritValue if value == 'INHERIT' else value

				value = getValue(getattr(context.selected_objects[0].gameExportSettings, propName))
				for object in context.selected_objects[1:]:
					if value != getValue(getattr(object.gameExportSettings, propName)):
						value = ''
						break
				if value: value = shortName[[i[0] for i in enum].index(value) - 1]
			else: value = ''

			if isInherit == 2: icon = 'DUPLICATE'
			elif isInherit == 1: icon = 'REMOVE'
			elif isOff == 2: icon = 'BLANK1'
			elif isOff == 0: icon = 'CHECKMARK'
			else: icon = 'REMOVE'

			row = layout.row(align=True)
			row.label(text=f'{name}{" (Inherit)" * (isInherit == 2)}')

			sub = row.row(align=True)
			sub.alignment = 'RIGHT'
			g = sub.operator(f'GAME_EXPORT_OT_selection_{codeName}', text=value, icon=icon, depress=(isOff == 0))
			g.value = enum[1][0] if isOff == 0 else 'LAZY_ON'
			if isInherit != 0: sub.enabled = False

			row.popover(f'GAME_EXPORT_PT_selection_{codeName}', text='', icon='DOWNARROW_HLT')

		def draw(self, context: bpy.types.Context):
			self.layout.label(text=name)
			column = self.layout.column(align=True)
			for i, enumValue in enumerate(enum):
				value = GAME_EXPORT_PT_selection_.getSelectionInfo(context, i)
				if i == 0: isInherit = value

				row = column.row(align=True)
				g = row.operator(f'GAME_EXPORT_OT_selection_{codeName}', text=enumValue[1], icon=['BLANK1', 'REMOVE', 'CHECKMARK'][value], depress=(value == 2 and (i == 0 or isInherit == 0)))
				g.value = enumValue[0]

	return (GAME_EXPORT_OT_selection_, GAME_EXPORT_PT_selection_)

(GAME_EXPORT_OT_selection_mesh_render, GAME_EXPORT_PT_selection_mesh_render) = selectionQuickToggleEnumEdit('Mesh Render', 'mesh_render', meshRenderEnum, 'meshRender')
(GAME_EXPORT_OT_selection_light_render, GAME_EXPORT_PT_selection_light_render) = selectionQuickToggleEnumEdit('Light Render', 'light_render', lightRenderEnum, 'lightRender')
(GAME_EXPORT_OT_selection_collider, GAME_EXPORT_PT_selection_collider) = selectionQuickToggleEnumEdit('Collider', 'collider', colliderEnum, 'collider', ['', 'Box', 'Mesh'])

class GAME_EXPORT_PT_selection_settings(bpy.types.Panel):
	bl_idname = 'GAME_EXPORT_PT_selection_settings'
	bl_label = 'Selected Objects Settings'
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = 'GameExport'

	@classmethod
	def poll(cls, context: bpy.types.Context):
		return len(context.selected_objects) > 0

	def draw(self, context: bpy.types.Context):
		self.layout.box().label(text=f'{len(context.selected_objects)} object{"s" if len(context.selected_objects) != 1 else ""} selected')

		GAME_EXPORT_PT_selection_static.drawSummary(context, self.layout)
		GAME_EXPORT_PT_selection_mesh_render.drawSummary(context, self.layout)
		GAME_EXPORT_PT_selection_light_render.drawSummary(context, self.layout)
		GAME_EXPORT_PT_selection_collider.drawSummary(context, self.layout)

classes = (
	GAME_EXPORT_OT_selection_static,
	GAME_EXPORT_PT_selection_static,
	GAME_EXPORT_OT_selection_mesh_render,
	GAME_EXPORT_PT_selection_mesh_render,
	GAME_EXPORT_OT_selection_light_render,
	GAME_EXPORT_PT_selection_light_render,
	GAME_EXPORT_OT_selection_collider,
	GAME_EXPORT_PT_selection_collider,
	GAME_EXPORT_PT_selection_settings,
)

def register():
	for cls in classes: bpy.utils.register_class(cls)

def unregister():
	for cls in reversed(classes): bpy.utils.unregister_class(cls)