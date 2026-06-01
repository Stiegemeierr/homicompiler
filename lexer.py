# =============================================================================
# lexer.py — Analisador Léxico (Scanner) da Linguagem Homi
# Utiliza o módulo ply.lex para tokenização.
# =============================================================================

import ply.lex as lex

# -----------------------------------------------------------------------------
# 1. PALAVRAS-CHAVE
# Mapeamento: texto em maiúsculas → nome do token.
# Usado para distinguir palavras-chave de entidades/identificadores.
# -----------------------------------------------------------------------------
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

# -----------------------------------------------------------------------------
# 2. LISTA DE TOKENS
# Combina as palavras-chave com os tokens dinâmicos.
# -----------------------------------------------------------------------------
tokens = (
    # --- Tokens dinâmicos ---
    'ENTIDADE',     # ex: sensor.porta_sala, light.luz_1
    'STRING',       # ex: "off", "disarmed"
    'EVENTO',       # ex: sunset, sunrise
    'TEMPO',        # ex: 10s, 5min, 01:30:00, -01:30:00
    'DOISPONTOS',   # caractere ':'
) + tuple(reserved.values())

# -----------------------------------------------------------------------------
# 3. REGRAS DE TOKENS — FUNÇÕES (ordem importa: mais específico primeiro)
# Em PLY, funções são avaliadas na ordem em que aparecem no código.
# Strings simples (t_XXXX) são avaliadas depois, da mais longa para a menor.
# -----------------------------------------------------------------------------


def t_STRING(t):
    r'"[^"]*"'
    # Captura qualquer sequência entre aspas duplas.
    # O valor armazenado mantém as aspas para facilitar a geração YAML posterior.
    return t


def t_TEMPO(t):
    r'-?\d{1,2}:\d{2}:\d{2}|\d+min|\d+s'
    # Três formatos aceitos (em ordem de alternância):
    #   1) [-]HH:MM:SS  — offset de tempo com sinal opcional (ex: -01:30:00)
    #   2) Nmin         — minutos (ex: 5min)
    #   3) Ns           — segundos (ex: 10s)
    return t


def t_ENTIDADE(t):
    r'[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*'
    # Padrão de identificadores do Home Assistant:
    #   domínio.nome_da_entidade
    # Cada parte começa com letra minúscula, seguida de letras, dígitos ou '_'.
    # O ponto (.) separa domínio de nome.
    #
    # IMPORTANTE: Antes de devolver, verifica se o texto completo (sem o ponto)
    # NÃO casa com uma palavra-chave. Entidades sempre possuem um ponto.
    return t


def t_EVENTO(t):
    r'sunset|sunrise'
    # Eventos conhecidos. Expandir esta alternância conforme a linguagem evoluir.
    return t


def t_DOISPONTOS(t):
    r':'
    # Captura o ':' que aparece após GATILHO, CONDICAO e ACAO.
    return t


def t_PALAVRA(t):
    r'[A-Za-z_][A-Za-z0-9_]*'
    # Captura qualquer sequência alfanumérica.
    # Se estiver no dicionário de palavras-chave, retorna o token correto.
    # Caso contrário, é um erro léxico (identificadores genéricos não são
    # parte da linguagem Homi nesta versão).
    t.type = reserved.get(t.value, 'EVENTO')
    # Se não for reservada, trata como EVENTO genérico (para extensibilidade).
    # Caso deseje rejeitar palavras desconhecidas, troque por um t_error.
    return t


# -----------------------------------------------------------------------------
# 4. REGRAS SIMPLES — IGNORAR ESPAÇOS E RASTREAR LINHAS
# -----------------------------------------------------------------------------

# Ignora espaços em branco e tabulações (não geram tokens).
t_ignore = ' \t'


def t_COMENTARIO(t):
    r'\#.*'
    # Ignora linhas de comentário iniciadas com '#'.
    pass  # Não retorna nada → token descartado.


def t_newline(t):
    r'\n+'
    # Rastreia quebras de linha para reporte preciso de erros.
    t.lexer.lineno += len(t.value)


# -----------------------------------------------------------------------------
# 5. TRATAMENTO DE ERROS
# -----------------------------------------------------------------------------

def t_error(t):
    """
    Chamado quando o lexer encontra um caractere que não casa com nenhuma regra.
    Imprime o caractere ilegal, sua linha, e avança o ponteiro em 1.
    """
    print(
        f"[ERRO LÉXICO] Caractere ilegal '{t.value[0]}' "
        f"na linha {t.lineno}, posição {t.lexpos}"
    )
    t.lexer.skip(1)


# -----------------------------------------------------------------------------
# 6. CONSTRUÇÃO DO LEXER
# -----------------------------------------------------------------------------

lexer = lex.lex()


# =============================================================================
# 7. TESTES EMBUTIDOS
# =============================================================================

if __name__ == '__main__':

    # Código de exemplo extraído diretamente de definicao.md (seção 3).
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
    print("  ANALISADOR LÉXICO — Linguagem Homi")
    print("=" * 70)
    print()
    print("Código de entrada:")
    print("-" * 70)
    print(codigo_exemplo)
    print("-" * 70)
    print()

    # Alimenta o lexer com o código de exemplo.
    lexer.input(codigo_exemplo)

    # Cabeçalho da tabela de tokens.
    print(f"{'Token':<15} {'Valor':<35} {'Linha':<8} {'Posição':<8}")
    print("-" * 70)

    # Itera sobre todos os tokens reconhecidos.
    while True:
        tok = lexer.token()
        if not tok:
            break
        print(f"{tok.type:<15} {tok.value:<35} {tok.lineno:<8} {tok.lexpos:<8}")

    print()
    print("=" * 70)
    print("  Análise léxica concluída com sucesso.")
    print("=" * 70)
