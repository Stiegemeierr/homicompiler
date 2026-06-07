# 📖 Guia de Estudos: `lexer.py`

## 1. Resumo do Papel no Pipeline do Compilador

O **Analisador Léxico** (`lexer.py`) é a **primeira fase** do seu compilador. 

Imagine que o compilador recebe o código-fonte como uma tripa única e gigante de caracteres brutos (`'A'`, `'U'`, `'T'`, `'O'`, `'\n'`, etc.). A responsabilidade exata deste arquivo é:
1. **Agrupamento (Tokenização):** Varrer esses caracteres da esquerda para a direita e agrupá-los em unidades lógicas mínimas com significado semântico, chamadas **Tokens** (ex: palavras-chave como `QUANDO`, identificadores de entidades como `light.sala`, ou strings como `"off"`).
2. **Filtragem de Ruído:** Descartar elementos que não importam para a lógica do compilador, como espaços em branco, tabulações e comentários (`# ...`).
3. **Rastreamento de Metadados:** Contar as quebras de linha para que, caso ocorra um erro mais adiante, o compilador saiba apontar exatamente em qual linha o problema aconteceu.

> **Analogia para a Apresentação:** O Lexer funciona como um leitor que separa uma frase em palavras individuais e classifica cada uma (substantivo, verbo, pontuação), jogando fora os espaços extras, antes de entregar as palavras estruturadas para o Analisador Sintático (Parser) validar a gramática da frase.

---

## 2. Desmembramento Técnico

O seu arquivo utiliza a biblioteca **PLY (Python Lex-Yacc)**, especificamente o módulo `ply.lex`. Vamos detalhar os principais componentes estruturais dele:

### A. O Dicionário de Palavras Reservadas (`reserved`) (Linhas 12-29)
```python
reserved = {
    'AUTOMACAO':  'AUTOMACAO',
    'MODO':       'MODO',
    'QUANDO':     'QUANDO',
    'SE':         'SE',
    'FACA':       'FACA',
    'FAÇA':       'FACA',
    'LIGAR':      'LIGAR',
    'DESLIGAR':   'DESLIGAR',
    'ESPERAR':    'ESPERAR',
    'ESTA':       'ESTA',
    'FIM':        'FIM',
    'ACIMA':      'ACIMA',
    'ABAIXO':     'ABAIXO',
    'ENTRE':      'ENTRE',
    'E':          'E',
    'HORARIO':    'HORARIO',
}
```
* **O que faz:** Mapeia strings exatas de palavras-chave da linguagem (em maiúsculas) para seus respectivos tipos de tokens. Note que `'FAÇA'` (com cedilha) e `'FACA'` (sem cedilha) mapeiam ambos para o token `FACA`, garantindo que o compilador aceite as duas grafias.
* **Por que existe:** Evita a necessidade de criar uma regra de expressão regular individual para cada palavra-chave. Em vez disso, quando o lexer lê uma palavra qualquer, ele primeiro checa se ela está nesse dicionário. Se estiver, ela é classificada com o token da palavra-chave; caso contrário, é tratada de forma genérica.

### B. A Tupla de Tokens (`tokens`) (Linhas 35-44)
* **O que faz:** Define a lista mestre contendo os nomes de todos os tokens válidos que o analisador sintático poderá receber. 
* *Nota de implementação:* Ela junta os tokens dinâmicos (que mudam de valor, como `ENTIDADE`, `STRING`, `NUMERO`, `TEMPO`, `EVENTO`, `DOISPONTOS`, `TRACO`) com os tokens das palavras reservadas através de `tuple(set(reserved.values()))`. O `set()` elimina duplicatas (como `FACA` que aparece duas vezes no dicionário).

### C. As Regras de Tokenização (`t_XXXX`)
No PLY, qualquer função ou variável que comece com o prefixo `t_` é interpretada como uma regra léxica baseada em Expressões Regulares (Regex).

* **`t_STRING(t)`** (Linha 53)
  * **Regex:** `r'"[^"]*"'`
  * **O que faz:** Captura qualquer texto delimitado por aspas duplas. O valor mantém as aspas para que a fase de geração de código YAML as preserve.
* **`t_TEMPO(t)`** (Linha 60)
  * **Regex:** `r'-?\d{1,2}:\d{2}:\d{2}|(?:\d+h[ \t]*)?(?:\d+min[ \t]*)?\d+s|(?:\d+h[ \t]*)?\d+min|\d+h'`
  * **O que faz:** Reconhece múltiplos formatos de tempo:
    1. Desvios horários negativos/positivos (ex: `-01:30:00`).
    2. Formatos compostos (ex: `1h 2min 3s`, `1min 45s`).
    3. Formatos isolados (ex: `5min`, `10s`, `2h`).
* **`t_NUMERO(t)`** (Linha 70)
  * **Regex:** `r'\d+'`
  * **O que faz:** Reconhece inteiros puros (ex: `20`, `75`). O valor é convertido para `int` antes de ser armazenado no token.
* **`t_ENTIDADE(t)`** (Linha 76)
  * **Regex:** `r'[a-z][a-z0-9_]*\.[a-z0-9][a-z0-9_]*'`
  * **O que faz:** Reconhece identificadores no formato clássico do *Home Assistant*: `dominio.nome_da_entidade` (ex: `light.sala`, `binary_sensor.1e1e192bce0cdc593a3e72dc6e996b46`). O domínio deve começar com letra minúscula, e o nome após o ponto pode começar com letra minúscula ou dígito.
* **`t_EVENTO(t)`** (Linha 88)
  * **Regex:** `r'sunset|sunrise'`
  * **O que faz:** Reconhece eventos de gatilho geográfico específicos.
* **`t_DOISPONTOS(t)`** (Linha 94)
  * **Regex:** `r':'`
  * **O que faz:** Captura o caractere `:` delimitador de seções (`QUANDO:`, `SE:`, `FAÇA:`).
* **`t_TRACO(t)`** (Linha 100)
  * **Regex:** `r'-'`
  * **O que faz:** Captura o caractere `-` usado como marcador de item de lista (prefixo de cada gatilho, condição ou ação).
* **`t_PALAVRA(t)`** (Linha 106)
  * **Regex:** `r'[A-Za-z_Çç][A-Za-z0-9_Çç]*'`
  * **O que faz:** Essa é a regra "pega-tudo" para cadeias de caracteres alfanuméricas (incluindo cedilha). Ela lê a palavra inteira e executa a linha `t.type = reserved.get(t.value, 'EVENTO')`. Ou seja: se a palavra for uma palavra-chave como `AUTOMACAO`, altera o tipo do token para `AUTOMACAO`. Se não for reservada, ela assume que é um `EVENTO` dinâmico genérico.

### D. Regras Especiais e Utilitários
* **`t_ignore = ' \t'`** (Linha 123): Diz ao PLY para ignorar silenciosamente espaços e tabulações.
* **`t_COMENTARIO(t)`** (Linha 126): Regex `r'\#.*'`. Usa a instrução `pass` (não retorna `t`). Isso faz com que o comentário seja consumido e descartado da saída do lexer.
* **`t_newline(t)`** (Linha 132): Toda vez que encontra um caractere `\n`, soma o total de quebras encontradas ao contador de linhas do lexer (`t.lexer.lineno`).
* **`t_error(t)`** (Linha 142): Função de tratamento de erros. Se o lexer encontrar um caractere ilegal (como `@`, `!`, `$` ou letras soltas fora do padrão), ele exibe uma mensagem amigável contendo a linha/posição e pula esse caractere usando `t.lexer.skip(1)` para tentar continuar a análise.

---

## 3. Fluxo de Dados

```mermaid
graph LR
    A[Código-Fonte Homi - String] --> B["lexer.py / ply.lex"]
    B --> C[Sequência de Objetos LexToken]
```

### 📥 O que entra:
Uma **única string** contendo todo o código-fonte do script Homi. Exemplo:
```text
- alarm_control_panel.alarmo ESTA "disarmed"
```

### 📤 O que sai (Formato Exato):
O analisador cospe uma sequência de objetos do tipo `LexToken` da biblioteca PLY. Cada objeto possui os atributos:
* `type`: O tipo de token (identificado na tupla `tokens`).
* `value`: A substring exata (lexema) que casou com a regra.
* `lineno`: A linha correspondente no arquivo fonte.
* `lexpos`: O índice numérico de início do token a partir do primeiro caractere da string.

**Exemplo Prático de Saída:**
Para a linha `- alarm_control_panel.alarmo ESTA "disarmed"`, o parser recebe:

| Ordem | `type` | `value` | `lineno` | `lexpos` |
|---|---|---|---|---|
| 1 | `'TRACO'` | `'-'` | `8` | `75` |
| 2 | `'ENTIDADE'` | `'alarm_control_panel.alarmo'` | `8` | `77` |
| 3 | `'ESTA'` | `'ESTA'` | `8` | `104` |
| 4 | `'STRING'` | `'"disarmed"'` | `8` | `109` |

---

## 4. Possíveis Gargalos e Perguntas de Banca ⚠️

Aqui estão as "pegadinhas" e os pontos de fragilidade do seu código. Se o professor quiser te testar ou pedir para alterar algo ao vivo, provavelmente será em um destes pontos:

### 🔍 Gargalo 1: A "Folga" da regra `t_PALAVRA`
* **A Fragilidade:** Na linha 112, qualquer palavra que não conste na lista de reservadas (`reserved`) vira automaticamente um token de tipo `'EVENTO'`. 
* **Por que isso é perigoso?** Se o estudante digitar errado a palavra-chave `QUANDO` como `QUANDOO`, o lexer **não gerará erro léxico**! Ele simplesmente dirá que `QUANDOO` é um `'EVENTO'`. O erro só será descoberto na fase Sintática (Parser), que reclamará que encontrou um `'EVENTO'` onde esperava um bloco de gatilhos.
* **Pergunta do Professor:** *"Por que um erro de grafia de palavra-chave passa batido pelo Lexer e só falha no Parser?"*
* **Sua Resposta:** *"Porque nossa especificação permite eventos dinâmicos. Assim, qualquer identificador genérico que não seja uma palavra reservada é rotulado temporariamente pelo Lexer como `EVENTO` para dar flexibilidade à linguagem, delegando a validação de ordem estrutural ao analisador sintático."*

### 🔍 Gargalo 2: Ordem de precedência implícita de regras no PLY
* **Como funciona:** O PLY segue uma regra interna rígida:
  1. Primeiro, avalia **todas as regras definidas por funções** (como `t_STRING`, `t_TEMPO`), respeitando a **ordem em que aparecem no arquivo** (de cima para baixo).
  2. Segundo, avalia as regras declaradas diretamente como **variáveis/strings** (ex: se tivéssemos um `t_SOMA = r'\+'`), classificando-as por tamanho do padrão da regex (da mais longa para a mais curta).
* **Por que é perigoso:** Se você colocar `t_PALAVRA` (que captura qualquer palavra alfanumérica genérica) **antes** de `t_EVENTO` ou `t_ENTIDADE`, a regra genérica `t_PALAVRA` "engolirá" os seus eventos e entidades! A ordem atual está correta porque regras específicas estão no topo.

### 🔍 Gargalo 3: Modificar Regras de Tempo (Exercício ao Vivo!)
* **O que o professor pode pedir:** *"Quero que a linguagem também aceite tempo em dias usando o formato '2d'. Altere o código léxico para isso."*
* **Como resolver ao vivo:**
  Você só precisaria alterar a expressão regular da função `t_TEMPO` (Linha 61), adicionando `|\d+d` ao final da alternância da regex.

### 🔍 Gargalo 4: Padrão Restrito de Entidades
* **A Fragilidade:** A regex `r'[a-z][a-z0-9_]*\.[a-z0-9][a-z0-9_]*'` exige **obrigatoriamente** letras minúsculas no domínio. 
* **Por que isso é frágil?** Se o usuário declarar um dispositivo como `Sensor.porta_sala` (com 'S' maiúsculo), o Lexer falhará, pois a regex espera estritamente minúsculas no início do domínio. Porém, o nome da entidade (após o ponto) pode começar com dígito, permitindo IDs como `binary_sensor.1e1e192bce0cdc593a3e72dc6e996b46`.

---

### Resumo de Dicas para a Apresentação:
1. **Fale com propriedade:** Use termos técnicos como *Tokens*, *Lexemas*, *Expressões Regulares*, *Autômatos Finitos* (o PLY monta um autômato internamente para processar essas regex) e *PLY*.
2. **Mostre o código rodando:** O arquivo possui uma seção `if __name__ == '__main__':` (Linha 166) maravilhosa. Se você executar `python lexer.py` diretamente no terminal, ele exibirá uma tabela linda mostrando a tokenização do script de exemplo. **Aproveite isso na apresentação para demonstrar o lexer em funcionamento isolado!**

Espero que este material clareie bastante a sua visão técnica do projeto. Se precisar de ajuda para entender os próximos passos do pipeline (como o analisador sintático ou a geração de YAML), conte comigo! Boa sorte na apresentação!
