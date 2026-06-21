import socket
import struct
import math
import time
import sys
import os
import subprocess
import argparse

def play_audio(file_path):
    """
    Plays the specified audio file asynchronously based on the platform.
    Windows uses native winsound (no packages required), macOS uses afplay.
    """
    if not os.path.exists(file_path):
        print(f"\n[WARNING] Audio file '{file_path}' not found! Place it in the script directory.")
        return

    if sys.platform == "win32":
        try:
            import winsound
            winsound.PlaySound(file_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
        except Exception as e:
            print(f"\n[ERROR] Failed to play sound on Windows winsound: {e}")
    elif sys.platform == "darwin":
        try:
            subprocess.Popen(["afplay", file_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            print(f"\n[ERROR] Failed to play sound on macOS afplay: {e}")
    else:
        # Linux fallback
        for player in ["aplay", "paplay", "ffplay -nodisp -autoexit"]:
            try:
                cmd = player.split() + [file_path]
                subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                break
            except Exception:
                continue

def parse_arguments():
    parser = argparse.ArgumentParser(description="Forza Horizon 6 Crash Detector (Windows Only)")
    parser.add_argument("--ip", type=str, default="0.0.0.0", help="IP address to listen on (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=20440, help="UDP port configured in Forza (default: 20440)")
    parser.add_argument("--threshold", type=float, default=50.0, help="G-force threshold to trigger audio (default: 50.0)")
    parser.add_argument("--audio", type=str, default="crash.wav", help="WAV audio file path (default: crash.wav)")
    parser.add_argument("--cooldown", type=float, default=12.0, help="Cooldown in seconds between alarm triggers (default: 12.0)")
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
    
    if not os.path.exists(args.audio):
        print(f"[WARNING] '{args.audio}' not found. The app will log crashes but won't make sound.")
        print("Please place a WAV file in this directory and rename it to 'crash.wav'.")
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
            if g_monitored >= args.threshold:
                if current_time - last_trigger_time >= args.cooldown:
                    last_trigger_time = current_time
                    print("\n" + "*" * 80)
                    print(f" [CRASH DETECTED] Telemetry trigger: {g_monitored:.2f} G!")
                    print(f" Impact Speed    : {speed_kmh:.1f} km/h ({speed_mph:.1f} mph)")
                    print(f" Force vectors   : Lateral G: {gx:.2f} | Vertical G: {gy:.2f} | Longitudinal G: {gz:.2f}")
                    print(f" Playing audio file: {args.audio}")
                    print("*" * 80)
                    play_audio(args.audio)

    except KeyboardInterrupt:
        print("\nExiting program... Good bye!")
    finally:
        sock.close()

if __name__ == "__main__":
    main()
