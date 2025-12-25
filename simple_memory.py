# simple_memory.py
import json
import os
from datetime import datetime

class SimpleMemory:
    """Mémoire hyper simple - juste un fichier JSON"""
    
    def __init__(self, file_path="chat_memory.json"):
        self.file_path = file_path
        self.memory = self._load_memory()
    
    def _load_memory(self):
        """Charge la mémoire depuis le fichier"""
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_memory(self):
        """Sauvegarde la mémoire dans le fichier"""
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(self.memory, f, ensure_ascii=False, indent=2)
    
    def get_context(self, user_id, max_messages=3):
        """Récupère les derniers messages d'un utilisateur"""
        if user_id not in self.memory:
            return ""
        
        # Récupérer les derniers messages
        messages = self.memory[user_id].get('messages', [])
        last_messages = messages[-max_messages:]  # 3 derniers
        
        # Format simple
        context_lines = []
        for msg in last_messages:
            context_lines.append(f"Utilisateur: {msg.get('user', '')}")
            context_lines.append(f"Assistant: {msg.get('bot', '')}")
        
        return "\n".join(context_lines)
    
    def save_message(self, user_id, user_message, bot_response):
        """Sauvegarde un échange"""
        if user_id not in self.memory:
            self.memory[user_id] = {
                'created': datetime.now().isoformat(),
                'messages': []
            }
        
        # Ajouter le nouvel échange
        self.memory[user_id]['messages'].append({
            'user': user_message,
            'bot': bot_response,
            'time': datetime.now().isoformat()
        })
        
        # Garder seulement les 10 derniers messages (pour éviter que le fichier grossisse)
        if len(self.memory[user_id]['messages']) > 10:
            self.memory[user_id]['messages'] = self.memory[user_id]['messages'][-10:]
        
        # Mettre à jour la date
        self.memory[user_id]['updated'] = datetime.now().isoformat()
        
        # Sauvegarder
        self._save_memory()
        
        print(f"💾 Mémoire sauvegardée pour {user_id}")

# Instance globale - UNE SEULE LIGNE à ajouter
memory = SimpleMemory()