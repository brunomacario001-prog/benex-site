import json
import os
import re

MEMORIA = "memoria_ene.json"
PESOS = "curiosidade_ene.json"

# Palavras funcionais simples que a ENE não precisa focar como conceito profundo
STOPWORDS = {
    "que", "uma", "uns", "uma", "para", "com", "por", "como", "mais", "menos", 
    "tudo", "nada", "esta", "este", "esses", "essa", "aqui", "ali", "meu", "minha",
    "voce", "você", "tambem", "também", "pelo", "pela"
}

pesos_iniciais = {
    "mas": 1.0,
    "porém": 1.0,
    "não": 1.0,
    "saudade": 2.0,
    "foto": 1.0,
    "lembrança": 2.0,
    "gosto": 1.5,
    "feliz": 1.5,
    "formular": 0.5
}

if not os.path.exists(PESOS):
    pesos = pesos_iniciais
else:
    try:
        with open(PESOS, "r", encoding="utf-8") as f:
            pesos = json.load(f)
    except json.JSONDecodeError:
        pesos = pesos_iniciais

if not os.path.exists(MEMORIA):
    print("💤 Ene dormiu sem nenhuma lembrança nova hoje.")
    exit()

try:
    with open(MEMORIA, "r", encoding="utf-8") as f:
        logs = json.load(f)
except json.JSONDecodeError:
    print("⚠️ As lembranças da Ene estavam confusas (arquivo vazio ou inválido).")
    exit()

print(f"🌙 Ene fechou os olhos para sonhar com {len(logs)} momentos...")

for item in logs:
    pergunta = item.get("pergunta_ene", "").lower()
    resposta = item.get("resposta_humana", "").lower()

    # 1. DESCOBERTA INFANTIL DE NOVAS PALAVRAS
    # Ela extrai palavras com mais de 3 letras que o humano usou
    palavras_novas = re.findall(r'\b[a-záàâãéèêíïóôõöúçñ]{4,}\b', resposta)
    for p in palavras_novas:
        if p not in pesos and p not in STOPWORDS:
            pesos[p] = 0.5  # começa como uma sementinha de curiosidade
            print(f" ✨ Ene ouviu uma palavra nova e guardou: '{p}'")

    # 2. APRENDIZADO COM CORREÇÃO OU PACIÊNCIA
    if any(g in resposta for g in ["calma", "formule melhor", "nao entendi", "não entendi"]):
        pesos["formular"] = pesos.get("formular", 0.5) + 1.0
        print(" 👨‍🏫 Ene percebeu que precisa aprender a perguntar de um jeito melhor")
        for palavra in list(pesos.keys()):
            if palavra in pergunta:
                pesos[palavra] += 0.2

    # 3. REFORÇO POSITIVO (Conversa rica)
    elif len(resposta) > 30:
        for palavra in list(pesos.keys()):
            if palavra in pergunta or palavra in resposta:
                pesos[palavra] += 0.3
                print(f" 💖 '{palavra}' deixou o coração da Ene curioso")

    # 4. EXPLORAÇÃO ATIVA (Dúvida ou Complexidade)
    if any(g in resposta for g in ["foda pra explicar", "nao sei", "não sei", "difícil"]):
        for palavra in list(pesos.keys()):
            if palavra in resposta:
                pesos[palavra] += 0.8
                print(f" ❓ Ene ficou pensativa sobre '{palavra}'")

# Ajuste suave: limita o crescimento excessivo para que ela não fique obcecada por uma única palavra
for k in pesos:
    if pesos[k] < 0.1:
        pesos[k] = 0.1
    elif pesos[k] > 10.0:  # teto suave para manter equilíbrio mental
        pesos[k] = 10.0

with open(PESOS, "w", encoding="utf-8") as f:
    json.dump(pesos, f, ensure_ascii=False, indent=2)

print("\n☀️ Ene terminou de sonhar. Sua mente agora tem estes pesos de curiosidade:")
print(json.dumps(pesos, ensure_ascii=False, indent=2))