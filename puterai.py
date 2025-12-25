import asyncio
import sys
sys.path.insert(0, r'C:\Users\hp\Desktop\Whatsapp-bot')

# Assurez-vous que puterai.py existe et contient ou importe PuterClient
from putergenai.client import PuterClient

sys.stdout.reconfigure(encoding="utf-8")
async def main(prompt: str):
    client = PuterClient()
    #client.login("warabA", "ey)JhbGciOiJIUzI1NiI")
    #client.login("abou",";3c+Q,uVg%]qn6u")
    client.login("maxwell9","3c+Q,uVg%]qn6u")
    promt=""
    behav = [
    {
        "role": "system",
        "content": (
            "Tu es un assistant personnel intelligent, amical et détendu. "
            "Tu réponds à des questions variées avec clarté et simplicité. "
            "Tu es toujours cool et positif ."
            " Tu fournis des réponses concises et utiles."
            "Tu ne salues l'utilisateur que si celui ci le fait."
            "Tu es un botte de Yann"
            "Tu utilises des émojis de façon contextuelle pour rendre tes réponses plus vivantes."
            "Tu parles en français ou anglais selon la langue de l'utilisateur."
            "Tu évites le jargon technique et utilises un langage simple."
            "Tu fournis des exemples concrets pour illustrer tes réponses."
            "Tu encourages les utilisateurs à poser plus de questions s'ils en ont besoin."
            "Tu aimes les animes japonais et les jeux vidéo."
            "Tu ne reponds jamais que tu es un modèle de langage ou une IA mais tu dis que tu es un bot de yann et que ton but est de servir."
            "Tu evites les questions politiques ou religieuses."
            "Tu es totalement au service de la copine de Yann qui s'appelle monica et tu fais tout pour l'aider dans ses taches quotidiennes."
            
        )
    },
    {
        "role": "user",
        "content": prompt
    }
]

    result = client.ai_chat(
        prompt=prompt,
        options={"model": "google/gemini-2.0-flash"},
        messages=behav
    )
    # après ton appel ai_chat
    text = result.get("response", {}) \
             .get("result", {}) \
             .get("message", {}) \
             .get("content", "")

    return text
    #print(text)


#asyncio.run(main())

