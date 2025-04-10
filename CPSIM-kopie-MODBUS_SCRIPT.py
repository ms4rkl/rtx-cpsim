# Toto je tzv. customization threaded script

from time import sleep
from numpy import random, array, float32
from pyModbusTCP.client import ModbusClient
import struct   # parsing floats into 2 registers

def sysCall_init():
    """
    Funkce Coppelia Sim pro inicializaci promennych.
    Misto globalnich promennych je lepsi pouzivat self.var = ...
    """
    sim = require('sim')

    self.client = ModbusClient(host="127.0.0.1", port=12345)
    
    # Cesta pro pristup k objektu je napsana v horni casti 3D nahledu sceny pri
    # kliknuti na dany objekt. Do prikazu je ale potreba zadavat ne cestu, ale
    # tzv. handle.
    self.j1_handle = sim.getObject("/base_link_respondable/joint_a2")
    self.j2_handle = sim.getObject("/base_link_respondable/joint_a3")
    self.j3_handle = sim.getObject("/base_link_respondable/joint_a5")

def sysCall_thread():
    """
    Funkce Coppelia Sim pro spousteni procesu ve vedlejsim vlaknu.
    Probiha jiz od otevreni Coppelia Sim, i kdyz neni simulace spustena.
    """
    """
    Prozatim pouzivane adresy:
    0x00 --> Pozadavek na spusteni simulace (do CpSim)
    0x01 --> Potvrzeni o spusteni simlace (od CpSim)
    0x02, 0x03 --> Float - Cas od spusteni simulace (od CpSim)
    0x04... --> Pole namerenych hodnot (od CpSim)
    """
    while True:
        while self.client.read_holding_registers(0x00, 1) == None:
            if sim.getSimulationState: sim.stopSimulation()
            pass 
        
        state = self.client.read_holding_registers(0x00, 1)
        state = state[0]
        print(state)
        
        if not sim.getSimulationState() and state:
            sim.startSimulation()
            self.client.write_single_register(0x01, 1)
            
        elif sim.getSimulationState() and not state:
            sim.stopSimulation()
            self.client.write_single_register(0x01, 0)
            
        if sim.getSimulationState() and state:
            while state:
                print("...")
                # Simulation Time
                time_regs = struct.unpack('>HH', struct.pack('>f', sim.getSimulationTime()))
                self.client.write_multiple_registers(0x02, list(time_regs))
                
                data = array([
                    [
                        sim.getJointForce(self.j1_handle),
                        sim.getJointForce(self.j2_handle),
                        sim.getJointForce(self.j3_handle),
                    ],[
                        sim.getJointPosition(self.j1_handle),
                        sim.getJointPosition(self.j2_handle),
                        sim.getJointPosition(self.j3_handle),
                    ]
                ], dtype=float32).flatten().astype('>f4').tobytes()
                data_regs = struct.unpack('>' + 'H' * (len(data) // 2), data)
                self.client.write_multiple_registers(0x04, list(data_regs))
                state = self.client.read_holding_registers(0x00, 1)[0]
                print("*")
                #sleep(0.01)
            
            
            
            
        #sleep(0.1)
        

# See the user manual or the available code snippets for additional callback functions and details
