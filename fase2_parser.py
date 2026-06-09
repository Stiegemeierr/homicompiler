# =============================================================================
# parser_homi.py — Analisador Sintático (Parser) da Linguagem Homi
# Utiliza ply.yacc para construir a AST a partir dos tokens do lexer.py.
# =============================================================================

import ply.yacc as yacc

# Importa os tokens definidos no lexer (obrigatório para o PLY).
from fase1_lexer import tokens, lexer  # noqa: F401 — 'tokens' é usado implicitamente pelo yacc

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
    '''automacao : AUTOMACAO STRING bloco_modo bloco_gatilho bloco_condicao bloco_acao FIM'''
    p[0] = {
        'tipo':      'automacao',
        'nome':      p[2],
        'modo':      p[3],
        'gatilhos':  p[4],
        'condicoes': p[5],
        'acoes':     p[6],
    }

def p_bloco_modo(p):
    '''bloco_modo : MODO IDENTIFICADOR'''
    p[0] = p[2]

def p_bloco_modo_vazio(p):
    '''bloco_modo : '''
    p[0] = 'single'


# -----------------------------------------------------------------------------
# <bloco_gatilho> ::= GATILHO DOISPONTOS <lista_gatilhos>
# -----------------------------------------------------------------------------

def p_bloco_gatilho(p):
    '''bloco_gatilho : QUANDO DOISPONTOS lista_gatilhos'''
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
    '''comando_gatilho : TRACO EVENTO TEMPO'''
    p[0] = {
        'tipo':   'gatilho_evento',
        'evento': p[2],
        'offset': p[3],
    }


def p_comando_gatilho_estado(p):
    '''comando_gatilho : TRACO ENTIDADE ESTA STRING'''
    p[0] = {
        'tipo':     'gatilho_estado',
        'entidade': p[2],
        'estado':   p[4],
    }


def p_comando_gatilho_acima(p):
    '''comando_gatilho : TRACO ENTIDADE ACIMA NUMERO'''
    p[0] = {
        'tipo':     'gatilho_numerico',
        'entidade': p[2],
        'operador': 'acima',
        'valor':    p[4],
    }


def p_comando_gatilho_abaixo(p):
    '''comando_gatilho : TRACO ENTIDADE ABAIXO NUMERO'''
    p[0] = {
        'tipo':     'gatilho_numerico',
        'entidade': p[2],
        'operador': 'abaixo',
        'valor':    p[4],
    }


def p_comando_gatilho_horario(p):
    '''comando_gatilho : TRACO HORARIO ENTRE TEMPO E TEMPO'''
    p[0] = {
        'tipo':   'gatilho_horario',
        'inicio': p[4],
        'fim':    p[6],
    }


# -----------------------------------------------------------------------------
# <bloco_condicao> ::= CONDICAO DOISPONTOS <lista_condicoes>
#                    | vazio (ε)
# Bloco opcional — automações podem não ter condições.
# -----------------------------------------------------------------------------

def p_bloco_condicao(p):
    '''bloco_condicao : SE DOISPONTOS lista_condicoes'''
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
    '''comando_condicao : TRACO ENTIDADE ESTA STRING'''
    p[0] = {
        'tipo':     'condicao_estado',
        'entidade': p[2],
        'estado':   p[4],
    }


def p_comando_condicao_acima(p):
    '''comando_condicao : TRACO ENTIDADE ACIMA NUMERO'''
    p[0] = {
        'tipo':     'condicao_numerica',
        'entidade': p[2],
        'operador': 'acima',
        'valor':    p[4],
    }


def p_comando_condicao_abaixo(p):
    '''comando_condicao : TRACO ENTIDADE ABAIXO NUMERO'''
    p[0] = {
        'tipo':     'condicao_numerica',
        'entidade': p[2],
        'operador': 'abaixo',
        'valor':    p[4],
    }


def p_comando_condicao_horario(p):
    '''comando_condicao : TRACO HORARIO ENTRE TEMPO E TEMPO'''
    p[0] = {
        'tipo':   'condicao_horario',
        'inicio': p[4],
        'fim':    p[6],
    }


# -----------------------------------------------------------------------------
# <bloco_acao> ::= ACAO DOISPONTOS <lista_acoes>
# -----------------------------------------------------------------------------

def p_bloco_acao(p):
    '''bloco_acao : FACA DOISPONTOS lista_acoes'''
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
    '''comando_acao : TRACO LIGAR ENTIDADE'''
    p[0] = {
        'tipo':     'acao_ligar',
        'entidade': p[3],
    }


def p_comando_acao_desligar(p):
    '''comando_acao : TRACO DESLIGAR ENTIDADE'''
    p[0] = {
        'tipo':     'acao_desligar',
        'entidade': p[3],
    }


def p_comando_acao_esperar(p):
    '''comando_acao : TRACO ESPERAR TEMPO'''
    p[0] = {
        'tipo':     'acao_esperar',
        'duracao':  p[3],
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
    parser.sintax_error = True
    p[0] = {
        'tipo':      'automacao_com_erro',
        'nome':      p[2],
        'modo':      'single',
        'gatilhos':  [],
        'condicoes': [],
        'acoes':     [],
    }


def p_error(p):
    """
    Chamada pelo yacc quando encontra um token inesperado.
    Implementa Modo Pânico: descarta tokens até encontrar um ponto de
    sincronização seguro (FIM, QUANDO, SE, FACA, AUTOMACAO).
    """
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

    # Descarta tokens até encontrar um ponto de sincronização.
    while True:
        tok = p.lexer.token()
        if tok is None:
            break  # EOF alcançado.
        if tok.type in sync_tokens:
            # Reinsere o token de sincronização para o parser consumir.
            parser.errok()
            parser.restart()
            # Injeta o token de volta de forma segura (one-shot).
            # A lambda é substituída pelo método original após a primeira
            # chamada, evitando loops infinitos caso o token reinjetado
            # também cause um erro.
            _original_token = parser.token
            parser.token = lambda _tok=tok, _orig=_original_token: (
                setattr(parser, 'token', _orig) or _tok
            )
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
