# =============================================================================
# parser_homi.py — Analisador Sintático (Parser) da Linguagem Homi
# Utiliza ply.yacc para construir a AST a partir dos tokens do lexer.py.
# =============================================================================

import ply.yacc as yacc

# Importa os tokens definidos no lexer (obrigatório para o PLY).
from lexer import tokens, lexer  # noqa: F401 — 'tokens' é usado implicitamente pelo yacc

# =============================================================================
# GRAMÁTICA — Regras de produção mapeadas da GLC (definicao.md, seção 2.B)
# =============================================================================

# -----------------------------------------------------------------------------
# <programa> ::= <automacao> | <programa> <automacao>
# O nó raiz é uma LISTA de automações.
# -----------------------------------------------------------------------------

def p_programa_unico(p):
    '''programa : automacao'''
    p[0] = [p[1]]


def p_programa_lista(p):
    '''programa : programa automacao'''
    p[0] = p[1] + [p[2]]


# -----------------------------------------------------------------------------
# <automacao> ::= AUTOMACAO STRING <bloco_gatilho> <bloco_condicao> <bloco_acao> FIM
# -----------------------------------------------------------------------------

def p_automacao(p):
    '''automacao : AUTOMACAO STRING bloco_gatilho bloco_condicao bloco_acao FIM'''
    p[0] = {
        'tipo':      'automacao',
        'nome':      p[2],
        'gatilhos':  p[3],
        'condicoes': p[4],
        'acoes':     p[5],
    }


# -----------------------------------------------------------------------------
# <bloco_gatilho> ::= GATILHO DOISPONTOS <lista_gatilhos>
# -----------------------------------------------------------------------------

def p_bloco_gatilho(p):
    '''bloco_gatilho : GATILHO DOISPONTOS lista_gatilhos'''
    p[0] = p[3]


# -----------------------------------------------------------------------------
# <lista_gatilhos> ::= <comando_gatilho>
#                    | <lista_gatilhos> <comando_gatilho>
# Acumula gatilhos em uma lista.
# -----------------------------------------------------------------------------

def p_lista_gatilhos_unico(p):
    '''lista_gatilhos : comando_gatilho'''
    p[0] = [p[1]]


def p_lista_gatilhos_lista(p):
    '''lista_gatilhos : lista_gatilhos comando_gatilho'''
    p[0] = p[1] + [p[2]]


# -----------------------------------------------------------------------------
# <comando_gatilho> ::= QUANDO EVENTO TEMPO
#                     | QUANDO ENTIDADE ESTA STRING
# Dois tipos de gatilho: por evento temporal ou por estado de entidade.
# -----------------------------------------------------------------------------

def p_comando_gatilho_evento(p):
    '''comando_gatilho : QUANDO EVENTO TEMPO'''
    p[0] = {
        'tipo':   'gatilho_evento',
        'evento': p[2],
        'offset': p[3],
    }


def p_comando_gatilho_estado(p):
    '''comando_gatilho : QUANDO ENTIDADE ESTA STRING'''
    p[0] = {
        'tipo':     'gatilho_estado',
        'entidade': p[2],
        'estado':   p[4],
    }


# -----------------------------------------------------------------------------
# <bloco_condicao> ::= CONDICAO DOISPONTOS <lista_condicoes>
#                    | vazio (ε)
# Bloco opcional — automações podem não ter condições.
# -----------------------------------------------------------------------------

def p_bloco_condicao(p):
    '''bloco_condicao : CONDICAO DOISPONTOS lista_condicoes'''
    p[0] = p[3]


def p_bloco_condicao_vazio(p):
    '''bloco_condicao : '''
    p[0] = []


# -----------------------------------------------------------------------------
# <lista_condicoes> ::= <comando_condicao>
#                     | <lista_condicoes> <comando_condicao>
# -----------------------------------------------------------------------------

def p_lista_condicoes_unico(p):
    '''lista_condicoes : comando_condicao'''
    p[0] = [p[1]]


def p_lista_condicoes_lista(p):
    '''lista_condicoes : lista_condicoes comando_condicao'''
    p[0] = p[1] + [p[2]]


# -----------------------------------------------------------------------------
# <comando_condicao> ::= SE ENTIDADE ESTA STRING
# -----------------------------------------------------------------------------

def p_comando_condicao(p):
    '''comando_condicao : SE ENTIDADE ESTA STRING'''
    p[0] = {
        'tipo':     'condicao_estado',
        'entidade': p[2],
        'estado':   p[4],
    }


# -----------------------------------------------------------------------------
# <bloco_acao> ::= ACAO DOISPONTOS <lista_acoes>
# -----------------------------------------------------------------------------

def p_bloco_acao(p):
    '''bloco_acao : ACAO DOISPONTOS lista_acoes'''
    p[0] = p[3]


# -----------------------------------------------------------------------------
# <lista_acoes> ::= <comando_acao>
#                 | <lista_acoes> <comando_acao>
# -----------------------------------------------------------------------------

def p_lista_acoes_unico(p):
    '''lista_acoes : comando_acao'''
    p[0] = [p[1]]


def p_lista_acoes_lista(p):
    '''lista_acoes : lista_acoes comando_acao'''
    p[0] = p[1] + [p[2]]


# -----------------------------------------------------------------------------
# <comando_acao> ::= LIGAR ENTIDADE
#                  | DESLIGAR ENTIDADE
#                  | ESPERAR TEMPO
# -----------------------------------------------------------------------------

def p_comando_acao_ligar(p):
    '''comando_acao : LIGAR ENTIDADE'''
    p[0] = {
        'tipo':     'acao_ligar',
        'entidade': p[2],
    }


def p_comando_acao_desligar(p):
    '''comando_acao : DESLIGAR ENTIDADE'''
    p[0] = {
        'tipo':     'acao_desligar',
        'entidade': p[2],
    }


def p_comando_acao_esperar(p):
    '''comando_acao : ESPERAR TEMPO'''
    p[0] = {
        'tipo':     'acao_esperar',
        'duracao':  p[2],
    }


# =============================================================================
# RECUPERAÇÃO DE ERROS — MODO PÂNICO
# =============================================================================

# Regra de erro no nível de automação: se a estrutura interna estiver inválida,
# descarta tokens até encontrar FIM (ponto de sincronização).
def p_automacao_erro(p):
    '''automacao : AUTOMACAO STRING error FIM'''
    print(
        f"[ERRO SINTÁTICO] Estrutura inválida na automação {p[2]}. "
        f"Recuperando no token FIM (linha {p.lineno(4)})."
    )
    p[0] = {
        'tipo':      'automacao_com_erro',
        'nome':      p[2],
        'gatilhos':  [],
        'condicoes': [],
        'acoes':     [],
    }


def p_error(p):
    """
    Chamada pelo yacc quando encontra um token inesperado.
    Implementa Modo Pânico: descarta tokens até encontrar um ponto de
    sincronização seguro (FIM, GATILHO, CONDICAO, ACAO, AUTOMACAO).
    """
    if p is None:
        print("[ERRO SINTÁTICO] Fim inesperado do arquivo (EOF).")
        return

    print(
        f"[ERRO SINTÁTICO] Token inesperado '{p.value}' "
        f"(tipo: {p.type}) na linha {p.lineno}."
    )

    # Tokens de sincronização — pontos seguros para retomar a análise.
    sync_tokens = {'FIM', 'GATILHO', 'CONDICAO', 'ACAO', 'AUTOMACAO'}

    # Descarta tokens até encontrar um ponto de sincronização.
    while True:
        tok = p.lexer.token()
        if tok is None:
            break  # EOF alcançado.
        if tok.type in sync_tokens:
            # Reinsere o token de sincronização para o parser consumir.
            parser.errok()
            parser.restart()
            parser.token = lambda _tok=tok: _tok  # Injeta o token de volta.
            break


# =============================================================================
# CONSTRUÇÃO DO PARSER
# =============================================================================

# Gera o parser LR. Os arquivos de tabela são criados na primeira execução.
parser = yacc.yacc(debug=False)


# =============================================================================
# TESTES EMBUTIDOS
# =============================================================================

if __name__ == '__main__':
    import pprint

    # Código de exemplo extraído de definicao.md (seção 3).
    codigo_exemplo = '''AUTOMACAO "Por do sol na Sala"

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
'''

    print("=" * 70)
    print("  ANALISADOR SINTÁTICO — Linguagem Homi")
    print("=" * 70)
    print()
    print("Código de entrada:")
    print("-" * 70)
    print(codigo_exemplo)
    print("-" * 70)
    print()

    # Reseta o contador de linhas do lexer antes de cada parse.
    lexer.lineno = 1

    # Executa o parser, que retorna a AST (lista de automações).
    resultado = parser.parse(codigo_exemplo, lexer=lexer)

    print("AST gerada:")
    print("-" * 70)
    pprint.pprint(resultado, width=60, sort_dicts=False)
    print()
    print("=" * 70)
    print("  Análise sintática concluída.")
    print("=" * 70)
