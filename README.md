# Compilador Homi

Um compilador construído em Python que traduz a linguagem Homi para arquivos de automação YAML do Home Assistant.

## Ordem de Execução (Pipeline)

O compilador opera nas seguintes fases, em ordem:
1. **`fase1_lexer.py`** (Analisador Léxico)
2. **`fase2_parser.py`** (Analisador Sintático)
3. **`fase3_semantic.py`** (Analisador Semântico)
4. **`fase4_codegen.py`** (Gerador de Código YAML)

## Pré-requisitos

Este projeto utiliza a biblioteca **PLY (Python Lex-Yacc)** para análise léxica e sintática. Para instalar as dependências, execute:

```bash
pip install -r requirements.txt
```

## Como Executar

Para compilar um arquivo de teste padrão (`exemplo.homi`), você pode utilizar o **Makefile**:

```bash
make run
```

Ou rodar manualmente apontando para um arquivo de entrada e especificando o arquivo de saída:

```bash
python main.py exemplo.homi -o output.yaml
```

## Limpeza

Para remover arquivos gerados temporariamente (como cache, e código YAML gerado), utilize:

```bash
make clean
```
