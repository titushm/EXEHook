# IMPORTS
import colorama, pymem, os, pathlib, datetime, re, configparser, win32com.client, inspect

# PREREQUISITES
colorama.init()
config = configparser.ConfigParser()

# VARIABLES
loaded_mods, mods, on_load_list, missing_files = [], [], [], []

# FUNCTIONS
def exitScript():
	print(f"{colorama.Fore.LIGHTBLACK_EX + getTimestamp() + colorama.Fore.YELLOW} Press any key to exit")
	os.system("@pause >nul")
	exit()

def getTimestamp():
	return f'[{datetime.datetime.now().strftime("%H:%M:%S.%f")}]'

def restrictImports(code, allowed_imports):
	import_regex = r'(?:^import|(?<=\n)import|(?<=\n)from)\s+(\w+(?:\s*,\s*\w+)*(?:\s+as\s+\w+)*|\w+\s+import\s+(\w+(?:\s*,\s*\w+)*(?:\s+as\s+\w+)*))'
	imports = re.findall(import_regex, code)
	imports = [i for sublist in imports for i in sublist if i]
	imports = ",".join(imports)
	imports = imports.split(',')
	for module in imports:
		if module not in allowed_imports:
			return True
	return False

def restrictCode(code):
	import_function_regex = r'__import__'
	matches = re.search(import_function_regex, code)
	if matches:
		return True
	return False

# CONSTANTS
MODS_PATH = pathlib.Path(f"{os.getcwd()}\\hookMods")
MODS_WATERMARK = colorama.Fore.LIGHTBLACK_EX + getTimestamp() + colorama.Fore.LIGHTBLUE_EX + ' {mod_info.name}' + colorama.Fore.RESET
SHELL = win32com.client.Dispatch("WScript.Shell")
GAME_PATH = SHELL.CreateShortCut("game.lnk").Targetpath
PROCESS_NAME = os.path.basename(GAME_PATH)
CONFIG_PROPERTIES = ["name", "author", "description", "version", "imports"]

# EVENTS
class hookEvents():
	def onLoad(callback):
		on_load_list.append(callback)
	def loaded():
		for callback in on_load_list:
			callback()

print(f"{colorama.Fore.LIGHTBLACK_EX + getTimestamp() + colorama.Fore.LIGHTGREEN_EX} Starting {PROCESS_NAME}")
try:
	os.startfile("game.lnk") # Start the game
except Exception as error:
	print(f"{colorama.Fore.LIGHTBLACK_EX + getTimestamp() + colorama.Fore.LIGHTRED_EX} Failed to start {PROCESS_NAME} {colorama.Fore.LIGHTBLACK_EX}Error: {error}")
	exitScript()
print(f"{colorama.Fore.LIGHTBLACK_EX + getTimestamp() + colorama.Fore.LIGHTGREEN_EX} Successfully started {PROCESS_NAME}")
print(f"{colorama.Fore.LIGHTBLACK_EX + getTimestamp() + colorama.Fore.YELLOW} Hooking into {PROCESS_NAME}")
try:
	GAME_MEMORY = pymem.Pymem(PROCESS_NAME) # Attach to the game memory so mods have an api to use
except:
	print(f"{colorama.Fore.LIGHTBLACK_EX + getTimestamp() + colorama.Fore.LIGHTRED_EX} Cannot find process {PROCESS_NAME}")
	exitScript()
print(f"{colorama.Fore.LIGHTBLACK_EX + getTimestamp() + colorama.Fore.LIGHTGREEN_EX} Successfully Hooked into {PROCESS_NAME}")
print(f"{colorama.Fore.LIGHTBLACK_EX + getTimestamp() + colorama.Fore.YELLOW} Loading mods")

for mod_path in MODS_PATH.glob("*/"): # Loop through every mod in the mods path
	config.read(f"{mod_path}\\config.ini")
	mod_name = "unknown"
	modFileMissing = not os.path.exists(f"{mod_path}\\mod.py")
	configFileMissing = not os.path.exists(f"{mod_path}\\config.ini")
	if modFileMissing and not configFileMissing: mod_name = config["mod"].name;
	if modFileMissing: missing_files.append("mod.py")
	if configFileMissing: missing_files.append("config.ini")
	if not os.path.exists(f"{mod_path}\\mod.py") or not os.path.exists(f"{mod_path}\\mod.py"):
		print(f"{colorama.Fore.LIGHTBLACK_EX + getTimestamp() + colorama.Fore.LIGHTRED_EX} Skipping mod '{mod_name}' did not contain all the required files, missing: {missing_files}")
		continue
	try:
		for config_property in CONFIG_PROPERTIES:
			config["mod"][config_property]
	except KeyError:
		print(f"{colorama.Fore.LIGHTBLACK_EX + getTimestamp() + colorama.Fore.LIGHTRED_EX} Skipping mod '{mod_info['name']}' invalid config file format")
		continue
	with open(f"{mod_path}\\mod.py", "r") as mod:
		mod_code = mod.read().replace("print(", f"print(f\"{MODS_WATERMARK}: \"+")
		mod_info = config["mod"]
		restricted_code = restrictCode(mod_code)
		restricted_import = restrictImports(mod_code, config["mod"]["imports"])
		if restricted_import:
			print(f"{colorama.Fore.LIGHTBLACK_EX + getTimestamp() + colorama.Fore.LIGHTRED_EX} Skipped loading mod \"{mod_info['name']}\" {colorama.Fore.LIGHTBLACK_EX}Error: Imported a module that not defined in the config imports") # Skip loading a mod if it has an undocumented import
			continue
		if restricted_code:
			print(f"{colorama.Fore.LIGHTBLACK_EX + getTimestamp() + colorama.Fore.LIGHTRED_EX} Skipped loading mod \"{mod_info['name']}\" {colorama.Fore.LIGHTBLACK_EX}Error: Contained code that could be used to bypass mod safety features") # Skip loading a mod if it has a security concern
			continue
		try:
			mods.append(mod_code)
		except Exception as mod_error:
			print(f"{colorama.Fore.LIGHTBLACK_EX + getTimestamp() + colorama.Fore.LIGHTRED_EX} Skipped loading mod \"{mod_info['name']}\" {colorama.Fore.LIGHTBLACK_EX}Error: {mod_error}") # Skip loading a mod if it has an error
		else:
			print(f"{colorama.Fore.LIGHTBLACK_EX + getTimestamp() + colorama.Fore.LIGHTBLACK_EX} Loaded mod {colorama.Fore.CYAN + mod_info['name']} {mod_info['version'] + colorama.Fore.LIGHTBLACK_EX} by {colorama.Fore.CYAN + mod_info['author']}")
			loaded_mods.append(mod_info['name']) # Add a mod to the loaded mods list if the mod load properly
			exec(mod_code)
mods_amount = len(list(MODS_PATH.glob("*/")))
loaded_mods_amount = len(loaded_mods)
print(f"{colorama.Fore.LIGHTBLACK_EX + getTimestamp() + colorama.Fore.LIGHTGREEN_EX} Loaded {colorama.Fore.LIGHTBLACK_EX + str(loaded_mods_amount)}/{str(mods_amount) + colorama.Fore.GREEN} mods {colorama.Fore.LIGHTBLACK_EX + str(loaded_mods)}")
hookEvents.loaded()

print(f"{colorama.Fore.LIGHTBLACK_EX + getTimestamp() + colorama.Fore.YELLOW} Press any key to exit")
os.system("@pause >nul")