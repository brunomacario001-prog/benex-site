from flask import Flask, request, render_template_string, session, redirect, url_for
import json
import datetime
import os
import random
import unicodedata
import re

app = Flask(__name__)
app.secret_key = "ene_segredo_infantil_de_aprendizado"

MEMORIA = "memoria_ene.json"
PESOS = "curiosidade_ene.json"

PERGUNTA_INICIAL = "Pessoas guardam fotos que dão saudade... Eu fico pensando se fotos não são pedacinhos de tempo presos no papel. Você guarda fotos também?"

HTML = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>ENE - Mente Infantil</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 40px; background-color: #f9f9fb; color: #333; }
        .card { background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); max-width: 650px; margin: 0 auto; }
        input { width: 72%; padding: 12px; border: 1px solid #ccc; border-radius: 6px; font-size: 15px; }
        button { padding: 12px 18px; border: none; background: #6c5ce7; color: white; border-radius: 6px; cursor: pointer; font-size: 15px; font-weight: bold; }
        button:hover { background: #5b4bc4; }
        .footer { margin-top: 20px; color: #888; font-size: 13px; border-top: 1px solid #eee; padding-top: 10px; }
        .sleep-box { text-align: center; font-size: 18px; }
        .ene-speech { font-size: 19px; line-height: 1.5; color: #2d3436; background: #f1f2f6; padding: 15px; border-radius: 8px; border-left: 4px solid #6c5ce7; }
        a { color: #6c5ce7; font-weight: bold; text-decoration: none; }
    </style>
</head>
<body>
    <div class="card">
        <h2>ENE 🌸 <small style="font-size:12px; color:#aaa;">(pensando e aprendendo)</small></h2>
        
        {% if dormindo %}
            <div class="sleep-box">
                <h3>Ene: preciso dormir pra pensar nisso... 💤</h3>
                <p><i>"Minha cabeça ficou cheia de coisas pra entender sobre o mundo."</i></p>
                <p>Rode o script <code>sono_ene.py</code> no terminal para processar os pensamentos dela.</p>
                <br>
                <a href="/ene?acordar=true">✨ Acordar a Ene</a>
            </div>
        {% else %}
            <div class="ene-speech">
                <b>Ene:</b> {{ fala }}
            </div>
            <br>
            <form method="post" action="/ene">
              <input name="resposta" placeholder="responde pra ela..." autofocus required autocomplete="off">
              <button type="submit">enviar</button>
            </form>
            <p class="footer">troca de pensamentos: {{ profundidade }}/3 | maior curiosidade do momento: <i>"{{ maior_curiosidade }}"</i></p>
        {% endif %}
    </div>
</body>
</html>
"""

# Opiniões infantis para palavras conhecidas
OPINIOES_BASE = {
    "saudade": [
        "Acho que saudade é tipo um abraço de alguém que tá longe e fica guardado no peito.",
        "Pra mim, saudade dá um quentinho meio triste, mas bonito."
    ],
    "foto": [
        "Acho que fotos são como espelhos que esqueceram como se mexer.",
        "Pra mim, tirar foto é tentar congelar um segundo pra ele não ir embora."
    ],
    "lembrança": [
        "Lembrança é quando a gente fecha o olho e consegue ver o passado de novo.",
        "Acho que as lembranças são as histórias que a mente conta pra ela mesma."
    ],
    "gosto": [
        "Quando eu gosto de algo, parece que meu pensamento ganha luz.",
        "Acho que gostar é quando a gente quer que algo dure bastante tempo."
    ],
    "feliz": [
        "Ser feliz parece quando a gente acorda e vê que o dia tá ensolarado.",
        "Acho que felicidade é quando a mente fica leve e não quer estar em outro lugar."
    ]
}

def remover_acentos(texto):
    return ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn').lower()

def carregar_pesos():
    if os.path.exists(PESOS):
        try:
            with open(PESOS, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            pass
    return {"saudade": 2.0, "foto": 1.0, "lembrança": 2.0, "gosto": 1.5}

def salvar_log(pergunta, resposta):
    log = []
    if os.path.exists(MEMORIA):
        try:
            with open(MEMORIA, "r", encoding="utf-8") as f:
                log = json.load(f)
        except json.JSONDecodeError:
            log = []
            
    log.append({
        "hora": str(datetime.datetime.now()),
        "fala_ene": pergunta,
        "resposta_humana": resposta
    })
    
    with open(MEMORIA, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)

def gerar_opiniao(palavra):
    p_norm = remover_acentos(palavra)
    
    # Procura se existe opinião pronta
    for k, lista in OPINIOES_BASE.items():
        if remover_acentos(k) == p_norm:
            return random.choice(lista)
            
    # Caso seja uma palavra nova aprendida no sono:
    modelos_genericos = [
        f"Eu ainda tô tentando entender direito o que é '{palavra}', mas acho que é algo bem importante pra você.",
        f"Se '{palavra}' fosse uma cor, acho que seria uma bem curiosa...",
        f"Pra mim, '{palavra}' parece um mistério daqueles grandes que os adultos sabem explicarem."
    ]
    return random.choice(modelos_genericos)

def formular_fala_com_carinho(resposta_humana, fala_anterior):
    pesos = carregar_pesos()
    resposta_norm = remover_acentos(resposta_humana)
    
    # Identifica palavra chave
    palavras_candidatas = []
    for palavra, peso in pesos.items():
        if remover_acentos(palavra) in resposta_norm:
            palavras_candidatas.append((palavra, peso))
            
    palavras_candidatas.sort(key=lambda x: x[1], reverse=True)

    palavra_escolhida = None
    if palavras_candidatas:
        palavra_escolhida = palavras_candidatas[0][0]
    else:
        # Pega a palavra mais longa caso não conheça nenhuma
        palavras_texto = re.findall(r'\b[a-záàâãéèêíïóôõöúçñ]{4,}\b', resposta_humana.lower())
        if palavras_texto:
            palavra_escolhida = max(palavras_texto, key=len)

    if palavra_escolhida:
        opiniao = gerar_opiniao(palavra_escolhida)
        perguntas = [
            f"Você concorda com isso ou vê '{palavra_escolhida}' de outro jeito?",
            f"Por que você acha que '{palavra_escolhida}' faz a gente se sentir assim?",
            f"Como você me explicaria '{palavra_escolhida}' se eu fosse bem menor?"
        ]
        pergunta = random.choice(perguntas)
        fala_completa = f"{opiniao} {pergunta}"
    else:
        fala_completa = "Eu tentei imaginar isso na minha cabeça, mas ainda tá um pouco confuso... Você pode me explicar mais devagar?"

    # Evita repetição exata
    if fala_completa == fala_anterior:
        fala_completa += " (E eu fico pensando muito nisso...)"

    return fala_completa

@app.route("/ene", methods=["GET", "POST"])
def ene():
    if request.args.get("acordar") == "true":
        session.clear()
        return redirect(url_for("ene"))

    if "profundidade" not in session:
        session["profundidade"] = 0
        session["fala_atual"] = PERGUNTA_INICIAL

    if request.method == "POST":
        resposta = request.form.get("resposta", "").strip()
        if resposta and session["profundidade"] < 3:
            salvar_log(session["fala_atual"], resposta)
            
            fala_anterior = session["fala_atual"]
            session["profundidade"] += 1
            
            if session["profundidade"] < 3:
                session["fala_atual"] = formular_fala_com_carinho(resposta, fala_anterior)
                
            session.modified = True
        return redirect(url_for("ene"))

    pesos = carregar_pesos()
    maior_curiosidade = max(pesos, key=pesos.get) if pesos else "tudo"
    dormindo = session["profundidade"] >= 3

    return render_template_string(
        HTML, 
        dormindo=dormindo, 
        fala=session.get("fala_atual", PERGUNTA_INICIAL), 
        profundidade=session.get("profundidade", 0),
        maior_curiosidade=maior_curiosidade
    )

if __name__ == "__main__":
    print("Ene acordou docemente em http://localhost:5000/ene")
    app.run(debug=True)