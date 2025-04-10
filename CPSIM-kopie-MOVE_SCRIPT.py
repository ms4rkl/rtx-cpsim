# Toto je jednoduchy simulation non-threaded script, ktery zpusobuje
# pohyb robota.

import numpy as np
from time import sleep

def sysCall_init():
    """
    Funkce Coppelia Sim pro inicializaci promennych.
    Misto globalnich promennych je lepsi pouzivat self.var = ...
    """
    sim = require('sim')

    self.handle = sim.getObjectHandle("/base_link_respondable/Dummy")
    duration = 2 #[s]
    startTimeStamp = sim.getSimulationTime()

def sysCall_actuation():
    """
    Funkce Coppelia Sim vykonavana v kazdem kroku simulace.
    """
    t = sim.getSimulationTime()
    position = [-0.55+0.3*np.cos(2*t) ,0 , 0.8+0.4*np.sin(t)]
    
    sim.setObjectPosition(self.handle, position, -1)
    pass

def sysCall_sensing():
    # put your sensing code here
    pass

def sysCall_cleanup():
    # do some clean-up here
    pass

# See the user manual or the available code snippets for additional callback functions and details
