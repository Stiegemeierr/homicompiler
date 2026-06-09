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
	$(PYTHON) fase1_lexer.py

# Executa apenas o parser para depuracao da AST.
parse:
	$(PYTHON) fase2_parser.py

# Executa apenas o analisador semantico com mock.
semantic:
	$(PYTHON) fase3_semantic.py

# Executa apenas o gerador de codigo com mock.
codegen:
	$(PYTHON) fase4_codegen.py

# Mostra ajuda do compilador.
help:
	$(PYTHON) main.py --help

.PHONY: run clean lex parse semantic codegen help
