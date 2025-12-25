# -*- coding: utf-8 -*-
import os, sys, json, glob, time
import logging, base64, requests, asyncio
from typing import Dict, Any
import threading
import tempfile
import speech_recognition as sr
from pydub import AudioSegment
from werkzeug.utils import secure_filename
import voice, datetime
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
# Flask imports
from flask import Flask, request, jsonify, send_from_directory
from twilio.twiml.messaging_response import MessagingResponse
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

sys.path.insert(0, r'C:\Users\hp\Desktop\Whatsapp-bot')
sys.stdout.reconfigure(encoding="utf-8")

try:
    from puterai import main
except ImportError:
    main = None

load_dotenv()

app = Flask(__name__)

# ========== CONFIGURATION ==========
IMAGE_DIR = "puter_images"
audio_files = "audio_files"
os.makedirs(IMAGE_DIR, exist_ok=True)

# ========== SERVICE D'UPLOAD POUR WHATSAPP ==========
class ImageUploader:
    """Upload les images vers un serveur public pour WhatsApp"""
    
    def upload_to_catbox(self, image_path: str) -> str:
        """Upload vers catbox.moe (gratuit, pas besoin d'API key)"""
        try:
            with open(image_path, 'rb') as f:
                files = {'fileToUpload': f}
                response = requests.post(
                    'https://catbox.moe/user/api.php',
                    files=files,
                    data={'reqtype': 'fileupload'},
                    timeout=30
                )
            
            if response.status_code == 200 and response.text.startswith('http'):
                logger.info(f"📤 Upload réussi: {response.text[:50]}...")
                return response.text.strip()
            else:
                logger.error(f"❌ Erreur catbox: {response.text[:100]}")
                return ""
                
        except Exception as e:
            logger.error(f"❌ Erreur upload catbox: {e}")
            return ""
    
    def upload_to_imgbb(self, image_path: str) -> str:
        """Upload vers imgbb.com (nécessite API key)"""
        try:
            api_key = os.getenv("IMGBB_API_KEY")
            if not api_key:
                return ""
            
            with open(image_path, 'rb') as f:
                response = requests.post(
                    f"https://api.imgbb.com/1/upload?key={api_key}",
                    files={'image': f},
                    timeout=30
                )
            
            if response.status_code == 200:
                data = response.json()
                return data['data']['url']
            else:
                logger.error(f"❌ Erreur imgbb: {response.status_code}")
                return ""
                
        except Exception as e:
            logger.error(f"❌ Erreur upload imgbb: {e}")
            return ""

# ========== ENVOI WHATSAPP ==========
def send_whatsapp_image(to_number: str, image_url: str, caption: str = "") -> bool:
    """Envoie une image sur WhatsApp via Twilio"""
    try:
        from twilio.rest import Client
        
        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        whatsapp_number = os.getenv("TWILIO_WHATSAPP_NUMBER")
        
        if not all([account_sid, auth_token, whatsapp_number]):
            logger.error("❌ Configuration Twilio manquante dans .env")
            return False
        
        client = Client(account_sid, auth_token)
        
        logger.info(f"📱 Envoi WhatsApp à {to_number}")
        logger.info(f"📸 URL image: {image_url[:50]}...")
        
        message = client.messages.create(
            from_=f"whatsapp:{whatsapp_number}",
            to=f"whatsapp:{to_number}",
            media_url=[image_url],
            body=caption[:1000] if caption else "🎨 Image générée "
        )
        
        logger.info(f"✅ WhatsApp envoyé! SID: {message.sid}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur envoi WhatsApp: {e}")
        return False

def send_whatsapp_audio(to_number: str, audio_url: str, caption: str = "") -> bool:
    """Envoie un audio sur WhatsApp via Twilio"""
    try:
        from twilio.rest import Client
        
        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        whatsapp_number = os.getenv("TWILIO_WHATSAPP_NUMBER")
        
        if not all([account_sid, auth_token, whatsapp_number]):
            logger.error("❌ Configuration Twilio manquante dans .env")
            return False
        
        client = Client(account_sid, auth_token)
        
        logger.info(f"📱 Envoi WhatsApp à {to_number}")
        logger.info(f"🎵 URL audio: {audio_url[:50]}...")
        
        message = client.messages.create(
            from_=f"whatsapp:{whatsapp_number}",
            to=f"whatsapp:{to_number}",
            media_url=[audio_url],
            body=caption[:1000] if caption else "🎵 Audio généré"
        )
        
        logger.info(f"✅ WhatsApp envoyé! SID: {message.sid}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur envoi WhatsApp: {e}")
        return False

# ========== GÉNÉRATEUR PUTER CORRIGÉ ==========
class PuterGenerator:
    """Génère des images avec Puter.js et les envoie automatiquement"""
    
    def __init__(self):
        self.uploader = ImageUploader()
    
    def generate_image_page(self, prompt: str, sender_number: str = "") -> Dict[str, Any]:
        """Crée une page HTML qui génère et envoie automatiquement"""
        try:
            timestamp = int(time.time())
            safe_prompt = "".join(c for c in prompt[:30] if c.isalnum() or c in (' ', '-', '_')).rstrip()
            
            filename = f"puter_{timestamp}.html"
            filepath = os.path.join(IMAGE_DIR, filename)
            
            html_content = self._create_html_page(prompt, sender_number, timestamp)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"📄 Page créée pour {sender_number}: {prompt[:30]}...")
            
            return {
                "success": True,
                "html_url": f"/puter-page/{filename}",
                "full_url": f"https://unsaluting-elucidative-gene.ngrok-free.dev/puter-page/{filename}",
                "prompt": prompt,
                "sender_number": sender_number
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur création page: {e}")
            return {"success": False, "error": str(e)}
    
    def _create_html_page(self, prompt: str, sender_number: str, timestamp: int) -> str:
        """Crée la page HTML qui fait tout automatiquement"""
        prompt_escaped = json.dumps(prompt)
        
        return f'''<!DOCTYPE html>
<html>
<head>
    <title>Puter.ai - Génération automatique</title>
    <script src="https://js.puter.com/v2/"></script>
    <style>
        body {{
            font-family: Arial, sans-serif;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
            text-align: center;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.1);
            padding: 30px;
            border-radius: 15px;
            backdrop-filter: blur(10px);
        }}
        h1 {{ margin-bottom: 30px; }}
        .status {{
            padding: 20px;
            background: rgba(255, 255, 255, 0.2);
            border-radius: 10px;
            margin: 20px 0;
        }}
        .loader {{
            border: 5px solid #f3f3f3;
            border-top: 5px solid #3498db;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            animation: spin 1s linear infinite;
            margin: 20px auto;
        }}
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        #imageContainer img {{
            max-width: 100%;
            border-radius: 10px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            margin: 20px 0;
        }}
        .success {{
            background: rgba(76, 175, 80, 0.3);
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
        }}
        .whatsapp-status {{
            margin-top: 30px;
            padding: 20px;
            background: rgba(37, 211, 102, 0.3);
            border-radius: 10px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 Puter.ai - Génération automatique</h1>
        
        <div class="status" id="status">
            <h3>🎨 Génération en cours...</h3>
            <p><strong>Prompt:</strong> "{prompt}"</p>
            <div class="loader"></div>
            <p>⏳ Patientez 15-30 secondes...</p>
            <p>L'image sera automatiquement envoyée sur WhatsApp</p>
        </div>
        
        <div id="imageContainer"></div>
        <div id="result"></div>
        <div id="whatsappStatus"></div>
        
        <p style="margin-top: 30px; font-size: 14px; opacity: 0.8;">
            Cette page se fermera automatiquement dans 10 secondes
        </p>
    </div>
    
    <script>
    const prompt = {prompt_escaped};
    const senderNumber = "{sender_number}";
    const timestamp = {timestamp};
    
    async function processImage() {{
        try {{
            // 1. Générer l'image avec Puter.js
            updateStatus("🚀 Lancement de Puter.ai...");
            
            if (!window.puter || !window.puter.ai) {{
                throw new Error("Puter.js non chargé");
            }}
            
            updateStatus("🎨 Création de l'image...");
            
            const imageElement = await puter.ai.txt2img(prompt, {{
                model: "gpt-image-1",
                quality: "low"
            }});
            
            // Récupérer l'URL
            let imageUrl = imageElement.src;
            if (!imageUrl && imageElement.querySelector) {{
                const img = imageElement.querySelector('img');
                if (img) imageUrl = img.src;
            }}
            
            if (!imageUrl) {{
                throw new Error("Impossible de récupérer l'image");
            }}
            
            // Afficher
            document.getElementById('imageContainer').innerHTML = '';
            document.getElementById('imageContainer').appendChild(imageElement);
            
            updateStatus("✅ Image générée!", true);
            
            // 2. Convertir en base64 pour l'envoi
            updateStatus("🔄 Préparation de l'image...");
            
            let imageData = imageUrl;
            if (!imageUrl.startsWith('data:')) {{
                const response = await fetch(imageUrl);
                const blob = await response.blob();
                imageData = await new Promise(resolve => {{
                    const reader = new FileReader();
                    reader.onloadend = () => resolve(reader.result);
                    reader.readAsDataURL(blob);
                }});
            }}
            
            // 3. Envoyer au serveur Flask
            updateStatus("📤 Envoi au serveur...");
            
            const serverResponse = await fetch('/api/process-puter-image', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{
                    image: imageData,
                    prompt: prompt,
                    timestamp: timestamp,
                    sender_number: senderNumber
                }})
            }});
            
            const serverResult = await serverResponse.json();
            
            if (serverResult.success) {{
                updateStatus("💾 Image sauvegardée!", true);
                
                // 4. Envoyer sur WhatsApp
                if (senderNumber && serverResult.public_url) {{
                    updateStatus("📱 Envoi sur WhatsApp...");
                    
                    const whatsappResponse = await fetch('/api/send-whatsapp-direct', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{
                            to_number: senderNumber,
                            image_url: serverResult.public_url,
                            prompt: prompt
                        }})
                    }});
                    
                    const whatsappResult = await whatsappResponse.json();
                    
                    if (whatsappResult.success) {{
                        document.getElementById('whatsappStatus').innerHTML = `
                            <div class="whatsapp-status">
                                <h3>✅ Image envoyée sur WhatsApp!</h3>
                                <p>Vérifiez votre téléphone 📱</p>
                                <p>L'image a été sauvegardée et envoyée avec succès.</p>
                            </div>
                        `;
                    }} else {{
                        document.getElementById('whatsappStatus').innerHTML = `
                            <div style="background: rgba(244, 67, 54, 0.3); padding: 20px; border-radius: 10px;">
                                <h3>⚠️ WhatsApp non envoyé</h3>
                                <p>Mais l'image est sauvegardée: <a href="${{serverResult.public_url}}" target="_blank" style="color: #90caf9;">Télécharger</a></p>
                            </div>
                        `;
                    }}
                }}
                
                // 5. Auto-fermeture
                setTimeout(() => {{
                    window.close();
                }}, 10000);
                
            }} else {{
                throw new Error("Échec serveur: " + (serverResult.error || "inconnu"));
            }}
            
        }} catch (error) {{
            console.error("Erreur:", error);
            updateStatus(`❌ Erreur: ${{error.message}}`, false);
        }}
    }}
    
    function updateStatus(message, success = false) {{
        const statusDiv = document.getElementById('status');
        const color = success ? '#4CAF50' : '#2196F3';
        statusDiv.innerHTML = `
            <h3 style="color: ${{color}};">${{message}}</h3>
            <p><strong>Prompt:</strong> "${{prompt}}"</p>
        `;
    }}
    
    // Démarrer le processus automatiquement
    document.addEventListener('DOMContentLoaded', processImage);
    </script>
</body>
</html>'''

# ========== INITIALISATION ==========
image_gen = PuterGenerator()
uploader = ImageUploader()

# ========== ROUTES API CORRIGÉES ==========
@app.route('/api/process-puter-image', methods=['POST'])
def api_process_puter_image():
    """Traite l'image de Puter: sauvegarde + upload + retourne URL publique"""
    try:
        data = request.json
        
        if not data or 'image' not in data:
            return jsonify({"success": False, "error": "Aucune image reçue"})
        
        image_data = data['image']
        prompt = data.get('prompt', 'puter_image')
        timestamp = data.get('timestamp', int(time.time()))
        sender_number = data.get('sender_number', '')
        
        # Extraire base64
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        # Décoder
        image_bytes = base64.b64decode(image_data)
        
        # Sauvegarder localement
        safe_prompt = "".join(c for c in prompt[:30] if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"puter_{safe_prompt}_{timestamp}.png"
        filepath = os.path.join(IMAGE_DIR, filename)
        
        with open(filepath, 'wb') as f:
            f.write(image_bytes)
        
        logger.info(f"💾 Image sauvegardée localement: {filename}")
        
        # Upload vers serveur public (pour WhatsApp)
        public_url = uploader.upload_to_catbox(filepath)
        
        if not public_url:
            # Fallback: utiliser l'URL locale (ne marchera pas pour WhatsApp)
            public_url = f"http://localhost:5000/image/{filename}"
            #public_url = f"https://unsaluting-elucidative-gene.ngrok-free.dev/image/{filename}"
            logger.warning(f"⚠️ Upload échoué, utilisation URL locale: {public_url}")
            logger.warning("⚠️ WhatsApp nécessite une URL publique! Configurez IMGBB_API_KEY")
        
        # Si un numéro WhatsApp est fourni, envoyer en arrière-plan
        if sender_number and public_url and not public_url.startswith('http://localhost'):
            # Lancer l'envoi WhatsApp en arrière-plan
            threading.Thread(
                target=send_whatsapp_delayed,
                args=(sender_number, public_url, prompt),
                daemon=True
            ).start()
        
        return jsonify({
            "success": True,
            "filename": filename,
            "local_url": f"/image/{filename}",
            "public_url": public_url,
            "prompt": prompt,
            "sender_number": sender_number
        })
        
    except Exception as e:
        logger.error(f"❌ Erreur traitement image: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/send-whatsapp-direct', methods=['POST'])
def api_send_whatsapp_direct():
    """API pour envoyer directement sur WhatsApp"""
    try:
        from twilio.rest import Client
        
        data = request.json
        to_number = data.get('to_number', '')
        image_url = data.get('image_url', '')
        audio_url = data.get('audio_url', '')
        prompt = data.get('prompt', '')
        
        if not to_number:
            return jsonify({"success": False, "error": "Numéro manquant"})
        
        if not image_url or image_url.startswith('http://localhost') or audio_url.startswith('http://localhost') or audio_url:
            return jsonify({"success": False, "error": "URL publique requise pour WhatsApp"})
        
        # Configuration Twilio
        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        whatsapp_number = os.getenv("TWILIO_WHATSAPP_NUMBER")
        
        if not all([account_sid, auth_token, whatsapp_number]):
            return jsonify({"success": False, "error": "Twilio non configuré"})
        
        client = Client(account_sid, auth_token)
        
        # Envoyer le message
        caption = f"🎨 {prompt[:100]}... "
        
        message = client.messages.create(
            from_=f"whatsapp:{whatsapp_number}",
            to=f"whatsapp:{to_number}",
            media_url=[image_url],
            body=caption
        )
        
        logger.info(f"✅ WhatsApp envoyé à {to_number}! SID: {message.sid}")
        
        return jsonify({
            "success": True,
            "message_sid": message.sid,
            "to_number": to_number,
            "image_url": image_url
        })
        
    except Exception as e:
        logger.error(f"❌ Erreur WhatsApp direct: {e}")
        return jsonify({"success": False, "error": str(e)})


def send_whatsapp_delayed(to_number: str, image_url: str, audio_url: str, prompt: str):
    """Envoi WhatsApp avec délai pour laisser le temps à l'upload"""
    import time
    time.sleep(2)  # Attendre 2 secondes pour être sûr
    
    success = send_whatsapp_image(to_number, image_url, f"🎨 {prompt[:100]}...")
    audio_url="https://unsaluting-elucidative-gene.ngrok-free.dev/audio/audio_"+to_number+"_"+timestamp+".mp3"
    success2=send_whatsapp_audio(to_number, audio_url, "🎵 Audio...")
    
    if success and success2:
        logger.info(f"✅ WhatsApp envoyé avec succès à {to_number}")
    else:
        logger.error(f"❌ Échec envoi WhatsApp à {to_number}")

# ========== ROUTES ==========
@app.route('/image/<filename>')
def serve_image(filename):
    """Sert les images locales"""
    try:
        return send_from_directory(IMAGE_DIR, filename)
    except:
        return "Image non trouvée", 404

@app.route('/puter-page/<filename>')
def serve_puter_page(filename):
    """Sert les pages Puter"""
    try:
        return send_from_directory(IMAGE_DIR, filename)
    except:
        return "Page non trouvée", 404
##AUDIO
# auto_sender.py
import os
import glob
from twilio.rest import Client
from datetime import datetime

def send_audio_file(file_path, ngrok_url):
    """Envoie un fichier audio via WhatsApp"""
    
    # Configuration Twilio
     
    # Vérifier Twilio
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    client = Client(account_sid, auth_token)
# Extraire le nom du fichier
    filename = os.path.basename(file_path)
    audio_url = f"{ngrok_url}/audio_files/{filename}"
    
    try:
        # Extraire le numéro du nom de fichier
        # Format: audio_212608595612_20251221_223400.mp3
        parts = filename.split('_')
        phone_number = None
        
        for part in parts:
            # Chercher une séquence de chiffres qui pourrait être un numéro
            if part.isdigit() and len(part) >= 9:  # Au moins 9 chiffres pour un numéro
                phone_number = f"whatsapp:+{part}"
                break
        
        if not phone_number:
            print(f"⚠️ Numéro non trouvé dans {filename}")
            return False
        
        # Délai pour éviter le rate limiting
        time.sleep(4)
        
        # Envoyer
        message = client.messages.create(
            media_url=[audio_url],
            from_='whatsapp:+14155238886',
            to=phone_number
        )
        
        print(f"✅ Envoyé à {phone_number}: {filename}")
        print(f"   SID: {message.sid}")
        print(f"   Status: {message.status}")
        
        return True
        
    except Exception as e:
        if e.status == 429:  # Rate limiting
            print(f"⏳ Rate limit détecté pour {filename}, attente 5 secondes...")
            time.sleep(5)
            # Option: retry une fois
            try:
                time.sleep(5)
                message = client.messages.create(
                    media_url=[audio_url],
                    from_='whatsapp:+14155238886',
                    to=phone_number
                )
                print(f"✅ Envoyé après retry: {filename}")
                return True
            except:
                print(f"❌ Échec après retry: {filename}")
                return False
        else:
            print(f"❌ Erreur Twilio avec {filename}: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur générale avec {filename}: {e}")
        return False
    
@app.route('/audio_files/<filename>')
def serve_audio(filename):
    ngrok_url = "https://unsaluting-elucidative-gene.ngrok-free.dev"
    
    # 1. Servir le fichier (pour les requêtes GET normales)
    file_path = os.path.join('audio_files', filename)
    if os.path.exists(file_path):
        # Envoyer le fichier via WhatsApp
        time.sleep(2)  # Petit délai pour s'assurer que le fichier est prêt
        send_audio_file(file_path, ngrok_url)
        
        # Archiver le fichier après envoi
        #archive_file(filename)
        
        # Retourner le fichier pour téléchargement
        time.sleep(2)  # Petit délai pour s'assurer que le fichier n'est plus utilisé
        return send_from_directory('audio_files', filename)
    
    return 'File not found', 404


# ========== LOGIQUE WHATSAPP ==========
def generate_reply(message: str, sender_number: str = "") -> Dict[str, Any]:
    """Génère la réponse pour WhatsApp"""
    
    msg = message.strip()
    
    if not msg:
        return {"text": "❓ Tapez 'help' pour les commandes."}
    
    if msg.lower().startswith("/image "):
        prompt = msg[7:].strip()
        
        if len(prompt) < 3:
            return {"text": "⚠️ Description trop courte (min 3 caractères)."}
        
        try:
            result = image_gen.generate_image_page(prompt, sender_number)
            
            if result["success"]:
                return {
                    "text": f"🎨Génération lancée!\n\n"
                           f"Prompt: \"{prompt}\"\n\n"
                           #f"📎 Ouvrez ce lien:\n{result['full_url']}\n\n"
                        #    f"⚠️ IMPORTANT:\n"
                        #    f"1. Ouvrez dans Chrome/Firefox\n"
                        #    f"2. Gardez la fenêtre ouverte\n"
                           f"3. L'image sera générée automatiquement\n"
                           f"4. Elle sera envoyée sur WhatsApp\n\n"
                           f"⏳ Temps: 20-40 secondes\n"
                           f"📱 Envoi automatique après génération",
                    "media_url": None
                }
            else:
                return {"text": f"❌ Erreur: {result.get('error', 'Inconnue')}"}
            
        except Exception as e:
            logger.error(f"❌ Erreur: {e}")
            return {"text": f"❌ Erreur: {str(e)[:80]}"}
    
    elif msg.lower() in ["help", "aide", "/help"]:
        return {"text": "🤖 Commandes Puter.ai:\n• /image [texte] - Génère une image\n• help - Aide"}
    
    else:
        if main:
            try:
                reply = asyncio.run(main(msg))
                return {"text": reply}
            except:
                return {"text": "🤖 Je suis votre assistant."}
        return {"text": "🤖 Utilisez /image pour générer."}

@app.route("/whatsapp", methods=["POST"])
def whatsapp_webhook():
    """Webhook WhatsApp"""
    from simple_memory import memory
    incoming_msg = request.values.get("Body", "").strip()
    sender = request.values.get("From", "").replace('whatsapp:', '')
    media_url = request.values.get("MediaUrl0", "")  # URL de l'audio
    
    # Récupérer le contexte
    context = memory.get_context(sender, max_messages=3)
    
    logger.info(f"📩 {sender}: {incoming_msg}")
    
    resp = MessagingResponse()
    msg = resp.message()
    
    # 1. Gérer l'audio SI présent
    if media_url:
        print(f"🎤 Audio reçu: {media_url}")
        
        # Transcrire l'audio
        transcribed_text = transcribe_audio_from_url(media_url, sender)
        
        if transcribed_text:
            print(f"📝 Transcription: {transcribed_text}")
            
            # === CORRECTION ICI : Utiliser enhanced_message pour l'audio aussi ===
            if context:
                enhanced_message = f"[Contexte: {context}] {transcribed_text}"
            else:
                enhanced_message = transcribed_text
            
            # Générer la réponse avec contexte
            reply = generate_reply(enhanced_message, sender)
            msg.body(reply["text"])
            
            # === SAUVEGARDER LA MÉMOIRE pour l'audio ===
            memory.save_message(sender, transcribed_text, reply['text'])
            
        else:
            msg.body("❌ Je n'ai pas pu transcrire votre audio.")
            return str(resp)
        
        return str(resp)
    
    # 2. Si pas d'audio MAIS avec texte
    if incoming_msg:
        # === CORRECTION ICI : Construire enhanced_message ===
        if context:
            enhanced_message = f"[Contexte: {context}] {incoming_msg}"
        else:
            enhanced_message = incoming_msg
        
        # Générer la réponse
        reply = generate_reply(enhanced_message, sender)
        
        # Création de l'audio
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"audio_{sender}_{timestamp}.mp3"
        audio_path = f"audio_files/{filename}"
        
        os.makedirs("audio_files", exist_ok=True)
        
        try:
            import voice
            voice.text_to_voices(reply['text'], audio_path)
            #voice.tts_to_voice(reply['text'], audio_path)
            print(f"✅ Audio généré: {filename}")
            
            # Envoyer le texte d'abord
            msg.body(reply["text"])
            
            # Envoyer l'audio en arrière-plan
            time.sleep(2)
            send_audio_async(sender, filename)
            
        except Exception as e:
            print(f"❌ Erreur génération audio: {e}")
            msg.body(reply["text"])
        
        # === SAUVEGARDER LA MÉMOIRE ===
        memory.save_message(sender, incoming_msg, reply['text'])
        
        return str(resp)
    
    # 3. Si pas d'audio ET pas de texte
    msg.body("Bonjour ! Envoyez-moi un message texte ou audio.")
    return str(resp)
# def whatsapp_webhook():
#     """Webhook WhatsApp"""
#     from simple_memory import memory
#     incoming_msg = request.values.get("Body", "").strip()
#     sender = request.values.get("From", "").replace('whatsapp:', '')
#     media_url = request.values.get("MediaUrl0", "")  # URL de l'audio
#     context = memory.get_context(sender, max_messages=3)
#     # 2. Combiner avec le nouveau message
#     if context:
#         enhanced_message = f"[Contexte: {context}] {incoming_msg}"
#     else:
#         enhanced_message = incoming_msg
#     logger.info(f"📩 {sender}: {incoming_msg}")
#     # 2. Initialiser la réponse
#     resp = MessagingResponse()
#     msg = resp.message()
#     # 3. Gérer l'audio si présent
#     if media_url:
#         print(f"🎤 Audio reçu: {media_url}")
        
#         # Transcrire l'audio
#         transcribed_text = transcribe_audio_from_url(media_url, sender)
        
#         if transcribed_text:
#             print(f"📝 Transcription: {transcribed_text}")
#             # Utiliser la transcription comme message
#             incoming_msg = transcribed_text
#             reply = generate_reply(incoming_msg, sender)
#             msg.body(reply["text"])
            
           
#         else:
#             msg.body("❌ Je n'ai pas pu transcrire votre audio. Pouvez-vous envoyer un message texte ?")
#             return str(resp)
#         return str(resp)
#     # 4. Si pas d'audio et pas de texte
#     if not incoming_msg and not media_url:
#         msg.body("Bonjour ! Envoyez-moi un message texte ou audio.")
#         return str(resp)
#     # 4. Si pas d'audio et pas de texte
#     if not incoming_msg and not media_url:
#         msg.body("Bonjour ! Envoyez-moi un message texte ou audio.")
#         return str(resp)
    
#     # Générer la réponse
#     #reply = generate_reply(incoming_msg, sender)
#     reply=generate_reply(enhanced_message, sender)
#     import datetime

#     # Création de l'audio
#     timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
#     filename = f"audio_{sender}_{timestamp}.mp3"
#     audio_path = f"audio_files/{filename}"
    
#     # Créer le dossier audio_files s'il n'existe pas
#     os.makedirs("audio_files", exist_ok=True)
    
#     # Générer l'audio (assurez-vous que voice.text_to_voice est correct)
#     try:
#         import voice
#         #voice.text_to_voice(reply['text'], audio_path, "pFZP5JQG7iQjIQuC4Bku")
#         voice.text_to_voices(reply['text'], audio_path)
#         print(f"✅ Audio généré: {filename}")
#     except Exception as e:
#         print(f"❌ Erreur génération audio: {e}")
#         resp = MessagingResponse()
#         msg = resp.message()
#         msg.body(reply["text"])
#         return str(resp)
    
#     msg.body(reply["text"])
    
#     # 2. Ensuite envoyer l'audio
#     # Note: Pour envoyer média après texte, on doit le faire via API Twilio
#     # On va utiliser un thread pour ne pas bloquer la réponse
    
#     # Démarrer l'envoi d'audio en arrière-plan
#     time.sleep(2)  # Petit délai pour s'assurer que le texte est envoyé d'abord
#     send_audio_async(sender, filename)
#     # Sauvegarder dans la mémoire
#     memory.save_message(sender, incoming_msg, reply['text'])
    
#     return str(resp)

def transcribe_audio_from_url(audio_url, sender_id):
    """Télécharge et transcrit un audio depuis une URL Twilio"""
    
    # INITIALISER les variables au début pour éviter UnboundLocalError
    temp_path = None
    wav_path = None
    
    try:
        print(f"🔽 Téléchargement audio depuis: {audio_url}")
        
        # 1. Vérifier que l'URL existe
        if not audio_url or audio_url.strip() == "":
            print("❌ URL audio vide")
            return None
        
        # 2. Vérifier que c'est une URL Twilio (nécessite auth)
        if 'api.twilio.com' in audio_url:
            print("🔐 URL Twilio détectée - authentification requise")
            
            # Récupérer les credentials Twilio
            account_sid = os.getenv("TWILIO_ACCOUNT_SID", "AC3cd7ac2d53d618e59e62e1cbb2a64873")
            auth_token = os.getenv("TWILIO_AUTH_TOKEN")
            
            if not auth_token:
                print("❌ TWILIO_AUTH_TOKEN manquant dans .env")
                return None
            
            # Préparer l'authentification
            from requests.auth import HTTPBasicAuth
            auth = HTTPBasicAuth(account_sid, auth_token)
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(audio_url, auth=auth, headers=headers, timeout=30)
            
        else:
            # URL normale (pas Twilio)
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(audio_url, headers=headers, timeout=30)
        
        # 3. Vérifier la réponse
        if response.status_code != 200:
            print(f"❌ Échec téléchargement: {response.status_code}")
            return None
        
        print(f"✅ Téléchargement réussi: {len(response.content)} bytes")
        
        # 4. Déterminer l'extension du fichier
        content_type = response.headers.get('Content-Type', '').lower()
        
        if 'ogg' in content_type or 'opus' in content_type:
            file_ext = '.ogg'
        elif 'aac' in content_type:
            file_ext = '.aac'
        elif 'mp4' in content_type:
            file_ext = '.m4a'
        elif 'mp3' in content_type or 'mpeg' in content_type:
            file_ext = '.mp3'
        else:
            file_ext = '.ogg'  # Par défaut pour WhatsApp
        
        print(f"📁 Type détecté: {content_type} -> extension: {file_ext}")
        
        # 5. Sauvegarder temporairement
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
            tmp_file.write(response.content)
            temp_path = tmp_file.name
        
        print(f"✅ Audio sauvegardé: {temp_path} ({os.path.getsize(temp_path)} bytes)")
        
        # 6. Convertir en WAV
        wav_path = temp_path.replace(file_ext, '.wav')
        
        try:
            # Essayer avec pydub d'abord
            from pydub import AudioSegment
            audio = AudioSegment.from_file(temp_path)
            audio.export(wav_path, format='wav')
            print("✅ Conversion WAV réussie avec pydub")
            
        except ImportError:
            print("⚠️ pydub non disponible, utilisation de ffmpeg")
            # Fallback avec ffmpeg
            import subprocess
            cmd = [
                'ffmpeg', '-i', temp_path,
                '-acodec', 'pcm_s16le',
                '-ar', '16000',
                '-ac', '1',
                '-y', wav_path
            ]
            subprocess.run(cmd, capture_output=True, timeout=15)
            
        except Exception as conv_error:
            print(f"⚠️ Erreur pydub, essai ffmpeg: {conv_error}")
            import subprocess
            cmd = [
                'ffmpeg', '-i', temp_path,
                '-acodec', 'pcm_s16le',
                '-ar', '16000',
                '-ac', '1',
                '-y', wav_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            
            if result.returncode != 0:
                print(f"❌ Erreur ffmpeg: {result.stderr[:200]}")
                return None
        
        # 7. Vérifier que le fichier WAV existe
        if not os.path.exists(wav_path):
            print(f"❌ Fichier WAV non créé: {wav_path}")
            return None
        
        print(f"✅ Fichier WAV créé: {wav_path} ({os.path.getsize(wav_path)} bytes)")
        
        # 8. Transcrire
        recognizer = sr.Recognizer()
        
        with sr.AudioFile(wav_path) as source:
            print("🎤 Début transcription...")
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio_data = recognizer.record(source)
            
            try:
                text = recognizer.recognize_google(audio_data, language='fr-FR')
                print(f"✅ Transcription réussie: {text[:100]}...")
                return text
                
            except sr.UnknownValueError:
                print("❌ Google n'a pas compris l'audio")
                return None
                
            except sr.RequestError as e:
                print(f"❌ Erreur API Google: {e}")
                return None
        
    except requests.exceptions.Timeout:
        print("❌ Timeout lors du téléchargement")
        return None
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur réseau: {e}")
        return None
        
    except Exception as e:
        print(f"❌ Erreur inattendue: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None
        
    finally:
        # Nettoyer les fichiers temporaires SI ils existent
        files_to_clean = []
        if temp_path and os.path.exists(temp_path):
            files_to_clean.append(temp_path)
        if wav_path and os.path.exists(wav_path):
            files_to_clean.append(wav_path)
        
        for file_path in files_to_clean:
            try:
                os.remove(file_path)
                print(f"🧹 Fichier nettoyé: {file_path}")
            except Exception as clean_error:
                print(f"⚠️ Erreur nettoyage {file_path}: {clean_error}")


def send_audio_async(sender, filename):
    """Envoie l'audio en arrière-plan"""
    import threading
    import time
    
    def send_audio_thread():
        # Attendre un peu pour que le texte soit envoyé d'abord
        time.sleep(2)
        
        ngrok_url = "https://unsaluting-elucidative-gene.ngrok-free.dev"
        audio_path = f"audio_files/{filename}"
        
        if os.path.exists(audio_path):
            # Extraire le numéro du sender
            phone_number = f"whatsapp:+{sender}" if not sender.startswith('+') else f"whatsapp:{sender}"
            
            # Envoyer l'audio
            account_sid = os.getenv("TWILIO_ACCOUNT_SID")
            auth_token = os.getenv("TWILIO_AUTH_TOKEN")
            
            if account_sid and auth_token:
                client = Client(account_sid, auth_token)
                audio_url = f"{ngrok_url}/audio_files/{filename}"
                
                try:
                    message = client.messages.create(
                        media_url=[audio_url],
                        from_='whatsapp:+14155238886',
                        to=phone_number
                    )
                    print(f"✅ Audio envoyé à {phone_number}: {message.sid}")
                    
                    # Archiver
                    #archive_file(filename)
                    
                except Exception as e:
                    print(f"❌ Erreur envoi audio: {e}")
            else:
                print("❌ Variables Twilio manquantes")
    
    # Démarrer le thread
    thread = threading.Thread(target=send_audio_thread)
    thread.daemon = True
    thread.start()

#Envoi automatique des audios en attente
def send_pending_audios():
    """Envoie tous les fichiers audio non envoyés"""
    import glob
    time.sleep(5)  # Attendre que le serveur soit prêt
    ngrok_url = "https://unsaluting-elucidative-gene.ngrok-free.dev"
    audio_files = glob.glob("audio_files/audio_*.mp3")
    
    print(f"📁 {len(audio_files)} fichiers audio trouvés")
    
    for audio_file in audio_files:
        # Vérifier si le fichier est déjà dans les archives
        filename = os.path.basename(audio_file)
        archive_path = os.path.join("audio_files", "archives", filename)
        
        if not os.path.exists(archive_path):
            print(f"📤 Envoi de {filename}...")
            success = send_audio_file(audio_file, ngrok_url)
            
            if success:
                #Archiver
                import subprocess
                # Lancer clean_audio.py avec pythonw (sans console visible)
                subprocess.run(["pythonw", "clean_audio.py"])
            else:
                print("⏸️ Échec, passage au suivant...")
            
            # Attendre entre les envois
            #time.sleep(3)
# ========== PAGE D'ACCUEIL ==========
@app.route("/")
def home():
    """Page d'accueil"""
    
    # Images récentes
    images = []
    if os.path.exists(IMAGE_DIR):
        images = [f for f in os.listdir(IMAGE_DIR) if f.endswith('.png')]
        images.sort(key=lambda x: os.path.getmtime(os.path.join(IMAGE_DIR, x)), reverse=True)
        images = images[:5]
    
    images_html = ""
    for img in images:
        images_html += f'''
        <div style="margin: 10px; display: inline-block;">
            <a href="/image/{img}" target="_blank">
                <img src="/image/{img}" style="width: 150px; height: 150px; object-fit: cover; border-radius: 8px;">
            </a>
        </div>
        '''
    
    return f'''<!DOCTYPE html>
<html>
<head>
    <title>🤖 Puter.ai Bot</title>
    <style>
        body {{ font-family: Arial; margin: 40px; }}
        .card {{ background: #f8f9fa; padding: 20px; border-radius: 10px; margin: 20px 0; }}
        button {{ padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; }}
        input {{ padding: 10px; width: 300px; margin-right: 10px; }}
    </style>
</head>
<body>
    <h1>🤖 Puter.ai Bot</h1>
    
    <div class="card">
        <h3>📱 WhatsApp:</h3>
        <p>Envoyez: <code>/image [description]</code></p>
        <p>Exemple: <code>/image un chat sur une table</code></p>
    </div>
    
    <div class="card">
        <h3>🧪 Test Rapide</h3>
        <p>Entrez un numéro WhatsApp pour le test:</p>
        <input type="text" id="testNumber" placeholder="+212612345678" style="margin-bottom: 10px;">
        <br>
        <input type="text" id="prompt" value="un chat sur une table">
        <button onclick="testPuter()">Tester avec WhatsApp</button>
        <div id="result" style="margin-top: 20px;"></div>
    </div>
    
    {f'<div class="card"><h3>📸 Images récentes</h3>{images_html}</div>' if images else ''}
    
    <script>
    function testPuter() {{
        const number = document.getElementById("testNumber").value;
        const prompt = document.getElementById("prompt").value;
        const result = document.getElementById("result");
        
        if (!number) {{
            result.innerHTML = "⚠️ Entrez un numéro WhatsApp";
            return;
        }}
        
        result.innerHTML = "⏳ Création de la page...";
        
        fetch(`/api/test-puter?prompt=${{encodeURIComponent(prompt)}}&number=${{encodeURIComponent(number)}}`)
            .then(r => r.json())
            .then(data => {{
                if (data.success) {{
                    window.open(data.url, '_blank', 'width=800,height=900');
                    result.innerHTML = "✅ Page ouverte! Gardez-la ouverte pour la génération.";
                }} else {{
                    result.innerHTML = "❌ " + data.error;
                }}
            }});
    }}
    </script>
</body>
</html>'''

@app.route('/api/test-puter')
def api_test_puter():
    """API de test"""
    prompt = request.args.get('prompt', 'a cat')
    number = request.args.get('number', '')
    
    try:
        result = image_gen.generate_image_page(prompt, number)
        
        if result["success"]:
            return jsonify({
                "success": True,
                "url": result["full_url"],
                "prompt": prompt
            })
        else:
            return jsonify({
                "success": False,
                "error": result.get("error", "Erreur inconnue")
            })
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })

@app.route('/audio_files/<filename>')
def serve_audio_file(filename):
    """Sert les fichiers audio"""
    return send_from_directory('audio_files', filename)

# ========== DÉMARRAGE ==========
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    
    # Vérifier Twilio
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    
    if not account_sid or not auth_token:
        logger.warning("⚠️ TWILIO_ACCOUNT_SID ou TWILIO_AUTH_TOKEN manquant dans .env")
        logger.warning("⚠️ WhatsApp ne fonctionnera pas sans Twilio configuré")
    
    logger.info(f"🚀 Démarrage sur http://localhost:{port}")
    logger.info(f"📁 Dossier images: {IMAGE_DIR}")
    logger.info("📤 Upload automatique vers catbox.moe activé")
    
    # Désactiver debug=True pour éviter les problèmes de threading sur Windows
    # Utiliser threaded=True pour supporter les requêtes concurrentes
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)