"""Every wire in Bob v3. One source for the wiring diagram, the wire table and the viewer's wiring layer.

NODES: id -> (label, sub, column, row, cad item for the 3D overlay or None)
WIRES: (from, to, kind, what, wire, connector, fuse)
kind: power36 | power12 | power5 | usb | ttl | signal | motor | estop
"""

NODES = {
    "charge": ("Charge socket", "GX16, base top", 0, 0, "charge_socket"),
    "batt": ("36 V pack", "10S2P · 158 Wh", 0, 2, "battery"),
    "fuse": ("Switch + fuse block", "30 A main", 1, 2, "fuse_block"),
    "estop": ("E-stop", "NC, 22 mm", 1, 5, "estop"),
    "b5": ("5 V regulator", "Pololu D36V50F5", 2, 1, "reg_5v"),
    "cont": ("Contactor", "e-stop loop", 2, 3, "contactor_relay"),
    "pi": ("Raspberry Pi 5", "robot computer", 3, 1, "pi5"),
    "b12a": ("12 V 10 A ×2", "DROK, one per arm", 3, 3, "buck_12v"),
    "b12m": ("12 V regulator", "Pololu D36V50F12", 3, 5, "reg_12v"),
    "hub": ("USB 3 hub", "bus-powered", 4, 0, "usb_hub"),
    "busl": ("Bus adapter left", "Feetech TTL", 4, 3, "servo_bus"),
    "busr": ("Bus adapter right", "Feetech TTL", 4, 4, "servo_bus_r"),
    "esp": ("DDSM Driver HAT (A)", "ESP32 + RS485", 4, 6, "ddsm_driver"),
    "cam": ("Head camera", "USB RGB, wide", 5, 0, "head_cam"),
    "wcam": ("Wrist cameras ×2", "USB 2", 5, 1, "wrist_cam_l"),
    "armio": ("XIAO ESP32-C3", "reads the halls", 5, 2, "arm_io"),
    "stl": ("Left arm + head", "STS IDs 1–7, 8–9", 5, 3, "gm_l_j1_servo"),
    "str": ("Right arm", "STS IDs 1–7", 5, 4, "gm_r_j1_servo"),
    "wheels": ("DDSM115 ×2", "IDs 1 and 2", 5, 6, "hub_l"),
    "tmc": ("TMC2209", "UART, StallGuard", 5, 7, "tmc2209"),
    "imu": ("BNO085 IMU", "I2C", 5, 8, "imu"),
    "lidar": ("RPLIDAR C1", "USB", 6, 0, "lidar"),
    "s3": ("XIAO ESP32-S3 eyes", "SPI to 2 × GC9A01", 6, 1, "esp32s3_head"),
    "halls": ("Hall index ×8", "one per GM-5", 6, 2, "gm_l_j2_hall"),
    "audio": ("Mic + speaker", "USB", 6, 3, "mic_array"),
    "nema": ("Lift NEMA 17", "+ limit switch", 6, 7, "lift_motor"),
}

WIRES = [
    ("charge", "batt", "power36", "Charge from the hoverboard charger, 42 V 2 A", "18 AWG", "GX16 3-pin", "BMS"),
    ("batt", "fuse", "power36", "Main battery feed", "12 AWG", "XT60", "30 A"),
    ("fuse", "b5", "power36", "Pi rail, always on", "20 AWG", "ferrules", "3 A"),
    ("fuse", "cont", "power36", "Motor feed", "14 AWG", "ring lugs M4", "25 A"),
    ("estop", "cont", "estop", "Coil loop through the NC e-stop", "22 AWG", "spade 4.8", "1 A"),
    ("cont", "b12a", "power36", "Arm converters", "16 AWG", "ferrules", "15 A"),
    ("cont", "b12m", "power36", "Base converter", "18 AWG", "ferrules", "5 A"),
    ("b5", "pi", "power5", "Pi 5 power, 5.1 V 5 A", "18 AWG", "GPIO 5V pins", ""),
    ("b12a", "busl", "power12", "Left arm + head servos", "16 AWG", "5.5/2.1 → bus", "10 A"),
    ("b12a", "busr", "power12", "Right arm servos", "16 AWG", "5.5/2.1 → bus", "10 A"),
    ("b12m", "esp", "power12", "Wheel and HAT power", "18 AWG", "XT60", "5 A"),
    ("b12m", "tmc", "power12", "Stepper driver VM", "20 AWG", "JST-XH", "3 A"),
    ("pi", "hub", "usb", "USB 3", "", "USB-A to USB-C", ""),
    ("pi", "busl", "usb", "USB", "", "USB-C", ""),
    ("pi", "busr", "usb", "USB", "", "USB-C", ""),
    ("pi", "esp", "usb", "USB serial, JSON commands", "", "USB-C", ""),
    ("hub", "cam", "usb", "USB", "", "USB-A", ""),
    ("hub", "wcam", "usb", "USB 2 ×2", "", "USB-A, down the arms", ""),
    ("hub", "armio", "usb", "USB serial", "", "USB-C", ""),
    ("hub", "lidar", "usb", "USB", "", "USB-A", ""),
    ("hub", "s3", "usb", "USB serial", "", "USB-C", ""),
    ("hub", "audio", "usb", "USB audio", "", "USB-A", ""),
    ("busl", "stl", "ttl", "Half-duplex TTL, 1 Mbit/s", "18 AWG", "Molex 5264 3-pin", ""),
    ("busr", "str", "ttl", "Half-duplex TTL, 1 Mbit/s", "18 AWG", "Molex 5264 3-pin", ""),
    ("esp", "wheels", "ttl", "RS485 A/B, 115200 baud; 12 V on XH2.54", "18 AWG + twisted pair", "ZH1.5 4-pin + XH2.54", ""),
    ("armio", "halls", "signal", "8 hall index inputs", "26 AWG", "JST-SH 3-pin", ""),
    ("esp", "tmc", "signal", "STEP, DIR, EN, UART", "22 AWG", "Dupont", ""),
    ("esp", "imu", "signal", "I2C", "26 AWG", "Qwiic", ""),
    ("esp", "estop", "signal", "E-stop sense (second NC contact)", "22 AWG", "Dupont", ""),
    ("tmc", "nema", "motor", "Stepper A/B, limit switch to the ESP32", "22 AWG", "JST-PH 4-pin", ""),
]

COLORS = {
    "power36": "#ff5a4f", "power12": "#ffd43b", "power5": "#c8f542",
    "usb": "#4da3ff", "ttl": "#63e6be", "signal": "#b197fc", "motor": "#adb5bd", "estop": "#ff2d2d",
}
LABELS = {
    "power36": "36 V", "power12": "12 V", "power5": "5 V", "usb": "USB",
    "ttl": "Servo TTL", "signal": "Logic", "motor": "Motor phases", "estop": "E-stop loop",
}
