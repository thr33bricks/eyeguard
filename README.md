<div align="center">

# 👁️ EyeGuard AI
### Real-time AI Eye Protection for Your Desktop

![Python](https://img.shields.io/badge/Python-100%25-3776AB?logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Debian%20Linux-0078D4)
![GPU](https://img.shields.io/badge/GPU-NVIDIA%20%7C%20Integrated-76B900)
![License](https://img.shields.io/badge/License-GPL--3.0-blue)
![Release](https://img.shields.io/badge/Release-v1.0-brightgreen)

*Monitors your eyes in real time and sends native desktop notifications before strain sets in.*

[Download v1.0](#download) · [How It Works](#how-it-works) · [Installation](#installation) · [Contributing](#contributing)

</div>

---

## What is EyeGuard AI?

EyeGuard AI is a background desktop application that uses your webcam and a custom computer vision model to watch for bad screen habits — and nudges you before your eyes pay the price.

It detects three key risk factors in real time:

| Detection | What It Catches |
|-----------|----------------|
| 🔴 **Proximity** | You're sitting too close to the screen |
| 👁️ **Blink Rate** | You've stopped blinking enough (the #1 cause of digital eye strain) |
| 😬 **Squinting** | Your eyes are squinting, often a sign of glare, poor lighting, or fatigue |

When any threshold is crossed, you get a native OS notification — no pop-ups stealing focus, no browser required.

**Everything runs locally. No cloud. No data leaves your machine.**

---

## Download

Head to the [**Releases**](https://github.com/thr33bricks/eyeguard/releases) page to grab the latest build.

| Platform | Status | Download |
|----------|--------|----------|
| Windows 10 / 11 | ✅ Available | [EyeGuard v1.0 (.exe)](https://github.com/thr33bricks/eyeguard/releases/tag/v1.0) |
| Debian / Ubuntu Linux | 🔜 Coming Soon | — |

> The Windows executable is standalone — no Python install required.

---

## How It Works

EyeGuard AI uses a custom-trained eye detection model (found in [`Eyes_model/`](Eyes_model/)) to analyse your webcam feed frame by frame. The [`Calculations/`](Calculations/) module handles the maths behind each detection:

```
Webcam Feed
    └── Face & Eye Detection  (Eyes_model)
            ├── Proximity      → face size / landmark span → estimated distance
            ├── Blink Rate     → eye aspect ratio (EAR) over a rolling time window
            └── Squint Level   → vertical eyelid aperture ratio
                    └── Threshold crossed? → Native OS Notification
```

The main application logic lives in [`Dev/`](Dev/).

GPU acceleration is handled automatically:
- **NVIDIA GPU present** → CUDA inference path for lower CPU load
- **Integrated / no GPU** → CPU inference fallback, still fully functional

---

## Installation (Run from Source)

### Prerequisites

- Python 3.9+
- A webcam
- Git

### Windows

```bash
git clone https://github.com/thr33bricks/eyeguard.git
cd eyeguard/Dev

pip install -r requirements.txt
python main.py
```

### Debian / Ubuntu Linux

```bash
git clone https://github.com/thr33bricks/eyeguard.git
cd eyeguard/Dev

sudo apt update && sudo apt install python3-pip libnotify-bin -y
pip3 install -r requirements.txt
python3 main.py
```

### NVIDIA GPU Acceleration (Optional)

If you have a CUDA-capable NVIDIA GPU, make sure you have the matching CUDA toolkit installed, then install the GPU requirements:

```bash
pip install -r requirements-cuda.txt
```

EyeGuard AI will automatically detect and use your GPU — no extra configuration needed.

---

## Project Structure

```
eyeguard/
├── Dev/              # Main application — entry point, notifications, app loop
├── Eyes_model/       # Custom-trained eye detection model and inference code
├── Calculations/     # Maths
├── LICENSE           # GPL-3.0
└── README.md
```

---

## Supported Platforms

| Platform | Notifications | GPU Acceleration |
|----------|--------------|-----------------|
| Windows 10 / 11 | ✅ Windows Toast | ✅ NVIDIA CUDA + Integrated |
| Debian / Ubuntu | ✅ libnotify (`notify-send`) | ✅ NVIDIA CUDA + Integrated |

---

## Hardware Requirements

| | Minimum | Recommended |
|-|---------|-------------|
| **CPU** | Dual-core 2 GHz | Quad-core 3 GHz+ |
| **RAM** | 4 GB | 8 GB |
| **Webcam** | 720p | 1080p |
| **GPU** | Integrated graphics | NVIDIA (CUDA-capable) |

---

## Contributing

All contributions are welcome — bug reports, feature ideas, and pull requests.

1. Fork this repository
2. Create a branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m "Add your feature"`
4. Push: `git push origin feature/your-feature`
5. Open a Pull Request

Please open an issue first for larger changes so we can discuss the approach.

---

## License

EyeGuard AI is licensed under the [GNU General Public License v3.0](LICENSE).

---

<div align="center">
<sub>Built with Python · Give your eyes a break.</sub>
</div>
