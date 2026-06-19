# BRAVIL — Automated Well-Plate Filler

A benchtop automated well-plate filler that dispenses biological media into
6-, 12-, and 24-well plates and agar petri dishes. Built as a six-person
senior design capstone at UC Riverside for under $1,500 in parts, as a
low-cost alternative to commercial liquid handlers that cost upward of $100,000.

**Awarded a Certificate of Achievement for an outstanding Bioengineering
presentation at the UC Riverside Senior Design Showcase (May 2026).**

## What it does

BRAVIL takes a plate and a target volume and fills it automatically, holding
dispensing precision within +/-5% per 100 uL across formats. Validated over
100 test runs.

## System overview

- **Motion** — NEMA 17 gantry on a BTT Octopus board running Klipper,
  positioned to sub-millimeter accuracy.
- **Fluidics** — three peristaltic pumps feeding a custom multi-nozzle array
  with motorized nozzle spacing for different plate pitches.
- **Vision** — camera + OpenCV pipeline that detects well positions directly
  off the plate.
- **Interface** — touchscreen kiosk UI for jogging, dispensing, plate presets,
  heat control, and a fill queue, talking to Klipper through Moonraker.

## My contribution

I owned the software, the computer-vision pipeline, and the structural and
motion design: the OpenCV well-detection system, the touchscreen control UI,
and the frame and twin-lead-screw motion mechanism.

## Results

| Metric | Result |
|---|---|
| Dispensing precision | +/-5% per 100 uL |
| Dispensing linearity | R-squared = 0.971 |
| Validation runs | 100 |
| Build cost | under $1,500 |

## Repository structure

```
firmware/
  printer.cfg              Klipper config: steppers, heaters, and fill macros
software/
  vision/
    Cameradetection.py     OpenCV well-detection pipeline
  ui/
    klipper-control.html   Touchscreen kiosk UI (Moonraker REST)
    installKiosk.sh        Raspberry Pi kiosk setup script
```

## Plate format support

| Format | Firmware (fill macros) | Vision detection |
|---|---|---|
| 6-well   | Yes | Yes |
| 12-well  | Yes | Yes |
| 24-well  | Yes | In progress |
| 96-well  | Yes | Planned |

The motion and dispensing macros handle all four ANSI/SLAS formats. The vision
pipeline currently auto-detects 6- and 12-well layouts; 24- and 96-well
detection is in progress.

## Running the vision pipeline

```
python Cameradetection.py path/to/plate.jpg
```

Outputs detected well coordinates in millimeters and a six-stage debug figure
showing each step of the detection process.

## Team

Six-person team, UC Riverside Department of Bioengineering. This repository is
hosted as a personal portfolio record of the project. CAD models and the design
history file are maintained separately and available on request.
