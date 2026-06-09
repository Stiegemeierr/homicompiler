# =============================================================================
# main.py — Ponto de entrada do Compilador Homi
# Pipeline: Arquivo .homi -> Lexer -> Parser -> Semantico -> Codegen -> .yaml
# =============================================================================

import sys
import argparse

from fase1_lexer import lexer
from fase2_parser import parser
from fase3_semantic import AnalisadorSemantico
from fase4_codegen import GeradorYAML


def compilar(codigo_fonte: str, arquivo_saida: str) -> bool:
    """
    Executa o pipeline completo do compilador.
    Retorna True se a compilacao foi bem-sucedida, False caso contrario.
    """

    # ---- FASE 1 & 2: Analise Lexica + Sintatica (Parser chama o Lexer) ----
    print("[1/4] Analise Lexica + Sintatica...")

    # Reseta o contador de linhas e flags antes de cada parse.
    lexer.lineno = 1
    lexer.lex_error = False
    parser.sintax_error = False

    ast = parser.parse(codigo_fonte, lexer=lexer)
    sucesso = True

    if getattr(lexer, 'lex_error', False):
        sucesso = False

    if getattr(parser, 'sintax_error', False):
        sucesso = False

    if ast is None:
        sucesso = False
        print("[ERRO FATAL] Falha critica na analise sintatica. AST nao gerada.")
        ast = []  # Permite que o analisador semantico rode vazio sem quebrar
    else:
        print(f"      -> {len(ast)} automacao(oes) encontrada(s).")

    # ---- FASE 3: Analise Semantica ----
    print("[2/4] Analise Semantica...")

    analisador = AnalisadorSemantico()
    sem_erros = analisador.analisar(ast)

    # Exibe a Tabela de Simbolos para depuracao.
    analisador.imprimir_tabela_simbolos()

    if not sem_erros:
        sucesso = False
        print()
        analisador.imprimir_relatorio()
        print()
        print("[ERRO] Erros semanticos encontrados.")
    else:
        print("      -> Nenhum erro semantico.")

    if not sucesso:
        print()
        print("[ERRO FATAL] Foram encontrados erros nas etapas anteriores.")
        print("Compilacao abortada. A geracao de codigo YAML foi desativada.")
        return False

    # ---- FASE 4: Geracao de Codigo YAML ----
    print("[3/4] Geracao de Codigo YAML...")

    gerador = GeradorYAML(ast)
    gerador.gerar()

    # ---- EXPORTACAO ----
    print(f"[4/4] Salvando arquivo de saida: {arquivo_saida}")

    gerador.salvar_arquivo(arquivo_saida)

    return True


def main():
    """Configura argparse e executa o pipeline do compilador."""

    # ---- ARGUMENTOS DE LINHA DE COMANDO ----
    arg_parser = argparse.ArgumentParser(
        prog='homicompiler',
        description='Compilador da linguagem Homi para Home Assistant YAML.',
        epilog='Exemplo: python main.py script.homi -o saida.yaml',
    )

    arg_parser.add_argument(
        'entrada',
        type=str,
        help='Caminho para o arquivo .homi de entrada.',
    )

    arg_parser.add_argument(
        '-o', '--output',
        type=str,
        default='output.yaml',
        help='Caminho para o arquivo YAML de saida (padrao: output.yaml).',
    )

    args = arg_parser.parse_args()

    # ---- LEITURA DO ARQUIVO DE ENTRADA ----
    print("=" * 70)
    print("  COMPILADOR HOMI -> HOME ASSISTANT YAML")
    print("=" * 70)
    print()

    try:
        with open(args.entrada, 'r', encoding='utf-8') as f:
            codigo_fonte = f.read()
    except FileNotFoundError:
        print(f"[ERRO] Arquivo nao encontrado: '{args.entrada}'")
        print("Verifique o caminho e tente novamente.")
        sys.exit(1)
    except PermissionError:
        print(f"[ERRO] Sem permissao para ler o arquivo: '{args.entrada}'")
        sys.exit(1)

    print(f"Arquivo de entrada: {args.entrada}")
    print(f"Arquivo de saida:   {args.output}")
    print()

    # ---- PIPELINE ----
    sucesso = compilar(codigo_fonte, args.output)

    print()
    if sucesso:
        print("=" * 70)
        print("  Compilacao concluida com sucesso!")
        print("=" * 70)
        sys.exit(0)
    else:
        print("=" * 70)
        print("  Compilacao finalizada com erros.")
        print("=" * 70)
        sys.exit(1)


if __name__ == '__main__':
    main()
