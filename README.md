# galaga-lab
Astronomy-themed visual sandbox for education &amp; outreach :-)

## General overview
Generating a random field of astronomical objects in an approachable, non-technical manner to learn about colors, distances, and objects and interpreting astronomical images in an interactive DASH interface

## Features of an AstroObject
Blah

## TODOs
Overall 
- [ ] What the hell does galaga stand for

Objects
- [ ] Actual brightness testing/"exposure time"/make high z objects actually visible (make base brightness more clear?)

Field
- [ ] Fake cosmic web/clustering (random generated field but multiple so it connects)

Frontend
- [ ] Combine Field + Galaxy code

## Installation
From the terminal, run
```sh
conda env create -f environment.yml
```
This will create a new conda environment called ```galaga-lab``` with all the required dependencies

## Quick Start
In the root directory, run
```sh
python app.py
```
The GUI is then available at `http://127.0.0.1:8050/`.
