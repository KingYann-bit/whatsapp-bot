# 🤖 WhatsApp Bot

Un bot WhatsApp automatisé développé en Python utilisant plusieurs technologies pour fournir des fonctionnalités avancées comme la synthèse vocale (TTS) et d'autres capacités interactives.

![GitHub](https://img.shields.io/github/license/KingYann-bit/Whatsapp-bot)
![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![GitHub last commit](https://img.shields.io/github/last-commit/KingYann-bit/Whatsapp-bot)

## ✨ Fonctionnalités

- 🤖 **Automation complète** - Interactions automatisées sur WhatsApp
- 🔊 **Synthèse vocale (TTS)** - Intégration avec un système TTS avancé
- 💬 **Gestion des conversations** - Réponses intelligentes et contextuelles
- 📁 **Gestion des médias** - Support pour images, vidéos et documents
- 🔧 **Configuration facile** - Paramétrage simple via fichiers de configuration

## 📋 Prérequis

- Python 3.8 ou supérieur
- Compte WhatsApp
- Accès à une API TTS (selon configuration)

## 🚀 Installation

### 1. Cloner le dépôt
```bash
git clone https://github.com/ton-username/Whatsapp-bot.git
cd Whatsapp-bot
```

### 2. Initialiser les sous-modules (si TTS est un sous-module)
```bash
git submodule update --init --recursive
```

### 3. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 4. Configurer les variables d'environnement
Crée un fichier `.env` à la racine du projet :
```env
# Exemple de configuration
WHATSAPP_API_KEY=votre_clé_api
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
TWILIO_WHATSAPP_NUMBER=...   # Twilio Sandbox WhatsApp number
HF_API_KEY=hf_...
openai_api_key=sk-proj-...
ELEVENLABS_API_KEY=sk_...
TTS_API_KEY=votre_clé_tts
LOG_LEVEL=INFO
```

### 5. Configurer le bot
Éditez le fichier `config/config.yaml` selon vos besoins.

## 🛠 Utilisation

### Lancer le bot
```bash
python main.py
```

### Ou avec des options spécifiques
```bash
python main.py --debug --config config/custom_config.yaml
```

## 📁 Structure du projet
```
Whatsapp-bot/
├── TTS/                    # Module de synthèse vocale
│   ├── __init__.py
│   ├── tts_engine.py
│   └── voices/
├── src/
│   ├── bot/               # Logique principale du bot
│   ├── handlers/          # Gestionnaires de messages
│   ├── utils/             # Utilitaires
│   └── config.py          # Configuration
├── config/
│   ├── config.yaml        # Configuration principale
│   └── responses.yaml     # Réponses pré-définies
├── requirements.txt       # Dépendances Python
├── main.py               Point d'entrée
└── README.md             Ce fichier
```

## ⚙️ Configuration

### Fichier de configuration principal (`config/config.yaml`)
```yaml
bot:
  name: "WhatsAppBot"
  auto_reply: true
  delay_response: 2

tts:
  enabled: true
  language: "fr-fr"
  speed: 1.0

logging:
  level: "INFO"
  file: "logs/bot.log"
```

## 🔧 Développement

### Ajouter une nouvelle fonctionnalité
1. Créez un nouveau handler dans `src/handlers/`
2. Enregistrez-le dans `src/bot/__init__.py`
3. Ajoutez la configuration nécessaire dans `config/config.yaml`

### Tests
```bash
python -m pytest tests/
```

## 🤝 Contribution

Les contributions sont les bienvenues ! Veuillez suivre ces étapes :

1. Fork le projet
2. Créez une branche (`git checkout -b feature/AmazingFeature`)
3. Committez vos changements (`git commit -m 'Add some AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrez une Pull Request

## 📝 Licence

Distribué sous licence MIT. Voir `LICENSE` pour plus d'informations.

## ⚠️ Avertissement

Ce projet est à des fins éducatives et de développement. Assurez-vous de :
- Respecter les conditions d'utilisation de WhatsApp
- Ne pas spammer ou harceler les utilisateurs
- Respecter les lois locales sur la vie privée

## 📞 Support

Pour toute question ou problème :
- [Ouvrir une Issue](https://github.com/ton-username/Whatsapp-bot/issues)
- Consultez la [documentation](docs/) (si disponible)

---

**Note** : Remplace `ton-username` par ton vrai nom d'utilisateur GitHub dans tous les liens. Tu peux aussi ajouter des badges, des captures d'écran ou des démonstrations vidéo pour améliorer ton README.



