from scipy.signal import spectrogram
import librosa
import numpy as np
import os
import hashlib
import redis
from dotenv import load_dotenv

class AudioFingerprint():

    def __init__(self):
        pass

    def load_song(self,file_names):
        songs = []
        for file_name in file_names:
            file_path = os.path.join('songs', file_name)
            audio, sr = librosa.load(file_path) 
            songs.append((audio, sr))
        return songs

    def preprocess_audio(self, audio, orig_sr, target_sr):
        if(audio.ndim>1):
            audio = audio.mean(axis=1)
        audio = audio/np.max(np.abs(audio))
        return librosa.resample(audio, orig_sr= orig_sr, target_sr= target_sr )

    def split_audio_sections(self, audio):
        window_size = 20000
        audio_sections = [audio[i:(i+window_size if audio.shape[0]>i+window_size else audio.shape[0])] for i in range(0,audio.shape[0],window_size)]
        return audio_sections

    def create_spectogram(self, audio_sections, sr):
        audio_spectrogram = []
        
        for audio in audio_sections:
            window = np.hamming(len(audio))
            windowed_audio = audio * window
            f, t, Sxx = spectrogram(windowed_audio, sr)
            audio_spectrogram.append((f, t, Sxx))
        
        return audio_spectrogram

    def get_max_amp_per_band(self, spectrogram_tuple):
        f, t, Sxx = spectrogram_tuple

        # Define frequency bands in Hz
        bands = [(0,100), (100,200), (200,400), (400,800), (800,1600), (1600,5110)]

        results = []

        for low, high in bands:
            # find indices of frequencies within this band
            idx = np.where((f >= low) & (f < high))[0]

            if len(idx) == 0:
                results.append((0,0,0))
                continue
            
            # For those freq rows, find maximum amplitude over all time frames
            band_matrix = Sxx[idx, :]
            freq_i, time_i = np.unravel_index(
                np.argmax(band_matrix),
                band_matrix.shape
            )
            peak_freq = f[idx[freq_i]]
            peak_time = t[time_i]
            peak_amp = band_matrix[freq_i, time_i]

            # Append tuple for this band
            results.append((peak_freq, peak_time, peak_amp))

        return results

    def create_anchor_target_pairs(self, band_peaks, fan_value=3, chunk_offset=0):
        pairs = []

        for i, anchor in enumerate(band_peaks):
            anchor_freq, anchor_time, _ = anchor

            # pick next N peaks as targets
            for j in range(i+1, min(i + 1 + fan_value, len(band_peaks))):
                target_freq, target_time, _ = band_peaks[j]

                delta_time = target_time - anchor_time
                if delta_time <= 0:
                    continue  # ignore invalid

                # store pair
                pairs.append((
                    anchor_freq,
                    target_freq,
                    delta_time,
                    anchor_time+chunk_offset
                ))

        return pairs

    def store_songs(self, song, song_name):

        load_dotenv()
        REDIS_HOST = os.environ.get("REDIS_HOST")
        REDIS_PORT = os.environ.get("REDIS_PORT")
        client = redis.Redis(host=REDIS_HOST, port=int(REDIS_PORT), decode_responses=True)
        audio, sr = song
        audio = self.preprocess_audio(audio, sr, 11000)
        sr = 11000
        audio_sections = self.split_audio_sections(audio)
        sections_spectrogram = self.create_spectogram(audio_sections, sr)
        for chunk_id, section_spectrogram in enumerate(sections_spectrogram):
            f, t, Sxx = section_spectrogram
            chunk_offset = (chunk_id * 20000) / sr
            peaks_per_band = self.get_max_amp_per_band(section_spectrogram)
            fingerprints = self.create_anchor_target_pairs(peaks_per_band, chunk_offset=chunk_offset)
            for fp in fingerprints:

                freq1, freq2, dt, at = fp
                fp_string = f"{freq1}|{freq2}|{round(dt,3)}"
                hashed_fp = hashlib.md5(fp_string.encode()).hexdigest()

                value = f"{song_name}|{at}"

                client.sadd(f"fingerprint:{hashed_fp}", value)
    
    def best_match(self, sample_map, possible: dict):
        song_score = {}

        for song, matches in possible.items():
            offsets = []
            # Collect offsets for all matching hashes
            for hash_val, stored_at in matches:
                if hash_val not in sample_map:
                    continue
                sample_at = sample_map[hash_val]
                offsets.append(stored_at - sample_at)
            # Too few matches = likely a false match
            if len(offsets) < 4:
                song_score[song] = float('inf')
                continue
            # Compute robust alignment
            median_offset = np.median(offsets)
            # Score = how tightly offsets cluster around median
            deviation = np.mean(np.abs(offsets - median_offset))
            song_score[song] = deviation

        return song_score

    def find_song(self, song):
        load_dotenv()
        REDIS_HOST = os.environ.get("REDIS_HOST")
        REDIS_PORT = os.environ.get("REDIS_PORT")
        client = redis.Redis(host=REDIS_HOST, port=int(REDIS_PORT), decode_responses=True)
        audio, sr = song
        processed_audio = self.preprocess_audio(audio, sr, 11000)
        sr = 11000
        audio_sections = self.split_audio_sections(processed_audio)
        sections_spectrogram = self.create_spectogram(audio_sections, sr)
        song_map = {}
        for chunk_id, section_spectrogram in enumerate(sections_spectrogram):
            peaks_per_band = self.get_max_amp_per_band(section_spectrogram)
            chunk_offset = (chunk_id * 20000) / sr
            fingerprints = self.create_anchor_target_pairs(peaks_per_band, chunk_offset=chunk_offset)
            for fp in fingerprints:

                freq1, freq2, dt, at = fp
                fp_string = f"{freq1}|{freq2}|{round(dt,3)}"
                hashed_fp = hashlib.md5(fp_string.encode()).hexdigest()
                song_map[hashed_fp] = at
        
        match_map = {}
        for hash in song_map.keys():
            values = client.smembers(f'fingerprint:{hash}')
            for value in values:
                song, at = value.split('|')
                at = float(at)
                if song not in match_map:
                    match_map[song] = []
                match_map[song].append((hash, at))
        
        song_score = self.best_match(song_map, match_map)
        return sorted(song_score.items(), key=lambda x:x[1])

if __name__=='__main__':
    af = AudioFingerprint()
    # song_name = ['Ishq Bawla.mp3', 'Paaro.mp3', 'Tension.mp3']
    # song_name = ['Issey Kehte Hip Hop.mp3']
    # songs = af.load_song(song_name)
    # idx = 0
    # for song in songs:
    #     af.store_songs(song, song_name[idx])
    #     idx +=1
    songs = af.load_song(['sample.mp3'])
    print(af.find_song(songs[0]))