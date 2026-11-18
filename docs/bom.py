"""Bill of materials for Bob v3. One source for BOM.md and the website.

Prices are US dollars, November 2026 listings, before shipping and tax. They move. Every
line has a link so you can check. 'have' marks parts Bob v2 already owns.
Fastener and insert counts come from the CAD build (cad/reports/manifest.json) plus 10%.
"""

BOM = [
    # section, item, qty, each, link, note, have
    ("Actuators", "Feetech STS3250 C001, 12 V, 50 kg·cm", 10, 50.00,
     "https://www.aliexpress.us/w/wholesale-feetech-sts3250.html",
     "8 in the GM-5 joint modules (J1–J4, both arms) and the 2 wrist-pitch joints. AliExpress $48–55; OpenELAB lists $74.", False),
    ("Actuators", "Feetech STS3215 C018, 12 V, 30 kg·cm", 6, 16.00,
     "https://robotshop.com/products/feetech-12v-30kgcm-magnetic-encoding-servo-sts3215",
     "Wrist roll and gripper on both arms, head pan and tilt.", False),
    ("Actuators", "NEMA 17 stepper, 48 mm, 17HS19-2004S1", 1, 14.00,
     "https://www.omc-stepperonline.com/nema-17-bipolar-59ncm-84oz-in-2a-42x48mm-4-wires-w-1m-cable-connector-17hs19-2004s1",
     "Lift. Lives in the mast cap, shaft down.", False),
    ("Actuators", "6.5 in hoverboard hub motor", 2, 30.00,
     "https://www.ebay.com/sch/i.html?_nkw=6.5+hoverboard+hub+motor", "Drive wheels. From Bob v2.", True),

    ("GM-5 joint modules (8)", "6807-2RS thin bearing, 35 x 47 x 7", 8, 3.00,
     "https://www.amazon.com/s?k=6807-2rs+bearing", "Carries each module's output.", False),
    ("GM-5 joint modules (8)", "Hall sensors (DRV5032 or A3144) + 3 x 2 mm magnets", 1, 8.00,
     "https://www.amazon.com/s?k=a3144+hall+sensor+magnets", "One index per module for homing at power-up.", False),
    ("GM-5 joint modules (8)", "ESP32-C3 mini board", 1, 5.00,
     "https://www.amazon.com/s?k=esp32-c3+super+mini", "Torso: reads the 8 hall sensors, USB to the Pi.", False),
    ("GM-5 joint modules (8)", "PETG-CF or PA-CF filament, 250 g", 1, 15.00,
     "https://www.amazon.com/s?k=petg+cf+filament+250g", "Suns, planets and housings wear longer in fibre-filled filament. Plain PETG works.", False),

    ("Motor drivers", "Waveshare Bus Servo Adapter (A)", 2, 12.00,
     "https://www.waveshare.com/bus-servo-adapter-a.htm", "One per arm; the head servos share the left bus.", False),
    ("Motor drivers", "BIGTREETECH TMC2209 stepper driver", 1, 6.00,
     "https://biqu.equipment/products/btt-tmc2209-stepper-driver", "Lift. UART mode, StallGuard as a backup home.", False),
    ("Motor drivers", "ZS-X11H BLDC controller", 2, 15.00,
     "https://www.amazon.com/s?k=ZS-X11H+brushless+controller", "Hub motors. From Bob v2.", True),
    ("Motor drivers", "ESP32 DevKit (WROOM-32)", 1, 8.00,
     "https://www.amazon.com/HiLetgo-ESP-WROOM-32-Development-Microcontroller-Integrated/dp/B0718T232Z",
     "Base controller: wheels, lift, IMU, e-stop sense. USB serial to the Pi.", False),

    ("Compute and sensors", "Raspberry Pi 5", 1, 175.00,
     "https://www.raspberrypi.com/products/raspberry-pi-5/",
     "From Bob v2. Runs the servos, cameras and the policy client; big models run on your desktop GPU over Wi-Fi. "
     "8 GB is $175 new (Nov 2026, after the DRAM price rises).", True),
    ("Compute and sensors", "Raspberry Pi 5 active cooler + 64 GB microSD", 1, 15.00,
     "https://www.raspberrypi.com/products/active-cooler/", "", False),
    ("Compute and sensors", "Wide-angle USB RGB camera, 1080p, 38 mm board", 1, 30.00,
     "https://www.amazon.com/s?k=usb+camera+module+1080p+wide+angle+38mm", "Head camera behind the visor window.", False),
    ("Compute and sensors", "USB UVC camera, 32 x 32 mm board, 1080p, wide angle", 2, 25.00,
     "https://www.amazon.com/s?k=32x32mm+usb+camera+module+1080p+wide+angle", "Wrist cameras.", False),
    ("Compute and sensors", "Slamtec RPLIDAR C1", 1, 69.00, "https://www.slamtec.com/en/C1", "2D lidar for mapping, in the base slot.", False),
    ("Compute and sensors", "BNO085 IMU board", 1, 12.00, "https://www.aliexpress.us/w/wholesale-bno085.html", "Base odometry with the wheel halls. Adafruit's is $20.", False),
    ("Compute and sensors", "GC9A01 1.28 in round TFT, 240 x 240", 2, 6.00, "https://www.amazon.com/s?k=GC9A01+1.28+round+display", "The eyes.", False),
    ("Compute and sensors", "ESP32-S3 mini board", 1, 10.00, "https://www.amazon.com/s?k=esp32-s3+mini+development+board", "Drives the eyes.", False),
    ("Compute and sensors", "USB 2-mic array board", 1, 12.00, "https://www.amazon.com/s?k=usb+2+mic+array+board", "Head top. A ReSpeaker Lite ($25) fits the same spot.", False),
    ("Compute and sensors", "40 mm 3 W speaker + USB audio amplifier", 1, 15.00, "https://www.amazon.com/s?k=usb+powered+speaker+module+3w", "Behind the chest grille.", False),
    ("Compute and sensors", "Powered USB 3 hub, 4 port", 1, 18.00, "https://www.amazon.com/s?k=powered+usb+3.0+hub+4+port", "Torso, on the back plate grid.", False),

    ("Power", "36 V 10S2P hoverboard battery (4.4 Ah, 158 Wh)", 1, 60.00,
     "https://www.ebay.com/sch/i.html?_nkw=36v+hoverboard+battery+4.4ah", "From Bob v2. About 3 h of mixed use.", True),
    ("Power", "42 V 2 A hoverboard charger", 1, 15.00, "https://www.amazon.com/s?k=42v+2a+hoverboard+charger", "From Bob v2.", True),
    ("Power", "DC-DC buck 36 V to 12 V, 25 A (300 W)", 1, 25.00, "https://www.amazon.com/s?k=dc+dc+step+down+36v+to+12v+25a",
     "Every motor: servos, stepper. Behind the contactor.", False),
    ("Power", "DC-DC buck 36 V to 5 V, 8 A", 1, 14.00, "https://www.amazon.com/s?k=dc+dc+step+down+36v+to+5v+8a", "Pi and USB hub, always on.", False),
    ("Power", "DC contactor 48 V 40 A, 12 V coil", 1, 15.00, "https://www.amazon.com/s?k=dc+contactor+48v+40a+12v+coil",
     "Drops every motor when the e-stop opens.", False),
    ("Power", "22 mm mushroom e-stop, NC", 1, 8.00, "https://www.amazon.com/s?k=22mm+mushroom+emergency+stop+NC", "Rear of the base top.", False),
    ("Power", "ATC fuse block, 6 way, with fuses", 1, 12.00, "https://www.amazon.com/s?k=6+way+atc+fuse+block", "One fuse per rail.", False),
    ("Power", "Rocker switch 20 A, panel 20 mm", 1, 5.00, "https://www.amazon.com/s?k=20a+rocker+switch+20mm", "Main power, rear wall.", False),
    ("Power", "XT60 pairs, silicone wire 14/18/22 AWG, ferrules", 1, 30.00, "https://www.amazon.com/s?k=xt60+silicone+wire+kit", "", False),

    ("Lift hardware", "12 mm chrome rod, 1000 mm", 2, 15.00, "https://www.amazon.com/s?k=12mm+linear+rod+1000mm", "", False),
    ("Lift hardware", "LM12UU linear bearing", 4, 2.00, "https://www.amazon.com/s?k=lm12uu", "Press into the carriage.", False),
    ("Lift hardware", "TR8x2 leadscrew 900 mm with brass flange nut", 1, 20.00,
     "https://www.amazon.com/s?k=T8+leadscrew+2mm+lead+900mm", "2 mm lead. It holds the torso with the power off.", False),
    ("Lift hardware", "5 to 8 mm flexible coupler, 25 mm", 1, 3.00, "https://www.amazon.com/s?k=5mm+to+8mm+flexible+coupler", "", False),
    ("Lift hardware", "Micro limit switch, roller lever (KW12)", 1, 2.00, "https://www.amazon.com/s?k=kw12+micro+limit+switch+roller", "Lift home.", False),
    ("Lift hardware", "WS2812B LED strip, 60/m, 0.5 m", 1, 5.00, "https://www.amazon.com/s?k=ws2812b+60+led+strip", "Mast cap light ring.", False),

    ("Fasteners", "M3 heat-set insert, M3 x 5.7", 350, 0.04, "https://www.amazon.com/s?k=m3+heat+set+insert+5.7mm", "Count from the CAD plus 10%.", False),
    ("Fasteners", "M3 socket head screw assortment (6-20 mm), plus M3 nuts", 1, 20.00,
     "https://www.amazon.com/s?k=m3+socket+head+screw+assortment+nuts", "Includes the 24 M3 x 20 planet pins. Count in the list below.", False),
    ("Fasteners", "M2 and M2.5 screw assortment", 1, 9.00, "https://www.amazon.com/s?k=m2+m2.5+screw+assortment", "Servo horns, pads, lidar, cameras.", False),
    ("Fasteners", "M5 x 30 socket head + M5 nut", 4, 0.30, "https://www.amazon.com/s?k=m5x30+socket+head", "Lift tongue to the torso.", False),
    ("Fasteners", "608ZZ bearing", 6, 0.80, "https://www.amazon.com/s?k=608zz+bearing", "Casters.", False),
    ("Fasteners", "M8 x 40 bolt, nyloc, washers", 4, 0.50, "https://www.amazon.com/s?k=m8x40+bolt+nyloc", "Caster axles and swivels.", False),
    ("Fasteners", "25 mm Velcro strap", 2, 1.50, "https://www.amazon.com/s?k=25mm+velcro+battery+strap", "Battery.", False),

    ("Filament", "PETG white, 1 kg", 4, 15.00, "https://www.amazon.com/s?k=petg+white+1kg", "Shells. $15/kg is the usual multi-roll price.", False),
    ("Filament", "PETG grey, 1 kg", 3, 15.00, "https://www.amazon.com/s?k=petg+grey+1kg", "Structure and the module housings.", False),
    ("Filament", "PETG black, 1 kg", 1, 15.00, "https://www.amazon.com/s?k=petg+black+1kg", "Visor, hands, wrists, cap, casters, carriers.", False),
    ("Filament", "TPU 95A, 250 g", 1, 12.00, "https://www.amazon.com/s?k=tpu+95a+filament", "Finger pads.", False),
]
