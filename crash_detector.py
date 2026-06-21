import socket
import struct
import math
import time
import sys
import os
import subprocess
import argparse
import threading
import random
import glob

# Global tracker for stopping playback after the 5-second hard limit
audio_timer = None

def stop_audio():
    """Stops any currently playing audio on Windows."""
    if sys.platform == "win32":
        try:
            import winsound
            winsound.PlaySound(None, winsound.SND_PURGE)
        except Exception:
            pass

def play_audio(file_path):
    """
    Plays the specified audio file asynchronously based on the platform.
    Windows uses native winsound (no packages required), macOS uses afplay.
    Enforces a hardcoded time limit of 5.0 seconds.
    """
    global audio_timer
    
    # Cancel any active stop timer
    if audio_timer is not None:
        audio_timer.cancel()
        audio_timer = None

    if not os.path.exists(file_path):
        print(f"\n[WARNING] Audio file '{file_path}' not found!")
        return

    if sys.platform == "win32":
        try:
            import winsound
            # Stop currently playing sound first to avoid overlapping issues
            winsound.PlaySound(None, winsound.SND_PURGE)
            # Play new sound asynchronously
            winsound.PlaySound(file_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
            
            # Start timer to stop the audio after 5 seconds
            audio_timer = threading.Timer(5.0, stop_audio)
            audio_timer.start()
        except Exception as e:
            print(f"\n[ERROR] Failed to play sound on Windows winsound: {e}")
    elif sys.platform == "darwin":
        try:
            proc = subprocess.Popen(["afplay", file_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            audio_timer = threading.Timer(5.0, lambda: proc.terminate() if proc.poll() is None else None)
            audio_timer.start()
        except Exception as e:
            print(f"\n[ERROR] Failed to play sound on macOS afplay: {e}")
    else:
        # Linux fallback
        for player in ["aplay", "paplay", "ffplay -nodisp -autoexit"]:
            try:
                cmd = player.split() + [file_path]
                proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                audio_timer = threading.Timer(5.0, lambda: proc.terminate() if proc.poll() is None else None)
                audio_timer.start()
                break
            except Exception:
                continue

def get_audio_files(path):
    """
    Returns a list of all .wav files in the target folder.
    If path is a directory, returns all .wav files in it.
    If path is a file, returns all .wav files in the directory containing the file.
    """
    if not path:
        return []
    
    if os.path.isdir(path):
        dir_name = path
    else:
        dir_name = os.path.dirname(path) or "."
        
    files = glob.glob(os.path.join(dir_name, "*.wav"))
    return sorted([f for f in files if os.path.isfile(f)])

def parse_arguments():
    parser = argparse.ArgumentParser(description="Forza Horizon 6 Crash Detector (Windows Only)")
    parser.add_argument("--ip", type=str, default="0.0.0.0", help="IP address to listen on (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=5700, help="UDP port configured in Forza (default: 5700)")
    parser.add_argument("--threshold", type=float, default=15.0, help="G-force threshold to trigger audio (default: 15.0)")
    parser.add_argument("--audio", type=str, default="sounds/crash.wav", help="WAV audio file path (default: sounds/crash.wav)")
    parser.add_argument("--cooldown", type=float, default=3.0, help="Cooldown in seconds between alarm triggers (default: 3.0)")
    parser.add_argument("--axis", type=str, choices=["all", "long", "lat"], default="all", 
                        help="Which G-force axis to monitor: all (3D G-force), long (longitudinal/deceleration only), lat (lateral only)")
    return parser.parse_args()

def main():
    args = parse_arguments()
    
    print("=" * 60)
    print("           FORZA HORIZON 6 CRASH ROAST DETECTOR")
    print("=" * 60)
    print(f" Listening on IP   : {args.ip}")
    print(f" Listening on Port : {args.port}")
    print(f" G-Force Threshold : {args.threshold} G")
    print(f" Monitor Axis      : {args.axis}")
    print(f" Audio Track file  : {args.audio}")
    print(f" Cooldown Period   : {args.cooldown} seconds")
    print("-" * 60)
    
    audio_files = get_audio_files(args.audio)
    if not audio_files:
        print(f"[WARNING] No matching audio files found for '{args.audio}'. The app will log crashes but won't make sound.")
        print("Please place a WAV file (e.g. 'crash.wav', 'crash_01.wav', etc.) in the directory.")
        print("-" * 60)
    else:
        print(f" Found {len(audio_files)} audio file(s) for playback:")
        for f in audio_files:
            print(f"   - {f}")
        print("-" * 60)

    # Setup socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.bind((args.ip, args.port))
    except Exception as e:
        print(f"[CRITICAL ERROR] Failed to bind to {args.ip}:{args.port} - {e}")
        print("Ensure no other app is using this port.")
        sys.exit(1)

    print("Status: Waiting for Forza telemetry...")
    
    last_trigger_time = 0.0
    packet_count = 0
    total_received = 0
    speed_history = []
    crash_history = []
    
    # We unpack specific fields from their standard byte offsets in the Forza packet
    # Offset 0: IsRaceOn (s32)
    # Offset 20: AccelerationX (f32, right=positive, m/s^2)
    # Offset 24: AccelerationY (f32, up=positive, m/s^2)
    # Offset 28: AccelerationZ (f32, forward=positive, m/s^2)
    # Offset 32: VelocityX (f32, m/s)
    # Offset 36: VelocityY (f32, m/s)
    # Offset 40: VelocityZ (f32, m/s)
    
    try:
        while True:
            # Forza packets are usually 311, 324, or 331 bytes
            data, addr = sock.recvfrom(1024)
            if len(data) < 44: # Minimum size to get acceleration and velocity
                continue
                
            total_received += 1
            is_race_on = struct.unpack_from("<i", data, 0)[0]

            if not is_race_on:
                print("\rStatus: In Menus / Paused                   ", end="", flush=True)
                continue
                
            packet_count += 1
            
            # Unpack acceleration (local space, m/s^2) and velocity (local space, m/s)
            ax, ay, az = struct.unpack_from("<fff", data, 20)
            vx, vy, vz = struct.unpack_from("<fff", data, 32)
            
            # Convert acceleration to Gs (1G = 9.80665 m/s^2)
            gx = ax / 9.80665
            gy = ay / 9.80665
            gz = az / 9.80665
            
            # Calculate speed (magnitude of velocity vector) in km/h and mph
            speed_ms = math.sqrt(vx**2 + vy**2 + vz**2)
            speed_kmh = speed_ms * 3.6
            speed_mph = speed_ms * 2.23694
            
            # Maintain a sliding window of the last 8 speeds (~130ms at 60Hz)
            speed_history.append(speed_kmh)
            if len(speed_history) > 8:
                speed_history.pop(0)
            
            # Determine G-force of interest based on the axis argument
            if args.axis == "long":
                # Longitudinal deceleration (negative Z acceleration)
                g_monitored = -gz if gz < 0 else 0.0
            elif args.axis == "lat":
                # Lateral force magnitude
                g_monitored = abs(gx)
            else:
                # 3D G-force magnitude
                g_monitored = math.sqrt(gx**2 + gy**2 + gz**2)
                
            # Calculate speed drop in the last 130ms
            speed_drop = speed_history[0] - speed_history[-1] if len(speed_history) >= 8 else 0.0
                
            current_time = time.time()
            cooldown_remaining = args.cooldown - (current_time - last_trigger_time)
            
            # Update console with live status (updates in-place)
            status_line = (
                f"\rSpeed: {speed_kmh:5.1f} km/h | "
                f"G-Force: {g_monitored:5.1f} G (X:{gx:+4.1f}, Y:{gy:+4.1f}, Z:{gz:+4.1f})"
            )
            if cooldown_remaining > 0:
                status_line += f" [Cooldown: {cooldown_remaining:4.1f}s]"
            else:
                status_line += " [Active]"
            
            # Only print updates every 10 packets to avoid console lag at 60Hz
            if packet_count % 10 == 0:
                print(status_line.ljust(80), end="", flush=True)
                
            # Crash detection logic
            # A real crash requires a G-force spike AND a sudden drop in speed (>= 12 km/h in 130ms)
            # This filters out fake spikes from bumps, landing jumps, or driving over curbs.
            if g_monitored >= args.threshold and speed_drop >= 12.0:
                if current_time - last_trigger_time >= args.cooldown:
                    last_trigger_time = current_time
                    print("\n" + "*" * 80)
                    print(f" [CRASH DETECTED] Telemetry trigger: {g_monitored:.2f} G | Speed Drop: {speed_drop:.1f} km/h!")
                    print(f" Impact Speed    : {speed_kmh:.1f} km/h ({speed_mph:.1f} mph)")
                    print(f" Force vectors   : Lateral G: {gx:.2f} | Vertical G: {gy:.2f} | Longitudinal G: {gz:.2f}")
                    
                    # Dynamically select a random audio file from discovered options
                    audio_files = get_audio_files(args.audio)
                    if audio_files:
                        chosen_audio = random.choice(audio_files)
                        print(f" Playing audio file: {chosen_audio} (out of {len(audio_files)} option(s)) [5s Limit]")
                        play_audio(chosen_audio)
                    else:
                        chosen_audio = "None"
                        print(f" [WARNING] No audio files found to play!")
                    
                    # Record telemetry to history list and CSV file
                    log_file = "crash_telemetry_log.csv"
                    file_exists = os.path.exists(log_file)
                    try:
                        with open(log_file, "a") as f:
                            if not file_exists:
                                f.write("Timestamp,TriggerGForce,SpeedKMH,SpeedMPH,LateralG,VerticalG,LongitudinalG,AudioPlayed\n")
                            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                            f.write(f"{timestamp},{g_monitored:.3f},{speed_kmh:.2f},{speed_mph:.2f},{gx:.3f},{gy:.3f},{gz:.3f},{chosen_audio}\n")
                        print(f" Telemetry recorded to {log_file}")
                    except Exception as le:
                        print(f" [ERROR] Could not log telemetry to file: {le}")
                        
                    crash_history.append({
                        "time": time.strftime("%H:%M:%S"),
                        "g_force": g_monitored,
                        "speed": speed_kmh,
                        "vectors": (gx, gy, gz)
                    })
                    print("*" * 80)

    except KeyboardInterrupt:
        print("\nExiting program... Good bye!")
        if crash_history:
            print("\n" + "=" * 80)
            print("                            CRASH SESSION SUMMARY")
            print("=" * 80)
            print(f" Total Crashes Recorded: {len(crash_history)}")
            print("-" * 80)
            print(f" {'Time':8} | {'G-Force':9} | {'Speed':12} | {'G-Vectors (X, Y, Z)':25}")
            print("-" * 80)
            for record in crash_history:
                gx, gy, gz = record["vectors"]
                print(f" {record['time']:8} | {record['g_force']:7.2f} G | {record['speed']:7.1f} km/h  | ({gx:+4.1f}, {gy:+4.1f}, {gz:+4.1f})")
            print("=" * 80)
    finally:
        sock.close()

if __name__ == "__main__":
    main()
