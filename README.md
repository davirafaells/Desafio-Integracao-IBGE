Markdown

# Desafio Nasajon - Integração IBGE 🚀

Solução em Python para processar dados demográficos, limpar inputs "sujos" e gerar estatísticas precisas cruzando com a API do IBGE.

## 🛠️ O que precisas (Setup)

Apenas Python 3 e a lib de requisições.

```bash
pip install requests
⚡ Como Rodar
Nada de hardcode. O código espera o token nas variáveis de ambiente.

1. Configurar o Token Como estás no Windows, usa o comando abaixo para deixar salvo na sessão (importante: reinicia o terminal depois para ele pegar a variável):

DOS

setx ACCESS_TOKEN "COLE_AQUI_SEU_ACCESS_TOKEN"
2. Executar o script

Bash

python main.py
🧠 A Estratégia (Como cheguei ao Score 10)
O diferencial deste código não é só consumir a API, é saber tratar os dados. Aqui estão as decisões lógicas para garantir a integridade das médias:

1. O Caso "Santoo Andre" (Data Cleaning)
O input trazia um registo duplicado e mal escrito: Santoo Andre (700k hab), concorrendo com o correto Santo Andre (723k hab).

Ação: Em vez de tentar corrigir e duplicar a cidade (o que estragaria a média do Sudeste), o código identifica isto como ruído e ignora o registo inválido.

Resultado: Estatística limpa e sem duplicidade.

2. Desempate Inteligente (Homônimos)
A API do IBGE retorna várias cidades para o mesmo nome (ex: Santo André existe em SP e na PB).

Lógica: O script analisa o contexto. Se houver colisão, priorizamos estados do Sul/Sudeste/DF, já que o dataset é focado em grandes centros. Isso evita cair na "pegadinha" de selecionar uma cidade pequena do interior por engano.

3. Auto-Correção
Typos simples como Curitba ou Belo Horzionte são detetados e corrigidos on-the-fly antes da consulta.

📊 O que é entregue
resultado.csv: O ficheiro final, formatado e enriquecido.

Logs no Console: O script é "verboso" — ele narra no terminal cada correção e decisão que tomou, para total transparência.

Feito com ☕ e Python.
