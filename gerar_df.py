import pandas as pd
import locale

# Ajustar locale para datas/valores (opcional, ignora erro se não suportado)
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except:
    pass

# Google Sheets
sheet_id = "1wn-_rJGaDBLPlAvfl_EGbZomxJWzzSbkmWGzFkIr_ZI"
sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid="

sheets = {
    "geclin": "1693925870",
    "tasy": "1802097687",
    "unidades": "1239341339",
    "classificacao": "1229723085",
    "convenios_especialidades": "1626985134",
    "competencia_validacao": "697188529",
    "Respostas ao formulário 1": "221347943"
}

def gerar_df_atendimentos():
    try:
        dataframes = {}
        for name, gid in sheets.items():
            url = sheet_url + gid
            df = pd.read_csv(url)
            dataframes[f"df_{name}"] = df

        df_convenios_especialidades = dataframes["df_convenios_especialidades"]

        # GECLIN
        df_geclin = dataframes["df_geclin"]
        df_geclin = df_geclin[df_geclin["Estado"] == "Finalizado"]
        df_geclin["Data Atendimento"] = pd.to_datetime(
            df_geclin["Data Atendimento"], dayfirst=True, errors="coerce"
        ).dt.normalize()
        df_geclin['Nota Clínica'] = None
        df_geclin['base'] = 'GECLIN'
        df_geclin['Procedimento'] = df_geclin['Procedimento'].str.split(" - ").str[0]
        df_geclin['Procedimento'] = pd.to_numeric(
            df_geclin['Procedimento'], errors='coerce'
        ).astype('Int64')
        df_geclin = df_geclin.rename(columns={'Estado': 'Status'})

        # TASY
        df = dataframes["df_tasy"]
        df['Convênio'] = 'UNIMED'
        df = df[df['Status'] == "Executada"]
        df_tasy = df[[
            'Data Evolução', 'Classificação', 'Paciente',
            'Convênio', 'Profissional Evolução', 'Especialidade',
            'Cód Procedimento', 'Status', 'Nota Clínica'
        ]].copy()
        df_tasy['base'] = 'TASY'
        df_tasy['Data Evolução'] = pd.to_datetime(
            df_tasy['Data Evolução'], format="%d/%m/%Y", errors='coerce'
        )
        df_tasy = df_tasy[df_tasy['Nota Clínica'].str.contains("Acoolher|Evolução", case=False, na=False)]
        df_tasy['Classificação'] = df_tasy['Classificação'].str.split(" - ").str[0]
        df_tasy = df_tasy.rename(columns={
            'Data Evolução': 'Data Atendimento',
            'Classificação': 'Unidade',
            'Profissional Evolução': 'Profissional',
            'Cód Procedimento': 'Procedimento'
        })

        # Remover possíveis colunas duplicadas
        for df in [df_geclin, df_tasy]:
            if 'Valor à receber' in df.columns:
                df.drop(columns=['Valor à receber'], inplace=True)

        # Unir bases
        df_atendimentos = pd.concat([df_geclin, df_tasy], ignore_index=True)

        # Merge com valores fixos
        if 'valor fixo' not in df_convenios_especialidades.columns:
            raise ValueError("Coluna 'valor fixo' não encontrada")

        df_atendimentos = df_atendimentos.merge(
            df_convenios_especialidades[['convênio', 'evento', 'valor fixo']],
            left_on=['Convênio', 'Procedimento'],
            right_on=['convênio', 'evento'],
            how='left'
        )
        df_atendimentos['Valor à Receber'] = df_atendimentos['valor fixo'].fillna(0)

        # Tratamento para convênio com evento nulo
        mask = (df_atendimentos['Valor à Receber'] == 0) & (df_atendimentos['convênio'].notna())
        if mask.any():
            df_convenios_nan = df_convenios_especialidades[
                df_convenios_especialidades['evento'].isna()
            ][['convênio', 'valor fixo']].rename(columns={'valor fixo': 'valor_fixo_conv'})

            temp_df = df_atendimentos.loc[mask].merge(
                df_convenios_nan,
                left_on='Convênio',
                right_on='convênio',
                how='left'
            )
            df_atendimentos.loc[mask, 'Valor à Receber'] = temp_df['valor_fixo_conv'].fillna(0)

        df_atendimentos['Valor à Receber'] = pd.to_numeric(
            df_atendimentos['Valor à Receber'], errors='coerce'
        ).fillna(0)

        df_atendimentos = df_atendimentos.drop(
            columns=['convênio', 'evento', 'valor fixo'], errors='ignore'
        )

        return df_atendimentos

    except Exception as e:
        print(f"Erro ao gerar df_atendimentos: {e}")
        return pd.DataFrame()
