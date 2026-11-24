"""Bill of materials for Bob v3. One source for BOM.md and the website.

Prices are US dollars from the linked product page on 2026-11-18, before shipping and tax. Every line links to
a specific product, not a search. Where a page could not be checked (the seller blocks automated fetches)
the note says so. 'have' marks parts Bob v2 already owns.
Fastener and insert counts come from the CAD build (cad/reports/manifest.json) plus 10%.
"""

BOM = [
    # section, item, qty, each, link, note, have
    ("Actuators", "Feetech STS3095-C002, 12 V, 95 kg·cm (30 x 65 x 48 mm, 15T dual shaft)", 6, 89.00,
     "https://rcdrone.top/products/feetech-sts3095-servo-motor",
     "J1 shoulder pitch, J2 shoulder roll, J4 elbow, both arms. Same grade Nori A3 uses on gravity joints. Some listings are $139.", False),
    ("Actuators", "Feetech STS3250-C001, 12 V, 50 kg·cm (45.22 x 24.72 x 35 mm, 25T)", 4, 99.00,
     "https://openelab.com/products/feetech-sts3250-c001-ttl-servo",
     "J3 upper-arm yaw and wrist pitch (J5) on both arms. Same 45 x 25 x 35 case as the STS3215.", False),
    ("Actuators", "Feetech STS3215-C018, 12 V, 30 kg·cm (45.2 x 24.7 x 35 mm, 25T)", 6, 27.99,
     "https://openelab.com/products/feetech-sts3215-c018-servo-12v",
     "Wrist roll, gripper, head pan and tilt.", False),
    ("Actuators", "Waveshare DDSM115 direct-drive hub motor (tire 100.7 x 43 mm, from Waveshare's STEP)", 2, 64.99,
     "https://www.waveshare.com/ddsm115.htm", "Drive wheels. 12-24 V, RS485, 0.96 N·m rated. Bolts to the printed bracket with 3 x M2.5.", False),
    ("Actuators", "StepperOnline 17HS19-2004S1 NEMA 17, 42 x 42 x 48 mm, 5 mm shaft", 1, 14.00,
     "https://www.omc-stepperonline.com/nema-17-bipolar-59ncm-84oz-in-2a-42x48mm-4-wires-w-1m-cable-and-connector.html",
     "Lift. Price is an estimate: the store blocks automated checks.", False),

    ("Motor drivers", "Waveshare Bus Servo Adapter (A), 42 x 33 mm", 2, 4.99,
     "https://www.waveshare.com/bus-servo-adapter-a.htm", "One per arm; the head servos share the left bus.", False),
    ("Motor drivers", "Waveshare DDSM Driver HAT (A), 85 x 57 mm, ESP32 + RS485", 1, 21.99,
     "https://www.waveshare.com/ddsm-driver-hat-a.htm", "Base controller: both wheels, the lift driver, IMU, e-stop sense.", False),
    ("Motor drivers", "BIGTREETECH TMC2209 V1.3", 1, 7.89,
     "https://us.biqu.equipment/products/bigtreetech-tmc2209-stepper-motor-driver-for-3d-printer-board-vs-tmc2208",
     "Lift. UART mode, StallGuard as a backup home.", False),

    ("Compute and sensors", "Raspberry Pi 5, 8 GB", 1, 200.00, "https://www.adafruit.com/product/5813",
     "From Bob v2. Big models run on your desktop GPU over Wi-Fi.", True),
    ("Compute and sensors", "Raspberry Pi Active Cooler", 1, 13.50, "https://www.adafruit.com/product/5815", "", False),
    ("Compute and sensors", "Raspberry Pi SD card, 64 GB", 1, 12.79, "https://www.adafruit.com/product/6011",
     "Out of stock at Adafruit on 2026-11-18; Waveshare sells the same card.", False),
    ("Compute and sensors", "1080p USB wide-angle camera, OV2710, 38 x 38 mm board, 120°", 1, 44.99,
     "https://openelab.com/products/1080p-usb-wide-angle-camera", "Head camera behind the visor window.", False),
    ("Compute and sensors", "Arducam UB0234 1080p USB camera, 32 x 32 mm board, M12 105°", 2, 45.00,
     "https://www.arducam.com/blog/product/arducam-2mp-wide-angle-usb2-0-camera-board-with-m12-lens-1-2-7-cmos-ov2710-uvc-usb-webcam-without-microphone-for-computer-laptop-android-device-and-raspberry-pi/",
     "Wrist cameras: 32 x 32 mm, 28 x 28 hole pitch. Price is an estimate (EUR 41.90 at Welectron, sold out).", False),
    ("Compute and sensors", "Slamtec RPLIDAR C1, 55.6 x 55.6 x 41.3 mm", 1, 79.99, "https://www.waveshare.com/rplidar-c1.htm", "", False),
    ("Compute and sensors", "Adafruit BNO085 IMU, 25.6 x 22.7 mm", 1, 29.50, "https://www.adafruit.com/product/4754", "", False),
    ("Compute and sensors", "Waveshare 1.28 in round LCD module (GC9A01, Ø37.5)", 2, 14.99,
     "https://www.waveshare.com/1.28inch-lcd-module.htm", "The eyes.", False),
    ("Compute and sensors", "Seeed XIAO ESP32-S3", 1, 7.49, "https://www.seeedstudio.com/XIAO-ESP32S3-p-5627.html", "Drives the eyes.", False),
    ("Compute and sensors", "Seeed ReSpeaker Lite (USB 2-mic)", 1, 24.90, "https://www.seeedstudio.com/ReSpeaker-Lite-p-5928.html", "", False),
    ("Compute and sensors", "Adafruit Mini External USB Stereo Speaker", 1, 12.50, "https://www.adafruit.com/product/3369", "", False),
    ("Compute and sensors", "Waveshare USB 3.2 Gen1 hub, 4 port", 1, 21.99,
     "https://www.waveshare.com/usb3.2-gen1-hub-2in-4out.htm", "Bus-powered from the Pi.", False),

    ("Power", "36 V 10S2P hoverboard battery, 4.4 Ah, 158 Wh", 1, 60.00, "https://www.wyat.dev/bob-v2/",
     "From Bob v2. Measure it: the cradle is drawn for 80 x 200 x 70 mm.", True),
    ("Power", "42 V 2 A hoverboard charger, GX16 3-pin plug", 1, 15.00, "https://www.wyat.dev/bob-v2/",
     "From Bob v2. Bob plugs it into the socket on top of his base himself.", True),
    ("Power", "GX16 3-pin panel-mount socket and plug pair, 16 mm hole", 1, 2.95,
     "https://www.elecbee.com/en/product-detail/gx16-aviation-connector-male-and-female-one-pair-3pin-straightpanel-mount-solder-type-connector_48546",
     "Charge socket, base top. Matches the hoverboard charger plug. 7 A rating.", False),
    ("Power", "Pololu D36V50F5, 5 V 5.5 A, 25.4 x 25.4 mm", 1, 44.95, "https://www.pololu.com/product/4091",
     "Pi, always on. 5.5-50 V input.", False),
    ("Power", "Pololu D36V50F12, 12 V 4.5 A, 25.4 x 25.4 mm", 2, 44.95, "https://www.pololu.com/product/4095",
     "One always on, ahead of the contactor: the contactor coil through the e-stop. One switched: wheels and the lift stepper. 13.3-50 V input.", False),
    ("Power", "DROK 24-60 V to 12 V 10 A step-down converter", 2, 26.00,
     "https://www.amazon.com/DROK-Waterproof-Converter-Regulator-Transformer/dp/B017SQ2PUG",
     "One per arm. The same listing as the Bob v2 page; price not checked by hand.", False),
    ("Power", "TE Connectivity 2071584-1 relay, 50 A, 12 V coil", 1, 57.00,
     "https://www.te.com/en/product-2071584-1.html", "E-stop contactor, ECK50B series. Coil 12 V DC, 5.5 W, fed from the always-on 12 V through the e-stop. TE's page says not currently available; DigiKey lists it at about $57.", False),
    ("Power", "Fuji AR22Q2R-01R 22 mm e-stop, 1 NC, 35 mm mushroom", 1, 30.50,
     "https://www.automationdirect.com/adc/shopping/catalog/pushbuttons_-z-_switches_-z-_indicators/emergency_stop_pushbuttons/ar22q2r-01r",
     "Rear of the base top.", False),
    ("Power", "Blue Sea Systems 5025 ST blade fuse block, 6 circuits", 1, 59.99,
     "https://thornebros.com/products/blue-sea-systems-st-blade-fuse-block-6-circuits-with-negative-bus-and-cover-5025", "", False),

    ("Lift hardware", "TR8x2 leadscrew 500 mm with brass nut (Ø22 flange)", 1, 24.99,
     "https://www.omc-stepperonline.com/tr8-trapezoidal-lead-screw-8mm-2mm-lead-500mm-length-with-copper-nut.html",
     "Cut to 266 mm. Drives the middle tube only. The tubes above it are belted. Check the nut's 4 x M3 on Ø16.", False),
    ("Lift hardware", "5 to 8 mm flexible coupler, 25 x Ø19 mm, 2 pack", 1, 39.99,
     "https://vxb.com/products/two-pack-5mm-to-8mm-aluminum-shaft-coupling-flexib", "", False),
    ("Lift hardware", "GT2 20T pulley, 6 mm belt, 5 mm bore, 2 pack", 2, 8.99,
     "https://www.omc-stepperonline.com/gt2-pulley-20-teeth-bore-5mm-for-6mm-belt.html",
     "Four pulleys. Two on the middle tube (belt A, upper tube at 2×) and two on the upper tube (belt B, inner tube at 3×).", False),
    ("Lift hardware", "GT2 open timing belt, 6 mm wide, 2 m", 1, 7.99,
     "https://www.omc-stepperonline.com/gt2-open-ended-timing-belt-width-6mm-2meters.html",
     "Two loops, about 1.2 m together. Belt A anchors on the outer tube. Belt B anchors on the middle tube.", False),
    ("Lift hardware", "1/4 in PET expandable sleeving, 10 ft", 1, 7.99,
     "https://www.amazon.com/Alex-Tech-Expandable-Braided-Sleeving/dp/B07BQ9GZN4",
     "One sleeve for the column umbilical. About 1.2 m is in the bore; the rest folds in the base trough. Price not checked by hand.", False),

    ("Fasteners", "CNC Kitchen M3 x 5.7 heat-set inserts, 100 pack", 4, 10.25,
     "https://cnckitchen.store/products/heat-set-insert-m3-x-5-7-100-pieces", "EUR 9.40 each; ships from the EU.", False),
    ("Fasteners", "M3 screw and nut kit, 750 pieces, M3 x 6-30", 1, 49.93,
     "https://vxb.com/products/ultimate-m3-screws-and-nuts-kit-for-3d-printing-75", "Clamshell bolts, servo-tab screws.", False),
    ("Fasteners", "M3 x 50 socket head cap screws, 12.9 black oxide, 25 pack", 1, 9.29,
     "https://www.amazon.com/Socket-Screws-Metric-Machine-Threaded/dp/B09682LBD7",
     "Four for the elbow-cover collars (they pass through the upper arm). Price from the listing, November 2026.", False),
    ("Fasteners", "Metric socket cap screw kit, M2-M8, 441 pieces", 1, 67.55,
     "https://www.albanycountyfasteners.com/metric-socket-cap-screw-assortment-kit-p/1060-090.htm",
     "M2 for horns and cameras. Buy M2.5 x 10 separately for the DDSM115 stubs.", False),
    ("Fasteners", "TOVOT CY-15A 5/8 in steel ball transfer, 44 lb, 4 pack", 1, 6.99,
     "https://www.amazon.com/dp/B07YYSW494",
     "The two casters, bolted under the pan; two spares. 48 x 32 x 20 mm, holes 39 mm apart. Price from the listing; the store blocks automated checks. Best on hard floors.", False),

    ("Filament", "Prusament PETG, 1 kg", 6, 23.99, "https://www.prusa3d.com/product/prusament-petg-anthracite-grey-1kg-nfc/",
     "Pick colours: white shells, grey structure, black trim.", False),
    ("Filament", "Bambu Lab TPU 95A HF, 1 kg", 1, 25.19, "https://us.store.bambulab.com/products/tpu-95a-hf",
     "Compliant TPU fingers (Nori-style).", False),
]

# Parts the wiring needs but whose part number or value is not checked against a datasheet yet.
# Kept off the site and out of BOM.md: publish.py and make_docs.py read BOM only.
# `python docs/wiring.py` prints this list with the wire budget.
TBD = [
    # section, what, qty, why it is open
    ("Power", "Flyback diode across the contactor coil", 1, "part number and rating not checked yet"),
]
