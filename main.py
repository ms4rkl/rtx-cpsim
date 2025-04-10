from PyQt5.QtWidgets import QApplication
import sys
from window import *


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = UI()
    app.exec_()


# 0x00:  SEND - start/stop Simulation Request
# 0x01:  RECIEVE - Simulation Status
# 0x02, 0x03:  RECIEVE - Simulation Time
# 0x04, 0x05:  RECIEVE - Joint 1 Torque
# 0x06, 0x07:  RECIEVE - Joint 2 Position