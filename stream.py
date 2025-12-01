import asyncio
import websockets
import base64
import librosa
import numpy as np
import io

CHUNK_DURATION = 5
TARGET_SR = 11000

async def stream():
    async with websockets.connect("ws://localhost:8000/stream") as ws:
        # Load the entire MP3 file with librosa and resample
        audio, sr = librosa.load("songs/sample2.mp3", sr=TARGET_SR)
        total_samples = len(audio)
        chunk_size = CHUNK_DURATION * TARGET_SR

        # Split into 5-second chunks
        for start in range(0, total_samples, chunk_size):
            chunk = audio[start:start + chunk_size]
            # Convert float32 to int16 for WAV
            int_chunk = np.int16(chunk / np.max(np.abs(chunk)) * 32767)
            buffer = io.BytesIO()
            import scipy.io.wavfile as wavfile
            wavfile.write(buffer, TARGET_SR, int_chunk)
            buffer.seek(0)
            # Encode chunk to base64 and send
            await ws.send(base64.b64encode(buffer.read()).decode())
            # Wait for server acknowledgement
            msg = await ws.recv()
            print(msg)

if __name__ == '__main__':
    asyncio.run(stream())