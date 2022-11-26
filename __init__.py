bl_info = {
	"name": "Game Exporter",
	"description": "Exports multiple game assets with one click.",
	"author": "codec-xyz",
	"version": (1, 0, 0),
	"blender": (3, 3, 0),
	"location": "View3D",
	"category": "Import-Export",
}

modulesNames = ['settings', 'export', 'view']

import sys
import importlib

modulesFullNames = {}
for currentModuleName in modulesNames:
	if 'DEBUG_MODE' in sys.argv:
		modulesFullNames[currentModuleName] = ('{}'.format(currentModuleName))
	else:
		modulesFullNames[currentModuleName] = ('{}.{}'.format(__name__, currentModuleName))
 
for currentModuleFullName in modulesFullNames.values():
	if currentModuleFullName in sys.modules:
		importlib.reload(sys.modules[currentModuleFullName])
	else:
		globals()[currentModuleFullName] = importlib.import_module(currentModuleFullName)
		setattr(globals()[currentModuleFullName], 'modulesNames', modulesFullNames)
 
def register():
	for currentModuleName in modulesFullNames.values():
		if currentModuleName in sys.modules:
			if hasattr(sys.modules[currentModuleName], 'register'):
				sys.modules[currentModuleName].register()
 
def unregister():
	for currentModuleName in modulesFullNames.values():
		if currentModuleName in sys.modules:
			if hasattr(sys.modules[currentModuleName], 'unregister'):
				sys.modules[currentModuleName].unregister()
 
if __name__ == "__main__":
	register()