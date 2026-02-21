from flask import Flask, render_template, request, send_file, jsonify
import librosa
import soundfile as sf
import numpy as np
import os
import tempfile
from werkzeug.utils import secure_filename
import uuid
from datetime import datetime
from scipy import signal
from scipy.ndimage import median_filter
import warnings
warnings.filterwarnings('ignore')

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'outputs'

# Create directories if they don't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'mp3', 'wav', 'flac', 'm4a', 'ogg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def separate_audio_sources(audio, sr):
    """Advanced audio source separation using librosa techniques"""
    # Harmonic-Percussive Source Separation
    harmonic, percussive = librosa.effects.hpss(audio)
    
    # Use STFT for frequency-based separation
    stft = librosa.stft(audio)
    magnitude = np.abs(stft)
    phase = np.angle(stft)
    
    # Get frequency bins
    freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)  # Default n_fft
    
    # Create frequency-based separations
    bass_stft = stft.copy()
    mid_stft = stft.copy()
    high_stft = stft.copy()
    
    # Apply frequency-based filtering
    for i, freq in enumerate(freqs):
        if freq > 250:  # Zero out bass frequencies for mid/high
            bass_stft[i, :] = 0
        if freq <= 250 or freq > 4000:  # Zero out non-mid frequencies
            mid_stft[i, :] = 0
        if freq <= 4000:  # Zero out low/mid frequencies for highs
            high_stft[i, :] = 0
    
    # Convert back to audio
    bass_audio = librosa.istft(bass_stft)
    mid_audio = librosa.istft(mid_stft)
    high_audio = librosa.istft(high_stft)
    
    # Ensure all outputs are the same length as input
    target_length = len(audio)
    bass_audio = librosa.util.fix_length(bass_audio, size=target_length)
    mid_audio = librosa.util.fix_length(mid_audio, size=target_length)
    high_audio = librosa.util.fix_length(high_audio, size=target_length)
    harmonic = librosa.util.fix_length(harmonic, size=target_length)
    percussive = librosa.util.fix_length(percussive, size=target_length)
    
    return {
        'harmonic': harmonic,
        'percussive': percussive,
        'bass': bass_audio,
        'mids': mid_audio,
        'highs': high_audio,
        'full_mix': audio
    }

def generate_synthetic_instruments(duration, sr, key='C', tempo=120):
    """Generate synthetic instrument sounds"""
    t = np.linspace(0, duration, int(duration * sr), False)
    
    instruments = {}
    
    # Fundamental frequency for the key (simplified - using A4 = 440Hz)
    fundamental = 440  # A4
    
    # Synthetic Piano (clean harmonics with natural decay)
    piano_freq = fundamental * 0.75  # Lower pitch for richness
    piano = (0.5 * np.sin(2 * np.pi * piano_freq * t) + 
             0.3 * np.sin(2 * np.pi * piano_freq * 2 * t) +
             0.1 * np.sin(2 * np.pi * piano_freq * 3 * t))
    # Natural piano decay
    decay = np.exp(-2 * t)
    piano *= decay
    instruments['piano'] = piano * 0.4
    
    # Synthetic Strings (rich harmonics with vibrato)
    string_freq = fundamental * 1.5
    strings_base = signal.sawtooth(2 * np.pi * string_freq * t)
    # Add vibrato (6Hz modulation)
    vibrato = 1 + 0.05 * np.sin(2 * np.pi * 6 * t)
    strings = strings_base * vibrato
    # String-like envelope
    string_env = np.exp(-0.5 * t)
    instruments['strings'] = strings * string_env * 0.3
    
    # Electronic Pad (warm, sustained)
    pad_freq = fundamental * 0.5
    pad = (0.4 * np.sin(2 * np.pi * pad_freq * t) +
           0.3 * np.sin(2 * np.pi * pad_freq * 1.5 * t) +
           0.2 * np.sin(2 * np.pi * pad_freq * 2 * t))
    # Sustained envelope
    pad_env = 1 - 0.1 * np.exp(-0.2 * t)
    instruments['pad'] = pad * pad_env * 0.25
    
    # Bass (sub-bass with punch)
    bass_freq = fundamental * 0.25  # Two octaves down
    bass = (0.7 * np.sin(2 * np.pi * bass_freq * t) +
            0.4 * np.sin(2 * np.pi * bass_freq * 2 * t) +
            0.2 * np.sin(2 * np.pi * bass_freq * 3 * t))
    # Bass envelope with punch
    bass_env = np.exp(-1.5 * t)
    instruments['bass'] = bass * bass_env * 0.5
    
    # Ambient Texture (filtered noise for atmosphere)
    noise = np.random.normal(0, 0.1, len(t))
    # Low-pass filter the noise
    nyquist = sr // 2
    cutoff = 800  # Hz
    if cutoff < nyquist:
        b, a = signal.butter(4, cutoff / nyquist, btype='low')
        ambient = signal.filtfilt(b, a, noise)
    else:
        ambient = noise
    # Very subtle ambient level
    instruments['ambient'] = ambient * 0.15
    
    return instruments

def create_mood_remix(separated_sources, sr, mood='happy', original_duration=None):
    """Create mood-specific remixes by replacing/modifying separated sources"""
    if original_duration is None:
        original_duration = len(separated_sources['full_mix']) / sr
    
    # Generate synthetic instruments
    synth_instruments = generate_synthetic_instruments(original_duration, sr)
    
    mood_configs = {
        'happy': {
            'keep_percussive': True,
            'replace_bass': True,
            'add_instruments': ['piano', 'strings'],
            'tempo_factor': 1.1,
            'pitch_shift': 2,
            'brightness': 1.5
        },
        'sad': {
            'keep_percussive': False,
            'replace_bass': True,
            'add_instruments': ['strings', 'ambient'],
            'tempo_factor': 0.8,
            'pitch_shift': -2,
            'brightness': 0.6
        },
        'energetic': {
            'keep_percussive': True,
            'replace_bass': True,
            'add_instruments': ['bass', 'pad'],
            'tempo_factor': 1.3,
            'pitch_shift': 1,
            'brightness': 1.8
        },
        'calm': {
            'keep_percussive': False,
            'replace_bass': False,
            'add_instruments': ['ambient', 'pad'],
            'tempo_factor': 0.9,
            'pitch_shift': 0,
            'brightness': 0.8
        },
        'dark': {
            'keep_percussive': True,
            'replace_bass': True,
            'add_instruments': ['bass', 'ambient'],
            'tempo_factor': 0.95,
            'pitch_shift': -3,
            'brightness': 0.4
        },
        'uplifting': {
            'keep_percussive': True,
            'replace_bass': False,
            'add_instruments': ['piano', 'pad'],
            'tempo_factor': 1.15,
            'pitch_shift': 3,
            'brightness': 1.6
        }
    }
    
    config = mood_configs.get(mood, mood_configs['happy'])
    
    # Start with base mix - reduce overall level to prevent clipping
    remix = np.zeros_like(separated_sources['full_mix'])
    current_level = 0.0  # Track cumulative audio level
    
    # Add percussive elements if keeping them
    if config['keep_percussive']:
        percussion = separated_sources['percussive'] * 0.5  # Reduced level
        remix += percussion
        current_level += 0.5
    
    # Add or replace harmonic content
    harmonic_base = separated_sources['harmonic'] * 0.4  # Reduced level
    
    # Apply pitch shifting to harmonic content
    if config['pitch_shift'] != 0:
        harmonic_base = librosa.effects.pitch_shift(harmonic_base, sr=sr, n_steps=config['pitch_shift'])
    
    remix += harmonic_base
    current_level += 0.4
    
    # Add synthetic instruments based on mood
    instrument_level = 0.3 / len(config['add_instruments']) if config['add_instruments'] else 0
    for instrument in config['add_instruments']:
        if instrument in synth_instruments:
            synth_part = synth_instruments[instrument]
            # Ensure exact same length as original
            synth_part = librosa.util.fix_length(synth_part, size=len(remix))
            remix += synth_part * instrument_level
            current_level += instrument_level
    
    # Apply brightness/EQ adjustments
    if config['brightness'] != 1.0:
        stft = librosa.stft(remix)
        freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
        
        # Adjust high frequencies based on brightness
        for i, freq in enumerate(freqs):
            if freq > 2000 and i < stft.shape[0]:  # High frequencies with bounds check
                stft[i, :] *= config['brightness']
        
        remix = librosa.istft(stft)
    
    # Apply tempo changes BEFORE final normalization
    if config['tempo_factor'] != 1.0:
        remix = librosa.effects.time_stretch(remix, rate=config['tempo_factor'])
        # Fix length after tempo change to match original duration
        target_length = len(separated_sources['full_mix'])
        remix = librosa.util.fix_length(remix, size=target_length)
    
    # Normalize the final mix with gentle compression
    remix = librosa.util.normalize(remix) * 0.8  # Leave headroom
    
    return remix
    
    return remix

def analyze_audio(audio, sr):
    """Analyze audio characteristics for the editor"""
    analysis = {}
    
    # Basic audio properties
    analysis['duration'] = len(audio) / sr
    analysis['channels'] = 1  # librosa loads as mono by default
    
    # Tempo and rhythm
    try:
        tempo, beats = librosa.beat.beat_track(y=audio, sr=sr)
        analysis['tempo'] = float(tempo)
        analysis['beats_count'] = len(beats)
    except:
        analysis['tempo'] = 120.0
        analysis['beats_count'] = 0
    
    # Key detection (simplified)
    try:
        chromagram = librosa.feature.chroma_stft(y=audio, sr=sr)
        key_strength = np.sum(chromagram, axis=1)
        estimated_key = np.argmax(key_strength)
        keys = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        analysis['estimated_key'] = keys[estimated_key]
    except:
        analysis['estimated_key'] = 'C'
    
    # Spectral features
    try:
        spectral_centroids = librosa.feature.spectral_centroid(y=audio, sr=sr)[0]
        analysis['brightness'] = float(np.mean(spectral_centroids))
        
        spectral_rolloff = librosa.feature.spectral_rolloff(y=audio, sr=sr)[0]
        analysis['spectral_rolloff'] = float(np.mean(spectral_rolloff))
        
        zero_crossings = librosa.feature.zero_crossing_rate(y=audio)[0]
        analysis['zero_crossing_rate'] = float(np.mean(zero_crossings))
    except:
        analysis['brightness'] = 1000.0
        analysis['spectral_rolloff'] = 2000.0
        analysis['zero_crossing_rate'] = 0.1
    
    # Dynamic range
    analysis['dynamic_range'] = float(np.max(audio) - np.min(audio))
    analysis['rms_energy'] = float(np.sqrt(np.mean(audio**2)))
    
    return analysis

def generate_mood_remixes(audio_data, sr, original_filename):
    """Generate mood-based remixes with instrument separation and replacement"""
    variations = []
    base_name = os.path.splitext(original_filename)[0]
    
    print(f"Separating audio sources for {original_filename}...")
    separated_sources = separate_audio_sources(audio_data, sr)
    
    # Define mood configurations
    mood_configs = [
        {'mood': 'happy', 'display': 'Happy & Bright', 'desc': 'Uplifting with bright instruments and major tonality'},
        {'mood': 'sad', 'display': 'Melancholic', 'desc': 'Emotional depth with strings and ambient textures'},
        {'mood': 'energetic', 'display': 'High Energy', 'desc': 'Driving rhythm with enhanced bass and tempo'},
        {'mood': 'calm', 'display': 'Peaceful & Serene', 'desc': 'Ambient soundscape with gentle pads'},
        {'mood': 'dark', 'display': 'Dark & Mysterious', 'desc': 'Deep bass and atmospheric elements'},
        {'mood': 'uplifting', 'display': 'Inspiring', 'desc': 'Soaring melodies with motivational energy'},
    ]
    
    for config in mood_configs:
        try:
            print(f"Creating {config['display']} remix...")
            
            # Create mood-specific remix
            mood_remix = create_mood_remix(separated_sources, sr, config['mood'])
            
            # Generate unique filename
            remix_filename = f"{base_name}_{config['mood']}_mood_{str(uuid.uuid4())[:8]}.wav"
            remix_path = os.path.join(app.config['OUTPUT_FOLDER'], remix_filename)
            
            # Save the remix
            sf.write(remix_path, mood_remix, sr)
            
            variations.append({
                'name': config['display'],
                'filename': remix_filename,
                'path': remix_path,
                'description': config['desc']
            })
            
        except Exception as e:
            print(f"Error creating {config['mood']} remix: {e}")
            continue
    
    return variations

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'audio_file' not in request.files:
        return jsonify({'error': 'No file selected'}), 400
    
    file = request.files['audio_file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        try:
            # Save uploaded file
            filename = secure_filename(file.filename)
            upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(upload_path)
            
            print(f"Processing file: {filename}")
            
            # Load audio file with librosa
            try:
                audio_data, sr = librosa.load(upload_path, sr=None)
                print(f"Loaded audio: {len(audio_data)} samples at {sr}Hz")
            except Exception as e:
                os.remove(upload_path)  # Cleanup on error
                return jsonify({'error': f'Could not load audio file: {str(e)}'}), 500
            
            # Limit audio length for processing (max 60 seconds)
            max_duration = 60  # seconds  
            original_duration = len(audio_data) / sr
            if len(audio_data) > sr * max_duration:
                audio_data = audio_data[:int(sr * max_duration)]
                print(f"Truncated to {max_duration} seconds")
            
            # Separate audio into components
            try:
                separated_sources = separate_audio_sources(audio_data, sr)
                print(f"Separated audio into {len(separated_sources)} components")
            except Exception as e:
                os.remove(upload_path)  # Cleanup on error
                return jsonify({'error': f'Error separating audio: {str(e)}'}), 500
            
            # Save separated tracks for editor
            base_name = os.path.splitext(filename)[0]
            track_files = {}
            
            for track_name, track_data in separated_sources.items():
                track_filename = f"{base_name}_{track_name}_{str(uuid.uuid4())[:8]}.wav"
                track_path = os.path.join(app.config['OUTPUT_FOLDER'], track_filename)
                
                # Normalize and save each track
                normalized_track = librosa.util.normalize(track_data) * 0.8
                sf.write(track_path, normalized_track, sr)
                
                track_files[track_name] = {
                    'filename': track_filename,
                    'duration': len(track_data) / sr,
                    'level': float(np.max(np.abs(track_data)))
                }
            
            # Generate audio analysis
            try:
                analysis = analyze_audio(audio_data, sr)
            except Exception as e:
                analysis = {'error': str(e)}
            
            # Clean up uploaded file
            try:
                os.remove(upload_path)
            except:
                pass
            
            return jsonify({
                'success': True,
                'original_file': filename,
                'duration': original_duration,
                'sample_rate': int(sr),
                'tracks': track_files,
                'analysis': analysis
            })
            
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return jsonify({'error': f'Error processing file: {str(e)}'}), 500
    else:
        return jsonify({'error': 'Invalid file type. Please upload MP3, WAV, FLAC, M4A, or OGG files.'}), 400

@app.route('/mix', methods=['POST'])
def mix_tracks():
    """Create a custom mix based on user's editor settings"""
    try:
        data = request.json
        track_settings = data.get('tracks', {})
        effects = data.get('effects', {})
        
        # Load the separated tracks
        mixed_audio = None
        sr = None
        
        for track_name, settings in track_settings.items():
            if not settings.get('enabled', True):
                continue
                
            filename = settings.get('filename')
            if not filename:
                continue
                
            track_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
            if not os.path.exists(track_path):
                continue
                
            # Load track
            track_audio, track_sr = librosa.load(track_path, sr=None)
            if sr is None:
                sr = track_sr
            
            # Apply track-specific settings
            volume = settings.get('volume', 1.0)
            pan = settings.get('pan', 0.0)  # -1 to 1
            
            # Apply volume
            track_audio *= volume
            
            # Simple panning simulation (for mono output)
            if pan != 0:
                track_audio *= (1 - abs(pan))
            
            # Add to mix
            if mixed_audio is None:
                mixed_audio = track_audio
            else:
                # Ensure same length
                min_length = min(len(mixed_audio), len(track_audio))
                mixed_audio = mixed_audio[:min_length] + track_audio[:min_length]
        
        if mixed_audio is None:
            return jsonify({'error': 'No tracks selected for mixing'}), 400
        
        # Apply global effects
        if effects.get('reverb', 0) > 0:
            # Simple reverb simulation
            reverb_amount = effects['reverb']
            delay_samples = int(0.05 * sr)  # 50ms delay
            delayed = np.concatenate([np.zeros(delay_samples), mixed_audio[:-delay_samples]])
            mixed_audio = (1 - reverb_amount) * mixed_audio + reverb_amount * delayed
        
        if effects.get('compression', 0) > 0:
            # Simple compression
            compression_amount = effects['compression']
            mixed_audio = np.tanh(mixed_audio * (1 + compression_amount)) / (1 + compression_amount)
        
        # Normalize and save
        mixed_audio = librosa.util.normalize(mixed_audio) * 0.9
        
        # Generate filename for final mix
        mix_filename = f"custom_mix_{str(uuid.uuid4())[:8]}.wav"
        mix_path = os.path.join(app.config['OUTPUT_FOLDER'], mix_filename)
        sf.write(mix_path, mixed_audio, sr)
        
        return jsonify({
            'success': True,
            'filename': mix_filename,
            'duration': len(mixed_audio) / sr
        })
        
    except Exception as e:
        return jsonify({'error': f'Error creating mix: {str(e)}'}), 500
def download_file(filename):
    """Serve generated audio files for download"""
    try:
        file_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/play/<filename>')
def play_file(filename):
    """Serve generated audio files for playback"""
    try:
        file_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
        if os.path.exists(file_path):
            return send_file(file_path)
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
