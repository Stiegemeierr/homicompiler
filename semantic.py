# =============================================================================
# semantic.py — Analisador Semântico da Linguagem Homi
# Percorre a AST gerada pelo parser usando o padrão Visitor,
# mantém uma Tabela de Símbolos e aplica regras de validação de tipos.
# =============================================================================


class AnalisadorSemantico:
    """
    Visitor que percorre a AST (lista de dicionários de automação)
    e executa duas responsabilidades principais:

    1. Tabela de Símbolos — registra cada entidade encontrada com seu domínio.
    2. Checagem de Tipos  — valida se ações LIGAR/DESLIGAR são aplicadas
       apenas a domínios atuadores (light, switch, fan, cover, etc.).

    Erros são acumulados (nunca aborta) e reportados ao final da análise.
    """

    # Domínios do Home Assistant que aceitam ações de estado (turn_on/turn_off).
    DOMINIOS_ATUADORES = {
        'light', 'switch', 'fan', 'cover', 'lock',
        'media_player', 'climate', 'vacuum', 'script',
        'automation', 'input_boolean', 'scene',
    }

    # Domínios de leitura — não aceitam LIGAR/DESLIGAR.
    DOMINIOS_SENSORES = {
        'sensor', 'binary_sensor', 'weather', 'sun',
        'device_tracker', 'zone', 'person',
    }

    def __init__(self):
        # Tabela de Símbolos: {entidade_completa: domínio}
        # Ex: {'light.sala': 'light', 'sensor.temp': 'sensor'}
        self.tabela_simbolos = {}

        # Lista de erros semânticos acumulados durante a análise.
        self.erros = []

    # -----------------------------------------------------------------
    # UTILITÁRIOS
    # -----------------------------------------------------------------

    def _extrair_dominio(self, entidade: str) -> str:
        """Extrai o domínio (parte antes do ponto) de uma entidade."""
        return entidade.split('.')[0]

    def _registrar_entidade(self, entidade: str):
        """Registra a entidade na Tabela de Símbolos se ainda não existir."""
        if entidade not in self.tabela_simbolos:
            dominio = self._extrair_dominio(entidade)
            self.tabela_simbolos[entidade] = dominio

    def _adicionar_erro(self, automacao_nome: str, mensagem: str):
        """Acumula um erro semântico (nunca aborta a execução)."""
        self.erros.append({
            'automacao': automacao_nome,
            'mensagem':  mensagem,
        })

    # -----------------------------------------------------------------
    # VISITOR — Ponto de entrada
    # -----------------------------------------------------------------

    def analisar(self, ast: list) -> bool:
        """
        Percorre toda a AST. Retorna True se nenhum erro for encontrado,
        False caso contrário. Erros ficam em self.erros.
        """
        for automacao in ast:
            self._visitar_automacao(automacao)

        return len(self.erros) == 0

    # -----------------------------------------------------------------
    # VISITOR — Nós da AST
    # -----------------------------------------------------------------

    def _visitar_automacao(self, no: dict):
        """Visita um nó de automação e despacha para seus sub-blocos."""
        nome = no.get('nome', '<sem nome>')

        # Pula automações que tiveram erro sintático no parser.
        if no.get('tipo') == 'automacao_com_erro':
            return

        # Visita cada bloco.
        for gatilho in no.get('gatilhos', []):
            self._visitar_gatilho(gatilho, nome)

        for condicao in no.get('condicoes', []):
            self._visitar_condicao(condicao, nome)

        for acao in no.get('acoes', []):
            self._visitar_acao(acao, nome)

    def _visitar_gatilho(self, no: dict, automacao_nome: str):
        """Registra entidades encontradas em gatilhos."""
        if no['tipo'] == 'gatilho_estado':
            self._registrar_entidade(no['entidade'])

        # gatilho_evento não tem entidade, nada a registrar.

    def _visitar_condicao(self, no: dict, automacao_nome: str):
        """Registra entidades encontradas em condições."""
        self._registrar_entidade(no['entidade'])

    def _visitar_acao(self, no: dict, automacao_nome: str):
        """
        Registra entidades e aplica checagem de tipos:
        LIGAR/DESLIGAR só são válidos para domínios atuadores.
        """
        if no['tipo'] in ('acao_ligar', 'acao_desligar'):
            entidade = no['entidade']
            self._registrar_entidade(entidade)
            dominio = self._extrair_dominio(entidade)

            # Checagem de tipo: sensor não aceita ações de estado.
            if dominio not in self.DOMINIOS_ATUADORES:
                verbo = 'LIGAR' if no['tipo'] == 'acao_ligar' else 'DESLIGAR'
                self._adicionar_erro(
                    automacao_nome,
                    f"Ação '{verbo}' inválida para a entidade '{entidade}'. "
                    f"O domínio '{dominio}' é de leitura e não aceita "
                    f"comandos de estado. Domínios válidos: "
                    f"{', '.join(sorted(self.DOMINIOS_ATUADORES))}."
                )

        # acao_esperar não envolve entidade — nada a validar.

    # -----------------------------------------------------------------
    # RELATÓRIO DE ERROS
    # -----------------------------------------------------------------

    def imprimir_relatorio(self):
        """Imprime um relatório amigável de todos os erros acumulados."""
        if not self.erros:
            print("[OK] Análise semântica concluída sem erros.")
            return

        print(f"[ERRO SEMÂNTICO] {len(self.erros)} erro(s) encontrado(s):")
        print("-" * 70)
        for i, erro in enumerate(self.erros, 1):
            print(f"  {i}. Automação: {erro['automacao']}")
            print(f"     -> {erro['mensagem']}")
        print("-" * 70)

    def imprimir_tabela_simbolos(self):
        """Imprime a Tabela de Símbolos para depuração."""
        print("Tabela de Símbolos:")
        print("-" * 45)
        print(f"  {'Entidade':<35} {'Domínio':<10}")
        print("-" * 45)
        for entidade, dominio in self.tabela_simbolos.items():
            print(f"  {entidade:<35} {dominio:<10}")
        print("-" * 45)


# =============================================================================
# TESTES EMBUTIDOS
# =============================================================================

if __name__ == '__main__':

    # ---- AST válida (sem erros) — replicando a saída do parser ----
    ast_valida = [
        {
            'tipo': 'automacao',
            'nome': '"Por do sol na Sala"',
            'gatilhos': [
                {'tipo': 'gatilho_evento', 'evento': 'sunset', 'offset': '-01:30:00'},
            ],
            'condicoes': [
                {'tipo': 'condicao_estado', 'entidade': 'alarm_control_panel.alarmo', 'estado': '"disarmed"'},
                {'tipo': 'condicao_estado', 'entidade': 'light.sala', 'estado': '"off"'},
            ],
            'acoes': [
                {'tipo': 'acao_ligar',    'entidade': 'light.sala'},
                {'tipo': 'acao_esperar',  'duracao': '5min'},
                {'tipo': 'acao_desligar', 'entidade': 'light.sala'},
            ],
        }
    ]

    # ---- AST com ERROS propositais ----
    ast_com_erros = [
        {
            'tipo': 'automacao',
            'nome': '"Alerta de Movimento"',
            'gatilhos': [
                {'tipo': 'gatilho_estado', 'entidade': 'binary_sensor.porta', 'estado': '"on"'},
            ],
            'condicoes': [],
            'acoes': [
                # ERRO: sensor é domínio de leitura → não pode LIGAR
                {'tipo': 'acao_ligar',    'entidade': 'sensor.movimento'},
                # ERRO: binary_sensor também é de leitura → não pode DESLIGAR
                {'tipo': 'acao_desligar', 'entidade': 'binary_sensor.porta'},
                # OK: switch é atuador válido
                {'tipo': 'acao_ligar',    'entidade': 'switch.alarme'},
            ],
        },
        {
            'tipo': 'automacao',
            'nome': '"Clima Errado"',
            'gatilhos': [
                {'tipo': 'gatilho_evento', 'evento': 'sunrise', 'offset': '00:30:00'},
            ],
            'condicoes': [
                {'tipo': 'condicao_estado', 'entidade': 'weather.casa', 'estado': '"sunny"'},
            ],
            'acoes': [
                # ERRO: weather é de leitura → não pode DESLIGAR
                {'tipo': 'acao_desligar', 'entidade': 'weather.casa'},
            ],
        }
    ]

    # =====================================================================
    # TESTE 1: AST válida (espera-se zero erros)
    # =====================================================================
    print("=" * 70)
    print("  ANALISADOR SEMÂNTICO — Linguagem Homi")
    print("=" * 70)
    print()
    print("TESTE 1: AST válida")
    print("-" * 70)

    analisador1 = AnalisadorSemantico()
    analisador1.analisar(ast_valida)
    analisador1.imprimir_tabela_simbolos()
    print()
    analisador1.imprimir_relatorio()

    # =====================================================================
    # TESTE 2: AST com erros propositais (espera-se 3 erros)
    # =====================================================================
    print()
    print("TESTE 2: AST com erros semânticos propositais")
    print("-" * 70)

    analisador2 = AnalisadorSemantico()
    analisador2.analisar(ast_com_erros)
    analisador2.imprimir_tabela_simbolos()
    print()
    analisador2.imprimir_relatorio()

    print()
    print("=" * 70)
    print("  Testes do analisador semântico concluídos.")
    print("=" * 70)
