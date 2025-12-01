from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fingerprint import AudioFingerprint
from pydantic import BaseModel
import base64
import librosa
import io
import os
import numpy as np
import scipy.io.wavfile as wavfile


class SongUpload(BaseModel):
    song_name: str
    file_base64: str

app = FastAPI()
CHUNK_DURATION = 10
TARGET_SR = 11000

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

def load_song(file_names):
        songs = []
        for file_name in file_names:
            file_path = os.path.join('songs', file_name)
            audio, sr = librosa.load(file_path) 
            songs.append((audio, sr))
        return songs

def convert_base64_to_audio(song_base64: str):
    audio_bytes = base64.b64decode(song_base64)
    audio, sr = librosa.load(io.BytesIO(audio_bytes), sr=TARGET_SR)
    if sr != TARGET_SR:
        audio = librosa.resample(audio, orig_sr= sr, target_sr=TARGET_SR)
        sr = TARGET_SR
    return audio, sr


@app.websocket('/stream')
async def stream_audio(ws: WebSocket):
    await ws.accept()
    buffer = np.array([], dtype=np.float32)
    audio_clip = np.array([], dtype=np.float32)
    fp = AudioFingerprint()

    while True:
        try: 
            message = await ws.receive_text()
        except:
            break

        try:
            # convert using librosa from base64 audio file
            audio_arr, sr = convert_base64_to_audio(message)
        except Exception as e:
            await ws.send_text(f"Error decoding audio: {str(e)}")
            continue

        buffer = np.concatenate([buffer, audio_arr])
        audio_clip = np.concatenate([audio_clip, buffer])

        if len(buffer) >= CHUNK_DURATION*TARGET_SR:
            buffer = np.array([], dtype=np.float32)  # clear temporary buffer
            fp = AudioFingerprint()
            result = fp.find_song((audio_clip, TARGET_SR))
            await ws.send_text(str(result))

    await ws.close()

@app.post('/store_song')
def store_song(song: SongUpload):
    audio, sr = convert_base64_to_audio(song.file_base64)
    audio_fingerprint = AudioFingerprint()
    audio_fingerprint.store_songs((audio, sr), song.song_name)
    return {'success': True}

@app.post('/find_song_details')
def find_song(song: SongUpload):
    audio, sr = convert_base64_to_audio(song.file_base64)
    fp = AudioFingerprint()
    response = fp.find_song((audio, sr))
    return {'response': str(response)}

def helper(song_filenames):
    songs = load_song(song_filenames)
    result = []
    idx = 0
    for audio, sr in songs:
        audio = np.int16(audio/ np.max(np.abs(audio))*32767)
        audio_bytes = io.BytesIO()
        wavfile.write(audio_bytes, sr, audio)
        audio_bytes.seek(0)
        base64_song = base64.b64encode(audio_bytes.read()).decode('utf-8')

        song = SongUpload(song_name=song_filenames[idx], file_base64=base64_song)
        result.append(song)
        idx+=1

    return result

if __name__ == '__main__':
    # b_songs = helper(['Paaro.mp3', 'Sahiba.mp3', 'Tension.mp3'])
    b_songs = helper(['sample32.mp3'])
    for b_song in b_songs:
        # print(store_song(b_song))
        print(find_song(b_song))
