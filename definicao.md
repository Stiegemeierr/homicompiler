# Projeto: Compilador da Linguagem Homi para Home Assistant

## 1. Visão Geral
Este projeto é um compilador desenvolvido em **Python 3** utilizando a biblioteca **PLY (Python Lex-Yacc)**. O compilador traduz scripts escritos na linguagem procedural `Homi` (focada em usuários leigos) para arquivos declarativos `.yaml` compatíveis com o sistema de automação Home Assistant.

## 2. Arquitetura e Fases do Compilador

### A. Analisador Léxico (Scanner)
* **Ferramenta:** PLY (`ply.lex`)
* **Tokens principais:** * Palavras-chave: `AUTOMACAO`, `GATILHO`, `CONDICAO`, `ACAO`, `QUANDO`, `SE`, `LIGAR`, `DESLIGAR`, `ESPERAR`, `FIM`, `ESTA`.
  * Identificadores: `ENTIDADE` (ex: `sensor.porta_sala`, `light.luz_teto`).
  * Valores: `STRING` (ex: `"off"`, `"disarmed"`), `TEMPO` (ex: `10s`, `5min`), `EVENTO` (ex: `sunset`, `sunrise`).
* **Tratamento:** Ignorar espaços em branco e quebras de linha, mas rastrear o número da linha (via `\n`) para reporte preciso de erros sintáticos/semânticos.

### B. Analisador Sintático (Parser)
* **Ferramenta:** PLY (`ply.yacc`) operando como Tabela Preditiva LR.
* **Recuperação de Erros (Modo Pânico):** O compilador não deve parar no primeiro erro. O parser deve utilizar regras de erro (ex: `error`) para ignorar tokens problemáticos até encontrar um ponto de sincronização seguro, como o token `FIM` de um bloco de automação ou um identificador de nova instrução.
* **Gramática Livre de Contexto (GLC) Base:**
  ```bnf
  <programa> ::= <automacao> | <programa> <automacao>
  <automacao> ::= "AUTOMACAO" STRING <bloco_gatilho> <bloco_condicao> <bloco_acao> "FIM"
  
  <bloco_gatilho> ::= "GATILHO:" <lista_gatilhos>
  <lista_gatilhos> ::= <comando_gatilho> | <lista_gatilhos> <comando_gatilho>
  <comando_gatilho> ::= "QUANDO" EVENTO TEMPO | "QUANDO" ENTIDADE "ESTA" STRING
  
  <bloco_condicao> ::= "CONDICAO:" <lista_condicoes> | vazio
  <lista_condicoes> ::= <comando_condicao> | <lista_condicoes> <comando_condicao>
  <comando_condicao> ::= "SE" ENTIDADE "ESTA" STRING
  
  <bloco_acao> ::= "ACAO:" <lista_acoes>
  <lista_acoes> ::= <comando_acao> | <lista_acoes> <comando_acao>
  <comando_acao> ::= "LIGAR" ENTIDADE | "DESLIGAR" ENTIDADE | "ESPERAR" TEMPO

### C. Analisador Semântico

* **Tabela de Símbolos:** O compilador deverá manter um dicionário rastreando as entidades encontradas (ex: guardando que `light.sala` pertence ao domínio `light`).
* **Checagem de Tipos:** Garantir consistência nas ações. Exemplo: lançar erro se o usuário tentar `LIGAR sensor.temperatura` (sensores são de leitura, não aceitam ações de estado), ou associar um estado numérico a um interruptor booleano.

### D. Geração de Código Intermediário/Alvo (YAML)

* A AST (Abstract Syntax Tree) gerada pelo parser será percorrida por um `Visitor`.
* O Visitor construirá estruturas de dicionários e listas nativas do Python.
* A exportação final utilizará a biblioteca `yaml` (PyYAML) para garantir que o arquivo de saída possua a indentação correta e obedeça ao schema oficial do Home Assistant (listas contendo `id`, `alias`, `triggers`, `conditions` e `actions`).

## 3. Exemplo de Entrada e Comportamento Esperado

**Entrada (Linguagem Homi):**

AUTOMACAO "Por do sol na Sala"

GATILHO:
    QUANDO sunset -01:30:00

CONDICAO:
    SE alarm_control_panel.alarmo ESTA "disarmed"
    SE light.sala ESTA "off"

ACAO:
    LIGAR light.sala
    ESPERAR 5min
    DESLIGAR light.sala
FIM

**Saída Esperada (YAML):** O sistema deve mapear as palavras-chave para a estrutura de `platform`, `entity_id` e `services` correspondentes no Home Assistant.
