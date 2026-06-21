# Forza Horizon 6 Crash Detector (Windows Only)

This is a simple, zero-dependency command-line Python application designed to run on Windows. It listens to the live UDP telemetry broadcast by *Forza Horizon 6* (and other recent Forza titles), calculates real-time G-forces, and automatically plays a local audio clip (`crash.wav`) when a crash/sudden deceleration exceeding 50G is detected.

---

## 1. Setup Audio File
Place a short audio clip in `.wav` format in the same directory as the script, and name it **`crash.wav`**. 
*(Note: Windows `winsound` API natively requires `.wav` files. You can convert any `.mp3` or other format to `.wav` using free online tools).*

---

## 2. In-Game Settings Configuration
To enable the telemetry stream in *Forza Horizon 6*:
1. Go to the game's **Settings** menu.
2. Select **HUD and Gameplay**.
3. Scroll to the bottom of the list to find the **DATA OUT** section.
4. Set the options as follows:
   *   **Data Out**: `ON`
   *   **Data Out IP Address**: `127.0.0.1` *(if running this Python script on the same gaming PC)* or the IP address of the PC/device running the script.
   *   **Data Out IP Port**: `20440`
   *   **Data Out Format**: `Car Dash` (sometimes labeled as "Vehicle Dashboard")

---

## 3. Running the Script
Open Command Prompt (`cmd`) or PowerShell on Windows in the directory containing the script and run:

```bash
python crash_detector.py
```

### Options
You can configure the behavior using command-line arguments:
*   `--port`: Change the UDP port to listen on (e.g. `--port 20440`).
*   `--threshold`: Adjust the trigger G-force (e.g. `--threshold 50.0` for 50G).
*   `--audio`: Specify a custom path to your sound file (e.g. `--audio custom_alert.wav`).
*   `--cooldown`: Seconds to wait before allowing another sound to play (default: `12.0`).
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
   *   For Forza Horizon 6, find the package name first by running:
       ```powershell
       Get-AppxPackage *ForzaHorizon6*
       ```
       Locate the `PackageFamilyName` in the output, and run:
       ```powershell
       CheckNetIsolation.exe LoopbackExempt -a -n="<PackageFamilyName>"
       ```
3. **Use a graphical tool**: Download a free loopback exemption tool such as **"AppContainer Loopback Exemption Utility"** (e.g., from Telerik or GitHub), find the game in the list, check the box to exempt it, and click Save.
