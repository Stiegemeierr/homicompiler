# Relatório Técnico — Compilador da Linguagem Homi

## Sumário

1. [Introdução e Visão Geral](#1-introdução-e-visão-geral)
2. [Descrição da Gramática Livre de Contexto (GLC)](#2-descrição-da-gramática-livre-de-contexto-glc)
3. [Descrição do Analisador Léxico](#3-descrição-do-analisador-léxico)
4. [Descrição do Analisador Sintático](#4-descrição-do-analisador-sintático)
5. [Descrição do Analisador Semântico](#5-descrição-do-analisador-semântico)
6. [Geração de Código e Exemplos](#6-geração-de-código-e-exemplos)
7. [Conclusão](#7-conclusão)

---

## 1. Introdução e Visão Geral

O presente relatório descreve o projeto e a implementação de um **compilador modular** para a linguagem **Homi**, desenvolvido em **Python 3** com auxílio da biblioteca **PLY (Python Lex-Yacc)**. A linguagem Homi foi concebida para permitir que **usuários leigos** descrevam automações residenciais de forma procedural e intuitiva, utilizando palavras-chave em português. O compilador traduz esses scripts para **arquivos declarativos YAML** compatíveis com o sistema de automação residencial **Home Assistant**.

### 1.1 Arquitetura do Pipeline

O compilador segue a arquitetura clássica de fases, organizada em quatro módulos sequenciais:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   lexer.py      │────▶│ parser_homi.py  │────▶│  semantic.py    │────▶│   codegen.py    │
│  (Fase Léxica)  │     │ (Fase Sintática)│     │ (Fase Semântica)│     │ (Geração YAML)  │
│                 │     │                 │     │                 │     │                 │
│ Código-fonte    │     │ Fluxo de tokens │     │ AST bruta       │     │ AST validada    │
│ .homi (string)  │     │ → AST (dicts)   │     │ → AST validada  │     │ → output.yaml   │
└─────────────────┘     └─────────────────┘     └─────────────────┘     └─────────────────┘
```

O ponto de entrada é o arquivo `main.py`, que orquestra a execução sequencial de todas as fases, lendo um arquivo `.homi` de entrada e produzindo um arquivo `.yaml` de saída:

```python
# Pipeline de compilação em main.py (simplificado)
ast = parser.parse(codigo_fonte, lexer=lexer)          # Fases 1 e 2
sem_erros = AnalisadorSemantico().analisar(ast)         # Fase 3
GeradorYAML(ast).salvar_arquivo(arquivo_saida)          # Fase 4
```

---

## 2. Descrição da Gramática Livre de Contexto (GLC)

A Gramática Livre de Contexto (GLC) que define a estrutura sintática da linguagem Homi é apresentada formalmente a seguir na notação BNF (Backus-Naur Form).

### 2.1 Símbolos Não-Terminais

Os **símbolos não-terminais** representam abstrações sintáticas que são expandidas por regras de produção. Estão delimitados por `< >`:

| Não-Terminal | Descrição |
|---|---|
| `<programa>` | Nó raiz: lista de uma ou mais automações |
| `<automacao>` | Estrutura completa de uma automação |
| `<bloco_modo>` | Declaração opcional do modo de execução |
| `<bloco_gatilho>` | Bloco obrigatório de gatilhos (`QUANDO:`) |
| `<lista_gatilhos>` | Sequência de um ou mais comandos de gatilho |
| `<comando_gatilho>` | Um gatilho individual (evento, estado, numérico ou horário) |
| `<bloco_condicao>` | Bloco opcional de condições (`SE:`) |
| `<lista_condicoes>` | Sequência de um ou mais comandos de condição |
| `<comando_condicao>` | Uma condição individual (estado, numérica ou horário) |
| `<bloco_acao>` | Bloco obrigatório de ações (`FAÇA:`) |
| `<lista_acoes>` | Sequência de um ou mais comandos de ação |
| `<comando_acao>` | Uma ação individual (ligar, desligar ou esperar) |

### 2.2 Símbolos Terminais

Os **símbolos terminais** são os tokens produzidos pelo analisador léxico e consumidos pelo parser:

| Terminal | Exemplo | Descrição |
|---|---|---|
| `AUTOMACAO` | `AUTOMACAO` | Palavra-chave de início de automação |
| `MODO` | `MODO` | Palavra-chave de declaração de modo |
| `QUANDO` | `QUANDO` | Palavra-chave de bloco de gatilhos |
| `SE` | `SE` | Palavra-chave de bloco de condições |
| `FACA` | `FAÇA` / `FACA` | Palavra-chave de bloco de ações |
| `FIM` | `FIM` | Delimitador de fim de automação |
| `LIGAR` | `LIGAR` | Ação de ativar uma entidade |
| `DESLIGAR` | `DESLIGAR` | Ação de desativar uma entidade |
| `ESPERAR` | `ESPERAR` | Ação de aguardar um tempo |
| `ESTA` | `ESTA` | Operador de comparação de estado |
| `ACIMA` | `ACIMA` | Operador de comparação numérica (>) |
| `ABAIXO` | `ABAIXO` | Operador de comparação numérica (<) |
| `ENTRE` | `ENTRE` | Operador de intervalo temporal |
| `E` | `E` | Conjunção para intervalos |
| `HORARIO` | `HORARIO` | Palavra-chave para condição/gatilho temporal |
| `STRING` | `"off"`, `"disarmed"` | Literal de texto entre aspas duplas |
| `ENTIDADE` | `light.sala` | Identificador de entidade do Home Assistant |
| `EVENTO` | `sunset`, `sunrise` | Evento geográfico/solar |
| `TEMPO` | `5min`, `-01:30:00` | Literal de duração temporal |
| `NUMERO` | `20`, `75` | Literal inteiro |
| `DOISPONTOS` | `:` | Delimitador de seção |
| `TRACO` | `-` | Prefixo de item de lista |

### 2.3 Produções da GLC

```bnf
<programa>        ::= <automacao>
                    | <programa> <automacao>

<automacao>       ::= AUTOMACAO STRING <bloco_modo> <bloco_gatilho> <bloco_condicao> <bloco_acao> FIM

<bloco_modo>      ::= MODO EVENTO
                    | ε

<bloco_gatilho>   ::= QUANDO DOISPONTOS <lista_gatilhos>

<lista_gatilhos>  ::= <comando_gatilho>
                    | <lista_gatilhos> <comando_gatilho>

<comando_gatilho> ::= TRACO EVENTO TEMPO
                    | TRACO ENTIDADE ESTA STRING
                    | TRACO ENTIDADE ACIMA NUMERO
                    | TRACO ENTIDADE ABAIXO NUMERO
                    | TRACO HORARIO ENTRE TEMPO E TEMPO

<bloco_condicao>  ::= SE DOISPONTOS <lista_condicoes>
                    | ε

<lista_condicoes> ::= <comando_condicao>
                    | <lista_condicoes> <comando_condicao>

<comando_condicao>::= TRACO ENTIDADE ESTA STRING
                    | TRACO ENTIDADE ACIMA NUMERO
                    | TRACO ENTIDADE ABAIXO NUMERO
                    | TRACO HORARIO ENTRE TEMPO E TEMPO

<bloco_acao>      ::= FACA DOISPONTOS <lista_acoes>

<lista_acoes>     ::= <comando_acao>
                    | <lista_acoes> <comando_acao>

<comando_acao>    ::= TRACO LIGAR ENTIDADE
                    | TRACO DESLIGAR ENTIDADE
                    | TRACO ESPERAR TEMPO
```

A produção `ε` (vazia) aparece em `<bloco_modo>` e `<bloco_condicao>`, tornando o modo de execução e o bloco de condições **opcionais**. Quando `<bloco_modo>` deriva ε, o valor padrão adotado é `'single'`.

---

## 3. Descrição do Analisador Léxico

### 3.1 Visão Geral

O **Analisador Léxico** (`lexer.py`) constitui a primeira fase do compilador. Sua função é varrer o código-fonte caractere a caractere (da esquerda para a direita) e agrupá-los em unidades lógicas mínimas com significado, denominadas **tokens**. Paralelamente, descarta elementos irrelevantes para a compilação (espaços, tabulações e comentários) e rastreia o número de linhas para reporte preciso de erros.

A implementação utiliza o módulo `ply.lex` da biblioteca PLY, que internamente constrói um **Autômato Finito Determinístico (AFD)** a partir das expressões regulares declaradas para cada regra de token.

### 3.2 Dicionário de Palavras Reservadas

O primeiro componente estrutural é o dicionário `reserved`, que mapeia cada palavra-chave da linguagem ao seu respectivo tipo de token:

```python
reserved = {
    'AUTOMACAO':  'AUTOMACAO',
    'MODO':       'MODO',
    'QUANDO':     'QUANDO',
    'SE':         'SE',
    'FACA':       'FACA',
    'FAÇA':       'FACA',       # Cedilha mapeada ao mesmo token
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

Destaca-se que `'FAÇA'` (com cedilha) e `'FACA'` (sem cedilha) mapeiam ambos para o token `FACA`, garantindo que o compilador aceite as duas grafias. A lista de tokens é construída combinando os tokens dinâmicos com os tokens das palavras reservadas, utilizando `set()` para eliminar duplicatas.

### 3.3 Estrutura do Autômato Finito Determinístico

O PLY internamente compila cada expressão regular declarada em uma máquina de estados (AFD), obedecendo a uma regra de precedência rígida:

1. **Regras definidas como funções** (`t_STRING`, `t_TEMPO`, etc.) são avaliadas na **ordem em que aparecem no arquivo-fonte** (de cima para baixo).
2. **Regras definidas como variáveis/strings** são avaliadas por **tamanho decrescente** do padrão regex.

Essa ordenação é fundamental para que regras mais específicas sejam aplicadas antes das genéricas.

#### 3.3.1 Reconhecimento de Tokens Complexos

**Token `ENTIDADE`** — Identificadores do Home Assistant no formato `domínio.nome`:

```python
def t_ENTIDADE(t):
    r'[a-z][a-z0-9_]*\.[a-z0-9][a-z0-9_]*'
    return t
```

O AFD para esta regra transita por um estado inicial esperando uma letra minúscula, seguida de zero ou mais caracteres alfanuméricos ou underscores, obrigatoriamente um ponto literal (`.`), e então uma segunda sequência iniciada por letra minúscula ou dígito. Exemplos válidos: `light.sala`, `binary_sensor.1e1e192bce0cdc593a3e72dc6e996b46`.

**Token `TEMPO`** — Múltiplos formatos temporais com alternâncias:

```python
def t_TEMPO(t):
    r'-?\d{1,2}:\d{2}:\d{2}|(?:\d+h[ \t]*)?(?:\d+min[ \t]*)?'
    r'\d+s|(?:\d+h[ \t]*)?\d+min|\d+h'
    t.value = t.value.strip()
    return t
```

A expressão regular utiliza o operador de alternância (`|`) para reconhecer três formatos:

| Formato | Exemplo | Padrão Regex |
|---|---|---|
| Offset `HH:MM:SS` | `-01:30:00` | `-?\d{1,2}:\d{2}:\d{2}` |
| Composto | `1h 2min 3s`, `1min 45s` | `(?:\d+h[ \t]*)?(?:\d+min[ \t]*)?\d+s` |
| Isolado | `5min`, `10s`, `2h` | `\d+h` / `\d+min` |

**Token `PALAVRA`** (regra genérica) — Captura qualquer cadeia alfanumérica e consulta o dicionário de reservadas:

```python
def t_PALAVRA(t):
    r'[A-Za-z_Çç][A-Za-z0-9_Çç]*'
    t.type = reserved.get(t.value, 'EVENTO')
    return t
```

Se a palavra estiver no dicionário `reserved`, o tipo do token é atualizado para a palavra-chave correspondente; caso contrário, é classificada como `EVENTO` genérico. Isso garante extensibilidade, mas delega a validação de nomes desconhecidos ao parser.

### 3.4 Tratamento de Comentários

Comentários iniciados por `#` são descartados silenciosamente pela seguinte regra:

```python
def t_COMENTARIO(t):
    r'\#.*'
    pass  # Não retorna nada → token descartado.
```

A instrução `pass` (ausência de `return t`) faz com que o PLY consuma o comentário inteiro sem emitir nenhum token para o parser.

### 3.5 Contagem de Linhas para Reporte de Erros

A contabilização de linhas é realizada pela regra `t_newline`:

```python
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)
```

A cada ocorrência de um ou mais caracteres de quebra de linha (`\n`), o contador `t.lexer.lineno` é incrementado pela quantidade de quebras encontradas. Esse valor é propagado automaticamente pelo PLY para os atributos `lineno` de todos os tokens subsequentes, permitindo que as fases seguintes (sintática e semântica) reportem erros com indicação precisa da linha.

### 3.6 Tratamento de Erros Léxicos

Quando o lexer encontra um caractere que não casa com nenhuma regra definida:

```python
def t_error(t):
    print(
        f"[ERRO LÉXICO] Caractere ilegal '{t.value[0]}' "
        f"na linha {t.lineno}, posição {t.lexpos}"
    )
    t.lexer.lex_error = True
    t.lexer.skip(1)
```

A função emite uma mensagem com o caractere ilegal, a linha e a posição. A flag `lex_error` é ativada para sinalização posterior, e o caractere é pulado com `skip(1)` para que o lexer tente continuar a análise sem abortar.

### 3.7 Exemplo de Saída do Lexer

Para a entrada `- alarm_control_panel.alarmo ESTA "disarmed"`, o lexer produz:

| Ordem | `type` | `value` | `lineno` | `lexpos` |
|---|---|---|---|---|
| 1 | `TRACO` | `-` | 8 | 75 |
| 2 | `ENTIDADE` | `alarm_control_panel.alarmo` | 8 | 77 |
| 3 | `ESTA` | `ESTA` | 8 | 104 |
| 4 | `STRING` | `"disarmed"` | 8 | 109 |

---

## 4. Descrição do Analisador Sintático

### 4.1 Abordagem Adotada

O Analisador Sintático (`parser_homi.py`) utiliza o módulo `ply.yacc`, que constrói um parser **Bottom-Up LALR(1)** (Look-Ahead LR com 1 token de lookahead). Trata-se de uma variante eficiente do algoritmo LR que utiliza tabelas de análise compactadas geradas automaticamente pelo PLY, persistidas no arquivo `parsetab.py`.

O parser LALR(1) opera por meio de duas operações fundamentais:
- **Shift** (empilhamento): desloca o token corrente para a pilha de análise.
- **Reduce** (redução): aplica uma regra de produção da gramática, substituindo os símbolos do topo da pilha pelo não-terminal da cabeça da regra.

### 4.2 Construção da AST

Cada regra gramatical é declarada como uma função Python prefixada com `p_`, cuja *docstring* descreve formalmente a produção BNF. O argumento `p` é um objeto `YaccProduction` que se comporta como uma lista indexada:
- `p[0]`: resultado da produção (lado esquerdo da regra).
- `p[1]`, `p[2]`, ...: símbolos do lado direito da regra.

A regra principal demonstra a construção do nó de automação na AST:

```python
def p_automacao(p):
    '''automacao : AUTOMACAO STRING bloco_modo bloco_gatilho bloco_condicao bloco_acao FIM'''
    p[0] = {
        'tipo':      'automacao',
        'nome':      p[2],
        'modo':      p[3],
        'gatilhos':  p[4],
        'condicoes': p[5],
        'acoes':     p[6],
    }
```

A AST resultante é uma **lista de dicionários Python**, onde cada dicionário encapsula hierarquicamente os componentes semânticos de uma automação. Exemplo de AST para o script de referência:

```python
[
  {
    'tipo': 'automacao',
    'nome': '"Por do sol na Sala"',
    'modo': 'single',
    'gatilhos': [
      {'tipo': 'gatilho_evento', 'evento': 'sunset', 'offset': '-01:30:00'}
    ],
    'condicoes': [
      {'tipo': 'condicao_estado', 'entidade': 'alarm_control_panel.alarmo', 'estado': '"disarmed"'},
      {'tipo': 'condicao_estado', 'entidade': 'light.sala', 'estado': '"off"'}
    ],
    'acoes': [
      {'tipo': 'acao_ligar',    'entidade': 'light.sala'},
      {'tipo': 'acao_esperar',  'duracao': '5min'},
      {'tipo': 'acao_desligar', 'entidade': 'light.sala'}
    ]
  }
]
```

### 4.3 Recuperação de Erros — Modo Pânico

O parser implementa uma estratégia de **recuperação de erros em Modo Pânico** (Panic Mode Recovery), permitindo que a compilação continue mesmo após encontrar erros sintáticos. Essa abordagem opera em dois níveis:

#### 4.3.1 Nível de Automação (`p_automacao_erro`)

Quando a estrutura interna de uma automação está inválida, o parser utiliza o token especial `error` do PLY para consumir e descartar tokens até encontrar o delimitador de sincronização `FIM`:

```python
def p_automacao_erro(p):
    '''automacao : AUTOMACAO STRING error FIM'''
    print(
        f"[ERRO SINTÁTICO] Estrutura inválida na automação {p[2]}. "
        f"Recuperando no token FIM (linha {p.lineno(4)})."
    )
    parser.sintax_error = True
    p[0] = {
        'tipo':      'automacao_com_erro',
        'nome':      p[2],
        'modo':      'single',
        'gatilhos':  [],
        'condicoes': [],
        'acoes':     [],
    }
```

O nó gerado é rotulado com `'tipo': 'automacao_com_erro'`, permitindo que as fases subsequentes (semântica e codegen) ignorem essa automação sem interromper o processamento das demais.

#### 4.3.2 Nível Global (`p_error`)

A função `p_error` é chamada automaticamente pelo Yacc no primeiro token que viola a gramática. Ela implementa a sincronização consumindo tokens até encontrar um ponto seguro:

```python
def p_error(p):
    if p is None:
        print("[ERRO SINTÁTICO] Fim inesperado do arquivo (EOF).")
        parser.sintax_error = True
        return

    print(
        f"[ERRO SINTÁTICO] Token inesperado '{p.value}' "
        f"(tipo: {p.type}) na linha {p.lineno}."
    )
    parser.sintax_error = True

    # Tokens de sincronização — pontos seguros para retomar a análise.
    sync_tokens = {'FIM', 'QUANDO', 'SE', 'FACA', 'AUTOMACAO'}

    while True:
        tok = p.lexer.token()
        if tok is None:
            break
        if tok.type in sync_tokens:
            parser.errok()      # Limpa estado de erro
            parser.restart()    # Reinicia o autômato
            # Reinjeta o token de sincronização para consumo
            _original_token = parser.token
            parser.token = lambda _tok=tok, _orig=_original_token: (
                setattr(parser, 'token', _orig) or _tok
            )
            break
```

O conjunto de **tokens de sincronização** (`FIM`, `QUANDO`, `SE`, `FACA`, `AUTOMACAO`) representa delimitadores de bloco que definem fronteiras estruturais seguras. Ao encontrar um desses tokens:

1. `parser.errok()` limpa a flag de estado de erro do PLY.
2. `parser.restart()` reinicia o estado interno do autômato LALR.
3. O token de sincronização é reinjetado na fila de leitura por meio de uma função `lambda` que substitui temporariamente o método `parser.token`, garantindo que o parser retome a análise a partir desse ponto.

**Exemplo prático:** para o arquivo `erro_sintatico.homi` (onde os dois-pontos após `QUANDO` foram omitidos):

```
AUTOMACAO "Erro Sintatico"
MODO single

QUANDO          # ← falta o ':'
- sunset -01:30:00

FAÇA:
- LIGAR light.sala
FIM
```

O parser detecta o token inesperado `-` após `QUANDO` (onde esperava `:`), consome tokens até `FIM`, e gera um nó `automacao_com_erro`, permitindo a compilação de automações subsequentes.

---

## 5. Descrição do Analisador Semântico

### 5.1 Visão Geral

O **Analisador Semântico** (`semantic.py`) constitui a terceira fase do compilador. Enquanto as fases anteriores validam a **forma** (léxica) e a **gramática** (sintática) do código, esta fase valida o **significado** e a **coerência lógica** do programa, garantindo que as operações escritas pelo usuário façam sentido no contexto do Home Assistant.

A implementação utiliza a classe `AnalisadorSemantico`, que adota o padrão de projeto **Visitor** para percorrer recursivamente os nós da AST.

### 5.2 Tabela de Símbolos

A Tabela de Símbolos é implementada como um dicionário Python (`self.tabela_simbolos`) que mapeia cada entidade encontrada no código-fonte ao seu respectivo domínio:

```python
def __init__(self):
    self.tabela_simbolos = {}   # {entidade_completa: domínio}
    self.erros = []             # Lista de erros acumulados

def _registrar_entidade(self, entidade: str):
    if entidade not in self.tabela_simbolos:
        dominio = self._extrair_dominio(entidade)
        self.tabela_simbolos[entidade] = dominio
```

O domínio é extraído da parte anterior ao ponto do identificador de entidade (ex: `'light'` de `'light.sala'`). A tabela é populada progressivamente conforme o Visitor percorre os blocos de gatilhos, condições e ações.

**Exemplo de Tabela de Símbolos** para o script de referência:

| Entidade | Domínio |
|---|---|
| `alarm_control_panel.alarmo` | `alarm_control_panel` |
| `light.sala` | `light` |

### 5.3 Checagem de Tipos e Consistência Externa

A validação semântica central do compilador impede que ações de controle (`LIGAR`/`DESLIGAR`) sejam aplicadas a entidades de domínios exclusivamente de leitura. Para isso, o analisador mantém dois conjuntos estáticos de classificação:

**Domínios Atuadores** (aceitam `LIGAR`/`DESLIGAR`):
```python
DOMINIOS_ATUADORES = {
    'light', 'switch', 'fan', 'cover', 'lock',
    'media_player', 'climate', 'vacuum', 'script',
    'automation', 'input_boolean', 'scene',
    'input_select', 'timer', 'notify', 'alexa_devices',
}
```

**Domínios Sensores** (somente leitura — protegidos de alteração):
```python
DOMINIOS_SENSORES = {
    'sensor', 'binary_sensor', 'weather', 'sun',
    'device_tracker', 'zone', 'person',
    'alarm_control_panel',
}
```

A checagem de tipos é realizada no método `_visitar_acao`:

```python
def _visitar_acao(self, no: dict, automacao_nome: str):
    if no['tipo'] in ('acao_ligar', 'acao_desligar'):
        entidade = no['entidade']
        self._registrar_entidade(entidade)
        dominio = self._extrair_dominio(entidade)

        if dominio not in self.DOMINIOS_ATUADORES:
            verbo = 'LIGAR' if no['tipo'] == 'acao_ligar' else 'DESLIGAR'
            self._adicionar_erro(
                automacao_nome,
                f"Ação '{verbo}' inválida para a entidade '{entidade}'. "
                f"O domínio '{dominio}' é de leitura e não aceita "
                f"comandos de estado."
            )
```

**Exemplo de erro semântico detectado:** para o arquivo `erro_semantico.homi`:

```
AUTOMACAO "Erro Semantico"
MODO single

QUANDO:
- sunset -01:30:00

FAÇA:
- LIGAR sensor.temperatura_externa
FIM
```

O analisador detecta que `sensor` não pertence ao conjunto `DOMINIOS_ATUADORES` e acumula a seguinte mensagem de erro:

```
Ação 'LIGAR' inválida para a entidade 'sensor.temperatura_externa'.
O domínio 'sensor' é de leitura e não aceita comandos de estado.
Domínios válidos: alexa_devices, automation, climate, cover, fan, ...
```

### 5.4 Resiliência e Acumulação de Erros

O analisador **nunca aborta** no primeiro erro encontrado. Todos os erros são acumulados na lista `self.erros`, permitindo que o relatório final apresente todas as inconsistências de uma só vez. Automações marcadas como `'automacao_com_erro'` pelo parser são silenciosamente ignoradas, evitando falsos positivos decorrentes de falhas sintáticas já reportadas.

---

## 6. Geração de Código e Exemplos

### 6.1 Visão Geral

O **Gerador de Código** (`codegen.py`) é a fase final (back-end) do compilador. A classe `GeradorYAML` implementa uma variação do padrão **Visitor** que percorre a AST validada e constrói estruturas de dicionários e listas Python que reproduzem fielmente o schema oficial de automações do Home Assistant.

### 6.2 Tradução da AST para YAML

#### 6.2.1 Esqueleto de uma Automação

O método `_gerar_automacao` cria o esqueleto base conforme o padrão oficial do Home Assistant:

```python
def _gerar_automacao(self, no: dict) -> dict:
    return {
        'id':          self._gerar_id(no['nome']),
        'alias':       self._limpar_string(no['nome']),
        'description': '',
        'triggers':    self._gerar_triggers(no.get('gatilhos', [])),
        'conditions':  self._gerar_conditions(no.get('condicoes', [])),
        'actions':     self._gerar_actions(no.get('acoes', [])),
        'mode':        no.get('modo', 'single'),
    }
```

#### 6.2.2 Geração de IDs Determinísticos

O compilador gera IDs determinísticos baseados em hash MD5 do nome da automação, garantindo que compilações idênticas produzam IDs idênticos:

```python
@staticmethod
def _gerar_id(nome: str) -> str:
    hash_hex = hashlib.md5(nome.encode('utf-8')).hexdigest()
    return str(int(hash_hex[:13], 16))
```

#### 6.2.3 Mapeamento de Gatilhos (Triggers)

Os gatilhos Homi são traduzidos para o schema correspondente do Home Assistant:

| Tipo Homi | Schema HA | Exemplo |
|---|---|---|
| `gatilho_evento` | `trigger: sun` | `- sunset -01:30:00` → `{event: sunset, offset: -01:30:00, trigger: sun}` |
| `gatilho_estado` | `trigger: state` | `- light.sala ESTA "on"` → `{entity_id: [light.sala], to: [on], trigger: state}` |
| `gatilho_numerico` | `trigger: numeric_state` | `- sensor.temp ACIMA 25` → `{entity_id: [...], above: 25, trigger: numeric_state}` |
| `gatilho_horario` | `trigger: time` | `- HORARIO ENTRE 18:00:00 E 06:00:00` → `{trigger: time, at: 18:00:00}` |

#### 6.2.4 Mapeamento de Condições (Conditions)

| Tipo Homi | Schema HA | Chaves |
|---|---|---|
| `condicao_estado` | `condition: state` | `entity_id`, `state` |
| `condicao_numerica` | `condition: numeric_state` | `entity_id`, `above`/`below` |
| `condicao_horario` | `condition: time` | `after`, `before` |

#### 6.2.5 Mapeamento de Ações (Actions)

O gerador extrai o domínio da entidade e formata o serviço correspondente no Home Assistant, com tratamento especial para domínios com comandos não-padrão:

```python
if a['tipo'] == 'acao_ligar':
    dominio = self._extrair_dominio(a['entidade'])
    if dominio == 'cover':
        action_str = f"{dominio}.open"
    elif dominio == 'automation':
        action_str = f"{dominio}.trigger"
    else:
        action_str = f"{dominio}.turn_on"
```

Para ações de `ESPERAR`, o tradutor temporal `_parsear_tempo` converte strings simplificadas para o dicionário de delay do HA:

```python
# '5min'  → {'hours': 0, 'minutes': 5, 'seconds': 0, 'milliseconds': 0}
# '1h 2min 3s' → {'hours': 1, 'minutes': 2, 'seconds': 3, 'milliseconds': 0}
```

### 6.3 Serialização e Indentação YAML

A exportação final utiliza a biblioteca `PyYAML` com parâmetros criticamente importantes:

```python
def exportar_yaml(self) -> str:
    return yaml.dump(
        self.automacoes_yaml,
        default_flow_style=False,
        sort_keys=False,
        allow_unicode=True,
    )
```

- `sort_keys=False`: preserva a ordem de inserção das chaves (`id`, `alias`, `triggers`, ...), garantindo legibilidade humana.
- `allow_unicode=True`: permite que caracteres acentuados (ex: "Pôr do sol") sejam salvos diretamente, sem sequências de escape.
- `default_flow_style=False`: força a serialização em estilo bloco (multilinha), mantendo a indentação rígida exigida pelo Home Assistant.

### 6.4 Exemplos Práticos Completos

#### Exemplo 1 — Script Básico com Evento Solar

**Entrada (Homi):**

```
AUTOMACAO "Por do sol na Sala"
MODO single

QUANDO:
    - sunset -01:30:00

SE:
    - alarm_control_panel.alarmo ESTA "disarmed"
    - light.sala ESTA "off"

FAÇA:
    - LIGAR light.sala
    - ESPERAR 5min
    - DESLIGAR light.sala
FIM
```

**Saída (YAML compilado):**

```yaml
- id: '1162936460885726'
  alias: Por do sol na Sala
  description: ''
  triggers:
  - event: sunset
    offset: -01:30:00
    trigger: sun
  conditions:
  - condition: state
    entity_id: alarm_control_panel.alarmo
    state:
    - disarmed
  - condition: state
    entity_id: light.sala
    state:
    - 'off'
  actions:
  - action: light.turn_on
    metadata: {}
    data: {}
    target:
      entity_id: light.sala
  - delay:
      hours: 0
      minutes: 5
      seconds: 0
      milliseconds: 0
  - action: light.turn_off
    metadata: {}
    data: {}
    target:
      entity_id: light.sala
  mode: single
```

#### Exemplo 2 — Script com Múltiplos Sensores e Horário

**Entrada (Homi):**

```
AUTOMACAO "Corda Corredor - movimento"
MODO restart

QUANDO:
- binary_sensor.corredor_suite_luminance_motion_sensor_movimento ESTA "on"
- binary_sensor.tz3000_6ygjfyll_ts0202 ESTA "on"
- binary_sensor.motion_sensor_movimento ESTA "on"

SE:
- switch.bb97c45f407329aca067d3f274499a81 ESTA "on"
- alarm_control_panel.37dc24654a788314bfb4de2e2c827fd0 ESTA "disarmed"
- light.corda_led_corredor ESTA "off"
- HORARIO ENTRE 12:00:00 E 01:15:00

FAÇA:
- LIGAR light.a4595b3013d5c452494f933e1e104129
- ESPERAR 1min 45s
- DESLIGAR light.a4595b3013d5c452494f933e1e104129
FIM
```

Neste exemplo, o compilador:
- Reconhece o modo `restart` (em vez do padrão `single`).
- Processa três gatilhos de estado com sensores binários.
- Trata quatro condições, incluindo uma condição temporal `HORARIO ENTRE`.
- Converte `ESPERAR 1min 45s` para o delay `{hours: 0, minutes: 1, seconds: 45, milliseconds: 0}`.

#### Exemplo 3 — Detecção de Erro Semântico

**Entrada (Homi):**

```
AUTOMACAO "Erro Semantico"
MODO single

QUANDO:
- sunset -01:30:00

FAÇA:
- LIGAR sensor.temperatura_externa
FIM
```

**Saída do compilador (erro):**

```
[ERRO SEMÂNTICO] 1 erro(s) encontrado(s):
----------------------------------------------------------------------
  1. Automação: "Erro Semantico"
     -> Ação 'LIGAR' inválida para a entidade 'sensor.temperatura_externa'.
        O domínio 'sensor' é de leitura e não aceita comandos de estado.
----------------------------------------------------------------------
Compilação abortada. A geração de código YAML foi desativada.
```

---

## 7. Conclusão

O compilador Homi demonstra uma implementação completa e funcional das quatro fases clássicas de um compilador: análise léxica (tokenização via AFD/regex), análise sintática (parser LALR(1) com construção de AST), análise semântica (tabela de símbolos e checagem de tipos) e geração de código (serialização YAML). A arquitetura modular permite a extensão independente de cada fase, e o sistema de recuperação de erros em Modo Pânico garante que múltiplos problemas sejam reportados em uma única execução, melhorando significativamente a experiência do usuário final.
