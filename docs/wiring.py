"""Every wire in Bob v3. One source for the wiring diagram, the wire table and the viewer's wiring layer.

NODES: id -> (label, sub, column, row, cad item for the 3D overlay or None)
WIRES: (from, to, kind, what, wire, connector, fuse)
kind: power36 | power24 | power12 | power19 | can | usb | ttl | signal | motor | estop
"""

NODES = {
    "batt": ("36 V pack", "10S2P · 158 Wh", 0, 2, "battery"),
    "charge": ("Charge port", "42 V 2 A", 0, 0, None),
    "fuse": ("Switch + fuse block", "30 A main", 1, 2, "fuse_block"),
    "estop": ("E-stop", "NC, 22 mm", 1, 5, "estop"),
    "cont": ("Contactor", "40 A, 12 V coil", 2, 3, "contactor_relay"),
    "relay": ("12 V relay", "30 A", 2, 5, None),
    "b19": ("19 V buck", "5 A, always on", 2, 1, "buck_19v"),
    "b24": ("24 V buck", "20 A", 3, 3, "buck_24v"),
    "b12": ("12 V buck", "10 A", 3, 5, "buck_12v"),
    "jet": ("Jetson Orin Nano", "main computer", 3, 1, "jetson"),
    "hub": ("USB 3 hub", "powered, 12 V", 4, 0, "usb_hub"),
    "canl": ("USB-CAN left", "1 Mbit/s", 4, 2, "can_l"),
    "canr": ("USB-CAN right", "1 Mbit/s", 4, 3, "can_r"),
    "busl": ("Bus adapter left", "Feetech TTL", 4, 4, "servo_bus"),
    "busr": ("Bus adapter right", "Feetech TTL", 4, 5, "servo_bus_r"),
    "esp": ("ESP32 base", "wheels · lift · IMU", 4, 7, "esp32"),
    "cam": ("RealSense D435i", "USB 3", 5, 0, "d435"),
    "wcam": ("Wrist cameras ×2", "USB 2", 5, 1, "wrist_cam_l"),
    "lidar": ("RPLIDAR C1", "USB", 6, 0, "lidar"),
    "s3": ("ESP32-S3 eyes", "SPI to 2 × GC9A01", 6, 1, "esp32s3_head"),
    "dml": ("Left arm J1–J4", "Damiao, 24 V, CAN", 5, 2, "j1_l"),
    "dmr": ("Right arm J1–J4", "Damiao, 24 V, CAN", 5, 3, "j1_r"),
    "stl": ("Left J5–J7 + head", "STS3215 IDs 1–3, 7, 8", 5, 4, "j5_l"),
    "str": ("Right J5–J7", "STS3215 IDs 1–3", 5, 5, "j5_r"),
    "zsx": ("ZS-X11H ×2", "hub controllers", 5, 6, "zsx11h_l"),
    "wheels": ("Hub motors ×2", "3 phase + hall", 6, 6, "hub_l"),
    "tmc": ("TMC2209", "UART, StallGuard", 5, 7, "tmc2209"),
    "nema": ("Lift NEMA 17", "+ limit switch", 6, 7, "lift_motor"),
    "imu": ("BNO085 IMU", "I2C", 5, 8, "imu"),
    "audio": ("Mic array + speaker", "USB", 6, 2, "mic_array"),
}

WIRES = [
    ("charge", "batt", "power36", "Charge", "18 AWG", "DC 5.5/2.1 panel jack", "BMS"),
    ("batt", "fuse", "power36", "Main battery feed", "12 AWG", "XT60", "30 A"),
    ("fuse", "b19", "power36", "Jetson rail, always on", "18 AWG", "ferrules", "5 A"),
    ("fuse", "cont", "power36", "Motor feed", "14 AWG", "ring lugs M4", "25 A"),
    ("fuse", "relay", "power36", "12 V branch feed", "16 AWG", "ferrules", "10 A"),
    ("estop", "cont", "estop", "Coil loop: 12 V through the NC e-stop", "22 AWG", "spade 4.8", "1 A"),
    ("estop", "relay", "estop", "Same loop, second coil", "22 AWG", "spade 4.8", ""),
    ("cont", "b24", "power36", "Arm buck input", "14 AWG", "ferrules", ""),
    ("cont", "zsx", "power36", "Hub controllers", "16 AWG", "XT60", "15 A each"),
    ("relay", "b12", "power36", "12 V buck input", "16 AWG", "ferrules", ""),
    ("b19", "jet", "power19", "Jetson power", "18 AWG", "DC 5.5/2.5 barrel", ""),
    ("b24", "dml", "power24", "Left arm, chained J1→J4", "16 AWG", "XT30", "10 A"),
    ("b24", "dmr", "power24", "Right arm, chained J1→J4", "16 AWG", "XT30", "10 A"),
    ("b12", "busl", "power12", "Left servo bus power", "18 AWG", "5.5/2.1", "5 A"),
    ("b12", "busr", "power12", "Right servo bus power", "18 AWG", "5.5/2.1", "5 A"),
    ("b12", "tmc", "power12", "Stepper driver VM", "20 AWG", "JST-XH", "3 A"),
    ("b12", "hub", "power12", "USB hub supply", "20 AWG", "5.5/2.1", "3 A"),
    ("jet", "hub", "usb", "USB 3", "", "USB-A to USB-C", ""),
    ("jet", "canl", "usb", "USB", "", "USB-A", ""),
    ("jet", "canr", "usb", "USB", "", "USB-A", ""),
    ("jet", "busl", "usb", "USB", "", "USB-C", ""),
    ("jet", "busr", "usb", "USB", "", "USB-C", ""),
    ("jet", "esp", "usb", "USB serial, 921600", "", "micro-USB", ""),
    ("hub", "cam", "usb", "USB 3", "", "USB-C, 1 m", ""),
    ("hub", "wcam", "usb", "USB 2 ×2", "", "USB-A, down the arms", ""),
    ("hub", "lidar", "usb", "USB", "", "USB-A", ""),
    ("hub", "s3", "usb", "USB serial", "", "USB-C", ""),
    ("hub", "audio", "usb", "USB audio", "", "USB-A", ""),
    ("canl", "dml", "can", "CAN H/L, 120 Ω at the far end", "twisted pair", "GH 1.25 2-pin", ""),
    ("canr", "dmr", "can", "CAN H/L, 120 Ω at the far end", "twisted pair", "GH 1.25 2-pin", ""),
    ("busl", "stl", "ttl", "Half-duplex TTL, 1 Mbit/s", "22 AWG", "Molex 5264 3-pin", ""),
    ("busr", "str", "ttl", "Half-duplex TTL, 1 Mbit/s", "22 AWG", "Molex 5264 3-pin", ""),
    ("esp", "zsx", "signal", "PWM, DIR, brake, hall speed", "22 AWG", "Dupont", ""),
    ("esp", "tmc", "signal", "STEP, DIR, EN, UART", "22 AWG", "Dupont", ""),
    ("esp", "imu", "signal", "I2C", "26 AWG", "Qwiic", ""),
    ("esp", "estop", "signal", "E-stop sense (second NC contact)", "22 AWG", "Dupont", ""),
    ("zsx", "wheels", "motor", "3 phase + 5 hall wires", "16 AWG + 26 AWG", "MT60 + JST", ""),
    ("tmc", "nema", "motor", "Stepper A/B, limit switch to the ESP32", "22 AWG", "JST-PH 4-pin", ""),
]

COLORS = {
    "power36": "#ff5a4f", "power24": "#ff9f43", "power12": "#ffd43b", "power19": "#c8f542",
    "can": "#f783ac", "usb": "#4da3ff", "ttl": "#63e6be", "signal": "#b197fc", "motor": "#adb5bd", "estop": "#ff2d2d",
}
LABELS = {
    "power36": "36 V", "power24": "24 V", "power12": "12 V", "power19": "19 V", "can": "CAN", "usb": "USB",
    "ttl": "Servo TTL", "signal": "Logic", "motor": "Motor phases", "estop": "E-stop loop",
}
