import bpy

class GAME_EXPORT_collection_settings(bpy.types.PropertyGroup):
	collection: bpy.props.PointerProperty(name = "Collection", type = bpy.types.Collection)
	shouldExport: bpy.props.BoolProperty(name = "Should Export", default = True)
	exportName: bpy.props.StringProperty(name = "Export Name", default = "gameExport")
	shouldIncludeMeshes: bpy.props.BoolProperty(name = "Should Include Meshes", default = True)
	shouldIncludeLights: bpy.props.BoolProperty(name = "Should Include Lights", default = True)
	shouldJoin: bpy.props.BoolProperty(name = "Should Join", default = True)
	lightMultiplier: bpy.props.FloatProperty(name = "Light Multiplier", default = 0.1, soft_min = 0)

class GAME_EXPORT_settings(bpy.types.PropertyGroup):
	filePath: bpy.props.StringProperty(name = "Export File Path", description="Choose a directory", default = "//", subtype='DIR_PATH')
	collectionList: bpy.props.CollectionProperty(type = GAME_EXPORT_collection_settings)
	collectionListIndex: bpy.props.IntProperty(name = "Export Collection Index", default = -1)