bl_info = {
	'name': 'Game Export',
	'description': 'Configure settings and export from Blender to Unity with one click.',
	'author': 'codec-xyz',
	'version': (2, 0, 1),
	'blender': (3, 4, 1),
	'location': 'View3D',
	'category': 'Import-Export',
}

DEV_MODE = False
def devPrint(*args):
	if DEV_MODE: print(*args)
devPrint('--------------------------------------game_export init load----------------------------------------')

import sys
import importlib

PIP_MODULES = ['xxhash']
MODULES = ['settings', 'install', 'panel_preferences']
MODULES_CORE = ['asset', 'unity', 'export', 'panel_exportSettings', 'panel_objectSettings']

def dependenciesAreLoaded():
	for module in PIP_MODULES:
		if f'{__package__}.{module}' not in sys.modules: return False
	return True

def loadModules(modules: 'list[str]'):
	for module in modules:
		moduleFullPath = f'{__package__}.{module}'
		try:
			if moduleFullPath in sys.modules: importlib.reload(sys.modules[moduleFullPath])
			else: importlib.import_module(moduleFullPath)
		except Exception as e:
			print(f'{__package__}: module "{module}" could not be loaded')
			print('\n'.join(e.args))

def registerModules(modules: 'list[str]'):
	for module in modules:
		try: sys.modules[f'{__package__}.{module}'].register()
		except: ''

def unregisterModules(modules: 'list[str]'):
	for module in reversed(modules):
		try: sys.modules[f'{__package__}.{module}'].unregister()
		except: ''

def register():
	devPrint(f'{__package__}: running register()')
	loadModules([*PIP_MODULES, *MODULES, *MODULES_CORE])
	registerModules([*MODULES, *MODULES_CORE] if dependenciesAreLoaded() else MODULES)

def unregister():
	devPrint(f'{__package__}: running unregister()')
	unregisterModules([*MODULES, *MODULES_CORE])