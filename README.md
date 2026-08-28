# Enterprise Express

An Irish train driving game with a 3D WebGL version and a Python/Tkinter fallback. Drive the Enterprise express from Belfast Grand Central to Dublin Connolly, calling at Portadown, Newry, Dundalk, and Drogheda.

## 3D version

Open `irish_train_game_3d.html` in a modern browser. It uses Three.js from a CDN, so an internet connection is needed the first time it loads.

The 3D version includes Class 9001/9003 Enterprise locomotives at each end with smoothly curved raked noses, the twin windscreen, yellow warning bowtie, red marker lamps and magenta/red swoosh livery, seven Mk3 coaches with the tall tinted window band and Enterprise wordmark, an MK3 generator coach, proper railway bogies with spinning wheelsets, continuous ballast track with dense sleepers and rust-shouldered rails, a 300 km/h powertrain with 150/70/45 approach boards, a large world (50 metres of track per map metre of route), animated river and lake water, a girder bridge, Belfast Grand Central and Dublin Connolly as glazed terminus buildings with stepped gable roof bays and platform canopies, blue Enterprise shelters at the other stations, signals, a chase camera, a cab camera with working gauges, and a departure announcement.

## Run

```text
python irish_train_game.py
```

For the 3D game, open `irish_train_game_3d.html` directly. The file `announcement.mp3` should stay beside the HTML file; it plays when the service starts.

## Controls

- `Up` or `W`: accelerate (to 300 km/h on open line)
- `Down` or `S`: brake
- `Space`: emergency brake
- `P`: pause
- `R`: restart

3D-only:

- `V`: switch between front and cab camera
- `F`: show the full formation, including both locomotives and the MK3 generator
- Click `SWITCH SIDE` or press `X`: switch the camera between the left and right side of the train
- Hold the right mouse button and drag: orbit the camera around the train

Speed limits drop to 150 km/h 14 km before each station, 70 km/h 7 km out, and 45 km/h in the final approach. Stop below 14 km/h inside each station's platform zone to score points.
