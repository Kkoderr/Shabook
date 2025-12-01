# Shabook 🎵

**Shabook** is a web and Python application for audio fingerprinting. It allows you to store songs and later identify them, including via live streaming from microphone input.
The system uses **Redis** as a fast in-memory database for storing and matching audio fingerprints.

---

## 🧩 Features

- **Store Songs**: Upload audio files and store them with a unique fingerprint.
- **Find Songs (Upload)**: Upload an audio clip to identify the song.
- **Redis-powered Matching** — Ultra-fast hash lookup for fingerprints  
- **Live Streaming**: Record audio using your microphone and stream it to the server in real-time for instant identification.
- **Cross-platform**: Works on modern browsers and a Python backend.

---

## 🛠️ Tech Stack

- **Frontend**: HTML, JavaScript (Web Audio API, WebSocket)
- **Backend**: Python 3, FastAPI, librosa, NumPy, Redis
- **Others**: Base64 encoding/decoding for audio streaming

---

## 🧰 Redis Setup

Shabook uses **Redis** to store and retrieve audio fingerprints.  
You can install Redis using Docker:

```bash
docker run -d \
  --name redis-shabook \
  -p 6379:6379 \
  redis
```
Or install locally:
https://redis.io/docs/install/

Make sure the Redis server is running before starting FastAPI.

---

## ⚙️ Installation

1. Clone the repository:

```bash
git clone https://github.com/Kkoderr/Shabook.git
cd Shabook
```

2.	Install dependencies:
```bash
pip install -r requirements.txt
```

3.	Run the FastAPI server:
```bash
uvicorn app:app --reload
```

4.	Open index.html in a browser to access the frontend.

---

## 📌 Usage
  - Store a Song
  	1.	Go to the Store Song tab.
  	2.	Enter the song name.
  	3.	Upload an audio file.
  	4.	Click Store Song to save it. A confirmation popup will appear.
  
  - Find a Song (Upload)
  	1.	Switch to the Find Song tab.
  	2.	Upload an audio clip.
  	3.	Click Find Song to get matching results.
  
  - Find a Song (Live Streaming)
  	1.	Click the 🎤 (microphone) button in Find Song tab.
  	2.	Allow the browser to access your microphone.
  	3.	The app streams audio in real-time and shows results as toast notifications.
  	4.	Click the 🎤 button again to stop streaming.

---

## 📁 Project Structure
  ```bash
  /Shabook
    ├── app.py             # FastAPI backend (REST & WebSocket)
    ├── fingerprint.py     # Audio fingerprint logic
    ├── index.html         # Frontend UI
    ├── requirements.txt   # Python dependencies
    ├── assets/            # CSS, images, etc.
    └── README.md          # This file
  ```

---

## 💡 Example Response
  Matching results are returned as a list of tuples:
  ```bash
  [('Paaro', 48.66), ('Ishq Bawla', inf), ('Sahiba', inf)]
```
  
  Where the first element is the song name and the second is the match score. (lower is better)

---

## 🚀 Future Improvements
  - Support more audio formats
  - Improved fingerprinting algorithm
  -	Enhanced UI with better toast notifications and recording indicators
  -	Optional user authentication and metadata storage
  -	Automated testing for fingerprinting and streaming

---

## 🤝 Contributing
  -	Fork the repository.
  -	Create a feature branch: git checkout -b feature/your-feature.
  -	Make changes and test locally.
  -	Submit a pull request.
