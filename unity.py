import random
import string
from .xxhash import xxh64_intdigest
from .asset import Transform
from mathutils import Vector

UNITY_LINK_TYPE_DEFAULT = 0 #used for nonexistant default things like default material
UNITY_LINK_TYPE_MATERIAL_FILE = 2 #file types like: mat
UNITY_LINK_TYPE_OTHER = 3 #other file types like: fbx, obj, prefab

class AssetLink:
	assetId: str = ''
	assetFileId: str = ''
	linkType: str = ''

	def __init__(self, assetId: str = '', assetFileId: str = '', linkType: str = UNITY_LINK_TYPE_OTHER):
		self.assetId = assetId
		self.assetFileId = assetFileId
		self.linkType = linkType

	def fromFile(self, assetId: str = ''):
		return AssetLink(assetId, self.assetFileId, self.linkType)

	def toString(self, fileId: str = ''):
		if self.assetId == '': return '{fileID: 0}'
		if self.assetFileId == fileId: return f'{{fileID: {self.assetId}}}'
		return f'{{fileID: {self.assetId}, guid: {self.assetFileId}, type: {self.linkType}}}'

#Default Material - {fileID: 10303, guid: 0000000000000000f000000000000000, type: 0}
UNITY_LINK_DEFAULT_MATERIAL = AssetLink('10303', '0000000000000000f000000000000000', UNITY_LINK_TYPE_DEFAULT)

NEWLINE = '\n'

def yamlFindFirstValue(file: str, variable: str, start: int = None, end: int = None):
	index = file.find(variable, start, end)
	if index == -1: return ''
	index += len(variable) + 2
	lineEnd = file.find('\n', index)
	if lineEnd == -1: return file[index:]
	return file[index:lineEnd]

def makeDefaultMetaFile_fbx(link: AssetLink):
	return f'''fileFormatVersion: 2
guid: {link.assetFileId}
ModelImporter:
  serializedVersion: 19301
  internalIDToNameTable: []
  externalObjects: {{}}
  materials:
    materialImportMode: 1
    materialName: 0
    materialSearch: 1
    materialLocation: 1
  animations:
    legacyGenerateAnimations: 4
    bakeSimulation: 0
    resampleCurves: 1
    optimizeGameObjects: 0
    motionNodeName: 
    rigImportErrors: 
    rigImportWarnings: 
    animationImportErrors: 
    animationImportWarnings: 
    animationRetargetingWarnings: 
    animationDoRetargetingWarnings: 0
    importAnimatedCustomProperties: 0
    importConstraints: 0
    animationCompression: 1
    animationRotationError: 0.5
    animationPositionError: 0.5
    animationScaleError: 0.5
    animationWrapMode: 0
    extraExposedTransformPaths: []
    extraUserProperties: []
    clipAnimations: []
    isReadable: 0
  meshes:
    lODScreenPercentages: []
    globalScale: 1
    meshCompression: 0
    addColliders: 0
    useSRGBMaterialColor: 1
    sortHierarchyByName: 1
    importVisibility: 1
    importBlendShapes: 1
    importCameras: 1
    importLights: 1
    fileIdsGeneration: 2
    swapUVChannels: 0
    generateSecondaryUV: 1
    useFileUnits: 1
    keepQuads: 0
    weldVertices: 1
    preserveHierarchy: 0
    skinWeightsMode: 0
    maxBonesPerVertex: 4
    minBoneWeight: 0.001
    meshOptimizationFlags: -1
    indexFormat: 0
    secondaryUVAngleDistortion: 8
    secondaryUVAreaDistortion: 15.000001
    secondaryUVHardAngle: 88
    secondaryUVPackMargin: 4
    useFileScale: 1
  tangentSpace:
    normalSmoothAngle: 60
    normalImportMode: 0
    tangentImportMode: 3
    normalCalculationMode: 4
    legacyComputeAllNormalsFromSmoothingGroupsWhenMeshHasBlendShapes: 0
    blendShapeNormalImportMode: 1
    normalSmoothingSource: 0
  referencedClips: []
  importAnimation: 1
  humanDescription:
    serializedVersion: 3
    human: []
    skeleton: []
    armTwist: 0.5
    foreArmTwist: 0.5
    upperLegTwist: 0.5
    legTwist: 0.5
    armStretch: 0.05
    legStretch: 0.05
    feetSpacing: 0
    globalScale: 1
    rootMotionBoneName: 
    hasTranslationDoF: 0
    hasExtraRoot: 0
    skeletonHasParents: 1
  lastHumanDescriptionAvatarSource: {{instanceID: 0}}
  autoGenerateAvatarMappingIfUnspecified: 1
  animationType: 2
  humanoidOversampling: 1
  avatarSetup: 0
  additionalBone: 0
  userData: 
  assetBundleName: 
  assetBundleVariant: 
'''

def makeDefaultMetaFile_prefab(link: AssetLink):
	return f'''fileFormatVersion: 2
guid: {link.assetFileId}
PrefabImporter:
  externalObjects: {{}}
  userData: 
  assetBundleName: 
  assetBundleVariant: 
'''

def getFbxMetaFileLink(file: str):
	return AssetLink('', yamlFindFirstValue(file, 'guid'))

def getMaterialMetaFileLink(file: str):
	#return AssetLink(yamlFindFirstValue(file, 'mainObjectFileID'), yamlFindFirstValue(file, 'guid'), UNITY_LINK_TYPE_MATERIAL_FILE)
	return AssetLink('2100000', yamlFindFirstValue(file, 'guid'), UNITY_LINK_TYPE_MATERIAL_FILE)

def getFbxId_mesh(name: str):
	hash = xxh64_intdigest(f'Type:Mesh->{name}0')
	if(hash < 9223372036854775807): return hash
	return hash - 18446744073709551616

def getFbxId_material(name: str):
	hash = xxh64_intdigest(f'Type:Material->{name}0')
	if(hash < 9223372036854775807): return hash
	return hash - 18446744073709551616

#used to id files
def makeRandomGuid():
	return ''.join(random.choice(string.hexdigits) for _ in range(32))

#labeled fileId by untiy, used to id things within a file
#64 bit signed int
def makeRandomAssetId():
	return random.getrandbits(63)

unityYamlHeader = '''%YAML 1.1
%TAG !u! tag:unity3d.com,2011:'''

def makeLinksList(componentLink: AssetLink, name: str, links: 'list[AssetLink]'):
	if len(links) == 0: return ' []'
	return ''.join(f'{NEWLINE}  - {name}{link.toString(componentLink.assetFileId)}' for link in links)

UNITY_GAME_OBJECT_STATIC_NOTHING = 0
UNITY_GAME_OBJECT_STATIC_EVERYTHING = 4294967295
UNITY_GAME_OBJECT_STATIC_CONTRIBUTE_GI = 1
UNITY_GAME_OBJECT_STATIC_OCCLUDER_STATIC = 2
UNITY_GAME_OBJECT_STATIC_OCCLUDEE_STATIC = 16
UNITY_GAME_OBJECT_STATIC_BATCHING_STATIC = 4
UNITY_GAME_OBJECT_STATIC_NAVIGATION_STATIC = 8
UNITY_GAME_OBJECT_STATIC_OFF_MESH_LINK_GENERATION = 32
UNITY_GAME_OBJECT_STATIC_REFLECTION_PROBE_STATIC = 64

def makeGameObject(link: AssetLink, name: str, componentLinks: 'list[AssetLink]', staticFlags: int = UNITY_GAME_OBJECT_STATIC_EVERYTHING):
	return f'''--- !u!1 &{link.assetId}
GameObject:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  serializedVersion: 6
  m_Component:{makeLinksList(link, 'component: ', componentLinks)}
  m_Layer: 0
  m_Name: {name}
  m_TagString: Untagged
  m_Icon: {{fileID: 0}}
  m_NavMeshLayer: 0
  m_StaticEditorFlags: {staticFlags}
  m_IsActive: 1'''

def makeTransfom(link: AssetLink, gameObjectLink: AssetLink, parentTransformLink: AssetLink, childTransformLinks: 'list[AssetLink]', transform: Transform):
	return f'''--- !u!4 &{link.assetId}
Transform:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {gameObjectLink.toString(link.assetFileId)}
  m_LocalRotation: {{x: {transform.rotation.x}, y: {-transform.rotation.z}, z: {transform.rotation.y}, w: {transform.rotation.w}}}
  m_LocalPosition: {{x: {-transform.location.x}, y: {transform.location.z}, z: {-transform.location.y}}}
  m_LocalScale: {{x: {transform.scale.x}, y: {transform.scale.z}, z: {transform.scale.y}}}
  m_Children:{makeLinksList(link, '', childTransformLinks)}
  m_Father: {parentTransformLink.toString(link.assetFileId)}
  m_RootOrder: 0
  m_LocalEulerAnglesHint: {{x: 0, y: 0, z: 0}}'''

def makeMeshFilter(link: AssetLink, gameObjectLink: AssetLink, meshLink: AssetLink):
	return f'''--- !u!33 &{link.assetId}
MeshFilter:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {gameObjectLink.toString(link.assetFileId)}
  m_Mesh: {meshLink.toString(link.assetFileId)}'''

#ignored if not GI static
UNITY_MESH_RENDERER_RECEIVE_GI_LIGHTMAPS = 1
UNITY_MESH_RENDERER_RECEIVE_GI_LIGHT_PROBES = 2

def makeMeshRenderer(link: AssetLink, gameObjectLink: AssetLink, materialLinks: 'list[AssetLink]', receiveGI: int = UNITY_MESH_RENDERER_RECEIVE_GI_LIGHTMAPS):
  return f'''--- !u!23 &{link.assetId}
MeshRenderer:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {gameObjectLink.toString(link.assetFileId)}
  m_Enabled: 1
  m_CastShadows: 1
  m_ReceiveShadows: 1
  m_DynamicOccludee: 1
  m_MotionVectors: 1
  m_LightProbeUsage: 1
  m_ReflectionProbeUsage: 1
  m_RayTracingMode: 2
  m_RenderingLayerMask: 1
  m_RendererPriority: 0
  m_Materials:{makeLinksList(link, '', materialLinks)}
  m_StaticBatchInfo:
    firstSubMesh: 0
    subMeshCount: 0
  m_StaticBatchRoot: {{fileID: 0}}
  m_ProbeAnchor: {{fileID: 0}}
  m_LightProbeVolumeOverride: {{fileID: 0}}
  m_ScaleInLightmap: 1
  m_ReceiveGI: {receiveGI}
  m_PreserveUVs: 0
  m_IgnoreNormalsForChartDetection: 0
  m_ImportantGI: 0
  m_StitchLightmapSeams: 1
  m_SelectedEditorRenderState: 3
  m_MinimumChartSize: 4
  m_AutoUVMaxDistance: 0.5
  m_AutoUVMaxAngle: 89
  m_LightmapParameters: {{fileID: 0}}
  m_SortingLayerID: 0
  m_SortingLayer: 0
  m_SortingOrder: 0'''

def makeMeshCollider(link: AssetLink, gameObjectLink: AssetLink, meshLink: AssetLink):
  return f'''--- !u!64 &{link.assetId}
MeshCollider:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {gameObjectLink.toString(link.assetFileId)}
  m_Material: {{fileID: 0}}
  m_IsTrigger: 0
  m_Enabled: 1
  serializedVersion: 4
  m_Convex: 0
  m_CookingOptions: 30
  m_Mesh: {meshLink.toString(link.assetFileId)}'''

def makeBoxCollider(link: AssetLink, gameObjectLink: AssetLink, size: Vector = Vector([1, 1, 1]), center: Vector = Vector([0, 0, 0])):
  return f'''--- !u!65 &{link.assetId}
BoxCollider:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {gameObjectLink.toString(link.assetFileId)}
  m_Material: {{fileID: 0}}
  m_IsTrigger: 0
  m_Enabled: 1
  serializedVersion: 2
  m_Size: {{x: {-size.x}, y: {size.z}, z: {-size.y}}}
  m_Center: {{x: {-center.x}, y: {center.z}, z: {-center.y}}}'''

UNITY_LIGHT_TYPE_SPOT = 0
UNITY_LIGHT_TYPE_DIRECTIONAL = 1
UNITY_LIGHT_TYPE_POINT = 2
UNITY_LIGHT_TYPE_AREA_RECTANGLE = 3
UNITY_LIGHT_TYPE_AREA_DISK = 4

UNITY_LIGHT_MODE_MIXED = 1
UNITY_LIGHT_MODE_BAKED = 2
UNITY_LIGHT_MODE_REALTIME = 4

UNITY_LIGHT_SHADOWS_NONE = 0
UNITY_LIGHT_SHADOWS_HARD = 1
UNITY_LIGHT_SHADOWS_SOFT = 2

def makeLight(link: AssetLink, gameObjectLink: AssetLink, type: int, mode: int, shadows: int, color: 'list[float]', inensity: float, spotlightAngleDeg: float, spotlightInnerAngleDeg: float, areaSize: 'list[float]', cutoffDistance: int = 10):
	return f'''--- !u!108 &{link.assetId}
Light:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {gameObjectLink.toString(link.assetFileId)}
  m_Enabled: 1
  serializedVersion: 10
  m_Type: {type}
  m_Shape: 0
  m_Color: {{r: {color[0]}, g: {color[1]}, b: {color[2]}, a: 1}}
  m_Intensity: {inensity}
  m_Range: {cutoffDistance}
  m_SpotAngle: {spotlightAngleDeg}
  m_InnerSpotAngle: {spotlightInnerAngleDeg}
  m_CookieSize: 10
  m_Shadows:
    m_Type: {shadows}
    m_Resolution: -1
    m_CustomResolution: -1
    m_Strength: 1
    m_Bias: 0.05
    m_NormalBias: 0.4
    m_NearPlane: 0.2
    m_CullingMatrixOverride:
      e00: 1
      e01: 0
      e02: 0
      e03: 0
      e10: 0
      e11: 1
      e12: 0
      e13: 0
      e20: 0
      e21: 0
      e22: 1
      e23: 0
      e30: 0
      e31: 0
      e32: 0
      e33: 1
    m_UseCullingMatrixOverride: 0
  m_Cookie: {{fileID: 0}}
  m_DrawHalo: 0
  m_Flare: {{fileID: 0}}
  m_RenderMode: 0
  m_CullingMask:
    serializedVersion: 2
    m_Bits: 4294967295
  m_RenderingLayerMask: 1
  m_Lightmapping: {mode}
  m_LightShadowCasterMode: 0
  m_AreaSize: {{x: {areaSize[0]}, y: {areaSize[0]}}}
  m_BounceIntensity: 1
  m_ColorTemperature: 6570
  m_UseColorTemperature: 0
  m_BoundingSphereOverride: {{x: 0, y: 0, z: 0, w: 0}}
  m_UseBoundingSphereOverride: 0
  m_ShadowRadius: 0
  m_ShadowAngle: 0'''