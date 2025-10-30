import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- Configuração da Página ---
st.set_page_config(
    page_title="Eco Lar | Calculadora de Consumo",
    page_icon="🏠",
    layout="wide"
)

# --- BASE DE DADOS INTERNA (CEMIG ND-5.1) ---
APARELHOS = {
    "Cozinha 🍳": {
        "Geladeira Comum (1 porta)": {"potencia_w": 250, "horas_default": 24.0},
        "Geladeira Duplex (2 portas)": {"potencia_w": 300, "horas_default": 24.0},
        "Freezer Vertical Pequeno": {"potencia_w": 300, "horas_default": 24.0},
        "Freezer Horizontal Médio": {"potencia_w": 400, "horas_default": 24.0},
        "Freezer Horizontal Grande": {"potencia_w": 500, "horas_default": 24.0},
        "Micro-ondas": {"potencia_w": 750, "horas_default": 0.3},
        "Forno Elétrico de Embutir": {"potencia_w": 4500, "horas_default": 1.0},
        "Fogão com Acendedor": {"potencia_w": 90, "horas_default": 0.1},
        "Air Fryer (similar Assadeira)": {"potencia_w": 1400, "horas_default": 0.5},
        "Máquina de Lavar Louça": {"potencia_w": 1500, "horas_default": 1.0},
        "Liquidificador Doméstico": {"potencia_w": 200, "horas_default": 0.1},
        "Batedeira de Bolo": {"potencia_w": 100, "horas_default": 0.1},
        "Espremedor de Frutas": {"potencia_w": 200, "horas_default": 0.1},
        "Cafeteira Elétrica Pequena": {"potencia_w": 600, "horas_default": 0.2},
        "Sanduicheira / Grill": {"potencia_w": 1200, "horas_default": 0.2},
        "Panela Elétrica": {"potencia_w": 1200, "horas_default": 1.0},
        "Exaustor / Coifa": {"potencia_w": 150, "horas_default": 1.0},
        "Ebulidor": {"potencia_w": 1000, "horas_default": 0.1},
    },
    "Casa de Banho 🚿": {
        "Chuveiro Elétrico (220V)": {"potencia_w": 6000, "horas_default": 0.3},
        "Chuveiro Elétrico (127V)": {"potencia_w": 4400, "horas_default": 0.3},
        "Chuveiro 4 Estações": {"potencia_w": 6500, "horas_default": 0.3},
        "Secador de Cabelo (Grande)": {"potencia_w": 1250, "horas_default": 0.2},
        "Secador de Cabelo (Pequeno)": {"potencia_w": 700, "horas_default": 0.2},
        "Torneira Elétrica": {"potencia_w": 2000, "horas_default": 0.2},
        "Banheira de Hidromassagem": {"potencia_w": 6600, "horas_default": 1.0},
    },
    "Quarto e Sala 🛋️": {
        "Ar Condicionado (10.000 BTU)": {"potencia_w": 1400, "horas_default": 8.0},
        "Ar Condicionado (18.000 BTU)": {"potencia_w": 2600, "horas_default": 8.0},
        "Aquecedor de Ambiente": {"potencia_w": 1000, "horas_default": 4.0},
        "Ventilador Médio": {"potencia_w": 200, "horas_default": 8.0},
        "Ventilador Pequeno": {"potencia_w": 70, "horas_default": 8.0},
        "Televisor Colorido (LED moderno)": {"potencia_w": 120, "horas_default": 4.0},
        "Computador (Desktop + Monitor)": {"potencia_w": 250, "horas_default": 6.0},
        "Impressora Comum": {"potencia_w": 90, "horas_default": 0.1},
        "Impressora Laser": {"potencia_w": 900, "horas_default": 0.1},
        "Scanner": {"potencia_w": 50, "horas_default": 0.1},
        "Conjunto de Som": {"potencia_w": 100, "horas_default": 2.0},
        "Console de Videojogos (moderna)": {"potencia_w": 180, "horas_default": 2.0},
    },
    "Lavandaria 🧺": {
        "Máquina de Lavar Roupa (sem aquec.)": {"potencia_w": 1000, "horas_default": 1.0},
        "Máquina de Secar Roupa (Residencial)": {"potencia_w": 1100, "horas_default": 1.5},
        "Ferro Elétrico Automático": {"potencia_w": 1000, "horas_default": 0.5},
        "Aspirador de Pó (Residencial)": {"potencia_w": 600, "horas_default": 0.2},
        "Enceradeira (Residencial)": {"potencia_w": 300, "horas_default": 0.2},
    },
    "Iluminação 💡": {
        "Lâmpada LED (9W equivalente 60W Inc.)": {"potencia_w": 9, "horas_default": 6.0},
        "Lâmpada Fluorescente (40W)": {"potencia_w": 40, "horas_default": 6.0},
        "Lâmpada Incandescente (60W)": {"potencia_w": 60, "horas_default": 6.0},
        "Lâmpada Incandescente (100W)": {"potencia_w": 100, "horas_default": 6.0},
    },
     "Outros  miscellaneous": { # Adicionado emoji para diferenciar
         "Bomba d'água (1/2 CV)": {"potencia_w": 570, "horas_default": 1.0},
         "Vaporizador": {"potencia_w": 300, "horas_default": 0.5},
     }
}

FATORES_GERAIS = {
    # "co2_fator_kwh_brasil": 0.08, # REMOVIDO CONFORME SOLICITADO
    "custo_kwh_bh": 1.05 # Custo aproximado em BH
}

# --- FUNÇÃO DE CÁLCULO ---
def calcular_impacto_total(inventario, custo_kwh, num_moradores):
    detalhes_consumo = []
    try:
        for comodo, aparelhos in inventario.items():
            for aparelho, dados in aparelhos.items():
                if dados['quantidade'] > 0:
                    # Verifica se a chave existe antes de acessar
                    if comodo in APARELHOS and aparelho in APARELHOS[comodo]:
                        potencia_w = APARELHOS[comodo][aparelho]['potencia_w']
                        horas_dia = dados['horas_dia']
                        quantidade = dados['quantidade']

                        # Ajustes específicos
                        if "Chuveiro Elétrico" in aparelho:
                            horas_dia *= num_moradores # Multiplica pelo número de moradores

                        kwh_diario = (potencia_w * horas_dia * quantidade) / 1000
                        kwh_mensal = kwh_diario * 30

                        detalhes_consumo.append({
                            "Aparelho": f"{aparelho.split('(')[0]} ({comodo.split(' ')[0]})", # Nome mais curto
                            "Consumo Mensal (kWh)": kwh_mensal
                        })
                    else:
                        st.warning(f"Aparelho '{aparelho}' no cômodo '{comodo}' não encontrado na base de dados. Verifique a consistência.")

        if not detalhes_consumo:
            st.warning("Nenhum aparelho foi selecionado. Adicione aparelhos ao inventário para calcular o consumo.")
            return None # Retorna None se nada foi calculado

        df_detalhes = pd.DataFrame(detalhes_consumo)
        total_kwh_mensal = df_detalhes["Consumo Mensal (kWh)"].sum()
        custo_total_mensal = total_kwh_mensal * custo_kwh
        # co2_total_anual = (total_kwh_mensal * 12) * FATORES_GERAIS["co2_fator_kwh_brasil"] # REMOVIDO

        return {
            "kwh_mensal": total_kwh_mensal,
            "custo_mensal": custo_total_mensal,
            # "co2_anual": co2_total_anual, # REMOVIDO
            "detalhes": df_detalhes
        }
    except Exception as e:
        st.error(f"Erro durante o cálculo: {e}")
        return None # Retorna None em caso de erro

# --- FUNÇÃO PARA MOSTRAR A TELA DE INVENTÁRIO ---
# (Esta é a versão correta da função, com o erro do 'step' corrigido)
def mostrar_tela_inventario():
    st.header("📝 Faça o Inventário da sua Casa")

    col1, col2 = st.columns([1, 3])
    with col1:
         # Usar session_state para lembrar o valor anterior ou usar default
         num_moradores_default = st.session_state.get('num_moradores_final', 2)
         num_moradores = st.number_input("Número de moradores:", 1, 10, num_moradores_default)

         custo_kwh_default = st.session_state.get('custo_kwh_final', FATORES_GERAIS["custo_kwh_bh"])
         custo_kwh = st.number_input("Custo do kWh (R$)", 0.0, 5.0, custo_kwh_default, format="%.2f", help="Valor em Reais (R$) da tarifa por kWh cobrada pela sua distribuidora.")
    with col2:
        st.info("Preencha a quantidade (Qtd.) e o tempo médio de uso diário (h : min) de cada aparelho.")

    st.markdown("---")

    inventario_inputs = {}
    inventario_anterior = st.session_state.get('inventario_final', {}) # Carregar inventário anterior

    # --- Loop Principal para Cômodos e Aparelhos ---
    for comodo, aparelhos in APARELHOS.items():
        st.subheader(comodo)
        inventario_inputs[comodo] = {}

        # Listar cada aparelho verticalmente
        for aparelho, detalhes in aparelhos.items():
            
            # --- Recuperar valores anteriores ou usar default ---
            qtd_anterior = inventario_anterior.get(comodo, {}).get(aparelho, {}).get('quantidade', 0)
            horas_dia_anterior = inventario_anterior.get(comodo, {}).get(aparelho, {}).get('horas_dia', detalhes['horas_default'])
            
            h_anterior = int(horas_dia_anterior)
            min_anterior = int(round((horas_dia_anterior - h_anterior) * 60)) # Arredondar minutos

            if h_anterior >= 24:
                 h_anterior = 24
                 min_anterior = 0

            # --- Layout da Linha para cada Aparelho ---
            row_cols = st.columns([
                4,   # Espaço para o nome do aparelho
                1,   # Input Quantidade
                1,   # Input Horas
                0.3, # Label 'h'
                1,   # Input Minutos
                0.5  # Label 'min'
            ])

            with row_cols[0]:
                st.markdown(f"**{aparelho}**") # Nome do aparelho na primeira coluna

            with row_cols[1]: # Quantidade
                qtd = st.number_input("Qtd", 0, 10, qtd_anterior, 1, key=f"qtd_{aparelho}", label_visibility="collapsed", help="Quantidade")

            with row_cols[2]: # Horas
                horas_input = st.number_input("H", 0, 24, h_anterior, 1, key=f"h_{aparelho}", label_visibility="collapsed", help="Horas/dia")
            
            with row_cols[3]: # Label 'h'
                st.markdown('<p style="text-align: left; margin-top: 25px;">h</p>', unsafe_allow_html=True) # Alinhado com input

            # Lógica para desabilitar minutos se horas = 24
            is_24h = (horas_input == 24)
            min_default = 0 if is_24h else min_anterior

            with row_cols[4]: # Minutos
                 # --- CORREÇÃO APLICADA AQUI ---
                 # Removido o '5' posicional, deixando apenas 'step=5'
                 minutos_input = st.number_input("Min", 0, 59, min_default, step=5, key=f"min_{aparelho}", label_visibility="collapsed", disabled=is_24h, help="Minutos/dia")
                 if is_24h:
                     minutos_input = 0 # Garante 0 se desabilitado

            with row_cols[5]: # Label 'min'
                 st.markdown('<p style="text-align: left; margin-top: 25px;">min</p>', unsafe_allow_html=True) # Alinhado com input

            # --- Fim do Layout da Linha ---

            # Calcular tempo total em horas decimais
            tempo_total_horas = horas_input + (minutos_input / 60.0)
            inventario_inputs[comodo][aparelho] = {
                'quantidade': qtd,
                'horas_dia': tempo_total_horas
            }
            
            st.divider() # Adiciona uma linha separadora fina entre os aparelhos

    st.markdown("---") # Divisor antes do botão

    # Botão Calcular
    if st.button("Calcular Impacto e Ver Resultados 📊", use_container_width=True, type="primary"):
        st.session_state.inventario_final = inventario_inputs
        st.session_state.custo_kwh_final = custo_kwh
        st.session_state.num_moradores_final = num_moradores
        st.session_state.resultados_calculados = calcular_impacto_total(inventario_inputs, custo_kwh, num_moradores)

        if st.session_state.resultados_calculados is not None:
             st.session_state.mostrar_resultados = True
             st.rerun()

# --- FUNÇÃO PARA MOSTRAR A TELA DE RESULTADOS ---
# (Função renomeada para o nome correto)
def mostrar_tela_resultados():
    st.header("📊 Resultados do seu Consumo")

    resultados = st.session_state.get('resultados_calculados')

    if not resultados:
        st.error("Ocorreu um erro ao carregar os resultados. Por favor, volte e calcule novamente.")
        if st.button("Voltar ao Inventário 📝"):
            st.session_state.mostrar_resultados = False
            st.rerun()
        return

    # Recuperar dados
    kwh_total = resultados.get('kwh_mensal', 0)
    custo_total = resultados.get('custo_mensal', 0)
    df_detalhes = resultados.get('detalhes')
    # co2_anual = resultados.get('co2_anual', 0) # REMOVIDO

    # --- Métricas Principais ---
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Consumo Total Mensal", f"{kwh_total:.2f} kWh")
    with col2:
        st.metric("Custo Total Mensal", f"R$ {custo_total:.2f}")

    st.markdown("---")
    st.subheader("💡 Dicas e Principais Vilões")

    # --- Métricas de Dicas (Removido CO2) ---
    st.metric("❄️ Ar Condicionado (8h/dia)", "pode custar R$ 110/mês", help="Exemplo de custo para um aparelho de 10.000 BTU (1400W) ligado 8h/dia, com tarifa de R$ 1.05/kWh.")

    # --- Gráfico e Tabela ---
    if df_detalhes is not None and not df_detalhes.empty:
        st.subheader("Consumo Detalhado por Aparelho")
        
        # Ordenar e pegar Top 10 para o gráfico
        df_top10 = df_detalhes.sort_values(by="Consumo Mensal (kWh)", ascending=False).head(10)

        fig = go.Figure(go.Pie(
            labels=df_top10['Aparelho'],
            values=df_top10['Consumo Mensal (kWh)'],
            pull=[0.05 if i == 0 else 0 for i in range(len(df_top10))], # Destaca o maior
            textinfo='percent+label',
            hole=.3
        ))
        fig.update_layout(
            title_text="Maiores Consumidores no seu Inventário (Top 10)",
            legend_title_text="Aparelhos"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Mostrar tabela completa
        with st.expander("Ver tabela com todos os aparelhos"):
            st.dataframe(
                df_detalhes.sort_values(by="Consumo Mensal (kWh)", ascending=False), 
                use_container_width=True
            )
            
    # Botão para voltar
    st.markdown("---")
    if st.button("⬅️ Voltar e Editar Inventário", use_container_width=True):
        st.session_state.mostrar_resultados = False
        st.rerun()


# --- LÓGICA PRINCIPAL DO APP ---
st.title("🏠 Eco Lar: Calculadora de Consumo Residencial")

# Inicializar o estado da sessão se for a primeira vez
if 'mostrar_resultados' not in st.session_state:
    st.session_state.mostrar_resultados = False

# Mostrar a tela apropriada com base no estado
if st.session_state.get('mostrar_resultados', False): # Usar .get para segurança
    mostrar_tela_resultados()
else:
    mostrar_tela_inventario()
