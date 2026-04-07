import os
import csv
import json
import requests
import unicodedata

# --- Configurações Gerais ---
URL_IBGE = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios"
# URL alterada para uma variável de ambiente ou endpoint genérico
URL_DESTINO = os.getenv("API_ENDPOINT_DESTINO", "https://api.exemplo.com/v1/submit")

# Lista de prioridade para resolver cidades com mesmo nome (homônimos).
UFS_PRIORIDADE = ['SP', 'RJ', 'MG', 'ES', 'PR', 'SC', 'RS', 'DF']

# Correções pontuais para erros de digitação comuns no dataset.
CORRECOES = {
    "belo horzionte": "belo horizonte",
    "curitba": "curitiba",
    "sao goncalo": "sao goncalo",
    "brasilia": "brasilia"
}

def normalizar(texto):
    """Remove acentos e espaços para comparação uniforme."""
    if not texto: return ""
    return "".join([c for c in unicodedata.normalize('NFKD', texto) if not unicodedata.combining(c)]).lower().strip()

def get_token():
    """Recupera o token de autenticação de forma segura."""
    token = os.getenv("AUTH_TOKEN")
    if not token:
        print("Erro: Variável AUTH_TOKEN não definida nas variáveis de ambiente.")
        exit(1)
    return token

# --- Fluxo de Processamento ---
print("\n>>> Iniciando Processamento de Dados Geográficos")

# 1. Carregar base de referência (IBGE)
print("[1/4] Sincronizando base de dados governamental...")
try:
    resp = requests.get(URL_IBGE)
    lista_ibge = resp.json()
    
    # Indexação para busca rápida
    mapa_cidades = {}
    for item in lista_ibge:
        nome_norm = normalizar(item['nome'])
        if nome_norm not in mapa_cidades:
            mapa_cidades[nome_norm] = []
        mapa_cidades[nome_norm].append(item)
        
    print(f"      Base carregada: {len(lista_ibge)} registros mapeados.")

except Exception as e:
    print(f"Erro ao acessar base de referência: {e}")
    exit(1)

# 2. Processar arquivo local
print("[2/4] Lendo arquivo de entrada (input.csv)...")

stats = {
    "total_municipios": 0, "total_ok": 0, "total_nao_encontrado": 0,
    "total_erro_api": 0, "pop_total_ok": 0, "medias_por_regiao": {}
}
dados_saida = []
acumulador_regiao = {} 

try:
    with open('input.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        reader.fieldnames = [col.strip() for col in reader.fieldnames]
        
        for row in reader:
            stats["total_municipios"] += 1
            nome_orig = row['municipio'].strip()
            pop = int(row['populacao'].strip())
            
            nome_busca = normalizar(nome_orig)
            if nome_busca in CORRECOES:
                nome_busca = CORRECOES[nome_busca]
            
            match = None
            candidatos = mapa_cidades.get(nome_busca)

            if candidatos:
                if len(candidatos) == 1:
                    match = candidatos[0]
                else:
                    # Lógica de desempate por região prioritária
                    match_prioritario = next((c for c in candidatos if c['microrregiao']['mesorregiao']['UF']['sigla'] in UFS_PRIORIDADE), None)
                    match = match_prioritario if match_prioritario else candidatos[0]
            
            item_out = {
                "municipio_input": nome_orig, "populacao_input": pop,
                "status": "NAO_ENCONTRADO", "municipio_ref": None, 
                "uf": None, "regiao": None, "id_externo": None
            }
            
            if match:
                stats["total_ok"] += 1
                stats["pop_total_ok"] += pop
                
                item_out["status"] = "OK"
                item_out["municipio_ref"] = match['nome']
                item_out["id_externo"] = match['id']
                item_out["uf"] = match['microrregiao']['mesorregiao']['UF']['sigla']
                
                regiao = match['microrregiao']['mesorregiao']['UF']['regiao']['nome']
                item_out["regiao"] = regiao
                
                if regiao not in acumulador_regiao: acumulador_regiao[regiao] = []
                acumulador_regiao[regiao].append(pop)
            else:
                stats["total_nao_encontrado"] += 1
            
            dados_saida.append(item_out)

except FileNotFoundError:
    print("Erro: Arquivo 'input.csv' não encontrado.")
    exit(1)

# 3. Consolidação de Estatísticas
print("[3/4] Consolidando métricas por região...")

for regiao, lista_pops in acumulador_regiao.items():
    if lista_pops:
        media = sum(lista_pops) / len(lista_pops)
        stats["medias_por_regiao"][regiao] = round(media, 2)

# Resumo para auditoria
print("\n" + "="*40)
print("RELATÓRIO DE PROCESSAMENTO:")
print(f"Total de registros: {stats['total_municipios']}")
print(f"Sucesso:           {stats['total_ok']}")
print(f"Falhas/Ignorados:  {stats['total_nao_encontrado']}")
print("Médias de População:")
for reg, val in stats["medias_por_regiao"].items():
    print(f"  > {reg}: {val:,.2f}")
print("="*40 + "\n")

# Salva arquivo de auditoria local
with open('resultado_processamento.csv', 'w', encoding='utf-8', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=dados_saida[0].keys())
    writer.writeheader()
    writer.writerows(dados_saida)

# 4. Exportação dos Resultados
print("[4/4] Enviando dados para o servidor de destino...")
token = get_token()

try:
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    # Envia os dados consolidados para a API configurada
    response = requests.post(URL_DESTINO, headers=headers, json={"data_summary": stats})
    
    if response.status_code in [200, 201]:
        print("Sincronização concluída com sucesso!")
        print(f"Resposta do Servidor: {response.text}")
    else:
        print(f"Aviso: O servidor retornou status {response.status_code}")

except Exception as e:
    print(f"Erro na comunicação com o servidor: {e}")
