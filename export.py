import bpy
from .settings import *

def findLayerCollection(collection: bpy.types.Collection, layerCollection: bpy.types.LayerCollection):
	for sub in layerCollection.children:
		if sub.collection == collection: return sub
		found = findLayerCollection(collection, sub)
		if(found): return found
	return None

def copyLinkedFlatCollectionObjects(fromC: bpy.types.Collection, toC: bpy.types.Collection, types: "set[str]"):
	for obj in fromC.all_objects:
		if(obj.type not in types): continue
		copyObj = obj.copy()
		toC.objects.link(copyObj)

def makeInstancesReal(collection: bpy.types.Collection):
	bpy.ops.object.select_all(action = 'DESELECT')
	for obj in collection.objects: obj.select_set(True)
	bpy.ops.object.duplicates_make_real()

def convertToMeshes(context: bpy.types.Context, collection: bpy.types.Collection):
	bpy.ops.object.select_all(action = 'DESELECT')
	affectedObjects = []
	for obj in collection.objects:
		if(obj.type in ["MESH", "CURVE", "SURFACE", "META", "FONT", "CURVES"]):
			affectedObjects.append(obj)
			obj.select_set(True)
	if(len(context.selected_objects) != 0):
		context.view_layer.objects.active = context.selected_objects[0]
		bpy.ops.object.convert(target = "MESH", keep_original = True)
	for obj in affectedObjects: bpy.data.objects.remove(obj)
	return [obj for obj in context.selected_objects]

def makeNormalsJoinable(context: bpy.types.Context, obj: bpy.types.Object):
	mesh: bpy.types.Mesh = obj.data
	context.view_layer.objects.active = obj
	if(not mesh.use_auto_smooth):
		mesh.auto_smooth_angle = 3.14159
		mesh.use_auto_smooth = True
		bpy.ops.mesh.customdata_custom_splitnormals_add()
	elif(not obj.data.has_custom_normals): bpy.ops.mesh.customdata_custom_splitnormals_add()

def joinObjects(context: bpy.types.Context, objs: "list[bpy.types.Object]"):
	if(len(objs) <= 1): return
	bpy.ops.object.select_all(action = 'DESELECT')
	for obj in objs: obj.select_set(True)
	context.view_layer.objects.active = objs[0]
	joinedMeshes = [obj.data for obj in objs[1:]]
	bpy.ops.object.join()
	for mesh in joinedMeshes: bpy.data.meshes.remove(mesh)
	return objs[0]

def exportCollection(context, filePath: str, settings: GAME_EXPORT_settings):
	source = settings.collection
	temp = bpy.data.collections.new(name = "Temp")
	context.scene.collection.children.link(temp)

	allowedType = set()
	if(settings.shouldIncludeMeshes): allowedType.update(["MESH", "CURVE", "SURFACE", "META", "FONT", "CURVES", "EMPTY"])
	if(settings.shouldIncludeLights): allowedType.update(["LIGHT", "EMPTY"])

	copyLinkedFlatCollectionObjects(source, temp, allowedType)
	makeInstancesReal(temp)

	createdMeshObjects = []
	if(settings.shouldIncludeMeshes):
		createdMeshObjects = convertToMeshes(context, temp)
		if(settings.shouldJoin and len(createdMeshObjects) >= 2):
			for obj in createdMeshObjects: makeNormalsJoinable(context, obj)
			joinedObject = joinObjects(context, createdMeshObjects)
			joinedObject.name = source.name
			createdMeshObjects = [joinedObject]
	
	createdLightData = []
	for obj in temp.objects:
		if(obj.type == "MESH" and settings.shouldIncludeMeshes): ""
		elif(obj.type == "LIGHT" and settings.shouldIncludeLights):
			obj.data = obj.data.copy()
			createdLightData.append(obj.data)
			obj.data.energy *= settings.lightMultiplier
		else:
			bpy.data.objects.remove(obj)
	
	context.view_layer.active_layer_collection = findLayerCollection(temp, context.view_layer.layer_collection)
	try:
		bpy.ops.export_scene.fbx(filepath = filePath + settings.exportName + ".fbx", use_active_collection = True, bake_space_transform = True)
	except Exception as e:
		print("Game Export: " + settings.exportName + " failed to export fbx\n" + e)
	
	for meshObject in createdMeshObjects: bpy.data.meshes.remove(meshObject.data)
	for lightData in createdLightData: bpy.data.lights.remove(lightData)
	for object in temp.objects: bpy.data.objects.remove(object)
	bpy.data.collections.remove(temp)