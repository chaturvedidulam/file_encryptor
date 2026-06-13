import os
import numpy as np
from pydub import AudioSegment

AudioSegment.converter = 'ffmpeg' 

def audio_to_amplitude_array(path: str, target_rate: int = 22050, downsample_window: int = 1024):
    """
    Load audio with pydub and return a 1D numpy array of per-window RMS amplitudes.
    """
    try:
        seg = AudioSegment.from_file(path)
        seg = seg.set_frame_rate(target_rate).set_channels(1)
        samples = np.array(seg.get_array_of_samples())
        
        dtype_info = samples.dtype
        maxv = float(np.iinfo(dtype_info).max)
        samples = samples.astype(np.float32) / maxv
        
        # compute RMS per window
        window = downsample_window
        # Ensure array size is divisible by the window size
        trimmed = samples[: len(samples) - (len(samples) % window)]
        arr = trimmed.reshape(-1, window)
        rms = np.sqrt((arr ** 2).mean(axis=1))
        
        return rms
        
    except Exception as e:
        print(f"DEBUG: Audio processing failed in audio_viz.py. Check FFmpeg setup. Error: {e}")
        return None
