from PyQt5.QtWidgets import QMainWindow, QPushButton, QLabel, QLineEdit, QComboBox
from PyQt5 import uic
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
import ctypes
from pyModbusTCP.server import ModbusServer
import pyqtgraph as pg
from threading import Thread
import struct
from numpy import array, append, frombuffer, zeros, savetxt, vstack
from time import sleep

class UI(QMainWindow):
    def __init__(self):
        super(UI, self).__init__()


        # Visual
        with open("./style.qss", "r") as file:
            self.style = file.read()
            self.setStyleSheet(self.style)
        self.gui = uic.loadUi("gui4.ui", self)
        myappid = 'mycompany.myproduct.subproduct.version' # arbitrary string
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        self.setWindowTitle("RTX")
        self.banner = self.findChild(QLabel, "label_2")
        self.banner.setPixmap(QPixmap("./img/banner.jpg"))
        self.banner.setScaledContents(True)


        # Modbus
        self.modbus = None
        self.l_modbus = self.findChild(QLabel, "label_4")
        self.start_modbus()


        # QPushButtons instances setup
        self.pb_sim_start = self.findChild(QPushButton, "pushButton")
        self.pb_sim_start.clicked.connect(self.start_simulation)
        self.pb_sim_start.setEnabled(True)
        self.pb_sim_start.setCursor(Qt.PointingHandCursor)

        self.pb_sim_stop = self.findChild(QPushButton, "pushButton_7")
        self.pb_sim_stop.clicked.connect(self.stop_simulation)
        self.pb_sim_stop.setEnabled(False)
        self.pb_sim_stop.setCursor(Qt.PointingHandCursor)

        self.pb_malfunc = self.findChild(QPushButton, "pushButton_6")
        self.pb_export_torq = self.findChild(QPushButton, "pushButton_2")
        self.pb_export_pos = self.findChild(QPushButton, "pushButton_3")
        self.pb_export_pred = self.findChild(QPushButton, "pushButton_4")
        self.pb_export_weight = self.findChild(QPushButton, "pushButton_5")
        for button in [self.pb_malfunc, self.pb_export_torq, self.pb_export_pos, self.pb_export_pred, self.pb_export_weight]:
            button.setEnabled(False)
            button.setCursor(Qt.PointingHandCursor)


        # PyQtGraph instances setup
        self.plt_11 = self.findChild(pg.PlotWidget, "widget")
        self.plt_21 = self.findChild(pg.PlotWidget, "widget_3")
        self.plt_31 = self.findChild(pg.PlotWidget, "widget_5")
        self.plt_12 = self.findChild(pg.PlotWidget, "widget_2")
        self.plt_22 = self.findChild(pg.PlotWidget, "widget_4")
        self.plt_32 = self.findChild(pg.PlotWidget, "widget_6")

        self.plots = [self.plt_11, self.plt_21, self.plt_31, self.plt_12, self.plt_22, self.plt_32]
        self.style_plots()


        # QComboBox instances setup
        self.cb_lnu = self.findChild(QComboBox, "comboBox")
        self.cb_lnu.setEnabled(True)
        self.cb_lnu.setCursor(Qt.PointingHandCursor)


        # QLineEdit instances setup
        self.le_batch = self.findChild(QLineEdit, "lineEdit")
        self.le_batch.setEnabled(False)


        # QLabel instances setup
        self.simstatus = False
        self.l_simstatus = self.findChild(QLabel, "label_6")
        self.l_time = self.findChild(QLabel, "label_9")
        self.l_time.setText("0 s")


        # Arrays inicialization
        self.arr_time = array([])
        self.arr_torq = zeros((0,  3))
        self.arr_pos = zeros((0, 3))


        
        self.thread = None

        self.show()

    
    def start_modbus(self):
        """
        Provides the setup of modbus master (server)
        """
        # Now using pyModbusTCP --> Coppelia Sim is waiting for a modbus coil at 0x00 to be set to 1 to start the simulation
        self.modbus = ModbusServer(host="127.0.0.1", port=12345, no_block=True)
        try:
            self.modbus.start()     # modbus stopped at self.closeEvent()
            print("Server Started")
            self.l_modbus.setText("Running")
            self.modbus.data_bank.set_holding_registers(0x00, [0])
        except:
            print("Server Unable to Start")


    def start_simulation(self):
        """
        Sets register 0x00 to 1 which causes Coppelia Sim threaded customization script to start the simulation
        """
        self.modbus.data_bank.set_holding_registers(0x00, [1])
        print("Request Simulation Start")

        self.pb_sim_start.setEnabled(False)
        self.pb_sim_stop.setEnabled(True)
        self.cb_lnu.setEnabled(False)
        self.pb_malfunc.setEnabled(True)
        for button in [self.pb_export_torq, self.pb_export_pos, self.pb_export_pred, self.pb_export_weight]:
            button.setEnabled(False)
        
        while not self.modbus.data_bank.get_holding_registers(0x01, 1)[0]:
            pass
        print("Simulation Started")
        self.simstatus = True
        self.l_simstatus.setText("Running")

        
        self.thread = Thread(target=self.process_data, daemon=True)
        self.thread.start()


    def stop_simulation(self):
        """
        Sets register 0x00 to 0 which causes Coppelia Sim threaded customization script to stop the simulation
        """
        self.modbus.data_bank.set_holding_registers(0x00, [0])
        print("Request Simulation Stop")

        self.pb_sim_start.setEnabled(True)
        self.pb_sim_stop.setEnabled(False)
        self.cb_lnu.setEnabled(True)
        self.pb_malfunc.setEnabled(False)
        for button in [self.pb_export_torq, self.pb_export_pos, self.pb_export_pred, self.pb_export_weight]:
            button.setEnabled(True)

        while self.modbus.data_bank.get_holding_registers(0x01, 1)[0]:
            pass
        print("Simulation Stopped")
        self.simstatus = False
        self.l_simstatus.setText("Not Running")


    def process_data(self):
        """
        Periodically reads data from registers and applies LNU to them
        """
        while self.simstatus:
            time = self.modbus.data_bank.get_holding_registers(0x02, 2)
            time = struct.unpack('>f', struct.pack('>HH', *time))[0]
            self.arr_time = append(self.arr_time, time)
            self.l_time.setText(f"{round(time)} s")

            data = self.modbus.data_bank.get_holding_registers(0x04, 12)
            data = struct.pack('>' + 'H' * len(data), *data)
            data = frombuffer(data, dtype='>f4').reshape((2, 3))
            self.arr_torq = vstack([self.arr_torq, data[0]])
            self.arr_pos = vstack([self.arr_pos, data[1]])
            print(data.shape)
            print("*")
            # sleep(0.1)

        
        

    
    def closeEvent(self, *args, **kwargs):
        super(QMainWindow, self).closeEvent(*args, **kwargs)
        try:
            self.modbus.data_bank.set_holding_registers(0x00, [0])
            self.modbus.stop()
            print("Server Stopped")
            self.thread.join()
            savetxt("pos.txt", self.arr_pos)
            savetxt("torq.txt", self.arr_torq)
        except:
            print("Server Already Stopped")

    def style_plots(self):
        for i, ax in enumerate(self.plots):
            ax.setBackground((255, 255, 255))
            # ax.setLabel("left", f"<font>&phi;</font>{jointIndices[i]} [rad]")
            # ax.setLabel("right", "Velocity [rad/s]")
            ax.setLabel("bottom", "t [s]")
            ax.showGrid(x=True, y=True)
        # leg = ax.addLegend(frame=True, colCount=2, offset=(0, 0))