#Nettoyage des fichiers audio plus anciens que 7
import os
import time
import shutil

AUDIO_DIR = "audio_files"
ARCHIVE_DIR = os.path.join(AUDIO_DIR, "archives")
MAX_AUDIO = 6
AUDIO_EXTENSIONS = (".wav", ".mp3", ".ogg", ".flac", ".m4a")

def archive_all_audios():
    # Créer le dossier d'archive de manière sécurisée
    try:
        if not os.path.exists(ARCHIVE_DIR):
            os.makedirs(ARCHIVE_DIR, exist_ok=True)
        elif not os.path.isdir(ARCHIVE_DIR):
            # Si c'est un fichier au lieu d'un dossier, le renommer
            backup_name = ARCHIVE_DIR + "_backup_" + str(int(time.time()))
            os.rename(ARCHIVE_DIR, backup_name)
            os.makedirs(ARCHIVE_DIR)
            print(f"⚠️ Renommé {ARCHIVE_DIR} en {backup_name}")
    except Exception as e:
        print(f"❌ Erreur création dossier archive: {e}")
        return

    files = [
        f for f in os.listdir(AUDIO_DIR)
        if f.lower().endswith(AUDIO_EXTENSIONS)
        and os.path.isfile(os.path.join(AUDIO_DIR, f))
    ]

    if len(files) <= MAX_AUDIO:
        print(f"✅ {len(files)} fichiers audio (limite: {MAX_AUDIO}) - pas d'archivage nécessaire")
        return

    print(f"📦 {len(files)} fichiers audio détectés → archivage en cours...")

    for filename in files:
        src = os.path.join(AUDIO_DIR, filename)
        dst = os.path.join(ARCHIVE_DIR, filename)

        try:
            shutil.move(src, dst)
            print(f"✅ Archivé : {filename}")
        except Exception as e:
            print(f"❌ Erreur avec {filename} : {e}")

if __name__ == "__main__":
    print("🧹 Démarrage du nettoyage automatique des fichiers audio...")
    print(f"📁 Dossier surveillé: {AUDIO_DIR}")
    print(f"📦 Limite: {MAX_AUDIO} fichiers")
    print(f"🗂️ Archive: {ARCHIVE_DIR}")
    print("-" * 50)

    while True:
        archive_all_audios()
        time.sleep(60)  # Vérifier chaque minute
        
