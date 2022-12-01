import time
import sys

import PySimpleGUI as sg
import pyvisa as visa

DIVIDER_FACTOR = 2025.4026
AGILENT_34401A_GUN_GPIB_ADDR: str = 'GPIB::10::INSTR'

layout = [[sg.Text("INITIALIZING", size=(0, 1), key='OUTPUT', font = ("Arial", 48))]]
window = sg.Window('GUN HV', layout, finalize=True)
window.refresh()


window['OUTPUT'].update(value='Initialize Agilent 34401A GUN')
window.refresh()
__resource_mgr = visa.ResourceManager()
try:
    __agilent_gpib_gun = __resource_mgr.open_resource(AGILENT_34401A_GUN_GPIB_ADDR)
except visa.Error:
    _logger.error('Couldn\'t connect to \'%s\', exiting now...', AGILENT_34401A_GUN_GPIB_ADDR)
    sys.exit() # TODO: change to adequate exit

window['OUTPUT'].update(value="*RST")
window.refresh()
__agilent_gpib_gun.write("*RST")
time.sleep(1.0)
window['OUTPUT'].update(value="CONF:VOLT:DC 10,0.00001")
window.refresh()
__agilent_gpib_gun.write("CONF:VOLT:DC 10,0.00001")
time.sleep(1)
window['OUTPUT'].update(value="DET:BAND 3")
window.refresh()
__agilent_gpib_gun.write("DET:BAND 3")
time.sleep(1)
window['OUTPUT'].update(value="INP:IMP:AUTO ON")
window.refresh()
__agilent_gpib_gun.write("INP:IMP:AUTO ON")
time.sleep(1)

window['OUTPUT'].update(value="VOLT:NPLC 100")
window.refresh()
__agilent_gpib_gun.write("VOLT:NPLC 100")
time.sleep(1)

window['OUTPUT'].update(value='Agilent 34401A initialization done')


while True:
    __agilent_gpib_gun.write('READ?')

    event, values = window.read(timeout=4000)
    if event == sg.WIN_CLOSED or event == 'Cancel':
        break

    voltage = float(__agilent_gpib_gun.read()) * DIVIDER_FACTOR
    window['OUTPUT'].update(value=f"VOLTAGE: {round(voltage):05d} V")

window.close()
