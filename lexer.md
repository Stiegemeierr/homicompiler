# 📖 Guia de Estudos: `lexer.py`

## 1. Resumo do Papel no Pipeline do Compilador

O **Analisador Léxico** (`lexer.py`) é a **primeira fase** do seu compilador. 

Imagine que o compilador recebe o código-fonte como uma tripa única e gigante de caracteres brutos (`'A'`, `'U'`, `'T'`, `'O'`, `'\n'`, etc.). A responsabilidade exata deste arquivo é:
1. **Agrupamento (Tokenização):** Varrer esses caracteres da esquerda para a direita e agrupá-los em unidades lógicas mínimas com significado semântico, chamadas **Tokens** (ex: palavras-chave como `GATILHO`, identificadores de entidades como `light.sala`, ou strings como `"off"`).
2. **Filtragem de Ruído:** Descartar elementos que não importam para a lógica do compilador, como espaços em branco, tabulações e comentários (`# ...`).
3. **Rastreamento de Metadados:** Contar as quebras de linha para que, caso ocorra um erro mais adiante, o compilador saiba apontar exatamente em qual linha o problema aconteceu.

> **Analogia para a Apresentação:** O Lexer funciona como um leitor que separa uma frase em palavras individuais e classifica cada uma (substantivo, verbo, pontuação), jogando fora os espaços extras, antes de entregar as palavras estruturadas para o Analisador Sintático (Parser) validar a gramática da frase.

---

## 2. Desmembramento Técnico

O seu arquivo utiliza a biblioteca **PLY (Python Lex-Yacc)**, especificamente o módulo `ply.lex`. Vamos detalhar os principais componentes estruturais dele:

### A. O Dicionário de Palavras Reservadas (`reserved`) (Linhas 13-25)
```python
reserved = {
    'AUTOMACAO':  'AUTOMACAO',
    'GATILHO':    'GATILHO',
    'CONDICAO':   'CONDICAO',
    'ACAO':       'ACAO',
    'QUANDO':     'QUANDO',
    'SE':         'SE',
    'LIGAR':      'LIGAR',
    'DESLIGAR':   'DESLIGAR',
    'ESPERAR':    'ESPERAR',
    'ESTA':       'ESTA',
    'FIM':        'FIM',
}
```
* **O que faz:** Mapeia strings exatas de palavras-chave da linguagem (em maiúsculas) para seus respectivos tipos de tokens.
* **Por que existe:** Evita a necessidade de criar uma regra de expressão regular individual para cada palavra-chave. Em vez disso, quando o lexer lê uma palavra qualquer, ele primeiro checa se ela está nesse dicionário. Se estiver, ela é classificada com o token da palavra-chave; caso contrário, é tratada de forma genérica.

### B. A Tupla de Tokens (`tokens`) (Linhas 31-38)
* **O que faz:** Define a lista mestre contendo os nomes de todos os tokens válidos que o analisador sintático poderá receber. 
* *Nota de implementação:* Ela junta os tokens dinâmicos (que mudam de valor, como `ENTIDADE` e `STRING`) com os tokens das palavras reservadas através de `tuple(reserved.values())`.

### C. As Regras de Tokenização (`t_XXXX`)
No PLY, qualquer função ou variável que comece com o prefixo `t_` é interpretada como uma regra léxica baseada em Expressões Regulares (Regex).

* **`t_STRING(t)`** (Linha 47)
  * **Regex:** `r'"[^"]*"'`
  * **O que faz:** Captura qualquer texto delimitado por aspas duplas. O valor mantém as aspas para que a fase de geração de código YAML as preserve.
* **`t_TEMPO(t)`** (Linha 54)
  * **Regex:** `r'-?\d{1,2}:\d{2}:\d{2}|\d+min|\d+s'`
  * **O que faz:** Reconhece três formatos de tempo diferentes:
    1. Desvios horários negativos/positivos (ex: `-01:30:00` para "uma hora e trinta minutos antes do pôr do sol").
    2. Minutos (ex: `5min`).
    3. Segundos (ex: `10s`).
* **`t_ENTIDADE(t)`** (Linha 63)
  * **Regex:** `r'[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*'`
  * **O que faz:** Reconhece identificadores no formato clássico do *Home Assistant*: `dominio.nome_da_entidade` (ex: `light.sala`). Exige que comecem com letra minúscula e tenham um ponto separador.
* **`t_EVENTO(t)`** (Linha 75)
  * **Regex:** `r'sunset|sunrise'`
  * **O que faz:** Reconhece eventos de gatilho geográfico específicos.
* **`t_DOISPONTOS(t)`** (Linha 81)
  * **Regex:** `r':'`
  * **O que faz:** Captura o caractere `:` delimitador de seções.
* **`t_PALAVRA(t)`** (Linha 87)
  * **Regex:** `r'[A-Za-z_][A-Za-z0-9_]*'`
  * **O que faz:** Essa é a regra "pega-tudo" para cadeias de caracteres alfanuméricas. Ela lê a palavra inteira e executa a linha `t.type = reserved.get(t.value, 'EVENTO')`. Ou seja: se a palavra for uma palavra-chave como `AUTOMACAO`, altera o tipo do token para `AUTOMACAO`. Se não for reservada, ela assume que é um `EVENTO` dinâmico genérico.

### D. Regras Especiais e Utilitários
* **`t_ignore = ' \t'`** (Linha 104): Diz ao PLY para ignorar silenciosamente espaços e tabulações.
* **`t_COMENTARIO(t)`** (Linha 107): Regex `r'\#.*'`. Usa a instrução `pass` (não retorna `t`). Isso faz com que o comentário seja consumido e descartado da saída do lexer.
* **`t_newline(t)`** (Linha 113): Toda vez que encontra um caractere `\n`, soma o total de quebras encontradas ao contador de linhas do lexer (`t.lexer.lineno`).
* **`t_error(t)`** (Linha 123): Função de tratamento de erros. Se o lexer encontrar um caractere ilegal (como `@`, `!`, `$` ou letras soltas fora do padrão), ele exibe uma mensagem amigável contendo a linha/posição e pula esse caractere usando `t.lexer.skip(1)` para tentar continuar a análise.

---

## 3. Fluxo de Dados

```mermaid
graph LR
    A[Código-Fonte Homi (String)] --> B(lexer.py / ply.lex)
    B --> C[Sequência de Objetos LexToken]
```

### 📥 O que entra:
Uma **única string** contendo todo o código-fonte do script Homi. Exemplo:
```text
SE light.sala ESTA "off"
```

### 📤 O que sai (Formato Exato):
O analisador cospe uma sequência de objetos do tipo `LexToken` da biblioteca PLY. Cada objeto possui os atributos:
* `type`: O tipo de token (identificado na tupla `tokens`).
* `value`: A substring exata (lexema) que casou com a regra.
* `lineno`: A linha correspondente no arquivo fonte.
* `lexpos`: O índice numérico de início do token a partir do primeiro caractere da string.

**Exemplo Prático de Saída:**
Para a linha `SE light.sala ESTA "off"`, o parser recebe:

| Ordem | `type` | `value` | `lineno` | `lexpos` |
|---|---|---|---|---|
| 1 | `'SE'` | `'SE'` | `5` | `75` |
| 2 | `'ENTIDADE'` | `'light.sala'` | `5` | `78` |
| 3 | `'ESTA'` | `'ESTA'` | `5` | `89` |
| 4 | `'STRING'` | `'"off"'` | `5` | `94` |

---

## 4. Possíveis Gargalos e Perguntas de Banca ⚠️

Aqui estão as "pegadinhas" e os pontos de fragilidade do seu código. Se o professor quiser te testar ou pedir para alterar algo ao vivo, provavelmente será em um destes pontos:

### 🔍 Gargalo 1: A "Folga" da regra `t_PALAVRA`
* **A Fragilidade:** Na linha 93, qualquer palavra que não conste na lista de reservadas (`reserved`) vira automaticamente um token de tipo `'EVENTO'`. 
* **Por que isso é perigoso?** Se o estudante digitar errado a palavra-chave `ACAO` como `ACAOO`, o lexer **não gerará erro léxico**! Ele simplesmente dirá que `ACAOO` é um `'EVENTO'`. O erro só será descoberto na fase Sintática (Parser), que reclamará que encontrou um `'EVENTO'` onde esperava um bloco de ações.
* **Pergunta do Professor:** *"Por que um erro de grafia de palavra-chave passa batido pelo Lexer e só falha no Parser?"*
* **Sua Resposta:** *"Porque nossa especificação permite eventos dinâmicos. Assim, qualquer identificador genérico que não seja uma palavra reservada é rotulado temporariamente pelo Lexer como `EVENTO` para dar flexibilidade à linguagem, delegando a validação de ordem estrutural ao analisador sintático."*

### 🔍 Gargalo 2: Ordem de precedência implícita de regras no PLY
* **Como funciona:** O PLY segue uma regra interna rígida:
  1. Primeiro, avalia **todas as regras definidas por funções** (como `t_STRING`, `t_TEMPO`), respeitando a **ordem em que aparecem no arquivo** (de cima para baixo).
  2. Segundo, avalia as regras declaradas diretamente como **variáveis/strings** (ex: se tivéssemos um `t_SOMA = r'\+'`), classificando-as por tamanho do padrão da regex (da mais longa para a mais curta).
* **Por que é perigoso:** Se você colocar `t_PALAVRA` (que captura qualquer palavra alfanumérica genérica) **antes** de `t_EVENTO` ou `t_ENTIDADE`, a regra genérica `t_PALAVRA` "engolirá" os seus eventos e entidades! A ordem atual está correta porque regras específicas estão no topo.

### 🔍 Gargalo 3: Modificar Regras de Tempo (Exercício ao Vivo!)
* **O que o professor pode pedir:** *"Quero que a linguagem também aceite tempo em horas usando o formato '2h' ou '12h'. Altere o código léxico para isso."*
* **Como resolver ao vivo:**
  Você só precisaria alterar a expressão regular da função `t_TEMPO` (Linha 55).
  * **Original:** `r'-?\d{1,2}:\d{2}:\d{2}|\d+min|\d+s'`
  * **Modificado:** `r'-?\d{1,2}:\d{2}:\d{2}|\d+min|\d+s|\d+h'` *(adicionando `|\d+h` ao final)*

### 🔍 Gargalo 4: Padrão Restrito de Entidades
* **A Fragilidade:** A regex `r'[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*'` exige **obrigatoriamente** letras minúsculas. 
* **Por que isso é frágil?** Se o usuário declarar um dispositivo como `sensor.Porta_Sala` (com 'P' e 'S' maiúsculos) ou `1sensor.porta`, o Lexer falhará gerando um `ERRO LÉXICO` de caractere ilegal, pois a regex espera estritamente minúsculas.

---

### Resumo de Dicas para a Apresentação:
1. **Fale com propriedade:** Use termos técnicos como *Tokens*, *Lexemas*, *Expressões Regulares*, *Autômatos Finitos* (o PLY monta um autômato internamente para processar essas regex) e *PLY*.
2. **Mostre o código rodando:** O arquivo possui uma seção `if __name__ == '__main__':` (Linha 146) maravilhosa. Se você executar `python lexer.py` diretamente no terminal, ele exibirá uma tabela linda mostrando a tokenização do script de exemplo. **Aproveite isso na apresentação para demonstrar o lexer em funcionamento isolado!**

Espero que este material clareie bastante a sua visão técnica do projeto. Se precisar de ajuda para entender os próximos passos do pipeline (como o analisador sintático ou a geração de YAML), conte comigo! Boa sorte na apresentação!
