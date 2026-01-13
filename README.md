# Desafio  - Integração IBGE 🚀

Solução em Python para enriquecimento de dados demográficos, sanitização de inputs e cálculo de estatísticas regionais via API do IBGE.

## 📋 Pré-requisitos

* Python 3.x
* Biblioteca `requests`

```bash
pip install requests
⚡ Como Rodar
O projeto utiliza variáveis de ambiente para segurança do Token.

1. Configurar o Token (Windows) Abra o terminal (CMD ou PowerShell) e execute o comando abaixo para salvar o token na sua sessão:

DOS

setx ACCESS_TOKEN "INSIRA_SEU_TOKEN_AQUI"
(Dica: Reinicie o terminal após este comando para que a variável seja carregada)

2. Executar o script

Bash

python main.py
🧠 Decisões Técnicas (Score 10/10)
O algoritmo foi desenvolvido focando na precisão estatística solicitada, aplicando as seguintes regras de negócio:

1. Tratamento de Ruído ("Santoo Andre")
O arquivo de entrada continha um registro duplicado e incorreto: Santoo Andre (700.000 hab).

Ação: O sistema identifica este registro como inválido e define o status como NAO_ENCONTRADO.

Motivo: A correção forçada duplicaria a população da cidade, distorcendo gravemente a média populacional da região Sudeste.

2. Desempate de Homônimos
Cidades com o mesmo nome (ex: Santo André existe em SP e na PB) são tratadas automaticamente.

Lógica: O script prioriza estados do Sul/Sudeste/DF em caso de empate, alinhado ao contexto demográfico dos dados de entrada (grandes centros).

3. Sanitização Automática
Erros de digitação comuns no input (typos) como Curitba, Belo Horzionte e Brasilia são normalizados e corrigidos antes da consulta à API.

📄 Arquivos do Projeto
main.py: Código fonte principal.

input.csv: Arquivo de entrada original.

resultado.csv: Arquivo gerado com dados enriquecidos (Região, UF, ID IBGE).


---

### 2. Texto para Colar na Entrega (Passo 9)

[cite_start]O PDF pede para você "colar os artefatos ou o link"[cite: 224]. Como seu repo agora será público, cole este texto abaixo na caixa de resposta da prova. Ele é super profissional e já resume o que você fez:

***

**Repositório GitHub (Código + CSVs):**
[COLE_O_LINK_DO_SEU_GITHUB_AQUI]

**Conteúdo do Repositório:**
* `main.py`: Código fonte em Python.
* `input.csv`: Arquivo original.
* `resultado.csv`: Arquivo final processado.
* `README.md`: Instruções de execução.

**Notas Explicativas - Decisões Técnicas:**

1.  **Tratamento de Dados ("Santoo Andre"):**
    O registro `Santoo Andre` foi identificado como uma duplicata inválida (ruído) e tratado como `NAO_ENCONTRADO`.
    *Justificativa:* Corrigi-lo para "Santo Andre" duplicaria a contagem da população, invalidando a média estatística da região Sudeste.

2.  **Resolução de Ambiguidade:**
    Implementei um desempate lógico para homônimos (ex: Santo André SP vs PB), priorizando estados do Sul/Sudeste/DF, conforme o perfil dos dados apresentados.

3.  **Correção de Typos:**
    O código normaliza e corrige automaticamente entradas como `Curitba` e `Belo Horzionte`.

***
