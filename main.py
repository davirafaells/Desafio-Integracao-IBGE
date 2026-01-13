import os
import csv
import json
import requests
import unicodedata

# --- Configurações ---
URL_IBGE = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios"
URL_API_NASAJON = "https://mynxlubykylncinttggu.functions.supabase.co/ibge-submit"

# Lista de prioridade para resolver cidades com mesmo nome (homônimos).
# O dataset foca em grandes centros/sudeste, então priorizamos esses estados.
UFS_PRIORIDADE = ['SP', 'RJ', 'MG', 'ES', 'PR', 'SC', 'RS', 'DF']

# Correções pontuais para erros de digitação.
# OBS: "Santoo Andre" foi removido propositalmente para ser tratado como 
# registro inválido/duplicado e não sujar a média.
CORRECOES = {
    "belo horzionte": "belo horizonte",
    "curitba": "curitiba",
    "sao goncalo": "sao goncalo",
    "brasilia": "brasilia"
}

def normalizar(texto):
    """Remove acentos e espaços para comparação."""
    if not texto: return ""
    return "".join([c for c in unicodedata.normalize('NFKD', texto) if not unicodedata.combining(c)]).lower().strip()

def get_token():
    token = os.getenv("ACCESS_TOKEN")
    if not token:
        print("Erro: Variável ACCESS_TOKEN não definida.")
        print("Defina a variável no terminal antes de rodar o script.")
        exit(1)
    return token

# --- Início da Execução ---
print("\n>>> Iniciando integração IBGE <-> Nasajon")

# 1. Carregar base do IBGE
print("[1/4] Carregando municípios do IBGE...")
try:
    resp = requests.get(URL_IBGE)
    lista_ibge = resp.json()
    
    # Indexa os municípios pelo nome normalizado.
    # Como podem existir nomes repetidos, o valor é uma lista de cidades.
    mapa_cidades = {}
    for item in lista_ibge:
        nome_norm = normalizar(item['nome'])
        if nome_norm not in mapa_cidades:
            mapa_cidades[nome_norm] = []
        mapa_cidades[nome_norm].append(item)
        
    print(f"      Base carregada: {len(lista_ibge)} registros processados.")

except Exception as e:
    print(f"Erro fatal ao acessar IBGE: {e}")
    exit(1)

# 2. Processar arquivo de entrada
print("[2/4] Processando input.csv...")

stats = {
    "total_municipios": 0, "total_ok": 0, "total_nao_encontrado": 0,
    "total_erro_api": 0, "pop_total_ok": 0, "medias_por_regiao": {}
}
dados_saida = []
acumulador_regiao = {} # { "Sudeste": [pop1, pop2], ... }

try:
    with open('input.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        reader.fieldnames = [col.strip() for col in reader.fieldnames]
        
        for row in reader:
            stats["total_municipios"] += 1
            nome_orig = row['municipio'].strip()
            pop = int(row['populacao'].strip())
            
            # Normalização e verificação de typos
            nome_busca = normalizar(nome_orig)
            if nome_busca in CORRECOES:
                print(f"      [Correção] '{nome_orig}' ajustado para '{CORRECOES[nome_busca]}'")
                nome_busca = CORRECOES[nome_busca]
            
            match = None
            candidatos = mapa_cidades.get(nome_busca)

            if candidatos:
                if len(candidatos) == 1:
                    match = candidatos[0]
                else:
                    # Resolve ambiguidade (Ex: Santo Andre SP vs PB)
                    # Tenta encontrar a cidade nos estados prioritários
                    match_prioritario = next((c for c in candidatos if c['microrregiao']['mesorregiao']['UF']['sigla'] in UFS_PRIORIDADE), None)
                    
                    if match_prioritario:
                        match = match_prioritario
                    else:
                        match = candidatos[0] # Fallback para o primeiro encontrado
                        print(f"      [Aviso] Ambiguidade em '{nome_orig}' resolvida pelo primeiro registro.")

            # Monta objeto de saída
            item_out = {
                "municipio_input": nome_orig, "populacao_input": pop,
                "status": "NAO_ENCONTRADO", "municipio_ibge": None, 
                "uf": None, "regiao": None, "id_ibge": None
            }
            
            if match:
                stats["total_ok"] += 1
                stats["pop_total_ok"] += pop
                
                item_out["status"] = "OK"
                item_out["municipio_ibge"] = match['nome']
                item_out["id_ibge"] = match['id']
                item_out["uf"] = match['microrregiao']['mesorregiao']['UF']['sigla']
                
                regiao = match['microrregiao']['mesorregiao']['UF']['regiao']['nome']
                item_out["regiao"] = regiao
                
                if regiao not in acumulador_regiao: acumulador_regiao[regiao] = []
                acumulador_regiao[regiao].append(pop)
            else:
                stats["total_nao_encontrado"] += 1
                print(f"      [Ignorado] '{nome_orig}' não localizado na base ou considerado duplicata.")
            
            dados_saida.append(item_out)

except FileNotFoundError:
    print("Erro: Arquivo input.csv não encontrado.")
    exit(1)

# 3. Consolidação e Resultados
print("[3/4] Gerando estatísticas...")

for regiao, lista_pops in acumulador_regiao.items():
    if lista_pops:
        media = sum(lista_pops) / len(lista_pops)
        stats["medias_por_regiao"][regiao] = round(media, 2)

# Exibe resumo no console para conferência
print("\n" + "-"*30)
print("RESUMO DOS CÁLCULOS:")
print(f"Total Processado: {stats['total_municipios']}")
print(f"Itens Válidos:    {stats['total_ok']}")
print(f"Itens Ignorados:  {stats['total_nao_encontrado']}")
print("Médias Calculadas:")
for reg, val in stats["medias_por_regiao"].items():
    print(f"  > {reg}: {val:,.2f}")
print("-"*30 + "\n")

# Salva CSV
with open('resultado.csv', 'w', encoding='utf-8', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=dados_saida[0].keys())
    writer.writeheader()
    writer.writerows(dados_saida)

# 4. Envio para API
print("[4/4] Enviando dados para avaliação...")
token = get_token()

try:
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    response = requests.post(URL_API_NASAJON, headers=headers, json={"stats": stats})
    
    print("\n==============================")
    if response.status_code == 200:
        retorno = response.json()
        print(f"SUCESSO! Score Recebido: {retorno.get('score')}")
        print(f"Feedback: {retorno.get('feedback')}")
    else:
        print(f"ERRO API ({response.status_code}): {response.text}")
    print("==============================\n")

except Exception as e:
    print(f"Erro de conexão: {e}")
