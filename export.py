import bpy
from .settings import *
from .asset import *
from .unity import *

def findLayerCollection(collection: bpy.types.Collection, layerCollection: bpy.types.LayerCollection):
	for sub in layerCollection.children:
		if sub.collection == collection: return sub
		found = findLayerCollection(collection, sub)
		if(found): return found
	return None

def exportCollection(context: bpy.types.Context, filePath: str, settings: GAME_EXPORT_collection_settings):
	hierarchyDict: 'dict[int, list[bpy.types.Collection | bpy.types.Object]]' = {}
	assetDict: 'dict[str, Asset]' = {}
	assetNameSet: 'set[str]' = set()
	exportMeshNames: 'dict[int, str]' = {} #possible mesh collisions
	depsgraph = context.evaluated_depsgraph_get()
	objectRenameList = []
	meshRenameList = []

	def addCollection(collection: bpy.types.Collection):
		collectionEntry = hierarchyDict.get(id(collection), [])

		for child in collection.children:
			collectionEntry.append(child)
			addCollection(child)
		
		for child in collection.objects:
			if child.parent:
				objectEntry = hierarchyDict.get(id(child.parent), [])
				objectEntry.append(child)
				hierarchyDict[id(child.parent)] = objectEntry
			else:
				collectionEntry.append(child)
		
		hierarchyDict[id(collection)] = collectionEntry

	addCollection(settings.collection)
	
	with open(filePath + settings.exportName + '.fbx.meta', 'a+') as file:
		file.seek(0)
		fbxMetaFile = file.read()
		if fbxMetaFile == '':
			fbxFileLink = AssetLink('', makeRandomGuid())
			file.write(makeDefaultMetaFile_fbx(fbxFileLink))
		else:
			fbxFileLink = getFbxMetaFileLink(fbxMetaFile)

	def yamlJoin(string1: str, string2: str):
		if string1 == '' or string2 == '': return string1 + string2
		return string1 + '\n' + string2

	def getAsset(object: bpy.types.Object) -> Asset:
		asset = assetDict.get(Asset.getDataUid(object))
		if asset: return asset

		asset = assetDict[Asset.getDataUid(object)] = Asset(depsgraph, object, settings.meshRender, settings.lightRender, settings.collider)
		if asset.name in assetNameSet:
			i = 0
			while f'{asset.name}.{str(i).rjust(3, "0")}' in assetNameSet: i += 1
			asset.name += f'.{str(i).rjust(3, "0")}'
		assetNameSet.add(asset.name)

		return asset

	materialLinksNameLookup = materialLinksNameLookupGet(settings)
	materialToUnityLink: 'dict[int, AssetLink]' = {}

	def getMaterialLink(material: bpy.types.Material) -> AssetLink:
		unityLink = materialToUnityLink.get(id(material))
		if unityLink != None: return unityLink

		materialLink = materialLinksNameLookup.get(material.name)
		if materialLink:
			try:
				with open(bpy.path.abspath(materialLink.filePath) + '.meta', 'r') as file:
					unityLink = getMaterialMetaFileLink(file.read())
					print(unityLink)
			except: ''
		
		if unityLink == None: unityLink = fbxFileLink.fromFile(getFbxId_material(material.name))
		materialToUnityLink[id(material)] = unityLink
		return unityLink

	def getMeshMaterialsFbxOrder(mesh: bpy.types.Mesh) -> 'list[bpy.types.Material]':
		materialIndexList = []
		materialCount = len(mesh.materials)
		for polygon in mesh.polygons:
			if polygon.material_index in materialIndexList: continue
			materialIndexList.append(polygon.material_index)
			if len(materialIndexList) == materialCount: break
		return [mesh.materials[index] for index in materialIndexList]

	def exportUnityLight(light: bpy.types.Light, componentLink: AssetLink, gameObjectLink: AssetLink) -> str:
		shadows = UNITY_LIGHT_SHADOWS_NONE
		color = light.color
		inensity = light.energy * settings.lightMultiplier
		spotlightAngleDeg = 0
		spotlightInnerAngleDeg = 0
		areaSize = [1, 1]

		if light.type == 'POINT': type = UNITY_LIGHT_TYPE_POINT
		elif light.type == 'SUN': type = UNITY_LIGHT_TYPE_DIRECTIONAL
		elif light.type == 'SPOT':
			type = UNITY_LIGHT_TYPE_SPOT
			spotlightAngleDeg = light.spot_size
			spotlightInnerAngleDeg = light.spot_size * (1 - light.spot_blend)
		elif light.type == 'AREA' and light.shape == 'SQUARE':
			type = UNITY_LIGHT_TYPE_AREA_RECTANGLE
			areaSize = [light.size, light.size]
		elif light.type == 'AREA' and light.shape == 'RECTANGLE':
			type = UNITY_LIGHT_TYPE_AREA_RECTANGLE
			areaSize = [light.size, light.size_y]
		elif light.type == 'AREA' and light.shape == 'DISK':
			type = UNITY_LIGHT_TYPE_AREA_DISK
			areaSize = [light.size, light.size]
		elif light.type == 'AREA' and light.shape == 'ELLIPSE':
			type = UNITY_LIGHT_TYPE_AREA_DISK
			size = (light.size + light.size_y) * 0.5
			areaSize = [size, size]
		
		if context.scene.render.engine == 'BLENDER_EEVEE':
			if light.use_shadow: shadows = UNITY_LIGHT_SHADOWS_SOFT
		elif context.scene.render.engine == 'CYCLES':
			if light.cast_shadow: shadows = UNITY_LIGHT_SHADOWS_SOFT

		return makeLight(componentLink, gameObjectLink, type, UNITY_LIGHT_MODE_BAKED, shadows, color, inensity, spotlightAngleDeg, spotlightInnerAngleDeg, areaSize, 10)

	def exportUnityAsset(asset: Asset, gameObjectLink: AssetLink, transformLink = AssetLink()) -> 'tuple[list[str], list[str], str, mathutils.Quaternion]':
		file = ''
		tansformLinks = []
		componentLinks = []
		applyRotation = mathutils.Quaternion([1, 0, 0, 0])

		#mesh
		if asset.mesh:
			componentLink = AssetLink(makeRandomAssetId())
			componentLinks.append(componentLink)
			meshName = exportMeshNames.get(id(asset.mesh))
			if not meshName:
				exportMeshNames[id(asset.mesh)] = meshName = asset.name
			file = yamlJoin(file, makeMeshFilter(componentLink, gameObjectLink, fbxFileLink.fromFile(getFbxId_mesh(meshName))))

			componentLink = AssetLink(makeRandomAssetId())
			componentLinks.append(componentLink)
			materialList = [getMaterialLink(material) for material in getMeshMaterialsFbxOrder(asset.mesh)]
			if len(materialList) == 0: materialList = [UNITY_LINK_DEFAULT_MATERIAL]
			file = yamlJoin(file, makeMeshRenderer(componentLink, gameObjectLink, materialList))
		
		#lights
		lightIndex = 0
		for light in asset.lights:
			if not asset.mesh and len(asset.lights) == 1 and len(asset.boxColliders) == 0 and len(asset.meshColliders) == 0:
				if not light.light.type == 'POINT': applyRotation = mathutils.Quaternion([0.7071068286895752, 0.7071068286895752, 0, 0])
				componentLink = AssetLink(makeRandomAssetId())
				componentLinks.append(componentLink)
				file = yamlJoin(file, exportUnityLight(light.light, componentLink, gameObjectLink))
				continue

			subGameObjectLink = AssetLink(makeRandomAssetId())
			subTransformLink = AssetLink(makeRandomAssetId())
			subComponentLink = AssetLink(makeRandomAssetId())
			file = yamlJoin(file, makeGameObject(subGameObjectLink, f'{asset.name}.light.{str(lightIndex).rjust(3, "0")}', [subTransformLink, subComponentLink]))
			transform = light.transform.copy()
			transform.rotation.rotate(mathutils.Quaternion([0.7071068286895752, 0.7071068286895752, 0, 0]))
			file = yamlJoin(file, makeTransfom(subTransformLink, subGameObjectLink, transformLink, [], transform))
			file = yamlJoin(file, exportUnityLight(light.light, subComponentLink, subGameObjectLink))

			lightIndex += 1
		
		#box colliders
		boxColliderIndex = 0
		for boxCollider in asset.boxColliders:
			if boxCollider.isNoRotation():
				componentLink = AssetLink(makeRandomAssetId())
				componentLinks.append(componentLink)
				file = yamlJoin(file, makeBoxCollider(componentLink, gameObjectLink, boxCollider.scale, boxCollider.location))
				continue

			subGameObjectLink = AssetLink(makeRandomAssetId())
			subTransformLink = AssetLink(makeRandomAssetId())
			subComponentLink = AssetLink(makeRandomAssetId())
			file = yamlJoin(file, makeGameObject(subGameObjectLink, f'{asset.name}.boxCollider.{str(boxColliderIndex).rjust(3, "0")}', [subTransformLink, subComponentLink]))
			file = yamlJoin(file, makeTransfom(subTransformLink, subGameObjectLink, transformLink, [], boxCollider))
			file = yamlJoin(file, makeBoxCollider(subComponentLink, subGameObjectLink))

			boxColliderIndex += 1

		#mesh colliders
		for i, meshCollider in enumerate(asset.meshColliders):
			componentLink = AssetLink(makeRandomAssetId())
			componentLinks.append(componentLink)
			meshName = exportMeshNames.get(id(meshCollider))
			if not meshName:
				if meshCollider == asset.mesh: meshName = asset.name
				else: meshName = f'{asset.name}.meshCollider.{str(i).rjust(3, "0")}'
				exportMeshNames[id(meshCollider)] = meshName
			file = yamlJoin(file, makeMeshCollider(componentLink, gameObjectLink, fbxFileLink.fromFile(getFbxId_mesh(meshName))))
			
		return (tansformLinks, componentLinks, file, applyRotation)

	def exportUnityObject(object: 'bpy.types.Collection | bpy.types.Object', parentTransformLink = AssetLink()) -> 'tuple[str, str]':
		file = ''
		children = hierarchyDict.get(id(object), [])
		gameObjectLink = AssetLink(makeRandomAssetId())
		transformLink = AssetLink(makeRandomAssetId())
		childTransformLinks = []
		childComponentLinks = [transformLink]

		for child in children:
			childData = exportUnityObject(child, transformLink)
			childTransformLinks.append(childData[0])
			file = yamlJoin(file, childData[1])
		
		assetData = None
		if type(object) == bpy.types.Collection: transformMatrix = mathutils.Matrix.Identity(4)
		else:
			transformMatrix = object.matrix_local
			assetData = exportUnityAsset(getAsset(object), gameObjectLink, transformLink)
			childTransformLinks.extend(assetData[0])
			childComponentLinks.extend(assetData[1])
			file = yamlJoin(file, assetData[2])
			

		staticFlagsList = settings.static
		if type(object) == bpy.types.Object and not object.gameExportSettings.static[0]: staticFlagsList = object.gameExportSettings.static[1:]
		staticFlags = sum([pow(2, i) * isOn for i, isOn in enumerate(staticFlagsList)])
		if staticFlags == 127: staticFlags = UNITY_GAME_OBJECT_STATIC_EVERYTHING

		file = yamlJoin(file, makeGameObject(gameObjectLink, object.name, childComponentLinks, staticFlags))
		transform = Transform().parentMatrix(transformMatrix)
		if assetData: transform.rotation.rotate(assetData[3])
		file = yamlJoin(file, makeTransfom(transformLink, gameObjectLink, parentTransformLink, childTransformLinks, transform))

		return (transformLink, file)
	
	prefabFile = yamlJoin(unityYamlHeader, exportUnityObject(settings.collection)[1])

	with open(filePath + settings.exportName + '.prefab', 'w') as file: file.write(prefabFile)

	tempCollection = bpy.data.collections.new(name = '')
	context.scene.collection.children.link(tempCollection)
	context.view_layer.active_layer_collection = findLayerCollection(tempCollection, context.view_layer.layer_collection)

	def freeObjectName(name: str):
		if name not in bpy.data.objects: return
		randomName = ''.join(random.choice(string.ascii_letters) for _ in range(16))
		bpy.data.objects[name].name = randomName
		objectRenameList.append((name, randomName))
	
	def freeMeshName(name: str):
		if name not in bpy.data.meshes: return
		randomName = ''.join(random.choice(string.ascii_letters) for _ in range(16))
		bpy.data.meshes[name].name = randomName
		meshRenameList.append((name, randomName))
	
	exportedMeshes: 'set[bpy.types.Mesh]' = set()
	def addExportMesh(mesh: bpy.types.Mesh):
			if mesh in exportedMeshes: return
			exportedMeshes.add(mesh)
			name = exportMeshNames.get(id(mesh))
			freeObjectName(name)
			if mesh.name != name:
				freeMeshName(name)
				meshRenameList.append((mesh.name, name))
				mesh.name = name
			object = bpy.data.objects.new(name, mesh)
			object.data.use_auto_smooth = True
			tempCollection.objects.link(object)

	for asset in assetDict.values():
		if asset.mesh:
			addExportMesh(asset.mesh)
		for meshCollider in asset.meshColliders:
			addExportMesh(meshCollider)

	changedMaterialValues = []

	if settings.fixFBXTextureTint:
		for materialName in materialNameSetGet(settings.collection):
			nodeTree = bpy.data.materials[materialName].node_tree

			materialOutput = None
			for node in nodeTree.nodes:
				if node.type == 'OUTPUT_MATERIAL':
					materialOutput = node
					break
			if materialOutput == None: continue

			surfaceLinks = materialOutput.inputs['Surface'].links
			if len(surfaceLinks) == 0: continue
			surfaceNode = surfaceLinks[0].from_node
			if surfaceNode.bl_idname != 'ShaderNodeBsdfPrincipled': continue

			if not surfaceNode.inputs['Base Color'].is_linked: continue

			changedMaterialValues.append((surfaceNode,
				[*surfaceNode.inputs['Base Color'].default_value],
			))

			surfaceNode.inputs['Base Color'].default_value = [1, 1, 1, 1]

	try:
		bpy.ops.export_scene.fbx(filepath = filePath + settings.exportName + ".fbx", use_active_collection = True, bake_space_transform = True)
	except Exception as e:
		print(f'{__package__}:  {settings.collection.name} failed to export fbx\n{e}')

	for change in changedMaterialValues:
		print(change[0], change[1])
		change[0].inputs['Base Color'].default_value = change[1]

	for object in tempCollection.objects: bpy.data.objects.remove(object)
	bpy.data.collections.remove(tempCollection)

	for rename in reversed(objectRenameList):
		if rename[1] not in bpy.data.objects: continue
		bpy.data.objects[rename[1]].name = rename[0]

	for rename in reversed(meshRenameList):
		if rename[1] not in bpy.data.meshes: continue
		bpy.data.meshes[rename[1]].name = rename[0]

	for asset in assetDict.values():
		asset.cleanUp()