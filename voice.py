#voice.py
import os
import requests
import sys
from gtts import gTTS
import pyttsx3
from pydub import AudioSegment
import numpy as np
import librosa, scipy
import soundfile as sf
sys.path.insert(0, r'C:\Users\hp\AppData\Local\Programs\Python\Python39\Lib\site-packages\elevenlabs')

sys.stdout.reconfigure(encoding="utf-8")
from elevenlabs import ElevenLabs, play
#api_key=os.getenv("ELEVENLABS_API_KEY")

# ElevenLabs Text-to-Voice
def view_voices():
        client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
        voices = client.voices.get_all()
        for v in voices.voices:
            print(v.voice_id, "-", v.name)
def text_to_voice(prompt, filename,voice_id):
    client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
    if voice_id:
        voice_id=voice_id
    else:
        voice_id="pNInz6obpgDQGcFmaJgB" #voice_id="pFZP5JQG7iQjIQuC4Bku"

    audio_stream = client.text_to_speech.convert(
        voice_id=voice_id,
        text=prompt,
        model_id="eleven_multilingual_v2",
        #speed=0.90,
        output_format="mp3_44100_128"
    )
    #view_voices()
    with open(filename, "wb") as f:
        for chunk in audio_stream:
            if chunk:
                f.write(chunk)
##en utilisant google text to speech ou le pc
def text_to_voices(text, output_path, voice_id=None):
    """
    Convert text to speech using free methods
    voice_id parameter kept for compatibility but not used
    """
    import re
    emoji_pattern = re.compile(
        
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map
        "\U0001F700-\U0001F77F"
        "*"
        "\U0001F780-\U0001F7FF"
        "\U0001F800-\U0001F8FF"
        "\U0001F900-\U0001F9FF"
        "\U0001FA00-\U0001FAFF"
        "\U00002702-\U000027B0"
        "]+",
        flags=re.UNICODE
    )

    def remove_emojis(text):
        return emoji_pattern.sub('', text)
    clean_text = remove_emojis(text).strip()
    if not clean_text:
        raise ValueError("Texte vide après suppression des emojis")

    print(f"🔊 Génération audio pour: {text[:50]}...")
    
    # Essayer gTTS d'abord (meilleure qualité)
    try:
        if len(text.strip()) < 5:
            raise ValueError("Le texte est trop court pour la conversion.")
        tts = gTTS(text=clean_text, lang='fr', slow=False)
        tts.save(output_path)
        print(f"✅ Audio généré avec gTTS: {output_path}")
        return True
    except Exception as e:
        print(f"⚠️ gTTS échoué, essai pyttsx3: {e}")
    
    # Fallback à pyttsx3
    try:
        engine = pyttsx3.init()
        
        # Configurer pour français si possible
        voices = engine.getProperty('voices')
        for voice in voices:
            langs="".join([str(lang).lower() for lang in voice.languages])
            if 'french' in voice.name.lower() or 'fr' in langs:
                engine.setProperty('rate', 200)  # Vitesse de la parole
                engine.setProperty('voice', voice.id)
                break

        engine.save_to_file(text=clean_text, output_path=output_path)
        engine.runAndWait()
        print(f"✅ Audio généré avec pyttsx3: {output_path}")
        return True
        
    except Exception as e:
        print(f"❌ Tous les TTS ont échoué: {e}")
        return False
def list_voices():
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    print("Voix disponibles:")
    for voice in voices:
        print(f"{voice.id} - {voice.name}")
## Utilisation de TTS avec post-traitement audio
def tts_to_voice(text, output_path):
    #youtube-dl https://youtube.com/shorts/jYosBW-zy5Q?si=tm0203WSWvw1Tk02 ffmpeg -i video.mp4 -ss 00:00:10 -t 10 -ar 22050 femme.wav
    #tts --model_name tts_models/fr/mai/tacotron2-DDC --text "Bonjour ! Je suis une voix féminine générée en français." --out_path francais_femme_ddc3.mp3
    from TTS.api import TTS
    import re
    emoji_pattern = re.compile(
        
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map
        "\U0001F700-\U0001F77F"
        "*"
        "\U0001F780-\U0001F7FF"
        "\U0001F800-\U0001F8FF"
        "\U0001F900-\U0001F9FF"
        "\U0001FA00-\U0001FAFF"
        "\U00002702-\U000027B0"
        "]+",
        flags=re.UNICODE
    )

    def remove_emojis(text):
        return emoji_pattern.sub('', text)
    clean_text = remove_emojis(text).strip()
    if not clean_text:
        raise ValueError("Texte vide après suppression des emojis")

    print(f"🔊 Génération audio pour: {text[:50]}...")

    tts = TTS("tts_models/multilingual/multi-dataset/your_tts")#tts_models/multilingual/multi-dataset/xtts_v2
    tts.tts_to_file(
        text=clean_text,
        speaker_wav="femme2.wav",
        language="fr-fr",
        file_path=output_path
    )
    

    # === Charger le fichier TTS ===
    audio_path = output_path
    y, sr = librosa.load(audio_path, sr=22050)  # charge en mono

    # === EQ simple: boost des médiums pour plus de clarté ===
    def eq_boost(y, sr):
        # filtre passe-bande 300-3000 Hz
        import scipy.signal
        sos = scipy.signal.butter(4, [300, 3000], btype='band', fs=sr, output='sos')
        y_eq = scipy.signal.sosfilt(sos, y)
        return y_eq

    y_eq = eq_boost(y, sr)

    # === Reverb légère ===
    def add_reverb(y, sr, reverb_factor=0.2):
        # convolution simple avec un petit IR simulé
        ir = np.zeros(int(0.03*sr))  # 30ms reverb
        ir[0] = 0.6
        ir[int(0.01*sr)] = reverb_factor
        y_rev = np.convolve(y, ir)[:len(y)]
        return y_rev

    y_rev = add_reverb(y_eq, sr)

    # === Réduction de bruit basique ===
    # simple filtrage passe-bas 8kHz pour réduire sifflements
    sos = scipy.signal.butter(4, 8000, btype='low', fs=sr, output='sos')
    y_clean = scipy.signal.sosfilt(sos, y_rev)

    # === Sauvegarder le résultat ===
    sf.write(f"{output_path}_post", y_clean, sr)
    #print("✅ Post-traitement terminé, fichier sauvegardé !")


# if __name__ == "__main__":
#     #text_to_voices("Bonjour, ceci est un test de conversion texte en parole.;😊", "test_audio.mp3")
#     text="Cette histoire classique raconte les aventures d'un bonhomme de pain d'épices créé par un couple âgé qui souhaitait avoir un enfant. Leur création prend vie et s'enfuit dès sa sortie du four, échappant successivement à une série de poursuivants : la vieille femme et le vieil homme, des déchiqueteuses, des tondeuses à gazon, une vache et un cochon, tous incapables de l'attraper. Son récit, répétant à chaque rencontre qu'il a échappé à ceux d'avant, souligne son habileté et sa ruse. Cependant, sa confiance le mène à sa perte lorsqu'il rencontre un renard rusé qui parvient à l'attraper en prétendant le défier également. À la fin, le bonhomme de pain d'épices est dévoré par le renard, illustrant la morale selon laquelle la vanité et la surestimation de ses propres capacités peuvent mener à sa chute. Cette histoire transmet des leçons importantes sur la prudence et la modestie."
#     tts_to_voice(text, "tts_audio.mp3")
