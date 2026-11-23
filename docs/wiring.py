"""Every wire in Bob v3. One source for the wiring diagram, the wire table and the viewer's wiring layer.

Column umbilical
  One PET sleeve, zip-tied at each stage and again on the inner-tube cap.
  The slack folds as a serpentine in the base trough (six printed drag-chain
  links) and pays out through the rear window of the outer tube, the open
  notch in the middle tube, and the bore of the upper and inner tubes.
  Travel is 558 mm. The sleeve passes the T8 bridge on the left (y about 20 mm).
  Power to the chest and the lidar USB ride that sleeve. Camera USB stays in
  the chest, the neck, and the arms.

  PATHS are polylines in each link's zero-pose CAD frame (mm). A point tagged
  "loop" is the trough coil. Cut length is the longer of the coiled route at
  lift = 0 and the paid-out route at full lift, over hanging and straight arms,
  plus 8 percent for terminations. The coil is not counted twice at full lift.

NODES: id -> (label, sub, column, row, cad item for the 3D overlay or None)
WIRES: (from, to, kind, what, wire, connector, fuse)
kind: power36 | power12 | power5 | usb | ttl | signal | motor | estop
"""

NODES = {
    "charge": ("Charge socket", "GX16, base top", 0, 4, "charge_socket"),
    "batt": ("36 V pack", "10S2P · 158 Wh", 0, 5, "battery"),
    "fuse": ("Switch + fuse block", "30 A main", 1, 5, "fuse_block"),
    "estop": ("E-stop", "NC, 22 mm", 0, 8, "estop"),
    "b5": ("5 V regulator", "Pololu D36V50F5", 2, 5, "reg_5v"),
    "cont": ("Contactor", "e-stop loop", 1, 8, "contactor_relay"),
    "pi": ("Raspberry Pi 5", "robot computer", 3, 5, "pi5"),
    "b12a": ("12 V 10 A ×2", "DROK, one per arm", 2, 7, "buck_12v"),
    "b12m": ("12 V regulator", "Pololu D36V50F12", 2, 9, "reg_12v"),
    "hub": ("USB 3 hub", "bus-powered", 4, 2, "usb_hub"),
    "busl": ("Bus adapter left", "Feetech TTL", 4, 6, "servo_bus"),
    "busr": ("Bus adapter right", "Feetech TTL", 4, 7, "servo_bus_r"),
    "esp": ("DDSM Driver HAT (A)", "ESP32 + RS485", 4, 10, "ddsm_driver"),
    "cam": ("Head camera", "USB RGB, wide", 5, 0, "head_cam"),
    "wcam": ("Wrist cameras ×2", "USB 2", 5, 1, "wrist_cam_l"),
    "stl": ("Left arm + head", "STS IDs 1–7, 8–9", 5, 6, "j1_l"),
    "str": ("Right arm", "STS IDs 1–7", 5, 7, "j1_r"),
    "wheels": ("DDSM115 ×2", "IDs 1 and 2", 5, 10, "hub_l"),
    "tmc": ("TMC2209", "UART, StallGuard", 4, 11, "tmc2209"),
    "imu": ("BNO085 IMU", "I2C", 5, 12, "imu"),
    "lidar": ("RPLIDAR C1", "USB", 5, 2, "lidar"),
    "s3": ("XIAO ESP32-S3 eyes", "SPI to 2 × GC9A01", 5, 4, "esp32s3_head"),
    "audio": ("Mic + speaker", "USB", 5, 3, "mic_array"),
    "nema": ("Lift NEMA 17", "+ limit switch", 5, 11, "lift_motor"),
}

WIRES = [
    ("charge", "batt", "power36", "Charge from the hoverboard charger, 42 V 2 A", "18 AWG", "GX16 3-pin", "BMS"),
    ("batt", "fuse", "power36", "Main battery feed", "12 AWG", "XT60", "30 A"),
    ("fuse", "b5", "power36", "Pi rail, always on", "20 AWG", "ferrules", "3 A"),
    ("fuse", "cont", "power36", "Motor feed", "14 AWG", "ring lugs M4", "25 A"),
    ("estop", "cont", "estop", "Coil loop through the NC e-stop", "22 AWG", "spade 4.8", "1 A"),
    ("cont", "b12a", "power36", "Arm converters", "16 AWG", "ferrules", "15 A"),
    ("cont", "b12m", "power36", "Base converter", "18 AWG", "ferrules", "5 A"),
    ("b5", "pi", "power5", "Pi 5 power, 5.1 V 5 A, up the column sleeve", "18 AWG", "GPIO 5V pins", ""),
    ("b12a", "busl", "power12", "Left arm + head servos, up the column sleeve", "16 AWG", "5.5/2.1 → bus", "10 A"),
    ("b12a", "busr", "power12", "Right arm servos, up the column sleeve", "16 AWG", "5.5/2.1 → bus", "10 A"),
    ("b12m", "esp", "power12", "Wheel and HAT power", "18 AWG", "XT60", "5 A"),
    ("b12m", "tmc", "power12", "Stepper driver VM", "20 AWG", "JST-XH", "3 A"),
    ("pi", "hub", "usb", "USB 3", "", "USB-A to USB-C", ""),
    ("pi", "busl", "usb", "USB", "", "USB-C", ""),
    ("pi", "busr", "usb", "USB", "", "USB-C", ""),
    ("pi", "esp", "usb", "USB serial, JSON commands", "", "USB-C", ""),
    ("hub", "cam", "usb", "USB", "", "USB-A", ""),
    ("hub", "wcam", "usb", "USB 2 ×2", "", "USB-A, down the arms", ""),
    ("hub", "lidar", "usb", "USB down the column sleeve", "", "USB-A", ""),
    ("hub", "s3", "usb", "USB serial", "", "USB-C", ""),
    ("hub", "audio", "usb", "USB audio", "", "USB-A", ""),
    ("busl", "stl", "ttl", "Half-duplex TTL, 1 Mbit/s", "18 AWG", "Molex 5264 3-pin", ""),
    ("busr", "str", "ttl", "Half-duplex TTL, 1 Mbit/s", "18 AWG", "Molex 5264 3-pin", ""),
    ("esp", "wheels", "ttl", "RS485 A/B, 115200 baud; 12 V on XH2.54", "18 AWG + twisted pair", "ZH1.5 4-pin + XH2.54", ""),
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
    cam = _pt("head_tilt", 65.0, 0.0, 648.0)
    s3 = _pt("head_tilt", 1.0, 0.0, 587.0)
    mic = _pt("head_tilt", 21.0, 0.0, 683.0)
    palm_l = _pt("l_link6", -16.0, 157.0, -70.0)
    palm_r = _pt("r_link6", -16.0, -157.0, -70.0)
    return {
        ("charge", "batt"): [_pt("base", 125.0, -110.0, 212.0), _pt("base", 80.0, -40.0, shelf), _pt("base", 0.0, 80.0, 130.0)],
        ("batt", "fuse"): [_pt("base", 0.0, 80.0, 130.0), _pt("base", 0.0, 20.0, shelf), _pt("base", 0.0, -72.0, shelf)],
        ("fuse", "b5"): [_pt("base", 0.0, -72.0, shelf), _pt("base", 0.0, -162.0, shelf)],
        ("fuse", "cont"): [_pt("base", 0.0, -72.0, shelf), _pt("base", -80.0, -80.0, shelf), _pt("base", -130.0, -96.0, shelf)],
        ("estop", "cont"): [_pt("base", -122.0, 112.0, 212.0), _pt("base", -140.0, 40.0, 180.0), _pt("base", -130.0, -96.0, shelf)],
        ("cont", "b12a"): [_pt("base", -130.0, -96.0, shelf), _pt("base", -72.0, -112.0, shelf), _pt("base", 72.0, -112.0, shelf)],
        ("cont", "b12m"): [_pt("base", -130.0, -96.0, shelf), _pt("base", -40.0, -120.0, shelf), _pt("base", 0.0, -132.0, shelf)],
        ("b5", "pi"): _column_up(_pt("base", 0.0, -162.0, shelf), pi),
        ("b12a", "busl"): _column_up(_pt("base", -72.0, -112.0, shelf), bus_l),
        ("b12a", "busr"): _column_up(_pt("base", 72.0, -112.0, shelf), bus_r),
        ("b12m", "esp"): [_pt("base", 0.0, -132.0, shelf), _pt("base", 0.0, -104.0, shelf)],
        ("b12m", "tmc"): [_pt("base", 0.0, -132.0, shelf), _pt("base", -80.0, -60.0, shelf), _pt("base", -130.0, -20.0, shelf)],
        ("pi", "hub"): [_pt("lift", 0.0, 78.0, 392.0), _pt("lift", 0.0, 0.0, 400.0), hub],
        ("pi", "busl"): [pi, _pt("lift", 10.0, 70.0, 360.0), bus_l],
        ("pi", "busr"): [pi, _pt("lift", 10.0, -40.0, 360.0), bus_r],
        ("pi", "esp"): _column_down(pi, _pt("base", 0.0, -104.0, shelf)),
        ("hub", "cam"): _neck(hub, cam),
        ("hub", "wcam"): _arm("l", hub, (palm_l,)) + [_pt("lift", 0.0, -20.0, 380.0)] + _arm("r", hub, (palm_r,))[1:],
        ("hub", "lidar"): _column_down(hub, _pt("base", 192.0, 0.0, 140.0)),
        ("hub", "s3"): _neck(hub, s3),
        ("hub", "audio"): _neck(hub, mic),
        ("busl", "stl"): _arm("l", bus_l),
        ("busr", "str"): _arm("r", bus_r),
        ("esp", "wheels"): [
            _pt("base", 0.0, -104.0, shelf), _pt("base", 0.0, 40.0, 80.0),
            _pt("base", 0.0, 120.0, 55.0), _pt("base", 0.0, -120.0, 55.0),
        ],
        ("esp", "tmc"): [_pt("base", 0.0, -104.0, shelf), _pt("base", -80.0, -50.0, shelf), _pt("base", -130.0, -20.0, shelf)],
        ("esp", "imu"): [_pt("base", 0.0, -104.0, shelf), _pt("base", -80.0, -70.0, shelf), _pt("base", -130.0, -45.0, shelf)],
        ("esp", "estop"): [_pt("base", 0.0, -104.0, shelf), _pt("base", -140.0, 0.0, 170.0), _pt("base", -122.0, 112.0, 200.0)],
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
