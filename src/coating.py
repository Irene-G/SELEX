'''
#####################################################
#  Coating of the samples.                          #
#  It is required:                                  #
#  * Three Falcon (different concentrations).       #
#  * One Falcon.                                    #
#  * Eppendorf plates.                              #
#  We printed our own custom modules.               #
#  Team: MADRID_UCM                                 #
#####################################################
'''

# TODO usar la multiple

from opentrons import labware, instruments, modules, robot
from opentrons.data_storage import database

metadata = {
   'protocolName' : 'Coating',
   'description'  : 'Coating of the samples',
   'source'       : 'https://github.com/Zildj1an/SELEX'
}

# [0] Our design for the three modules

'''
database.delete_container('Falcon_Samples')
database.delete_container('Eppendorf_Samples')
'''

plate_falcon = 'Falcon_Samples'
if plate_falcon not in labware.list():
   Falcon = labware.create(
      plate_falcon,
      grid = (3,2),
      spacing = (35,43),
      diameter = 10,
      depth  = 110,
      volume = 800)

plate_eppendorf = 'Eppendorf_Samples'
if plate_eppendorf not in labware.list():
   Eppendorf = labware.create(
      plate_eppendorf,
      grid = (8,4),
      spacing = (15,20),
      diameter = 10,
      depth  = 32,
      volume = 100)

# [1] Labware

Falcon           = labware.load(plate_falcon,    slot = '2')
Eppendorf        = labware.load(plate_eppendorf, slot = '5')
tiprack          = labware.load('tiprack-10ul',  slot = '6')
trash            = labware.load('trash-box',     slot = '12', share = True)
plate_samples    = labware.load('96-flat',       slot = '11')                       # Samples

# [2] Pipettes

pipette_l = instruments.P50_Single(mount = 'left', tip_racks=[tiprack], trash_container = trash)

def custom_transfer(pipette,quantity,pos1,pos2,A,B):

   times = quantity // 50

   pipette.pick_up_tip()

   for i in range(1,times):
      pipette.aspirate(50,pos1.wells(A).bottom(1))
      pipette.dispense(50,pos2.wells(B))

   quantity = quantity - (times * 50)

   if quantity > 0:
      pipette.aspirate(quantity,pos1.wells(A).bottom(1))
      pipette.dispense(quantity,pos2.wells(B))


# [3] Execution

# Previous:
# Each Falcon has 1 ml shaked of PBS (Human part BEFORE Protocol)

# (1) Each Falcon to Eppendorfs:

falcon50 = 'A3'
val = 1

for falcon in ['A1','B1','B2']:

    # 1st Eppendorf -> 400 ul of PBS + 400 ul of Falcon15
    custom_transfer(pipette_l,400,Falcon,Eppendorf,falcon50,'A'+ str(val))
    pipette_l.mix(2,50,Falcon.wells(falcon))
    pipette_l.drop_tip()
    custom_transfer(pipette_l,400,Falcon,Eppendorf,falcon,  'A' + str(val))

    # 2nd Eppendorf -> 640 ul of PBS + 160 ul of Falcon15
    custom_transfer(pipette_l,640,Falcon,Eppendorf,falcon50,'B' + str(val))
    pipette_l.mix(2,50,Falcon.wells(falcon))
    pipette_l.drop_tip()
    custom_transfer(pipette_l,160,Falcon,Eppendorf,falcon,  'B' + str(val))

    # 3rd Eppendorf -> 720 ul of PBS + 80 ul of Falcon
    custom_transfer(pipette_l,720,Falcon,Eppendorf,falcon50,'C' + str(val))
    pipette_l.mix(2,50,Falcon.wells(falcon))
    pipette_l.drop_tip()
    custom_transfer(pipette_l,80,Falcon,Eppendorf,falcon,   'C' + str(val))

    # 3rd Eppendorf -> 784 ul of PBS + 16 ul of Falcon
    custom_transfer(pipette_l,784,Falcon,Eppendorf,falcon50,'D' + str(val))
    pipette_l.mix(2,50,Falcon.wells(falcon))
    pipette_l.drop_tip()
    custom_transfer(pipette_l,16,Falcon,Eppendorf,falcon,   'D' + str(val))

    val = val + 1

    for pos in ['A','B','C','D']:

        init = 1
        end = 6

        if falcon == 'B1':
           init = 1
           end  = 6

        for i in range(init,end):

           pipette_l.transfer(100,Eppendorf.wells(pos + str(val)),plate_samples.wells(pos + str(i)), new_tip='never')

        pipette_l.drop_tip()

robot._driver.turn_off_rail_lights()
robot._driver.home()


