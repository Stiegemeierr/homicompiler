# Relatório Técnico — Compilador da Linguagem Homi para Home Assistant

---

## 1. Introdução

### 1.1. Objetivo

O presente relatório descreve o projeto e a implementação de um compilador que traduz programas escritos na linguagem procedural **Homi** para arquivos declarativos no formato **YAML**, compatíveis com o sistema de automação residencial *Home Assistant*. A linguagem Homi foi concebida como uma abstração de alto nível que permite a usuários não especialistas descreverem regras de automação doméstica — tais como acionamento de luzes, verificação de estados de sensores e temporizações — por meio de uma sintaxe imperativa em português, dispensando o conhecimento prévio do esquema YAML nativo da plataforma-alvo.

### 1.2. Ferramentas e Tecnologias

O compilador foi integralmente desenvolvido na linguagem **Python 3** e fundamenta-se nas seguintes bibliotecas:

| Biblioteca | Módulo utilizado | Papel no compilador |
|---|---|---|
| **PLY** (Python Lex-Yacc) | `ply.lex` | Especificação e geração do analisador léxico por meio de expressões regulares. |
| **PLY** (Python Lex-Yacc) | `ply.yacc` | Especificação da gramática e construção do analisador sintático ascendente LALR(1). |
| **PyYAML** | `yaml` | Serialização das estruturas de dados Python para o formato YAML de saída. |
| **Biblioteca Padrão** | `re`, `time`, `argparse`, `sys` | Processamento de expressões regulares auxiliares, geração de identificadores, tratamento de argumentos de linha de comando e controle de fluxo do processo. |

### 1.3. Arquitetura Geral do Pipeline

O compilador adota a arquitetura clássica de múltiplas fases sequenciais. O módulo `main.py` orquestra a execução do pipeline completo, conforme ilustrado a seguir:

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Arquivo     │     │  Analisador  │     │  Analisador  │     │  Analisador  │     │  Gerador de  │
│  .homi       │────▶│  Léxico      │────▶│  Sintático   │────▶│  Semântico   │────▶│  Código YAML │
│  (entrada)   │     │  (lexer.py)  │     │ (parser_     │     │ (semantic.py)│     │ (codegen.py) │
│              │     │              │     │  homi.py)    │     │              │     │              │
└──────────────┘     └──────┬───────┘     └──────┬───────┘     └──────┬───────┘     └──────┬───────┘
                            │                    │                    │                    │
                     Fluxo de             AST (dicionários     AST validada +       Arquivo .yaml
                     objetos              e listas Python)     Tabela de             (saída final)
                     LexToken                                  Símbolos
```

Cada fase comunica-se com a subsequente por meio de estruturas de dados bem definidas, garantindo a modularidade e a independência entre os estágios de compilação.

---

## 2. Definição da Gramática (GLC)

A linguagem Homi é definida por uma **Gramática Livre de Contexto** (GLC), formalmente expressa na notação BNF (Backus-Naur Form). A seguir, apresenta-se a gramática completa, na qual os **símbolos terminais** são grafados em caixa alta (correspondentes diretamente aos tokens do analisador léxico) e os **símbolos não-terminais** são delimitados por chaves angulares (`⟨ ⟩`).

### 2.1. Produções da GLC

```bnf
⟨programa⟩           ::= ⟨automacao⟩
                        | ⟨programa⟩ ⟨automacao⟩

⟨automacao⟩          ::= AUTOMACAO  STRING  ⟨bloco_modo⟩  ⟨bloco_gatilho⟩  ⟨bloco_condicao⟩  ⟨bloco_acao⟩  FIM

⟨bloco_modo⟩         ::= MODO  EVENTO
                        | ε

⟨bloco_gatilho⟩      ::= QUANDO  DOISPONTOS  ⟨lista_gatilhos⟩

⟨lista_gatilhos⟩     ::= ⟨comando_gatilho⟩
                        | ⟨lista_gatilhos⟩ ⟨comando_gatilho⟩

⟨comando_gatilho⟩    ::= TRACO  EVENTO  TEMPO
                        | TRACO  ENTIDADE  ESTA  STRING
                        | TRACO  ENTIDADE  ACIMA  NUMERO
                        | TRACO  ENTIDADE  ABAIXO  NUMERO
                        | TRACO  HORARIO  ENTRE  TEMPO  E  TEMPO

⟨bloco_condicao⟩     ::= SE  DOISPONTOS  ⟨lista_condicoes⟩
                        | ε

⟨lista_condicoes⟩    ::= ⟨comando_condicao⟩
                        | ⟨lista_condicoes⟩ ⟨comando_condicao⟩

⟨comando_condicao⟩   ::= TRACO  ENTIDADE  ESTA  STRING
                        | TRACO  ENTIDADE  ACIMA  NUMERO
                        | TRACO  ENTIDADE  ABAIXO  NUMERO
                        | TRACO  HORARIO  ENTRE  TEMPO  E  TEMPO

⟨bloco_acao⟩         ::= FACA  DOISPONTOS  ⟨lista_acoes⟩

⟨lista_acoes⟩        ::= ⟨comando_acao⟩
                        | ⟨lista_acoes⟩ ⟨comando_acao⟩

⟨comando_acao⟩       ::= TRACO  LIGAR  ENTIDADE
                        | TRACO  DESLIGAR  ENTIDADE
                        | TRACO  ESPERAR  TEMPO
```

### 2.2. Classificação dos Símbolos

**Terminais (Tokens):**

| Token | Descrição | Exemplo de lexema |
|---|---|---|
| `AUTOMACAO` | Palavra-chave de abertura de bloco | `AUTOMACAO` |
| `MODO` | Palavra-chave de definição de modo de execução | `MODO` |
| `QUANDO` | Delimitador de seção de gatilhos | `QUANDO` |
| `SE` | Delimitador de seção de condições | `SE` |
| `FACA` | Delimitador de seção de ações (aceita `FAÇA`) | `FAÇA` |
| `LIGAR` | Comando de ativação de dispositivo | `LIGAR` |
| `DESLIGAR` | Comando de desativação de dispositivo | `DESLIGAR` |
| `ESPERAR` | Comando de temporização | `ESPERAR` |
| `ESTA` | Operador de verificação de estado | `ESTA` |
| `FIM` | Palavra-chave de encerramento de bloco | `FIM` |
| `ACIMA` | Operador de comparação numérica (maior que) | `ACIMA` |
| `ABAIXO` | Operador de comparação numérica (menor que) | `ABAIXO` |
| `ENTRE` | Operador de intervalo temporal | `ENTRE` |
| `E` | Conjunção para intervalo temporal | `E` |
| `HORARIO` | Palavra-chave para gatilho/condição de horário | `HORARIO` |
| `DOISPONTOS` | Delimitador estrutural | `:` |
| `TRACO` | Marcador de item de lista | `-` |
| `ENTIDADE` | Identificador de dispositivo (domínio.nome) | `light.sala` |
| `STRING` | Literal de cadeia de caracteres | `"off"` |
| `EVENTO` | Evento geográfico/temporal ou modo de execução | `sunset`, `single` |
| `TEMPO` | Expressão de duração ou deslocamento | `5min`, `1h 2min 3s`, `-01:30:00` |
| `NUMERO` | Literal numérico inteiro | `20`, `75` |

**Não-terminais:** `⟨programa⟩`, `⟨automacao⟩`, `⟨bloco_modo⟩`, `⟨bloco_gatilho⟩`, `⟨lista_gatilhos⟩`, `⟨comando_gatilho⟩`, `⟨bloco_condicao⟩`, `⟨lista_condicoes⟩`, `⟨comando_condicao⟩`, `⟨bloco_acao⟩`, `⟨lista_acoes⟩`, `⟨comando_acao⟩`.

### 2.3. Observações sobre a Gramática

- O não-terminal `⟨bloco_condicao⟩` admite derivação para a cadeia vazia (ε), tornando o bloco de condições facultativo. Essa propriedade permite a declaração de automações que possuem apenas gatilhos e ações, sem condições restritivas.
- O não-terminal `⟨bloco_modo⟩` também admite derivação para ε, tornando a declaração de modo opcional. Quando omitido, o valor padrão `'single'` é assumido.
- As regras de `⟨lista_gatilhos⟩`, `⟨lista_condicoes⟩` e `⟨lista_acoes⟩` são definidas por recursão à esquerda, uma vez que o algoritmo LALR(1) empregado pelo PLY trata de forma nativa esse tipo de recursão sem introdução de conflitos na tabela de análise.
- A gramática não apresenta ambiguidades: cada sequência de tokens possui uma única derivação possível, dispensando a declaração de regras de precedência ou associatividade.
- O token `TRACO` (`-`) funciona como marcador de item de lista, precedendo cada gatilho, condição e ação. Isso permite uma sintaxe visual semelhante a listas em YAML/Markdown, melhorando a legibilidade.

---

## 3. Análise Léxica

### 3.1. Visão Geral

A fase de análise léxica é implementada no módulo `lexer.py` por meio da biblioteca `ply.lex`. O analisador léxico (scanner) percorre o fluxo de caracteres do código-fonte e o segmenta em uma sequência de **tokens** — as unidades léxicas mínimas com significado gramatical. Internamente, o PLY constrói um **autômato finito determinístico (AFD)** a partir das expressões regulares declaradas, percorrendo o texto de entrada da esquerda para a direita em uma única passagem.

### 3.2. Especificação dos Tokens

As regras léxicas são especificadas de duas formas complementares no PLY:

1. **Funções** (`def t_NOME(t)`): Avaliadas na ordem de declaração no arquivo-fonte (do topo à base). Utilizadas quando se necessita de lógica adicional além do simples reconhecimento de padrão.
2. **Variáveis de cadeia** (`t_NOME = r'...'`): Avaliadas após todas as funções, ordenadas automaticamente pelo comprimento decrescente da expressão regular.

A tabela a seguir enumera as expressões regulares associadas aos principais tokens:

| Token | Expressão Regular | Formato reconhecido |
|---|---|---|
| `STRING` | `r'"[^"]*"'` | Qualquer sequência delimitada por aspas duplas |
| `TEMPO` | `r'-?\d{1,2}:\d{2}:\d{2}\|(?:\d+h[ \t]*)?(?:\d+min[ \t]*)?\d+s\|(?:\d+h[ \t]*)?\d+min\|\d+h'` | Desvio `HH:MM:SS`, compostos (`1h 2min 3s`), isolados (`Nmin`, `Ns`, `Nh`) |
| `NUMERO` | `r'\d+'` | Inteiros positivos |
| `ENTIDADE` | `r'[a-z][a-z0-9_]*\.[a-z0-9][a-z0-9_]*'` | Identificador no formato `domínio.nome` |
| `EVENTO` | `r'sunset\|sunrise'` | Eventos geográficos predefinidos |
| `DOISPONTOS` | `r':'` | Caractere `:` |
| `TRACO` | `r'-'` | Caractere `-` |

### 3.3. Resolução de Palavras-Chave

A distinção entre palavras-chave e identificadores genéricos é realizada por meio de um dicionário de palavras reservadas (`reserved`). A função `t_PALAVRA`, definida com a expressão regular `r'[A-Za-z_Çç][A-Za-z0-9_Çç]*'`, captura qualquer sequência alfanumérica (incluindo caracteres com cedilha) e, em seguida, consulta o dicionário `reserved` para determinar o tipo correto do token. Caso a cadeia reconhecida não conste no dicionário, o token é classificado como `EVENTO`, permitindo extensibilidade futura da linguagem. Essa abordagem é também utilizada para aceitar valores de modo de execução como `single`, `restart` e `parallel`, que são recebidos como tokens `EVENTO`.

### 3.4. Tratamento de Elementos Descartáveis

- **Espaços e tabulações:** Ignorados silenciosamente pela atribuição `t_ignore = ' \t'`.
- **Comentários:** Linhas iniciadas por `#` são consumidas pela regra `t_COMENTARIO` (expressão regular `r'\#.*'`), que não retorna o token, descartando-o do fluxo de saída.
- **Quebras de linha:** A função `t_newline` (expressão regular `r'\n+'`) incrementa o contador de linhas `t.lexer.lineno`, utilizado para reporte preciso de erros nas fases posteriores.

### 3.5. Tratamento de Erros Léxicos

Quando o scanner encontra um caractere que não satisfaz nenhuma expressão regular registrada, a função `t_error` é invocada. Essa função emite uma mensagem diagnóstica contendo o caractere ilegal, o número da linha e a posição no fluxo de entrada, e avança o ponteiro de leitura em uma posição (`t.lexer.skip(1)`), permitindo a continuidade da análise sobre o restante do arquivo.

### 3.6. Formato de Saída

Cada token emitido pelo analisador léxico é um objeto `LexToken` da biblioteca PLY, contendo os seguintes atributos:

| Atributo | Tipo | Descrição |
|---|---|---|
| `type` | `str` | Nome do tipo de token (e.g., `'AUTOMACAO'`, `'ENTIDADE'`) |
| `value` | `str` ou `int` | Lexema original reconhecido (e.g., `'light.sala'`); tokens `NUMERO` possuem valor inteiro |
| `lineno` | `int` | Número da linha em que o token foi encontrado |
| `lexpos` | `int` | Posição absoluta (índice) do início do token na cadeia de entrada |

---

## 4. Análise Sintática

### 4.1. Visão Geral

A análise sintática é implementada no módulo `parser_homi.py` por meio da biblioteca `ply.yacc`. O PLY gera automaticamente um analisador sintático **ascendente** (bottom-up) do tipo **LALR(1)** — *Look-Ahead Left-to-right Rightmost derivation* com um símbolo de antecipação (*lookahead*). O algoritmo emprega tabelas de análise pré-computadas (armazenadas no arquivo `parsetab.py` gerado na primeira execução), construídas a partir da gramática livre de contexto definida pelas docstrings das funções `p_` do módulo.

### 4.2. Especificação das Regras de Produção

Cada regra de produção da GLC é mapeada para uma função Python cujo nome obedece à convenção `p_<nome_da_regra>`. A docstring da função contém a produção na notação `símbolo_cabeça : corpo`, e o corpo da função executa as **ações semânticas** que constroem incrementalmente a AST.

O parâmetro `p`, do tipo `YaccProduction`, comporta-se como um vetor indexado:
- `p[0]` corresponde ao lado esquerdo da produção (valor sintetizado do não-terminal).
- `p[1]`, `p[2]`, ..., `p[n]` correspondem, sequencialmente, aos símbolos do lado direito da produção.

### 4.3. Construção da Árvore Sintática Abstrata (AST)

A AST é materializada como uma hierarquia de **dicionários e listas nativas do Python**, construída durante as reduções sintáticas. Cada nó da árvore é um dicionário com uma chave discriminadora `'tipo'` que identifica a natureza do nó. A estrutura geral da AST para uma automação válida é a seguinte:

```python
[                                        # ⟨programa⟩: lista de automações
  {
    'tipo':      'automacao',            # Tipo do nó raiz
    'nome':      '"Nome da Automação"',  # Literal STRING do código-fonte
    'modo':      'single',               # Modo de execução (padrão: 'single')
    'gatilhos':  [ ... ],                # Lista de nós ⟨comando_gatilho⟩
    'condicoes': [ ... ],                # Lista de nós ⟨comando_condicao⟩ (pode ser [])
    'acoes':     [ ... ],                # Lista de nós ⟨comando_acao⟩
  }
]
```

Os nós-folha dos sub-blocos assumem os seguintes formatos:

| Tipo do nó | Chaves do dicionário |
|---|---|
| `gatilho_evento` | `tipo`, `evento`, `offset` |
| `gatilho_estado` | `tipo`, `entidade`, `estado` |
| `gatilho_numerico` | `tipo`, `entidade`, `operador`, `valor` |
| `gatilho_horario` | `tipo`, `inicio`, `fim` |
| `condicao_estado` | `tipo`, `entidade`, `estado` |
| `condicao_numerica` | `tipo`, `entidade`, `operador`, `valor` |
| `condicao_horario` | `tipo`, `inicio`, `fim` |
| `acao_ligar` | `tipo`, `entidade` |
| `acao_desligar` | `tipo`, `entidade` |
| `acao_esperar` | `tipo`, `duracao` |

### 4.4. Recuperação de Erros — Modo Pânico

O compilador implementa a técnica de **Modo Pânico** (*Panic Mode Recovery*) para assegurar a resiliência da análise sintática perante entradas malformadas. A estratégia opera em dois níveis complementares:

**Nível 1 — Regra de produção com token `error`:**

A produção `automacao : AUTOMACAO STRING error FIM` utiliza o pseudo-token `error` do PLY para capturar qualquer sequência de tokens inválidos entre o cabeçalho da automação (`AUTOMACAO STRING`) e o delimitador de encerramento (`FIM`). Ao reduzir essa regra, o parser emite uma mensagem diagnóstica e insere na AST um nó marcado com `'tipo': 'automacao_com_erro'`, cujos campos de gatilhos, condições e ações permanecem como listas vazias. Essa marcação permite que as fases subsequentes (semântica e geração de código) ignorem graciosamente a automação corrompida.

**Nível 2 — Função `p_error(p)`:**

Quando o parser encontra um token inesperado que não é capturado pela regra de erro estrutural acima, a função `p_error` é invocada. Essa função implementa a sincronização por descarte: consome tokens do fluxo léxico iterativamente por meio de chamadas a `p.lexer.token()` até localizar um **token de sincronização** pertencente ao conjunto `{'FIM', 'QUANDO', 'SE', 'FACA', 'AUTOMACAO'}`. Ao encontrá-lo, o estado de erro do parser é limpo (`parser.errok()`), o autômato é reiniciado (`parser.restart()`), e o token de sincronização é reinjetado no fluxo de análise por meio de uma substituição dinâmica do método de leitura do parser (`parser.token = lambda _tok=tok: _tok`).

Essa abordagem em dois níveis permite que o compilador reporte **múltiplos erros** em uma única passagem, prosseguindo a análise das automações subsequentes àquela que continha o erro.

---

## 5. Análise Semântica

### 5.1. Visão Geral

A análise semântica é implementada no módulo `semantic.py` por meio da classe `AnalisadorSemantico`, que emprega o padrão de projeto **Visitor** para percorrer recursivamente a AST produzida pelo parser. Enquanto as fases léxica e sintática verificam a conformidade estrutural do programa (ortografia dos tokens e ordenação gramatical), a análise semântica valida a **coerência lógica** das operações descritas no código-fonte.

### 5.2. Tabela de Símbolos

A Tabela de Símbolos é materializada como um dicionário Python (`self.tabela_simbolos`) que mapeia cada entidade encontrada no código-fonte ao seu respectivo domínio. O domínio é extraído da porção anterior ao caractere ponto (`.`) no identificador de entidade.

```
Tabela de Símbolos (exemplo):
┌───────────────────────────────────┬────────────────────┐
│ Entidade                          │ Domínio            │
├───────────────────────────────────┼────────────────────┤
│ alarm_control_panel.alarmo        │ alarm_control_panel│
│ light.sala                        │ light              │
└───────────────────────────────────┴────────────────────┘
```

O registro ocorre de forma incremental durante a visitação dos nós de gatilhos de estado, gatilhos numéricos, condições e ações. Entidades previamente registradas não são inseridas novamente, evitando duplicações.

### 5.3. Checagem de Tipos

A principal validação semântica consiste na verificação de compatibilidade entre ações e domínios de entidade. A classe `AnalisadorSemantico` declara dois conjuntos estáticos de domínios:

- **`DOMINIOS_ATUADORES`**: Conjuntos de domínios que aceitam comandos de alteração de estado (`turn_on` / `turn_off`), tais como `light`, `switch`, `fan`, `cover`, `lock`, `media_player`, `climate`, `vacuum`, `script`, `automation`, `input_boolean` e `scene`.
- **`DOMINIOS_SENSORES`**: Conjunto de domínios exclusivamente de leitura, como `sensor`, `binary_sensor`, `weather`, `sun`, `device_tracker`, `zone` e `person`.

Ao visitar um nó de ação do tipo `acao_ligar` ou `acao_desligar`, o analisador extrai o domínio da entidade-alvo e verifica se esse domínio pertence ao conjunto `DOMINIOS_ATUADORES`. Caso não pertença, um erro semântico é registrado, indicando que a operação solicitada é incompatível com a natureza do dispositivo.

### 5.4. Acúmulo de Erros

O analisador adota a estratégia de **acúmulo de erros**: a execução nunca é abortada prematuramente. Cada violação semântica detectada é acumulada em uma lista interna (`self.erros`), onde cada entrada é um dicionário contendo o nome da automação e a mensagem descritiva do erro. Ao término da visitação de toda a AST, o método `analisar` retorna um valor booleano indicando a presença ou ausência de erros.

Essa abordagem permite ao usuário corrigir múltiplos problemas em uma única iteração de compilação, melhorando significativamente a experiência de desenvolvimento.

### 5.5. Tratamento de Nós com Erro Sintático

Automações marcadas pelo parser com o tipo `'automacao_com_erro'` são silenciosamente ignoradas durante a visitação semântica. Essa decisão de projeto evita a emissão de falsos positivos decorrentes de nós cuja estrutura interna é desconhecida.

---

## 6. Geração de Código

### 6.1. Visão Geral

A geração de código é implementada no módulo `codegen.py` por meio da classe `GeradorYAML`, que percorre a AST validada e constrói estruturas de dicionários e listas compatíveis com o esquema oficial de automações do *Home Assistant*. A saída final é serializada em formato YAML pela biblioteca PyYAML e gravada em disco.

### 6.2. Estratégia de Tradução

O gerador opera como um **Visitor** que mapeia cada categoria de nó da AST para a representação correspondente no esquema YAML do *Home Assistant*. A tradução segue as seguintes regras de mapeamento:

**Nó `automacao` → Objeto raiz da automação:**

| Chave AST | Chave YAML gerada | Descrição |
|---|---|---|
| `nome` | `alias` | Nome da automação (aspas removidas) |
| — | `id` | Identificador único gerado via `time.time() * 1000` |
| — | `description` | Campo vazio (string vazia) |
| `gatilhos` | `triggers` | Lista de gatilhos traduzidos |
| `condicoes` | `conditions` | Lista de condições traduzidas |
| `acoes` | `actions` | Lista de ações traduzidas |
| `modo` | `mode` | Modo de execução (ex: `single`, `restart`; padrão: `single`) |

**Nó `gatilho_evento` → Trigger solar:**
```yaml
- event: sunset          # Atributo 'evento' da AST
  offset: "-01:30:00"    # Atributo 'offset' da AST
  trigger: sun           # Tipo fixo: 'sun'
```

**Nó `gatilho_estado` → Trigger de mudança de estado:**
```yaml
- entity_id:
  - light.sala           # Atributo 'entidade', envelopado em lista
  to:
  - "off"                # Atributo 'estado' (aspas removidas), envelopado em lista
  trigger: state         # Tipo fixo: 'state'
```

**Nó `gatilho_numerico` → Trigger de estado numérico:**
```yaml
- trigger: numeric_state
  entity_id:
  - sensor.temperatura   # Atributo 'entidade', envelopado em lista
  above: 25              # ou 'below: 10', conforme o operador
```

**Nó `gatilho_horario` → Trigger de horário:**
```yaml
- trigger: time
  at: "18:00:00"         # Atributo 'inicio' da AST
```

**Nó `condicao_estado` → Condição de estado:**
```yaml
- condition: state       # Tipo fixo: 'state'
  entity_id: light.sala  # Atributo 'entidade'
  state:
  - "off"                # Atributo 'estado' (aspas removidas)
```

**Nó `condicao_numerica` → Condição de estado numérico:**
```yaml
- condition: numeric_state
  entity_id: sensor.temp # Atributo 'entidade'
  above: 25              # ou 'below: 10', conforme o operador
```

**Nó `condicao_horario` → Condição de horário:**
```yaml
- condition: time
  after: "18:00:00"      # Atributo 'inicio'
  before: "06:00:00"     # Atributo 'fim'
```

**Nó `acao_ligar` / `acao_desligar` → Chamada de serviço:**
```yaml
- action: light.turn_on  # Concatenação: domínio + '.turn_on' ou '.turn_off'
  metadata: {}
  data: {}
  target:
    entity_id: light.sala  # Atributo 'entidade'
```

**Nó `acao_esperar` → Atraso temporal:**
```yaml
- delay:
    hours: 0
    minutes: 5           # Valor convertido pelo método _parsear_tempo
    seconds: 0
    milliseconds: 0
```

### 6.3. Conversão de Grandezas Temporais

O método `_parsear_tempo` realiza a tradução de expressões temporais simplificadas da linguagem Homi para o dicionário de atraso (*delay*) nativo do *Home Assistant*. A conversão emprega expressões regulares para identificar o formato de entrada:

| Formato de entrada | Método de extração | Exemplo de conversão |
|---|---|---|
| `HH:MM:SS` | `re.match(r'^-?(\d{1,2}):(\d{2}):(\d{2})$')` | `'01:30:00'` → `{hours: 1, minutes: 30, seconds: 0, milliseconds: 0}` |
| Composto (`NhNminNs`) | `re.search` para cada componente | `'1h 2min 3s'` → `{hours: 1, minutes: 2, seconds: 3, milliseconds: 0}` |
| `Nmin Ns` | `re.search` para `min` e `s` | `'1min 45s'` → `{hours: 0, minutes: 1, seconds: 45, milliseconds: 0}` |
| `Ns` (segundos) | `re.search(r'(\d+)s')` | `'10s'` → `{hours: 0, minutes: 0, seconds: 10, milliseconds: 0}` |
| `Nmin` (minutos) | `re.search(r'(\d+)min')` | `'5min'` → `{hours: 0, minutes: 5, seconds: 0, milliseconds: 0}` |
| `Nh` (horas) | `re.search(r'(\d+)h')` | `'2h'` → `{hours: 2, minutes: 0, seconds: 0, milliseconds: 0}` |

### 6.4. Serialização e Exportação

A exportação final é realizada pelo método `exportar_yaml`, que invoca `yaml.dump` com os seguintes parâmetros de configuração:

- `default_flow_style=False`: Garante a serialização em formato de bloco (com indentação), em vez do formato compacto em linha.
- `sort_keys=False`: Preserva a ordem de inserção das chaves nos dicionários, mantendo o arquivo gerado em conformidade com a convenção legível do *Home Assistant* (sequência: `id`, `alias`, `triggers`, `conditions`, `actions`, `mode`).
- `allow_unicode=True`: Permite a serialização direta de caracteres Unicode (acentos e caracteres especiais) sem recorrer a sequências de escape.

O método `salvar_arquivo` grava o conteúdo YAML resultante em disco, no caminho especificado pelo argumento de linha de comando `--output` (padrão: `output.yaml`).

---

## 7. Exemplos Práticos

### 7.1. Código-Fonte Homi (Entrada)

O exemplo abaixo define uma automação denominada "Corda Corredor - movimento" que aciona a iluminação da sala uma hora e trinta minutos antes do pôr do sol, sob a condição de que o alarme esteja desarmado e a luz esteja desligada, aguarda cinco minutos e, em seguida, desativa a iluminação:

```
AUTOMACAO "Corda Corredor - movimento"
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

### 7.2. Saída da Análise Léxica (Tokens)

A tabela de tokens gerada pelo analisador léxico para o código-fonte acima é a seguinte:

| Token | Valor | Linha | Posição |
|---|---|---|---|
| `AUTOMACAO` | `AUTOMACAO` | 1 | 0 |
| `STRING` | `"Corda Corredor - movimento"` | 1 | 10 |
| `MODO` | `MODO` | 2 | 40 |
| `EVENTO` | `single` | 2 | 45 |
| `QUANDO` | `QUANDO` | 4 | 52 |
| `DOISPONTOS` | `:` | 4 | 58 |
| `TRACO` | `-` | 5 | 60 |
| `EVENTO` | `sunset` | 5 | 62 |
| `TEMPO` | `-01:30:00` | 5 | 69 |
| `SE` | `SE` | 7 | 80 |
| `DOISPONTOS` | `:` | 7 | 82 |
| `TRACO` | `-` | 8 | 84 |
| `ENTIDADE` | `alarm_control_panel.alarmo` | 8 | 86 |
| `ESTA` | `ESTA` | 8 | 113 |
| `STRING` | `"disarmed"` | 8 | 118 |
| `TRACO` | `-` | 9 | 130 |
| `ENTIDADE` | `light.sala` | 9 | 132 |
| `ESTA` | `ESTA` | 9 | 144 |
| `STRING` | `"off"` | 9 | 149 |
| `FACA` | `FAÇA` | 11 | 155 |
| `DOISPONTOS` | `:` | 11 | 159 |
| `TRACO` | `-` | 12 | 161 |
| `LIGAR` | `LIGAR` | 12 | 163 |
| `ENTIDADE` | `light.sala` | 12 | 169 |
| `TRACO` | `-` | 13 | 181 |
| `ESPERAR` | `ESPERAR` | 13 | 183 |
| `TEMPO` | `5min` | 13 | 191 |
| `TRACO` | `-` | 14 | 196 |
| `DESLIGAR` | `DESLIGAR` | 14 | 198 |
| `ENTIDADE` | `light.sala` | 14 | 207 |
| `FIM` | `FIM` | 15 | 219 |

### 7.3. Saída da Análise Sintática (AST)

A Árvore de Sintaxe Abstrata gerada pelo parser para o exemplo acima assume a seguinte forma:

```python
[
    {
        'tipo': 'automacao',
        'nome': '"Corda Corredor - movimento"',
        'modo': 'single',
        'gatilhos': [
            {
                'tipo': 'gatilho_evento',
                'evento': 'sunset',
                'offset': '-01:30:00'
            }
        ],
        'condicoes': [
            {
                'tipo': 'condicao_estado',
                'entidade': 'alarm_control_panel.alarmo',
                'estado': '"disarmed"'
            },
            {
                'tipo': 'condicao_estado',
                'entidade': 'light.sala',
                'estado': '"off"'
            }
        ],
        'acoes': [
            {'tipo': 'acao_ligar',    'entidade': 'light.sala'},
            {'tipo': 'acao_esperar',  'duracao': '5min'},
            {'tipo': 'acao_desligar', 'entidade': 'light.sala'}
        ]
    }
]
```

### 7.4. Saída da Análise Semântica (Tabela de Símbolos)

```
Tabela de Símbolos:
---------------------------------------------
  Entidade                            Domínio
---------------------------------------------
  alarm_control_panel.alarmo          alarm_control_panel
  light.sala                          light
---------------------------------------------
[OK] Análise semântica concluída sem erros.
```

### 7.5. Código YAML Gerado (Saída Final)

O arquivo YAML produzido pelo compilador contém:

```yaml
- id: '1780322493826'
  alias: Corda Corredor - movimento
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

### 7.6. Execução Completa do Compilador

A invocação do compilador pela linha de comando produz a seguinte saída:

```
$ python main.py exemplo.homi -o saida.yaml

======================================================================
  COMPILADOR HOMI -> HOME ASSISTANT YAML
======================================================================

Arquivo de entrada: exemplo.homi
Arquivo de saida:   saida.yaml

[1/4] Analise Lexica + Sintatica...
      -> 1 automacao(oes) encontrada(s).
[2/4] Analise Semantica...
Tabela de Simbolos:
---------------------------------------------
  Entidade                            Domínio
---------------------------------------------
  alarm_control_panel.alarmo          alarm_control_panel
  light.sala                          light
---------------------------------------------
      -> Nenhum erro semantico.
[3/4] Geracao de Codigo YAML...
[4/4] Salvando arquivo de saida: saida.yaml
[OK] Arquivo salvo em: saida.yaml

======================================================================
  Compilacao concluida com sucesso!
======================================================================
```

---

## 8. Considerações Finais

O compilador Homi demonstra, de forma funcional e didática, a aplicação prática dos conceitos fundamentais da teoria de compiladores: análise léxica baseada em autômatos finitos e expressões regulares, análise sintática ascendente LALR(1), construção de árvore de sintaxe abstrata por ações semânticas acopladas às reduções, análise semântica com tabela de símbolos e checagem de tipos, e geração de código-alvo por percurso da representação intermediária. A adoção da técnica de Modo Pânico na recuperação de erros sintáticos, combinada com o acúmulo de erros semânticos, confere ao sistema robustez e uma experiência de diagnóstico significativamente superior à de compiladores que interrompem a execução na primeira falha detectada.

---

*Relatório gerado para fins acadêmicos — Disciplina de Compiladores.*
