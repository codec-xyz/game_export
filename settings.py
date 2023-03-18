import bpy

meshRenderEnum = [
	('INHERIT', 'Inherit', ''),
	('NONE', 'None', ''),
	('MESH_RENDERER', 'Mesh Renderer', ''),
	#('SKINNED_MESH_RENDERER', 'Skinned Mesh Renderer', ''),
]

lightRenderEnum = [
	('INHERIT', 'Inherit', ''),
	('NONE', 'None', ''),
	('LIGHT', 'Light', ''),
]

colliderEnum = [
	('INHERIT', 'Inherit', ''),
	('NONE', 'None', ''),
	('BOX', 'Box Collider', ''),
	('MESH', 'Mesh Collider', ''),
]

class GAME_EXPORT_collection_material_link_settings(bpy.types.PropertyGroup):
	material: bpy.props.PointerProperty(name='Material', type=bpy.types.Material)
	filePath: bpy.props.StringProperty(name='Material File Path', description='Choose a material file', default = '//', subtype='FILE_PATH')

class GAME_EXPORT_collection_settings(bpy.types.PropertyGroup):
	collection: bpy.props.PointerProperty(name='Collection', type=bpy.types.Collection)
	shouldExport: bpy.props.BoolProperty(name='Should Export', default=True)
	exportName: bpy.props.StringProperty(name='Export Name', default='gameExport')
	lightMultiplier: bpy.props.FloatProperty(name='Light Multiplier', default=0.1, soft_min=0)
	fixFBXTextureTint: bpy.props.BoolProperty(name='Fix FBX Texture Tint', description='Fixes FBX exporter exporting material textures with the hidden color value as the tint', default=True)

	#inherit settings
	static: bpy.props.BoolVectorProperty(name='Static Flags', size=7, default=[True]*7)
	meshRender: bpy.props.EnumProperty(name='Mesh Render', items=meshRenderEnum[1:], default='MESH_RENDERER')
	lightRender: bpy.props.EnumProperty(name='Light Render', items=lightRenderEnum[1:], default='LIGHT')
	collider: bpy.props.EnumProperty(name='Collider', items=colliderEnum[1:], default='NONE')

	materialLinks: bpy.props.CollectionProperty(type=GAME_EXPORT_collection_material_link_settings)

class GAME_EXPORT_settings(bpy.types.PropertyGroup):
	filePath: bpy.props.StringProperty(name = 'Export File Path', description='Choose a directory', default = '//', subtype='DIR_PATH')
	collectionList: bpy.props.CollectionProperty(type = GAME_EXPORT_collection_settings)
	collectionListIndex: bpy.props.IntProperty(name = 'Export Collection Index', default = -1)

class GAME_EXPORT_object_settings(bpy.types.PropertyGroup):
	static: bpy.props.BoolVectorProperty(name='Static Flags', size=8, default=[True]*8)
	meshRender: bpy.props.EnumProperty(name='Mesh Render', items=meshRenderEnum, default='INHERIT')
	lightRender: bpy.props.EnumProperty(name='Light Render', items=lightRenderEnum, default='INHERIT')
	collider: bpy.props.EnumProperty(name='Collider', items=colliderEnum, default='INHERIT')

def materialNameSetGet(collection: bpy.types.Collection) -> 'set[str]':
	materialsNameSet: 'set[str]' = set()
	for object in collection.all_objects:
		if object.type == 'EMPTY' and object.instance_collection:
			materialsNameSet.update(materialNameSetGet(object.instance_collection))
		for materialName in object.material_slots:
			materialsNameSet.add(materialName.name)
	return materialsNameSet

def materialLinksNameLookupGet(collectionSettings: GAME_EXPORT_collection_settings) -> 'dict[str, GAME_EXPORT_collection_material_link_settings]':
	materialLinksLookup = {}
	for materialLink in collectionSettings.materialLinks:
		if materialLink.material == None: continue
		materialLinksLookup[materialLink.material.name] = materialLink
	return materialLinksLookup

classes = (
	GAME_EXPORT_collection_material_link_settings,
	GAME_EXPORT_collection_settings,
	GAME_EXPORT_settings,
	GAME_EXPORT_object_settings,
)

def register():
	for cls in classes: bpy.utils.register_class(cls)
	bpy.types.Scene.gameExportSettings = bpy.props.PointerProperty(name = 'Game Export Settings', type = GAME_EXPORT_settings)
	bpy.types.Object.gameExportSettings = bpy.props.PointerProperty(name = 'Game Export Object Settings', type = GAME_EXPORT_object_settings)

def unregister():
	for cls in reversed(classes): bpy.utils.unregister_class(cls)
	del bpy.types.Scene.gameExportSettings
	del bpy.types.Object.gameExportSettings

def doesDataExist():
	return hasattr(bpy.types.Scene, 'gameExportSettings')

def deleteData():
	del bpy.types.Scene.gameExportSettings
	del bpy.types.Object.gameExportSettings

	for scene in bpy.data.scenes: del scene['gameExportSettings']
	for object in bpy.data.objects: del object['gameExportSettings']
