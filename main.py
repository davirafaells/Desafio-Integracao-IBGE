import csv
import requests
import unicodedata
from collections import defaultdict


def normalizar(texto):
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return texto.lower().strip()


print("Buscando municípios no IBGE...")

url = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios"
resposta = requests.get(url)

if resposta.status_code != 200:
    print("Erro ao acessar a API do IBGE")
    exit(1)

municipios_ibge = resposta.json()
print(f"Total retornado pelo IBGE: {len(municipios_ibge)}")


indice_ibge = {}

for m in municipios_ibge:
    uf_info = m["regiao-imediata"]["regiao-intermediaria"]["UF"]
    chave = normalizar(m["nome"])

    indice_ibge[chave] = {
        "municipio_ibge": m["nome"],
        "uf": uf_info["sigla"],
        "regiao": uf_info["regiao"]["nome"],
        "id_ibge": m["id"],
    }


resultados = []

with open("input.csv", encoding="utf-8") as arquivo:
    leitor = csv.DictReader(arquivo)

    for linha in leitor:
        municipio = linha["municipio"]
        populacao = int(linha["populacao"])
        chave = normalizar(municipio)

        if chave in indice_ibge:
            info = indice_ibge[chave]
            resultados.append({
                "municipio_input": municipio,
                "populacao_input": populacao,
                "municipio_ibge": info["municipio_ibge"],
                "uf": info["uf"],
                "regiao": info["regiao"],
                "id_ibge": info["id_ibge"],
                "status": "OK"
            })
        else:
            resultados.append({
                "municipio_input": municipio,
                "populacao_input": populacao,
                "municipio_ibge": "",
                "uf": "",
                "regiao": "",
                "id_ibge": "",
                "status": "NAO_ENCONTRADO"
            })


with open("resultado.csv", "w", newline="", encoding="utf-8") as arquivo:
    campos = [
        "municipio_input",
        "populacao_input",
        "municipio_ibge",
        "uf",
        "regiao",
        "id_ibge",
        "status"
    ]

    writer = csv.DictWriter(arquivo, fieldnames=campos)
    writer.writeheader()
    writer.writerows(resultados)


total_municipios = len(resultados)
total_ok = sum(1 for r in resultados if r["status"] == "OK")
total_nao_encontrado = sum(1 for r in resultados if r["status"] == "NAO_ENCONTRADO")
total_erro_api = 0

pop_total_ok = sum(r["populacao_input"] for r in resultados if r["status"] == "OK")

pop_por_regiao = defaultdict(list)
for r in resultados:
    if r["status"] == "OK":
        pop_por_regiao[r["regiao"]].append(r["populacao_input"])

medias_por_regiao = {
    regiao: sum(pops) / len(pops)
    for regiao, pops in pop_por_regiao.items()
}


print("_______ ESTATÍSTICAS _______")
print(f"Total de municípios processados: {total_municipios}")
print(f"Total OK: {total_ok}")
print(f"Total não encontrados: {total_nao_encontrado}")
print(f"Total erro API: {total_erro_api}\n")

print(f"População total (status OK): {pop_total_ok:,}".replace(",", "."))

print("\nMédia de população por região:")
for regiao, media in medias_por_regiao.items():
    print(f"- {regiao}: {media:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

print("________________________________")
print("Processamento finalizado.")
