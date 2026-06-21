import sys
import os
import subprocess
import glob

def convert_file(mp3_path, wav_path=None):
    if not wav_path:
        base, _ = os.path.splitext(mp3_path)
        wav_path = base + ".wav"
        
    # Standard PCM 16-bit WAV conversion
    cmd = [
        "ffmpeg",
        "-y",
        "-i", mp3_path,
        "-acodec", "pcm_s16le",
        "-ar", "44100",
        wav_path
    ]
    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        print(f"  [SUCCESS] Converted: {os.path.basename(mp3_path)} -> {os.path.basename(wav_path)}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"  [ERROR] Failed to convert {os.path.basename(mp3_path)}: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Convert single file:  python convert_mp3_to_wav.py <input.mp3> [output.wav]")
        print("  Convert whole folder: python convert_mp3_to_wav.py <directory_path>")
        sys.exit(1)
        
    path = sys.argv[1]
    
    # Check if ffmpeg is available
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: 'ffmpeg' was not found on your system's PATH.")
        print("Please install ffmpeg or add it to your PATH to run this script.")
        sys.exit(1)

    if os.path.isdir(path):
        print(f"Scanning directory '{path}' for MP3 files...")
        mp3_files = glob.glob(os.path.join(path, "*.mp3"))
        if not mp3_files:
            print("No MP3 files found in the directory.")
            return
            
        print(f"Found {len(mp3_files)} MP3 file(s). Starting conversion...")
        successful = 0
        for f in mp3_files:
            if convert_file(f):
                successful += 1
        print(f"Done! Successfully converted {successful} of {len(mp3_files)} files.")
    elif os.path.isfile(path):
        output_wav = sys.argv[2] if len(sys.argv) > 2 else None
        convert_file(path, output_wav)
    else:
        print(f"Error: Path '{path}' is not a valid file or directory.")
        sys.exit(1)

if __name__ == "__main__":
    main()
