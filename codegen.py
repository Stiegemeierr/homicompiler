# =============================================================================
# codegen.py — Gerador de Código YAML para Home Assistant
# Converte a AST validada da linguagem Homi para o formato automations.yaml.
# =============================================================================

import time
import re
import yaml


class GeradorYAML:
    """
    Visitor que percorre a AST (lista de dicionários de automação)
    e constrói estruturas de dicionários/listas compatíveis com o
    schema de automações do Home Assistant.
    """

    def __init__(self, ast: list):
        self.ast = ast
        self.automacoes_yaml = []

    # -----------------------------------------------------------------
    # UTILITÁRIOS
    # -----------------------------------------------------------------

    @staticmethod
    def _gerar_id() -> str:
        """Gera um ID único baseado em timestamp (milissegundos)."""
        return str(int(time.time() * 1000))

    @staticmethod
    def _extrair_dominio(entidade: str) -> str:
        """Extrai o domínio (parte antes do ponto) de uma entidade."""
        return entidade.split('.')[0]

    @staticmethod
    def _limpar_string(valor: str) -> str:
        """Remove aspas duplas envolventes de uma string da AST."""
        return valor.strip('"')

    @staticmethod
    def _parsear_tempo(tempo_str: str) -> dict:
        """
        Converte uma string de tempo da linguagem Homi para o dicionário
        de delay do Home Assistant.

        Formatos aceitos:
          - '10s'        -> {hours: 0, minutes: 0, seconds: 10, milliseconds: 0}
          - '5min'       -> {hours: 0, minutes: 5, seconds: 0, milliseconds: 0}
          - '01:30:00'   -> offset string (usado em triggers, não em delay)
          - '-01:30:00'  -> offset string negativo
        """
        # Formato: Ns (segundos)
        match_s = re.match(r'^(\d+)s$', tempo_str)
        if match_s:
            return {
                'hours': 0,
                'minutes': 0,
                'seconds': int(match_s.group(1)),
                'milliseconds': 0,
            }

        # Formato: Nmin (minutos)
        match_min = re.match(r'^(\d+)min$', tempo_str)
        if match_min:
            return {
                'hours': 0,
                'minutes': int(match_min.group(1)),
                'seconds': 0,
                'milliseconds': 0,
            }

        # Formato HH:MM:SS — converte para dicionário de delay
        match_hms = re.match(r'^-?(\d{1,2}):(\d{2}):(\d{2})$', tempo_str)
        if match_hms:
            return {
                'hours': int(match_hms.group(1)),
                'minutes': int(match_hms.group(2)),
                'seconds': int(match_hms.group(3)),
                'milliseconds': 0,
            }

        # Fallback — retorna a string bruta se o formato não for reconhecido.
        return {'hours': 0, 'minutes': 0, 'seconds': 0, 'milliseconds': 0}

    # -----------------------------------------------------------------
    # GERAÇÃO — Ponto de entrada
    # -----------------------------------------------------------------

    def gerar(self) -> list:
        """Percorre a AST e retorna a lista de automações no formato HA."""
        for automacao in self.ast:
            # Pula automações que tiveram erro sintático no parser.
            if automacao.get('tipo') == 'automacao_com_erro':
                continue

            no_yaml = self._gerar_automacao(automacao)
            self.automacoes_yaml.append(no_yaml)

        return self.automacoes_yaml

    # -----------------------------------------------------------------
    # GERAÇÃO — Nó de automação
    # -----------------------------------------------------------------

    def _gerar_automacao(self, no: dict) -> dict:
        """Converte um nó de automação da AST para o formato HA."""
        return {
            'id':          self._gerar_id(),
            'alias':       self._limpar_string(no['nome']),
            'description': '',
            'triggers':    self._gerar_triggers(no.get('gatilhos', [])),
            'conditions':  self._gerar_conditions(no.get('condicoes', [])),
            'actions':     self._gerar_actions(no.get('acoes', [])),
            'mode':        'single',
        }

    # -----------------------------------------------------------------
    # GERAÇÃO — Triggers (gatilhos)
    # -----------------------------------------------------------------

    def _gerar_triggers(self, gatilhos: list) -> list:
        """Converte a lista de gatilhos da AST para triggers HA."""
        triggers = []
        for g in gatilhos:
            if g['tipo'] == 'gatilho_evento':
                # Trigger por evento solar (sunset/sunrise com offset).
                # Schema HA: {trigger: sun, event: sunset, offset: "-01:30:00"}
                triggers.append({
                    'event':   g['evento'],
                    'offset':  g['offset'],
                    'trigger': 'sun',
                })

            elif g['tipo'] == 'gatilho_estado':
                # Trigger por mudança de estado de entidade.
                # Schema HA: {trigger: state, entity_id: [...], to: [...]}
                triggers.append({
                    'entity_id': [g['entidade']],
                    'to':        [self._limpar_string(g['estado'])],
                    'trigger':   'state',
                })

        return triggers

    # -----------------------------------------------------------------
    # GERAÇÃO — Conditions (condições)
    # -----------------------------------------------------------------

    def _gerar_conditions(self, condicoes: list) -> list:
        """Converte a lista de condições da AST para conditions HA."""
        conditions = []
        for c in condicoes:
            # Schema HA: {condition: state, entity_id: ..., state: [...]}
            conditions.append({
                'condition': 'state',
                'entity_id': c['entidade'],
                'state':     [self._limpar_string(c['estado'])],
            })

        return conditions

    # -----------------------------------------------------------------
    # GERAÇÃO — Actions (ações)
    # -----------------------------------------------------------------

    def _gerar_actions(self, acoes: list) -> list:
        """Converte a lista de ações da AST para actions HA."""
        actions = []
        for a in acoes:
            if a['tipo'] == 'acao_ligar':
                dominio = self._extrair_dominio(a['entidade'])
                # Schema HA: {action: <dominio>.turn_on, data: {}, target: {entity_id: ...}}
                actions.append({
                    'action':   f"{dominio}.turn_on",
                    'metadata': {},
                    'data':     {},
                    'target': {
                        'entity_id': a['entidade'],
                    },
                })

            elif a['tipo'] == 'acao_desligar':
                dominio = self._extrair_dominio(a['entidade'])
                # Schema HA: {action: <dominio>.turn_off, data: {}, target: {entity_id: ...}}
                actions.append({
                    'action':   f"{dominio}.turn_off",
                    'metadata': {},
                    'data':     {},
                    'target': {
                        'entity_id': a['entidade'],
                    },
                })

            elif a['tipo'] == 'acao_esperar':
                # Schema HA: {delay: {hours: 0, minutes: N, seconds: N, milliseconds: 0}}
                actions.append({
                    'delay': self._parsear_tempo(a['duracao']),
                })

        return actions

    # -----------------------------------------------------------------
    # EXPORTAÇÃO YAML
    # -----------------------------------------------------------------

    def exportar_yaml(self) -> str:
        """
        Serializa a lista de automações para texto YAML formatado.
        Usa sort_keys=False para manter a ordem das chaves conforme inseridas.
        """
        if not self.automacoes_yaml:
            self.gerar()

        return yaml.dump(
            self.automacoes_yaml,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
        )

    def salvar_arquivo(self, caminho: str = 'automations_gerado.yaml'):
        """Salva o YAML gerado em um arquivo."""
        conteudo = self.exportar_yaml()
        with open(caminho, 'w', encoding='utf-8') as f:
            f.write(conteudo)
        print(f"[OK] Arquivo salvo em: {caminho}")


# =============================================================================
# TESTES EMBUTIDOS
# =============================================================================

if __name__ == '__main__':

    # AST mock — replicando exatamente a saida do parser para o exemplo
    # "Por do sol na Sala" definido em definicao.md (secao 3).
    ast_exemplo = [
        {
            'tipo': 'automacao',
            'nome': '"Por do sol na Sala"',
            'gatilhos': [
                {
                    'tipo': 'gatilho_evento',
                    'evento': 'sunset',
                    'offset': '-01:30:00',
                },
            ],
            'condicoes': [
                {
                    'tipo': 'condicao_estado',
                    'entidade': 'alarm_control_panel.alarmo',
                    'estado': '"disarmed"',
                },
                {
                    'tipo': 'condicao_estado',
                    'entidade': 'light.sala',
                    'estado': '"off"',
                },
            ],
            'acoes': [
                {'tipo': 'acao_ligar',    'entidade': 'light.sala'},
                {'tipo': 'acao_esperar',  'duracao': '5min'},
                {'tipo': 'acao_desligar', 'entidade': 'light.sala'},
            ],
        }
    ]

    print("=" * 70)
    print("  GERADOR DE CODIGO — Linguagem Homi -> Home Assistant YAML")
    print("=" * 70)
    print()

    gerador = GeradorYAML(ast_exemplo)
    yaml_gerado = gerador.exportar_yaml()

    print("YAML gerado:")
    print("-" * 70)
    print(yaml_gerado)
    print("-" * 70)

    # Salva em arquivo para inspecao.
    gerador.salvar_arquivo('automations_gerado.yaml')

    print()
    print("=" * 70)
    print("  Geracao de codigo concluida.")
    print("=" * 70)
