"""Every wire in Bob v3. One source for the wiring diagram, the wire table and the viewer's wiring layer.

Column umbilical
  One PET sleeve, zip-tied at each stage and again on the inner-tube cap.
  The slack folds as a serpentine in the base trough (six printed drag-chain
  links) and pays out through the rear window of the outer tube, the open
  notch in the middle tube, and the bore of the upper and inner tubes.
  Travel is 558 mm. The sleeve passes the T8 bridge on the left (y about 20 mm).
  Power to the chest and the lidar USB ride that sleeve. The Pi's 5 V
  regulator sits in the torso: 36 V goes up the sleeve at under 1 A and
  the 5 A run to the Pi is short. Camera USB stays in
  the chest, the neck, and the arms.

  PATHS are polylines in each link's zero-pose CAD frame (mm). A point tagged
  "loop" is the trough coil. Cut length is the longer of the coiled route at
  lift = 0 and the paid-out route at full lift, over hanging and straight arms,
  plus 8 percent for terminations. The coil is not counted twice at full lift.

NODES: id -> (label, sub, column, row, cad item for the 3D overlay or None)
WIRES: (from, to, kind, what, wire, connector, fuse)
kind: power36 | power18 | power12 | power5 | gnd | usb | ttl | signal | motor | estop
Every power wire is a pair. Its negative half is listed as a gnd wire back to the star ground.
elec() gives volts, design amps and peak amps for every wire. `python docs/wiring.py` prints them with
the wire size and length and checks gauge, fuse, voltage drop and regulator, hub and Pi USB budgets.
"""

NODES = {
    "charge": ("Charge socket", "GX16, base top", 0, 4, "charge_socket"),
    "batt": ("36 V pack", "10S2P · 158 Wh", 0, 5, "battery"),
    "gnd": ("Star ground", "every return, base", 0, 6, None),
    "estop": ("E-stop", "2 NC: coil + sense", 0, 8, "estop"),
    "fuse": ("Main switch + fuses", "58 V fuses, 36 V side", 1, 5, "fuse_block"),
    "cont": ("Contactor", "12 V coil, aux NO", 1, 8, "contactor_relay"),
    "b5": ("5 V regulator", "D36V50F5, in the torso", 2, 5, "reg_5v"),
    "b12c": ("12 V always on", "D36V50F12: coil, hub", 2, 6, None),
    "b12a": ("12 V 20 A ×2", "one per arm, in the torso", 2, 7, "buck_12v"),
    "b18": ("18 V regulator", "D42V55F18: wheels, lift", 2, 9, "reg_12v"),
    "pi": ("Raspberry Pi 5", "robot computer", 3, 5, "pi5"),
    "hub": ("USB 3 hub", "12 V powered, 4 ports", 4, 2, "usb_hub"),
    "busl": ("Bus adapter left", "Feetech TTL, Pi UART2", 4, 6, "servo_bus"),
    "busr": ("Bus adapter right", "Feetech TTL, Pi UART4", 4, 7, "servo_bus_r"),
    "esp": ("DDSM Driver HAT (A)", "ESP32 + RS485", 4, 10, "ddsm_driver"),
    "tmc": ("TMC2209", "UART, StallGuard", 4, 11, "tmc2209"),
    "audio": ("Mic array", "ReSpeaker Lite, USB", 5, 3, "mic_array"),
    "s3": ("XIAO ESP32-S3", "drives the eyes", 5, 4, "esp32s3_head"),
    "eyes": ("Eyes ×2", "GC9A01 1.28 in, SPI", 5, 5, "eye_l"),
    "stl": ("Left arm", "STS IDs 1–7", 5, 6, "j1_l"),
    "str": ("Right arm", "STS IDs 1–7", 5, 7, "j1_r"),
    "head": ("Head pan + tilt", "STS3215 IDs 8–9", 5, 8, "pan_servo"),
    "wheels": ("DDSM115 ×2", "IDs 1 and 2", 5, 10, "hub_l"),
    "nema": ("Lift NEMA 17", "17HS19-2004S1", 5, 11, "lift_motor"),
    "cam": ("Head camera", "USB RGB, wide", 6, 0, "head_cam"),
    "wcl": ("Left wrist camera", "UB0234, USB 2", 6, 1, "wrist_cam_l"),
    "wcr": ("Right wrist camera", "UB0234, USB 2", 6, 2, "wrist_cam_r"),
    "lidar": ("RPLIDAR C1", "USB", 6, 3, "lidar"),
    "lim": ("Lift limit switches", "top and bottom", 6, 9, "limit_top"),
    "imu": ("BNO085 IMU", "I2C", 6, 12, "imu"),
}

WIRES = [
    # 36 V, always on
    ("charge", "batt", "power36", "Charge from the hoverboard charger, 42 V 2 A", "18 AWG", "GX16 3-pin", "BMS"),
    ("batt", "fuse", "power36", "Main battery feed through the main fuse to the main switch", "12 AWG", "XT60, 3/8 in ring lug", "30 A, 58 V"),
    ("fuse", "b5", "power36", "Pi rail, 36 V always on, up the column sleeve to the regulator in the torso", "20 AWG", "ferrules", "3 A, 58 V"),
    ("fuse", "b12c", "power36", "Always-on 12 V supply, ahead of the contactor", "20 AWG", "ferrules", "3 A, 58 V"),
    ("fuse", "cont", "power36", "Motor feed", "12 AWG", "ring lugs M4", "25 A, 58 V"),
    # e-stop loop and its read-back
    ("b12c", "estop", "estop", "Contactor coil feed, 12 V, through the NC e-stop", "22 AWG", "spade 4.8", "1 A"),
    ("estop", "cont", "estop", "E-stop NC contact on to the coil, diode across the coil", "22 AWG", "spade 4.8", ""),
    ("estop", "esp", "signal", "E-stop sense: second NC contact block, 12 V loop", "22 AWG", "Dupont", ""),
    ("cont", "esp", "signal", "Contactor aux contact (NO) read-back, 12 V loop", "22 AWG", "Dupont", ""),
    # 36 V, switched by the contactor
    ("cont", "b12a", "power36", "Switched 36 V up the column sleeve to the arm converters in the torso", "14 AWG", "ferrules", "20 A, 58 V"),
    ("cont", "b18", "power36", "Switched 36 V to the wheel and lift regulator", "18 AWG", "ferrules", "5 A, 58 V"),
    # regulated rails
    ("b5", "pi", "power5", "Pi 5 power, 5 V 5 A, short run in the torso; PSU_MAX_CURRENT=5000 for 1.6 A USB", "18 AWG", "GPIO 5V pins 2 and 4", ""),
    ("b12c", "hub", "power12", "Hub DC input (7-36 V), up the column sleeve", "20 AWG", "hub screw terminal", "3 A"),
    ("b12a", "busl", "power12", "Left arm + head servos, 12 V", "14 AWG", "adapter screw terminal", ""),
    ("b12a", "busr", "power12", "Right arm servos, 12 V", "14 AWG", "adapter screw terminal", ""),
    ("b18", "esp", "power18", "Wheel power through the HAT, 18 V (DDSM115 rated 18 V)", "16 AWG", "XT60", ""),
    ("b18", "tmc", "power18", "Stepper driver VM, 18 V (VM 4.75-28 V)", "20 AWG", "JST-XH", ""),
    # returns: every power run is a pair; these are the negative halves
    ("batt", "gnd", "gnd", "Battery negative to the star ground", "12 AWG", "XT60, ring lug", ""),
    ("gnd", "b5", "gnd", "Pi rail return, paired up the column sleeve", "20 AWG", "ferrules", ""),
    ("gnd", "b12c", "gnd", "Always-on 12 V return", "20 AWG", "ferrules", ""),
    ("gnd", "cont", "gnd", "Contactor coil return", "22 AWG", "spade 4.8", ""),
    ("gnd", "b12a", "gnd", "Arm converter return, paired up the column sleeve", "14 AWG", "ferrules", ""),
    ("gnd", "b18", "gnd", "Wheel and lift regulator return", "18 AWG", "ferrules", ""),
    # data: the Pi has 4 USB ports (hub, HAT, eyes, mic); the hub has 4 (three cameras, lidar)
    ("pi", "hub", "usb", "USB 3", "", "USB-A to USB-C", ""),
    ("pi", "esp", "usb", "USB serial, JSON commands", "", "USB-C", ""),
    ("pi", "s3", "usb", "USB serial, through the neck", "", "USB-C", ""),
    ("pi", "audio", "usb", "USB audio, through the neck", "", "USB-A", ""),
    ("pi", "busl", "signal", "Pi UART2 (GPIO4/5), adapter jumper on UART", "22 AWG", "Dupont", ""),
    ("pi", "busr", "signal", "Pi UART4 (GPIO12/13), adapter jumper on UART", "22 AWG", "Dupont", ""),
    ("hub", "cam", "usb", "USB", "", "USB-A", ""),
    ("hub", "wcl", "usb", "USB 2, down the left arm", "", "USB-A", ""),
    ("hub", "wcr", "usb", "USB 2, down the right arm", "", "USB-A", ""),
    ("hub", "lidar", "usb", "USB down the column sleeve", "", "USB-A", ""),
    ("busl", "stl", "ttl", "Half-duplex TTL, 1 Mbit/s", "18 AWG", "Molex 5264 3-pin", ""),
    ("busl", "head", "ttl", "Half-duplex TTL, 1 Mbit/s, pan in the torso, tilt through the neck", "18 AWG", "Molex 5264 3-pin", ""),
    ("busr", "str", "ttl", "Half-duplex TTL, 1 Mbit/s", "18 AWG", "Molex 5264 3-pin", ""),
    ("s3", "eyes", "signal", "SPI to both displays, one bus, two chip selects", "26 AWG", "module header", ""),
    ("esp", "wheels", "ttl", "RS485 A/B, 115200 baud; 18 V on XH2.54", "18 AWG + twisted pair", "ZH1.5 4-pin + XH2.54", ""),
    ("esp", "tmc", "signal", "STEP, DIR, EN, UART", "22 AWG", "Dupont", ""),
    ("esp", "lim", "signal", "Lift limit switches, top and bottom", "22 AWG", "Dupont", ""),
    ("esp", "imu", "signal", "I2C", "26 AWG", "Qwiic", ""),
    ("tmc", "nema", "motor", "Stepper A/B", "22 AWG", "JST-PH 4-pin", ""),
]

COLORS = {
    "power36": "#ff5a4f", "power18": "#ff922b", "power12": "#ffd43b", "power5": "#c8f542", "gnd": "#dee2e6",
    "usb": "#4da3ff", "ttl": "#63e6be", "signal": "#b197fc", "motor": "#adb5bd", "estop": "#ff2d2d",
}
LABELS = {
    "power36": "36 V", "power18": "18 V", "power12": "12 V", "power5": "5 V", "gnd": "Return",
    "usb": "USB", "ttl": "Servo TTL", "signal": "Logic", "motor": "Motor phases", "estop": "E-stop loop",
}


def _pt(link, x, y, z, tag=None):
    return (link, float(x), float(y), float(z), tag) if tag else (link, float(x), float(y), float(z))


def _loop():
    """Serpentine in the trough, about half a metre of sleeve waiting to pay out."""
    pts = []
    for i in range(8):
        z = 52.0 + (i % 4) * 3.0
        x = -80.0 if i < 4 else -70.0
        y0, y1 = (24.0, 88.0) if i % 2 == 0 else (88.0, 24.0)
        pts.append(_pt("base", x, y0, z, "loop"))
        pts.append(_pt("base", x, y1, z, "loop"))
    return pts


def _bore():
    """Points on the inner tube. They rise with the lift."""
    return [_pt("lift", -6.0, 16.0, z) for z in (200.0, 300.0, 390.0, 436.0)]


def _column_up(start, end):
    """Base device, trough coil, rear window, bore, chest device."""
    return [start, _pt("base", -60.0, 20.0, 90.0), *_loop(), _pt("base", -48.0, 20.0, 100.0), *_bore(), end]


def _column_down(start, end):
    """Chest device, bore, window, coil, base device (lidar USB)."""
    return [start, *_bore()[::-1], _pt("base", -48.0, 20.0, 100.0), *_loop(), _pt("base", -40.0, 10.0, 120.0), end]


def _neck(start, end):
    return [start, _pt("lift", 5.0, 0.0, 490.0), _pt("head_pan", 5.0, 0.0, 530.0),
            _pt("head_tilt", 20.0, 0.0, 580.0), end]


def _arm(side, start, extra=()):
    sy = 1.0 if side == "l" else -1.0
    link = f"{side}_"
    bow = 16.0 * sy
    pts = [
        start,
        _pt("lift", 18.0, 96.0 * sy, 400.0),
        _pt(link + "link1", 9.0, 128.0 * sy, 452.0),
        _pt(link + "link2", 9.0, 157.0 * sy, 420.0),
        _pt(link + "link2", 9.0, 157.0 * sy + bow, 339.0),
        _pt(link + "link3", 9.0, 157.0 * sy, 270.0),
        _pt(link + "link3", 9.0, 157.0 * sy + bow, 200.0),
        _pt(link + "link4", 9.0, 157.0 * sy, 100.0),
        _pt(link + "link5", 9.0, 157.0 * sy, 0.0),
    ]
    pts.extend(extra)
    return pts


def routes():
    """One polyline per wire, in link frames. Missing wires fall back to part centres in the viewer."""
    shelf = 160.0
    bus_l = _pt("lift", 30.0, 72.0, 326.0)
    bus_r = _pt("lift", 30.0, -72.0, 326.0)
    hub = _pt("lift", 0.0, -78.0, 392.0)
    pi = _pt("lift", 0.0, 78.0, 392.0)
    reg5 = _pt("lift", -20.0, 78.0, 370.0)  # 5 V regulator beside the Pi; the torso CAD moves it here
    conv = _pt("lift", -30.0, 0.0, 300.0)  # arm converters, torso; the torso CAD moves them here
    conv_l = _pt("lift", -30.0, 40.0, 300.0)
    conv_r = _pt("lift", -30.0, -40.0, 300.0)
    cam = _pt("head_tilt", 65.0, 0.0, 648.0)
    s3 = _pt("head_tilt", 1.0, 0.0, 587.0)
    mic = _pt("head_tilt", 21.0, 0.0, 683.0)
    eyes = _pt("head_tilt", 55.0, 0.0, 640.0)
    pan = _pt("lift", 5.0, 0.0, 450.0)
    palm_l = _pt("l_link6", -16.0, 157.0, -70.0)
    palm_r = _pt("r_link6", -16.0, -157.0, -70.0)
    batt = _pt("base", 0.0, 80.0, 130.0)
    fuse = _pt("base", 0.0, -72.0, shelf)
    gnd = _pt("base", 20.0, -50.0, shelf)
    cont = _pt("base", -130.0, -96.0, shelf)
    b12c = _pt("base", -40.0, -150.0, shelf)
    b18 = _pt("base", 0.0, -132.0, shelf)
    esp = _pt("base", 0.0, -104.0, shelf)
    estop = _pt("base", -122.0, 112.0, 212.0)
    return {
        ("charge", "batt"): [_pt("base", 125.0, -110.0, 212.0), _pt("base", 80.0, -40.0, shelf), batt],
        ("batt", "fuse"): [batt, _pt("base", 0.0, 20.0, shelf), fuse],
        ("fuse", "b5"): _column_up(fuse, reg5),
        ("fuse", "b12c"): [fuse, _pt("base", -40.0, -90.0, shelf), b12c],
        ("fuse", "cont"): [fuse, _pt("base", -80.0, -80.0, shelf), cont],
        ("b12c", "estop"): [b12c, _pt("base", -140.0, -60.0, shelf), _pt("base", -140.0, 40.0, 180.0), estop],
        ("estop", "cont"): [estop, _pt("base", -140.0, 40.0, 180.0), cont],
        ("estop", "esp"): [_pt("base", -122.0, 112.0, 200.0), _pt("base", -140.0, 0.0, 170.0), esp],
        ("cont", "esp"): [cont, _pt("base", -60.0, -104.0, shelf), esp],
        ("cont", "b12a"): _column_up(cont, conv),
        ("cont", "b18"): [cont, _pt("base", -40.0, -120.0, shelf), b18],
        ("b5", "pi"): [reg5, pi],
        ("b12c", "hub"): _column_up(b12c, hub),
        ("b12a", "busl"): [conv_l, _pt("lift", 0.0, 60.0, 310.0), bus_l],
        ("b12a", "busr"): [conv_r, _pt("lift", 0.0, -60.0, 310.0), bus_r],
        ("b18", "esp"): [b18, esp],
        ("b18", "tmc"): [b18, _pt("base", -80.0, -60.0, shelf), _pt("base", -130.0, -20.0, shelf)],
        ("batt", "gnd"): [batt, _pt("base", 20.0, 20.0, shelf), gnd],
        ("gnd", "b5"): _column_up(gnd, reg5),
        ("gnd", "b12c"): [gnd, _pt("base", -20.0, -110.0, shelf), b12c],
        ("gnd", "cont"): [gnd, _pt("base", -80.0, -70.0, shelf), cont],
        ("gnd", "b12a"): _column_up(gnd, conv),
        ("gnd", "b18"): [gnd, _pt("base", 10.0, -100.0, shelf), b18],
        ("pi", "hub"): [pi, _pt("lift", 0.0, 0.0, 400.0), hub],
        ("pi", "esp"): _column_down(pi, esp),
        ("pi", "s3"): _neck(pi, s3),
        ("pi", "audio"): _neck(pi, mic),
        ("pi", "busl"): [pi, _pt("lift", 10.0, 70.0, 360.0), bus_l],
        ("pi", "busr"): [pi, _pt("lift", 10.0, -40.0, 360.0), bus_r],
        ("hub", "cam"): _neck(hub, cam),
        ("hub", "wcl"): _arm("l", hub, (palm_l,)),
        ("hub", "wcr"): _arm("r", hub, (palm_r,)),
        ("hub", "lidar"): _column_down(hub, _pt("base", 150.0, 0.0, 140.0)),
        ("busl", "stl"): _arm("l", bus_l),
        ("busl", "head"): [bus_l, _pt("lift", 20.0, 30.0, 420.0), pan, _pt("head_pan", 5.0, 0.0, 530.0),
                           _pt("head_tilt", 20.0, 0.0, 580.0)],
        ("busr", "str"): _arm("r", bus_r),
        ("s3", "eyes"): [s3, _pt("head_tilt", 30.0, 0.0, 620.0), eyes],
        ("esp", "wheels"): [
            esp, _pt("base", 0.0, 40.0, 80.0),
            _pt("base", 0.0, 120.0, 55.0), _pt("base", 0.0, -120.0, 55.0),
        ],
        ("esp", "tmc"): [esp, _pt("base", -80.0, -50.0, shelf), _pt("base", -130.0, -20.0, shelf)],
        ("esp", "lim"): [esp, _pt("base", -80.0, -40.0, shelf), _pt("base", -60.0, 20.0, 90.0), _pt("base", 13.0, 56.0, 388.0)],
        ("esp", "imu"): [esp, _pt("base", -80.0, -70.0, shelf), _pt("base", -130.0, -45.0, shelf)],
        ("tmc", "nema"): [
            _pt("base", -130.0, -20.0, shelf), _pt("base", -40.0, -10.0, 100.0), _pt("base", 0.0, 0.0, 70.0),
            _pt("base", 20.0, 40.0, 130.0), _pt("base", 13.0, 56.0, 388.0),
        ],
    }


_CACHE = None


def wire_records():
    """WIRES plus len_mm and a viewer path. Lengths use the CAD joint tree."""
    global _CACHE
    if _CACHE is not None:
        return _CACHE
    import sys
    from pathlib import Path

    import numpy as np

    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / "cad"))
    import params as P
    import robot

    table = routes()
    hang = {f"{s}_{k}": 0.0 for s in ("l", "r") for k in
            ("shoulder_pitch", "shoulder_roll", "upper_arm_yaw", "elbow", "wrist_pitch", "wrist_roll")}
    straight = {f"{s}_{k}": v for s in ("l", "r") for k, v in {
        "shoulder_pitch": -1.55, "shoulder_roll": 0.2, "upper_arm_yaw": 0.0,
        "elbow": -0.15, "wrist_pitch": 0.2, "wrist_roll": 0.0}.items()}
    poses = [
        {"lift": 0.0, **hang},
        {"lift": 0.0, **straight},
        {"lift": P.LIFT_TRAVEL / 1000.0, **hang},
        {"lift": P.LIFT_TRAVEL / 1000.0, **straight},
    ]
    transforms = [(pose.get("lift", 0.0), robot.link_transforms(pose)) for pose in poses]

    def length_of(pts, lift, T):
        drop = lift > 0.2
        acc = 0.0
        prev = None
        for item in pts:
            if drop and len(item) == 5 and item[4] == "loop":
                continue
            q = T[item[0]] @ np.array([item[1], item[2], item[3], 1.0])
            if prev is not None:
                acc += float(np.linalg.norm(q[:3] - prev))
            prev = q[:3]
        return acc

    out = []
    for row in WIRES:
        pts = table.get((row[0], row[1]))
        if not pts:
            out.append({"len_mm": None, "path": []})
            continue
        longest = max(length_of(pts, lift, T) for lift, T in transforms)
        path = [{"link": p[0], "x": round(p[1], 1), "y": round(p[2], 1), "z": round(p[3], 1),
                 **({"loop": True} if len(p) == 5 and p[4] == "loop" else {})} for p in pts]
        out.append({"len_mm": int(round(longest * 1.08)), "path": path})
    _CACHE = out
    return out


# ---------------------------------------------------------------- electrical budget
# Volts, design current and peak current for every wire, and a check: python docs/wiring.py
#
# Sources: Pololu product pages (regulator ratings), Daygreen B20-3648-12 page (30-60 V in, 12 V 20 A,
# up to 95 %), TE 2071584-1 (coil 12 V, 5.5 W), Waveshare DDSM115 (18 V, 1.25 A rated, 2.7 A locked) and
# USB hub (2 A per port, 5 A total), Arducam UB0234 (200 mA), Slamtec RPLIDAR C1 (230 mA), Seeed XIAO
# ESP32-S3 (about 140 mA), Raspberry Pi 5 (5 A in, 1.6 A USB with PSU_MAX_CURRENT=5000), Fuji AR9B291
# (5 mA min) and the TE aux contact (10 mA min).
# Assumptions, not datasheet numbers (they stay here and off the site): regulator efficiencies, the
# arm hold current (from the sim check torques), the stepper supply current, 500 mA for USB devices
# with no published current, and the AMPACITY design table.

V_PACK_MIN = 30.0  # 10S at 3.0 V per cell; the arm converters stop at 30 V in
EFF = {"b5": 0.90, "b12c": 0.90, "b12a": 0.93, "b18": 0.90, "hub": 0.85}  # assumed
RATING_A = {"b5": 5.5, "b12c": 4.5, "b12a": 20.0, "b18": 4.0}  # per unit, at the output; b12a is one per arm
PI_USB_A = 1.6
HUB_PORT_A, HUB_TOTAL_A = 2.0, 5.0
USB_UNKNOWN_A = 0.5  # USB 2 port limit, used where the maker publishes no current

# design current, peak current at the device (A)
ARM_HOLD_A, ARM_STALL_A = 17.5, 43.2  # per arm at 12 V: hold from the sim torques; stall = sum of servo stall currents
HEAD_A, HEAD_STALL_A = 1.8, 5.4  # two STS3215: 0.9 A rated, 2.7 A stall each
WHEELS_A, WHEELS_PEAK_A = 2.5, 5.4  # two DDSM115
STEPPER_A, STEPPER_PEAK_A = 1.0, 2.0  # assumed supply current; 2.0 A per phase rated
COIL_A = 0.462
SENSE_A = 0.010
USB_DEV_A = {"cam": USB_UNKNOWN_A, "wcl": 0.2, "wcr": 0.2, "lidar": 0.23, "s3": 0.14, "audio": USB_UNKNOWN_A, "esp": 0.0}

# design limit per gauge, bundled in a sleeve: a deliberately low rule, not a datasheet number
AMPACITY = {26: 2.2, 24: 3.5, 22: 5.0, 20: 7.5, 18: 10.0, 16: 15.0, 14: 20.0, 12: 30.0}

# known problems this PR records but does not fix: (a, b) -> owner
OPEN = {
    ("busl", "stl"): "bob hands: the first servo hop carries the whole arm; needs a 12 V trunk in the arm",
    ("busr", "str"): "bob hands: the first servo hop carries the whole arm; needs a 12 V trunk in the arm",
}


def awg(wire: str):
    import re
    m = re.match(r"\s*(\d+)\s*AWG", wire or "")
    return int(m.group(1)) if m else None


def ohm_per_m(gauge: int) -> float:
    d_mm = 0.127 * 92 ** ((36 - gauge) / 39)
    return 0.017241 / (3.141592653589793 * d_mm * d_mm / 4)


def _hub_in(total_5v):
    return 5.0 * total_5v / EFF["hub"] / 12.0


def elec():
    """(a, b) -> dict(volts, amps, peak). amps is the design current, peak the worst short burst."""
    hub_5v = sum(USB_DEV_A[k] for k in ("cam", "wcl", "wcr", "lidar"))
    out = {
        ("b5", "pi"): (5.0, 5.0, 5.0),
        ("b12c", "estop"): (12.0, COIL_A, COIL_A),
        ("estop", "cont"): (12.0, COIL_A, COIL_A),
        ("gnd", "cont"): (12.0, COIL_A, COIL_A),
        ("estop", "esp"): (12.0, SENSE_A, SENSE_A),
        ("cont", "esp"): (12.0, SENSE_A, SENSE_A),
        ("b12c", "hub"): (12.0, _hub_in(hub_5v), _hub_in(HUB_TOTAL_A)),
        ("b12a", "busl"): (12.0, ARM_HOLD_A + HEAD_A, ARM_STALL_A + HEAD_STALL_A),
        ("b12a", "busr"): (12.0, ARM_HOLD_A, ARM_STALL_A),
        ("busl", "stl"): (12.0, ARM_HOLD_A, ARM_STALL_A),
        ("busr", "str"): (12.0, ARM_HOLD_A, ARM_STALL_A),
        ("busl", "head"): (12.0, HEAD_A, HEAD_STALL_A),
        ("b18", "esp"): (18.0, WHEELS_A, WHEELS_PEAK_A),
        ("esp", "wheels"): (18.0, WHEELS_A, WHEELS_PEAK_A),
        ("b18", "tmc"): (18.0, STEPPER_A, STEPPER_PEAK_A),
        ("tmc", "nema"): (18.0, 2.0, 2.0),
        ("charge", "batt"): (42.0, 2.0, 2.0),
    }
    for (a, b) in [w[:2] for w in WIRES]:
        if (a, b) not in out and a in ("pi", "hub") and b in USB_DEV_A:
            out[(a, b)] = (5.0, USB_DEV_A[b], USB_DEV_A[b])

    def rail_in(node):
        """36 V input current of a regulator, at the lowest pack voltage."""
        outs = [(v, a, p) for (x, _), (v, a, p) in out.items() if x == node]
        n_units = 2 if node == "b12a" else 1
        cap = RATING_A[node] * n_units
        a = sum(v * i for v, i, _ in outs) / EFF[node] / V_PACK_MIN
        p = sum(v * min(i, cap) for v, _, i in outs) / EFF[node] / V_PACK_MIN
        return a, min(p, outs[0][0] * cap / EFF[node] / V_PACK_MIN)

    for node, feed in (("b5", "fuse"), ("b12c", "fuse"), ("b12a", "cont"), ("b18", "cont")):
        a, p = rail_in(node)
        out[(feed, node)] = (36.0, a, p)
        out[("gnd", node)] = (36.0, a, p)
    a = out[("cont", "b12a")][1] + out[("cont", "b18")][1]
    p = out[("cont", "b12a")][2] + out[("cont", "b18")][2]
    out[("fuse", "cont")] = (36.0, a, p)
    a += out[("fuse", "b5")][1] + out[("fuse", "b12c")][1]
    p += out[("fuse", "b5")][2] + out[("fuse", "b12c")][2]
    out[("batt", "fuse")] = (36.0, a, p)
    out[("batt", "gnd")] = (36.0, a, p)
    for a, b, kind, *_ in WIRES:  # data-only wires: logic level, no load
        if (a, b) not in out and kind in ("usb", "signal"):
            out[(a, b)] = (5.0 if kind == "usb" else 3.3, 0.0, 0.0)
    return {k: dict(volts=v, amps=round(a, 3), peak=round(p, 3)) for k, (v, a, p) in out.items()}


def check(lengths=None):
    """Rule check over every wire. Returns (rows, fails, opens)."""
    import re
    E = elec()
    rows, fails, opens = [], [], []
    lengths = lengths or {}
    for a, b, kind, what, wire, conn, fuse in WIRES:
        e = E.get((a, b))
        g = awg(wire)
        msg = []
        if kind.startswith("power") or kind in ("gnd", "estop") or (e and e["amps"] >= 1.0):
            if e is None:
                msg.append("FAIL no volts/amps recorded")
            elif g is None:
                msg.append("FAIL no wire size")
            else:
                cap = AMPACITY[g]
                if e["amps"] > cap:
                    msg.append(f"FAIL {e['amps']:.1f} A over the {g} AWG limit {cap:g} A")
                elif e["peak"] > cap:
                    msg.append(f"note: peak {e['peak']:.1f} A over {cap:g} A (short bursts)")
                m = re.match(r"(\d+(?:\.\d+)?) A", fuse)
                if m:
                    f = float(m.group(1))
                    if f > cap:
                        msg.append(f"FAIL fuse {f:g} A over the {g} AWG limit {cap:g} A")
                    if e["amps"] > 0.8 * f:
                        msg.append(f"FAIL {e['amps']:.1f} A is over 80% of the {f:g} A fuse")
                    if kind == "power36" and "58 V" not in fuse:
                        msg.append("FAIL 36 V fuse without a 58 V rating")
                L = lengths.get((a, b))
                if L:
                    drop = 2 * L / 1000.0 * ohm_per_m(g) * e["amps"] / e["volts"] * 100
                    if drop > 5:
                        msg.append(f"FAIL {drop:.1f}% drop over {L} mm")
                    elif drop > 3:
                        msg.append(f"note: {drop:.1f}% drop over {L} mm")
        if (a, b) in OPEN and any(x.startswith("FAIL") for x in msg):
            opens.append((a, b, OPEN[(a, b)], [x for x in msg if x.startswith("FAIL")]))
            msg = [("OPEN " + x[5:]) if x.startswith("FAIL") else x for x in msg]
        fails += [(a, b, x) for x in msg if x.startswith("FAIL")]
        rows.append((a, b, kind, e, g, lengths.get((a, b)), fuse, "; ".join(msg) or "ok"))
    # regulator, hub and Pi USB budgets
    for node, rating in RATING_A.items():
        outs = [(y, e["amps"]) for (x, y), e in E.items() if x == node]
        if node == "b12a":  # one converter per arm
            fails += [(node, y, f"FAIL {i:.1f} A over one converter's {rating:g} A") for y, i in outs if i > rating]
        elif sum(i for _, i in outs) > rating:
            fails.append((node, "*", f"FAIL {sum(i for _, i in outs):.1f} A over the {rating:g} A rating"))
    hub = [E[("hub", k)]["amps"] for k in ("cam", "wcl", "wcr", "lidar")]
    if max(hub) > HUB_PORT_A or sum(hub) > HUB_TOTAL_A:
        fails.append(("hub", "*", "FAIL hub port or total current"))
    pi_usb = sum(E[("pi", k)]["amps"] for k in ("s3", "audio", "esp"))
    if pi_usb > PI_USB_A:
        fails.append(("pi", "*", f"FAIL Pi USB {pi_usb:.2f} A over {PI_USB_A} A"))
    return rows, fails, opens


def main() -> int:
    try:
        lengths = {w[:2]: r["len_mm"] for w, r in zip(WIRES, wire_records())}
        note = "lengths from the CAD joint tree"
    except Exception as ex:  # no CAD tree or numpy: budget without voltage drop
        lengths, note = {}, f"no lengths ({type(ex).__name__}); voltage drop not checked"
    rows, fails, opens = check(lengths)
    print(f"{'from':>6} {'to':<7} {'kind':<8} {'V':>4} {'A':>6} {'peak':>6} {'AWG':>4} {'mm':>5}  fuse        result")
    for a, b, kind, e, g, L, fuse, res in rows:
        v, i, p = (e["volts"], e["amps"], e["peak"]) if e else (0, 0, 0)
        print(f"{a:>6} {b:<7} {kind:<8} {v:>4.1f} {i:>6.2f} {p:>6.2f} {g or '':>4} {L or '':>5}  {fuse:<11} {res}")
    print(f"\n{note}")
    for a, b, why, what in opens:
        print(f"OPEN  {a} -> {b}: {why}")
    try:
        from bom import TBD
    except ImportError:
        TBD = []
    for sec, what, qty, why in TBD:
        print(f"TBD   {what} x{qty}: {why}")
    for a, b, x in fails:
        print(f"{x}  ({a} -> {b})")
    print("RESULT", "FAIL" if fails else "PASS")
    return 1 if fails else 0


if __name__ == "__main__":
    import sys as _sys
    _sys.exit(main())
