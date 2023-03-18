import bpy
import mathutils

class Transform():
	location: mathutils.Vector
	rotation: mathutils.Quaternion
	scale: mathutils.Vector

	def __init__(self):
		self.location = mathutils.Vector([0, 0, 0])
		self.rotation = mathutils.Quaternion([1, 0, 0, 0])
		self.scale = mathutils.Vector([1, 1, 1])

	def parentMatrix(self, matrix: mathutils.Matrix):
		result = matrix @ mathutils.Matrix.LocRotScale(self.location, self.rotation, self.scale)
		self.location = result.to_translation()
		self.rotation = result.to_quaternion()
		self.scale = result.to_scale()
		return self
	
	def isIdentity(self) -> bool:
		return (self.location == mathutils.Vector([0, 0, 0])
		and self.rotation == mathutils.Quaternion([1, 0, 0, 0])
		and self.scale == mathutils.Vector([1, 1, 1]))
	
	def isNoRotation(self) -> bool:
		return self.rotation == mathutils.Quaternion([1, 0, 0, 0])
	
	def copy(self):
		copy = Transform()
		copy.location = self.location.copy()
		copy.rotation = self.rotation.copy()
		copy.scale = self.scale.copy()
		return copy

class Light():
	transform: Transform
	light: bpy.types.Light

	def __init__(self):
		self.transform = Transform()

def hasActiveModifiers(object: bpy.types.Object):
	for modifier in object.modifiers.values():
		if modifier.show_viewport: return True
	return False

def toMesh(depsgraph: bpy.types.Depsgraph, object: bpy.types.Object, transform: 'mathutils.Matrix | None') -> bpy.types.Mesh:
	if object.type == 'MESH' and not transform and not hasActiveModifiers(object): return object.data

	mesh = bpy.data.meshes.new_from_object(object.evaluated_get(depsgraph), preserve_all_data_layers = True, depsgraph = depsgraph)
	if not mesh: mesh = bpy.data.meshes.new(name='')
	if transform: mesh.transform(transform @ object.matrix_world)
	return mesh

def makeNormalsJoinable(context: bpy.types.Context, obj: bpy.types.Object):
	mesh: bpy.types.Mesh = obj.data
	context.view_layer.objects.active = obj
	if(not mesh.use_auto_smooth):
		mesh.auto_smooth_angle = 3.14159
		mesh.use_auto_smooth = True
		bpy.ops.mesh.customdata_custom_splitnormals_add()
	elif(not obj.data.has_custom_normals): bpy.ops.mesh.customdata_custom_splitnormals_add()

def makeUVsJoinable(mesh: bpy.types.Mesh):
	for index, uvLayer in enumerate(mesh.uv_layers):
		mesh.uv_layers[0].name = f'UVMap{index}'

def joinMeshes(context: bpy.types.Context, meshes: 'list[bpy.types.Mesh]') -> 'bpy.types.Mesh | None':
	if len(meshes) == 0: return None
	if len(meshes) == 1: return meshes[0]

	tempCollection = bpy.data.collections.new(name = '')
	context.scene.collection.children.link(tempCollection)
	bpy.ops.object.select_all(action = 'DESELECT')

	for mesh in meshes:
		object = bpy.data.objects.new('', mesh)
		tempCollection.objects.link(object)
		object.select_set(True)
		makeNormalsJoinable(context, object)
		makeUVsJoinable(mesh)
	
	joinMesh = bpy.data.meshes.new('')
	joinObject = bpy.data.objects.new('', joinMesh)
	tempCollection.objects.link(joinObject)
	joinObject.select_set(True)
	context.view_layer.objects.active = joinObject

	bpy.ops.object.join()

	bpy.data.collections.remove(tempCollection)
	bpy.data.objects.remove(joinObject)

	return joinMesh

def canConvertToMesh(object: bpy.types.Object) -> bool:
	return object.type in ['MESH', 'CURVE', 'SURFACE', 'META', 'FONT', 'CURVES']

def getBoxCollider(object: bpy.types.Object, transform: 'mathutils.Matrix | None') -> Transform:
	x = [vec[0] for vec in object.bound_box]
	y = [vec[1] for vec in object.bound_box]
	z = [vec[2] for vec in object.bound_box]

	minVec = mathutils.Vector([min(x), min(y), min(z)])
	maxVec = mathutils.Vector([max(x), max(y), max(z)])

	colliderTransform = Transform()
	colliderTransform.location = (minVec + maxVec) / 2
	colliderTransform.scale = maxVec - minVec

	if transform: colliderTransform.parentMatrix(transform @ object.matrix_world)
	
	return colliderTransform

def getLightSettings(object: bpy.types.Object, transform: 'mathutils.Matrix | None') -> Light:
	light = Light()
	if(object.type != 'LIGHT'):
		light.light = bpy.data.lights.new("")
		return light

	if transform: light.transform.parentMatrix(transform @ object.matrix_world)
	
	light.light = object.data
	return light

class Asset():
	name: str
	mesh: 'bpy.types.Mesh | None'
	lights: 'list[Light]'
	boxColliders: 'list[Transform]'
	meshColliders: 'list[bpy.types.Mesh]'

	def __init__(self, depsgraph: bpy.types.Depsgraph, assetObject: bpy.types.Object, inheritMeshRender: str, inheritLightRender: str, inheritCollider: str):
		self.lights = []
		self.boxColliders = []
		self.meshColliders = []

		if assetObject.type == 'EMPTY' and assetObject.instance_collection: self.name = assetObject.instance_collection.name
		elif assetObject.type != 'EMPTY': self.name = assetObject.data.name
		else: self.name = assetObject.name

		meshParts: 'list[bpy.types.Mesh]' = []

		def addObject(object: bpy.types.Object, transform: 'mathutils.Matrix | None'):
			#viewport hidden objects do not get evaluted correctly
			if object.hide_viewport: return

			if object.type == 'EMPTY' and object.instance_collection:
				for subObject in object.instance_collection.all_objects:
					addObject(subObject, transform @ object.matrix_world if transform else mathutils.Matrix.Identity(4))

			meshRender = inheritMeshRender if object.gameExportSettings.meshRender == 'INHERIT' else object.gameExportSettings.meshRender
			lightRender = inheritLightRender if object.gameExportSettings.lightRender == 'INHERIT' else object.gameExportSettings.lightRender
			collider = inheritCollider if object.gameExportSettings.collider == 'INHERIT' else object.gameExportSettings.collider

			if meshRender == 'MESH_RENDERER' and canConvertToMesh(object):
				meshParts.append(toMesh(depsgraph, object, transform))

			elif lightRender == 'LIGHT' and object.type == 'LIGHT':
				self.lights.append(getLightSettings(object, transform))

			if collider == 'MESH' and canConvertToMesh(object):
				self.meshColliders.append(toMesh(depsgraph, object, transform))

			elif collider == 'BOX' and canConvertToMesh(object):
				self.boxColliders.append(getBoxCollider(object, transform))
		
		addObject(assetObject, None)
		
		self.mesh = joinMeshes(bpy.context, meshParts)

		for meshPart in meshParts:
			if meshPart.users == 0 and meshPart != self.mesh: bpy.data.meshes.remove(meshPart)
	
	def preview(self):
		object = bpy.data.objects.new('preview', self.mesh)
		object.data.use_auto_smooth = True
		bpy.context.scene.collection.objects.link(object)

	def cleanUp(self):
		if self.mesh and self.mesh.users == 0: bpy.data.meshes.remove(self.mesh)
		for meshCollider in self.meshColliders:
			if meshCollider.users == 0: bpy.data.meshes.remove(meshCollider)
	
	def getDataUid(object: bpy.types.Object):
		if object.type == 'EMPTY' and object.instance_collection: return str(id(object.instance_collection))
		if object.type == 'MESH' and not hasActiveModifiers(object): return str(id(object.data)) + object.gameExportSettings.meshRender + object.gameExportSettings.lightRender + object.gameExportSettings.collider
		if object.type == 'LIGHT': return str(id(object.data))
		return str(id(object))