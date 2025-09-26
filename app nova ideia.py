import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- Configuração da Página ---
st.set_page_config(
    page_title="Eco Lar | Calculadora de Consumo",
    page_icon="🏠",
    layout="wide"
)

# --- BASE DE DADOS INTERNA ---
# Dicionário com a potência média (em Watts) de eletrodomésticos comuns.
# Fonte: Valores médios baseados em dados do Inmetro e Procel.
APARELHOS = {
    "Cozinha": {
        "Geladeira (Simples)": {"potencia_w": 150},
        "Micro-ondas": {"potencia_w": 1200},
        "Forno Elétrico": {"potencia_w": 1500},
        "Air Fryer": {"potencia_w": 1400},
        "Máquina de Lavar Louça": {"potencia_w": 1700},
        "Liquidificador": {"potencia_w": 500},
    },
    "Casa de Banho": {
        "Chuveiro Elétrico": {"potencia_w": 5500},
        "Secador de Cabelo": {"potencia_w": 1800},
    },
    "Quarto": {
        "Ar Condicionado (Janela)": {"potencia_w": 1000},
        "Ventilador de Teto": {"potencia_w": 150},
        "Televisão LED (42')": {"potencia_w": 100},
        "Computador (Desktop + Monitor)": {"potencia_w": 250},
    },
    "Sala": {
        "Televisão LED (55')": {"potencia_w": 150},
        "Home Theater / Som": {"potencia_w": 200},
        "Consola de Videojogos": {"potencia_w": 180},
    },
    "Lavandaria": {
        "Máquina de Lavar Roupa": {"potencia_w": 1000},
        "Ferro de Passar": {"potencia_w": 1200},
    },
    "Iluminação": {
        "Lâmpada LED (9W)": {"potencia_w": 9},
        "Lâmpada Incandescente (60W)": {"potencia_w": 60},
    }
}

FATORES_GERAIS = {
    "co2_fator_kwh_brasil": 0.08, # kg de CO2 por kWh
    "custo_kwh_bh": 1.05,
    "custo_m3_agua_bh": 12.50
}

# --- FUNÇÃO PRINCIPAL DE CÁLCULO ---
def calcular_impacto_total(inventario, custo_kwh):
    """Calcula o consumo, custo e CO2 para todo o inventário da casa."""
    total_kwh_mensal = 0
    detalhes_consumo = []

    for comodo, aparelhos in inventario.items():
        for aparelho, dados in aparelhos.items():
            if dados['quantidade'] > 0:
                potencia_w = APARELHOS[comodo][aparelho]['potencia_w']
                kwh_diario = (potencia_w * dados['horas_dia'] * dados['quantidade']) / 1000
                kwh_mensal = kwh_diario * 30
                
                total_kwh_mensal += kwh_mensal
                detalhes_consumo.append({
                    "Aparelho": aparelho,
                    "Cômodo": comodo,
                    "Consumo Mensal (kWh)": kwh_mensal
                })

    custo_total_mensal = total_kwh_mensal * custo_kwh
    co2_total_anual = (total_kwh_mensal * 12) * FATORES_GERAIS["co2_fator_kwh_brasil"]

    return {
        "kwh_mensal": total_kwh_mensal,
        "custo_mensal": custo_total_mensal,
        "co2_anual": co2_total_anual,
        "detalhes": pd.DataFrame(detalhes_consumo)
    }


# --- INTERFACE DO APLICATIVO (STREAMLIT) ---

st.title("🏠 Eco Lar: Calculadora de Consumo e Impacto Residencial")
st.write("Faça um inventário da sua casa para entender para onde vai a sua energia e como economizar.")

# --- BARRA LATERAL PARA INPUTS ---
inventario_casa = {}
with st.sidebar:
    st.header("📝 Faça o Inventário da sua Casa")
    
    # Inputs Gerais
    num_moradores = st.slider("Número de moradores na residência:", 1, 10, 3)
    custo_kwh = st.number_input("Custo do kWh na sua fatura (R$)", 0.0, 5.0, FATORES_GERAIS["custo_kwh_bh"], 0.01, "%.2f")

    # Inventário por Cômodo
    for comodo, aparelhos in APARELHOS.items():
        with st.expander(f"🛋️ {comodo}", expanded=(comodo == "Cozinha")):
            inventario_casa[comodo] = {}
            for aparelho in aparelhos:
                st.markdown(f"**{aparelho}**")
                cols = st.columns(2)
                inventario_casa[comodo][aparelho] = {
                    'quantidade': cols[0].number_input(f"Qtd.", min_value=0, value=0, step=1, key=f"qtd_{aparelho}"),
                    'horas_dia': cols[1].slider(f"Horas/dia", 0.0, 24.0, 1.0, 0.5, key=f"hrs_{aparelho}")
                }

# --- CÁLCULO E EXIBIÇÃO DOS RESULTADOS ---
if st.sidebar.button("Calcular Impacto!", use_container_width=True):
    
    resultados = calcular_impacto_total(inventario_casa, custo_kwh)
    
    st.header("📊 Seu Relatório Energético Personalizado")

    # Métricas Principais
    col1, col2, col3 = st.columns(3)
    col1.metric("Consumo Mensal Estimado", f"{resultados['kwh_mensal']:.0f} kWh")
    col2.metric("Custo Mensal Estimado", f"R$ {resultados['custo_mensal']:.2f}")
    col3.metric("Pegada de Carbono Anual", f"{resultados['co2_anual']:.1f} kg CO₂")
    
    st.markdown("---")
    
    # Gráfico de Breakdown
    st.subheader("De onde vem o seu consumo?")
    df_detalhes = resultados['detalhes']
    
    if not df_detalhes.empty:
        df_detalhes = df_detalhes.sort_values(by="Consumo Mensal (kWh)", ascending=False)
        
        fig = go.Figure(data=[go.Pie(
            labels=df_detalhes['Aparelho'],
            values=df_detalhes['Consumo Mensal (kWh)'],
            hole=.4,
            textinfo='label+percent',
            insidetextorientation='radial'
        )])
        fig.update_layout(
            title_text="Distribuição do Consumo por Aparelho",
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)

        # Tabela Detalhada
        with st.expander("Ver consumo detalhado por aparelho"):
            st.dataframe(df_detalhes.set_index("Aparelho"))
        
        # Dicas Personalizadas
        st.subheader("💡 Dicas para Reduzir seu Consumo")
        maior_vilao = df_detalhes.iloc[0]
        st.info(f"O seu maior consumidor de energia é **{maior_vilao['Aparelho']}**, responsável por {maior_vilao['Consumo Mensal (kWh)']:.0f} kWh/mês. Reduzir o seu uso ou trocá-lo por um modelo mais eficiente (selo Procel A) pode gerar uma grande economia.")
        
        if "Chuveiro Elétrico" in df_detalhes['Aparelho'].values:
            st.warning("**Dica para o Chuveiro:** Reduzir o tempo de banho de cada morador em apenas 5 minutos por dia pode economizar mais de R$ 50,00 por mês na sua fatura!")

    else:
        st.warning("Nenhum aparelho foi adicionado ao inventário. Preencha os dados na barra lateral para ver a análise.")

else:
    st.info("Preencha o inventário na barra lateral à esquerda e clique em 'Calcular Impacto!' para ver a sua análise personalizada.")