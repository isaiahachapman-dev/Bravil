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
- **Fluidics** — Kamoer peristaltic pump feeding a custom multi-nozzle array.
- **Vision** — camera + OpenCV pipeline that detects well positions directly
  off the plate.
- **Interface** — touchscreen UI for volume, temperature, and plate format.

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

- `firmware/` — Klipper config and macros
- `software/vision/` — OpenCV detection pipeline
- `software/ui/` — touchscreen control interface
- `cad/` — CAD models and exports
- `docs/` — design history file, figures, validation data

## Team

Six-person team, UC Riverside Department of Bioengineering. This repository is
hosted as a personal portfolio record of the project.
