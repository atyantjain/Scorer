# Audio Editor 🎛️

A professional Flask web application that dissects music files into separate components and provides a full editor interface for rebuilding them with custom settings.

## Features

- **Audio Dissection**: Separates music into harmonic, percussive, bass, mid, and high frequency components
- **Full Editor Interface**: Professional mixing console with individual track controls
- **Real-time Audio Analysis**: Displays tempo, key, brightness, dynamic range, and more
- **Individual Track Controls**: 
  - Volume sliders (0-200%)
  - Pan controls (Left/Right)
  - Solo/Mute buttons
  - Enable/disable tracks
- **Global Effects**: 
  - Reverb with adjustable amount
  - Compression with adjustable intensity
- **Visual Interface**: Clean, dark-themed editor inspired by professional DAWs
- **Custom Mix Generation**: Create and export your personalized mix
- **In-Browser Playback**: Listen to individual tracks and final mixes
- **File Support**: Accepts MP3, WAV, FLAC, M4A, and OGG formats

## Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Application**:
   ```bash
   python app.py
   ```

3. **Open Your Browser**:
   Navigate to `http://localhost:5000`

## Usage

1. **Upload**: Click the upload area or drag and drop a music file
2. **Editor Opens**: Professional interface loads with separated tracks
3. **Mix**: Adjust individual track volumes, panning, and effects
4. **Analyze**: View real-time audio analysis (tempo, key, brightness, etc.)
5. **Export**: Generate your custom mix and download as WAV

## Technical Details

- **Max File Size**: 16MB
- **Processing Limit**: First 60 seconds of audio (for performance)
- **Output Format**: WAV files at original sample rate
- **Audio Separation**: Uses librosa's harmonic-percussive separation + frequency domain filtering
- **Interface**: Responsive web design with professional DAW-style layout
- **Real-time Analysis**: Tempo detection, key estimation, spectral analysis
- **Temporary Storage**: Generated tracks and mixes stored in the `outputs/` directory

## Requirements

- Python 3.7+
- Flask for web framework
- librosa for music analysis and manipulation
- scipy for advanced signal processing
- soundfile for audio file I/O
- numpy for numerical operations

## File Structure

```
Scorer/
├── app.py              # Main Flask application
├── requirements.txt    # Python dependencies
├── templates/
│   └── index.html     # Web interface
├── uploads/           # Temporary upload storage (auto-created)
└── outputs/           # Generated sample storage (auto-created)
```

## Notes

- The app automatically creates `uploads/` and `outputs/` directories
- Uploaded files are deleted after processing to save disk space
- Generated tracks and mixes include unique IDs to prevent filename conflicts
- Processing time varies based on file size and audio complexity
- Each separated track uses optimized algorithms for best quality
- The editor interface works best on desktop/tablet screens
- Audio analysis provides insights into musical characteristics
- Individual track separation quality depends on source material complexity
- Processing time varies based on file size and length