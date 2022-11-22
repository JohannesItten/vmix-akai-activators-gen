import copy
import xml.etree.ElementTree as ETree

def GetInputsGuid(Filename):
    ApiTree = ETree.parse(Filename)
    ApiTreeRoot = ApiTree.getroot()
    InputsTree = ApiTreeRoot.find('inputs')
    Inputs = {}
    for Input in InputsTree.findall('input'):
        Inputs[Input.attrib['number']] = Input.attrib['key']
    return Inputs


def GetShortcutsInfo(Filename):
    ShortcutsTree = ETree.parse(Filename)
    ShortcutsTreeRoot = ShortcutsTree.getroot()
    ShortcutsRoot = ShortcutsTreeRoot.find('Shortcuts')
    Shortcuts = []
    for Shortcut in ShortcutsRoot.findall('Shortcut'):
        InputNumber = Shortcut.find('Input').find('Number').text
        if InputNumber and int(InputNumber) != 0: #Exclude shortcuts without info about input
            Shortcuts.append({
                'function': Shortcut.find('Function').text,
                'note': Shortcut.find('MIDINote').text,
                'channel': Shortcut.find('MIDIChannel').text,
                'inputNumber': InputNumber,
                'mix': Shortcut.find('Mix').text
            })
    return Shortcuts


def GetOverlayNumber(FunctionName):
    OverlayNumber = 1
    for Char in FunctionName:
        if Char.isnumeric():
            OverlayNumber = int(Char)
            break
    return OverlayNumber


#AKAI Globals
#Circle: 64-71, 82-89
AKAI_CIRCLE_BUTTON_NAME = 'AKAI APCmini Circle LED'
AKAI_CIRCLE_BUTTON_RANGE = [*range(64, 72)] + [*range(82, 90)]
AKAI_SQUARE_BUTTON_NAME = 'AKAI APCmini Square LED'

AKAI_RED = 'Red'
AKAI_RED_BLINK = 'Red Blink'
AKAI_YELLOW = 'Yellow'
AKAI_YELLOW_BLINK = 'Yellow Blink'
AKAI_GREEN = 'Green'
AKAI_GREEN_BLINK = 'Green Blink'

AKAI_COLORS = {AKAI_RED: '#FF0000', AKAI_RED_BLINK: '#AA0000', AKAI_YELLOW: '#FFFF00', AKAI_YELLOW_BLINK: '#AAAA00', AKAI_GREEN: '#00FF00', AKAI_GREEN_BLINK: '#00AA00'}
AKAI_MIDI_VELOCITY = {AKAI_RED: 3, AKAI_RED_BLINK: 4, AKAI_YELLOW: 5, AKAI_YELLOW_BLINK: 6, AKAI_GREEN: 1, AKAI_GREEN_BLINK: 2}

#Input activator config
MIX_COLORS = [AKAI_RED, AKAI_GREEN, AKAI_YELLOW, AKAI_RED] #Color for mix. Mix1, Mix2, Mix3, Mix4
OVERLAY_FUNCTIONS = ['OverlayInput1', 'OverlayInput2', 'OverlayInput3', 'OverlayInput4']
ACTIVATORS_FUNCTION_CONFIG = {
    'PreviewInput': ['Input'],
    'Cut': ['Input'],
    'Fade': ['Input'],
    'Merge': ['Input'],
    'Stinger1': ['Input'],
    'Stinger2': ['Input'],
    'Stinger3': ['Input'],
    'Stinger4': ['Input'],
    'OverlayInput1': ['Overlay1', AKAI_RED_BLINK],
    'OverlayInput2': ['Overlay2', AKAI_GREEN_BLINK],
    'OverlayInput3': ['Overlay3', AKAI_YELLOW_BLINK],
    'OverlayInput4': ['Overlay4', AKAI_RED_BLINK],
    'Audio': ['InputAudio', AKAI_RED],
    'Solo': ['InputSolo', AKAI_YELLOW]
}

#MainGlobals
ConfigDir = 'vmixConfigs'
ApiFilename = 'api.xml'
ShortcutTemplateFilename = 'soccer.vMixShortcutTemplate'
ActivatorsFileExtension = 'vMixActivators'

#parse ApiXML to get input's guid's
InputsGuidInfo = GetInputsGuid(ConfigDir + '/' + ApiFilename)
#parse ShortcutsXML to get shortcut function, MIDI note, MIDI channel and input number
ShortcutsInfo = GetShortcutsInfo(ConfigDir + '/' + ShortcutTemplateFilename)

#load activators clean XML template
ACTIVATORS_TEMPLATE_FILENAME = "template/template." + ActivatorsFileExtension;
ActivatorsTemplateFile = ETree.parse(ACTIVATORS_TEMPLATE_FILENAME)
TemplateRoot = ActivatorsTemplateFile.getroot()
ActivatorTemplate = TemplateRoot.find('activator')

#create new activators in ET
for Shortcut in ShortcutsInfo:
    Function = Shortcut['function']
    Mix = int(Shortcut['mix'])
    InputNumber = Shortcut['inputNumber']
    if (Function not in ACTIVATORS_FUNCTION_CONFIG):
        continue

    ActivatorConfig = ACTIVATORS_FUNCTION_CONFIG[Function]

    Activator = copy.deepcopy(ActivatorTemplate)
    ActivatorFunction = ActivatorConfig[0]
    if Mix > 0:
        ActivatorFunction += 'Mix' + str(Mix + 1) #Added 1, cause vmix starts count mixes from 0 in ShortcutsXML

    Activator.find('event').text = ActivatorFunction
    Activator.find('inputGuid').text = InputsGuidInfo[InputNumber]
    Activator.find('inputNumber').text = InputNumber
    Activator.find('channel').text = Shortcut['channel']
    Activator.find('note').text = Shortcut['note']

    ActivatorColorName = AKAI_RED
    if (len(ActivatorConfig) > 1):
        ActivatorColorName = ActivatorConfig[1]
    else:
        ActivatorColorName = MIX_COLORS[Mix]

    IsOverlayFunction = Function in OVERLAY_FUNCTIONS
    IsButtonCircle = int(Shortcut['note']) in AKAI_CIRCLE_BUTTON_RANGE

    DisplayName = ''
    ActivatorVelocity = AKAI_MIDI_VELOCITY[ActivatorColorName]

    if IsButtonCircle and IsOverlayFunction:
        DisplayName = 'Blink'
        ActivatorVelocity = 2
    elif IsButtonCircle:
        DisplayName = 'Default'
        ActivatorVelocity = 1
    elif not IsButtonCircle and IsOverlayFunction:
        DisplayName = ActivatorColorName

    Activator.find('value').attrib = {
        'displayName': DisplayName,
        'minimum': '0',
        # 'maximum' means Midi answer Velocity. 1 - Green, 2 - Green Blinky, 3 - Red, 4 - Red Blinky, 5 - Yellow, 6 - Yellow Blinky
        'maximum': str(ActivatorVelocity),
        'range': 'False',
        'noteOffDisabled': 'True',
        'displayColor': AKAI_COLORS[ActivatorColorName],
        'typeDisplayName': 'AKAI APCmini Circle LED' if IsButtonCircle else 'AKAI APCmini Square LED'
    }
    TemplateRoot.append(Activator)

#remove ActivatorTemplate from file
TemplateRoot.remove(ActivatorTemplate)
#write new activators preset
ActivatorsTemplateFile.write(file_or_filename = 'gen/test.' + ActivatorsFileExtension, encoding = 'utf-8', xml_declaration = True)