from fastapi import FastAPI
from fingerprint import AudioFingerprint

app = FastAPI()

@app.post('/store_song')
def store_song(song, song_name):
    audio_fingerprint = AudioFingerprint()
    audio_fingerprint.store_songs(song, song_name)

@app.post('/fing_song_details')
def find_song(song):
    pass

