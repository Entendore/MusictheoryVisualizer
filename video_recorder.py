import os, sys, wave, subprocess, shutil, tempfile
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QMessageBox

class VideoRecorder:
    def __init__(self, main_window, audio_engine):
        self.main_window = main_window
        self.audio = audio_engine
        self.timer = QTimer()
        self.timer.timeout.connect(self._capture_frame)
        self.is_recording = False
        self.frames = []
        self.fps = 30
        self.output_path = ''
        self.temp_dir = ''

    def start(self, output_path):
        self.output_path = output_path
        self.temp_dir = tempfile.mkdtemp(prefix='mtv_rec_')
        self.frames = []
        self.is_recording = True
        self.audio.start_recording()
        self.timer.start(int(1000 / self.fps))

    def stop_and_encode(self):
        self.timer.stop()
        self.is_recording = False
        raw_audio = self.audio.stop_recording()
        self.main_window.statusBar().showMessage("Encoding video... Please wait.")

        # 1. Save Audio
        wav_path = os.path.join(self.temp_dir, 'audio.wav')
        with wave.open(wav_path, 'w') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(44100)
            wf.writeframes(raw_audio)

        # 2. Encode with FFmpeg
        ffmpeg_exe = 'ffmpeg'
        if sys.platform == 'win32': ffmpeg_exe = 'ffmpeg.exe'
        has_ffmpeg = shutil.which(ffmpeg_exe) is not None

        if has_ffmpeg:
            cmd = [
                ffmpeg_exe, '-y',
                '-framerate', str(self.fps),
                '-i', os.path.join(self.temp_dir, 'frame_%05d.png'),
                '-i', wav_path,
                '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-preset', 'fast',
                '-c:a', 'aac', '-b:a', '192k',
                '-shortest', self.output_path
            ]
            try:
                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                QMessageBox.information(self.main_window, "Recording Complete", f"Video saved to:\n{self.output_path}")
                shutil.rmtree(self.temp_dir)
                self.main_window.statusBar().showMessage("Ready")
                return True
            except Exception as e:
                QMessageBox.warning(self.main_window, "Encoding Failed", f"FFmpeg failed: {e}\n\nSaving raw files instead.")
        else:
            msg = "FFmpeg not found! Cannot auto-encode.\n\n"

        # Fallback: Save script and raw files
        fallback_dir = os.path.splitext(self.output_path)[0] + "_raw_frames"
        try:
            shutil.move(self.temp_dir, fallback_dir)
        except Exception:
            shutil.rmtree(fallback_dir)
            shutil.move(self.temp_dir, fallback_dir)

        script_path = os.path.join(fallback_dir, 'encode.bat' if sys.platform == 'win32' else 'encode.sh')
        with open(script_path, 'w') as f:
            f.write(f"{ffmpeg_exe} -y -framerate {self.fps} -i frame_%05d.png -i audio.wav -c:v libx264 -pix_fmt yuv420p -c:a aac -shortest \"{os.path.abspath(self.output_path)}\"\n")
        
        QMessageBox.information(self.main_window, "Raw Files Saved", f"Frames and audio saved to:\n{fallback_dir}\n\nRun the script inside to encode!")
        self.main_window.statusBar().showMessage("Ready")
        return False

    def _capture_frame(self):
        if not self.is_recording: return
        idx = len(self.frames)
        path = os.path.join(self.temp_dir, f"frame_{idx:05d}.png")
        pixmap = self.main_window.grab()
        pixmap.save(path)
        self.frames.append(path)