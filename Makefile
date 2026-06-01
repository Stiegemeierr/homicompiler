# =============================================================================
# Makefile — Compilador Homi
# =============================================================================

# Arquivo de teste padrao
TESTE = exemplo.homi
SAIDA = output.yaml
PYTHON = python

# ---- Regras ----

# Executa o compilador com o arquivo de teste padrao.
run:
	$(PYTHON) main.py $(TESTE) -o $(SAIDA)

# Remove arquivos gerados pelo PLY e pelo compilador.
clean:
	del /Q parser.out parsetab.py output.yaml automations_gerado.yaml 2>nul || echo Limpeza concluida.
	del /Q __pycache__\*.pyc 2>nul || echo Sem cache.

# Executa apenas o lexer para depuracao de tokens.
lex:
	$(PYTHON) lexer.py

# Executa apenas o parser para depuracao da AST.
parse:
	$(PYTHON) parser_homi.py

# Executa apenas o analisador semantico com mock.
semantic:
	$(PYTHON) semantic.py

# Executa apenas o gerador de codigo com mock.
codegen:
	$(PYTHON) codegen.py

# Mostra ajuda do compilador.
help:
	$(PYTHON) main.py --help

.PHONY: run clean lex parse semantic codegen help
