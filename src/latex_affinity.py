'''
 Latex beads affinity test

'''

from opentrons import labware, instruments, modules, robot
from opentrons.util.vector import Vector
from opentrons.drivers.rpi_drivers.gpio import set_button_light
from time import sleep, monotonic, perf_counter
import logging

metadata = {
   'protocolName' : 'Latex affinity',
   'description'  : 'Latex beads affinity test',
   'author'       : 'Carlos Bilbao, Pablo Villalobos',
   'source'       : 'https://github.com/Zildj1an/SELEX'
}

# [1] Labware

Falcon           = labware.load('Falcon_Samples',    slot = '1')
plate_samples    = labware.load('96-flat',       slot = 3)
Eppendorf        = labware.load('Eppendorf_Samples', slot = 4)
tiprack        = labware.load('opentrons-tiprack-300ul', slot=5)

# Use the regular trash as trash_liquid, but displace the pipette to avoid collisions
trash = robot.fixed_trash().top()
displacement = Vector(0,30,100)
trash_liquid = (trash[0], displacement)

# [2] Pipettes
pipette = instruments.P300_Single(mount = 'left', tip_racks=[tiprack])

# Pipette flow rates: left and right, aspirate and dispense
flow_rate = {'a_l': 300, 'd_l': 300}

max_speed_per_axis = {'x': 600,'y': 400,'z': 125,'a': 125,'b': 40,'c': 40}
robot.head_speed(**max_speed_per_axis)


def robot_wait_tiprack():

    if not robot.is_simulating():
       robot.comment("Waiting...")
       while not robot._driver.read_button():
          set_button_light(blue=True, red=True, green=False)
          sleep(0.5)

       robot._driver.turn_on_blue_button_light()


def custom_pick_up_tip(*args, **kwargs):
   # Attemp to pick up tip, if there are no more tips wait until the user presses the button
   # and pick again from the beginning.
   try:
      return pipette.pick_up_tip(*args, **kwargs)
   except:
      robot_wait_tiprack()
      pipette.reset()
      return pipette.pick_up_tip(*args, **kwargs)

def addrow(well, num):
   # addrow('A1',1) -> 'B1'
   return chr(ord(well[0])+num) + well[1:]


def storage_samples(where, vol, new_tip='once', module = Eppendorfs, safe_flow_rate=15, mix=False, measure_time=True, downto=5):

   # Where is an array: ['A1'] will always aspirate from that well. ['A1','A2','A3'] will transfer
   # from well A1 in module to first col in samples, A2 to second col, etc

   # safe_flow_rate sets the dispense rate

   if new_tip == 'once':
      custom_pick_up_tip()

   if len(where) < 3:
      # Support for different origins
      where *= 3

   first_dispense=True
   start_time=0
   
   for sample,origin in zip(['A6', 'D6', 'D7'], where):

      # For every well in A1 - A3

      if mix:
         pipette.set_flow_rate(aspirate=flow_rate['a_r'], dispense=flow_rate['d_r'])
         pipette.mix(3,25,module.wells(origin))
         pipette.set_flow_rate(aspirate = 50, dispense = safe_flow_rate)
      pipette.aspirate(vol,module.wells(origin).bottom())
      pipette.dispense(vol,plate_samples.wells(sample).bottom(downto))
      pipette.blow_out(plate_samples.wells(sample).bottom(downto))

   if new_tip == 'once':
      pipette.drop_tip()

   pipette.set_flow_rate(aspirate=flow_rate['a_r'], dispense=flow_rate['d_r'])

def samples_trash(vol, new_tip='once', safe_flow_rate=15, downto=0):

   # safe_flow_rate sets the aspirate rate

   pipette.set_flow_rate(aspirate = safe_flow_rate, dispense = 50)

   if new_tip == 'once':
      custom_pick_up_tip()

   for sample in ['A6', 'D6', 'D7']:

      if new_tip == 'always':
         custom_pick_up_tip()

      pipette.aspirate(vol,plate_samples.wells(sample).bottom(downto))
      pipette.dispense(vol,trash_liquid)
      pipette.blow_out(trash_liquid)

      if new_tip == 'always':
         pipette.drop_tip()

   if new_tip == 'once':
      pipette.drop_tip()

   pipette.set_flow_rate(aspirate=flow_rate['a_r'], dispense=flow_rate['d_r'])


def robot_wait():

    if not robot.is_simulating():
       robot.comment("Waiting...")
       robot._driver.turn_on_red_button_light()
       while not robot._driver.read_button():
          sleep(0.5)

       robot._driver.turn_on_blue_button_light()
   
def tween_wash(times=1):

   # (3) Lavado x3 con PBS 1x tween 0.1
   for x in range(1,times+1):
      # TODO altura
      storage_samples(['A1'],200, module=Falcon, new_tip='once', downto = 11.7)
      samples_trash(200, new_tip='once', downto = 0)





# ============== START =============================================================
       
robot._driver.turn_on_rail_lights()
pipette.set_flow_rate(aspirate=flow_rate['a_l'], dispense=flow_rate['d_l'])

# (1) Retirar buffer coating
samples_trash(220, new_tip='once', downto = 0)

# (2) Lavado PBS-T x1
tween_wash()

# (3) BSA 200
storage_samples(['A1', 'A1', 'A2'],200, new_tip='once', mix=True, downto = 10)

# (4) Incubar 1h
robot_wait()

# (5) Retirar BSA
samples_trash(220, new_tip='once', downto = 0)

# (6) Lavado x2
tween_wash(times = 2)

# (5) Add 100ul latex beads

for epp,dest in [('C1','A6'), ('C1','A7'), ('C1','D7'), ('C1','A8'), ('C1','D8')]:
   # source, dest

   pipette.pick_up_tip()

   for pos in range(1,4):
      pipette.mix(3,50,Eppendorf.wells(epp))
      pipette.set_flow_rate(dispense=20)
      pipette.transfer(100,Eppendorf.wells(epp),plate_samples.wells(addrow(dest,pos-1)).bottom(10), new_tip='never', blow_out=True)
      pipette.set_flow_rate(dispense=200)

   pipette.drop_tip()

# (6) Pausar para incubar 1h - PAUSE (Hand made)
robot_wait()

# (7) Retirar 100ul
samples_trash(100, new_tip='once', downto=0);

# (8) Lavado x2 con tween TODO RESUSPENDER A VEL MEDIA
tween_wash(times=2)

# (9) Añadir 100ul H2O
storage_samples(['B1'],100, new_tip='once');

robot.turn_off_rail_lights()
robot._driver.home()
