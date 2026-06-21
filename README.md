# Forza Horizon 6 Crash Detector (Windows Only)

This is a simple, zero-dependency command-line Python application designed to run on Windows. It listens to the live UDP telemetry broadcast by *Forza Horizon 6* (and other recent Forza titles) and automatically plays a local audio clip (`crash.wav`) when a crash is detected (using a combined G-force spike and sudden speed-drop algorithm).

---

## 1. Setup Audio File
Create a folder named **`sounds`** in the same directory as the script, and place your short audio clips in `.wav` format inside it (for example, `sounds/crash.wav`, `sounds/roast.wav`, etc.).

### Random Audio Playback / Multiple Clips
The app automatically scans the `sounds` folder for **all** `.wav` files. Each time a crash is detected, it will randomly select and play one of these files!

*(Note: Windows `winsound` API natively requires `.wav` files. You can convert any `.mp3` or other format to `.wav` using free online tools. There is a hardcoded playback limit of **5 seconds** per alert).*

---

## 2. Configure Forza Horizon 6
In FH6, open:

Settings -> HUD and Gameplay
Set:

Data Out:            On
Data Out IP Address: 127.0.0.1
Data Out IP Port:    5700

Use 127.0.0.1 when the app runs on the same PC as the game.


## 3. Running the Script
Open Command Prompt (`cmd`) or PowerShell on Windows in the directory containing the script and run:

```bash
python crash_detector.py
```

### Options
You can configure the behavior using command-line arguments:
*   `--port`: Change the UDP port to listen on (e.g. `--port 5700`).
*   `--threshold`: Adjust the trigger G-force threshold (default: `15.0`).
*   `--audio`: Specify a custom path to your sound file (e.g. `--audio custom_alert.wav`).
*   `--cooldown`: Seconds to wait before allowing another sound to play (default: `3.0`).
*   `--axis`: Limit monitoring to a specific axis (`all` for 3D G-force, `long` for forward-backward deceleration, `lat` for side-to-side drift impacts).

Example:
```bash
python crash_detector.py --threshold 45.0 --cooldown 15.0 --axis long
```

---

## 4. Troubleshooting Local Loopback (Microsoft Store / Xbox App Version)
If you run the game and the script on the same Windows PC, and you are using the **Microsoft Store or Xbox Game Pass** version of the game, Windows security isolation blocks Microsoft Store Apps from sending UDP traffic to localhost (`127.0.0.1`). 

### Solution (Choose one):
1. **Steam version**: If you own the Steam version of the game, it is a desktop app and does not have this restriction. It will work immediately.
2. **Exempt the Game (AppContainer Loopback Exemption)**:
   You can exempt the game using Windows command line.
   *   Open PowerShell as **Administrator**.
   *   For Forza Horizon 5, run:
       ```powershell
       CheckNetIsolation.exe LoopbackExempt -a -n="Microsoft.624F8CE97B47E_8wekyb3d8bbwe"
       ```
    *   For Forza Horizon 6 (Windows Store / Game Pass version), run:
        ```powershell
        CheckNetIsolation.exe LoopbackExempt -a -n="Microsoft.ForteBaseGame_8wekyb3d8bbwe"
        ```
3. **Use a graphical tool**: Download a free loopback exemption tool such as **"AppContainer Loopback Exemption Utility"** (e.g., from Telerik or GitHub), find the game in the list, check the box to exempt it, and click Save.


