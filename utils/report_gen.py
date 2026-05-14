import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from datetime import datetime


def _create_heatmap(self, df):
    plt.figure(figsize=(12, 8))
    pivot = df.pivot_table(
        index="target_name", columns="sensitivity_level", aggfunc="size", fill_value=0
    )
    sns.heatmap(pivot, annot=True, cmap="YlOrRd", fmt="d")
    plt.title("Mapa de Calor - Concentração de Dados Sensíveis por Destino")
    plt.tight_layout()
    plt.savefig("heatmap_sensibilidade.png")


def create_risk_heatmap(df):
    plt.figure(figsize=(10, 6))
    # Criamos uma matriz de contagem
    pivot = (
        df.groupby(["target_name", "sensitivity_level"]).size().unstack(fill_value=0)
    )

    # Cores: Verde (Baixo) -> Amarelo (Médio) -> Vermelho (Alto)
    sns.heatmap(
        pivot, annot=True, cmap="YlOrRd", fmt="d", cbar_kws={"label": "Qtd. Achados"}
    )
    plt.title("Mapa de Calor - Exposição por Ativo")
    plt.xlabel("Nível de Sensibilidade")
    plt.ylabel("Servidor / Origem")
    plt.savefig("heatmap_risco.png")


class ReportGenerator:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def generate_comprehensive_report(self):
        engine = self.db_manager.engine
        df = pd.read_sql("SELECT * FROM audit_findings", engine)

        if df.empty:
            print("Nenhum dado encontrado para gerar relatório.")
            return

        # 1. Heatmap de Sensibilidade (Estado Atual)
        self._create_heatmap(df)

        # 2. Análise de Evolução (Timeline)
        # Agrupamos por data para ver a evolução de achados sensíveis
        df["date"] = pd.to_datetime(df["timestamp"]).dt.date
        evolution = (
            df.groupby(["date", "sensitivity_level"]).size().unstack(fill_value=0)
        )

        # 3. Exportação para Excel Multi-Abas
        file_name = f"Relatorio_Compliance_{datetime.now().strftime('%Y%m%d')}.xlsx"
        with pd.ExcelWriter(file_name, engine="openpyxl") as writer:
            # Aba Principal: Todos os achados
            df.sort_values(by="timestamp", ascending=False).to_excel(
                writer, sheet_name="Inventário Completo", index=False
            )

            # Aba de Resumo Executivo
            summary = (
                df.groupby(["target_name", "sensitivity_level"])
                .size()
                .reset_index(name="Total")
            )
            summary.to_excel(writer, sheet_name="Resumo de Riscos", index=False)

            # Aba de Evolução Temporal
            evolution.to_excel(writer, sheet_name="Evolução Temporal")

        print(f"Relatório gerado com sucesso: {file_name}")


def get_mitigation_plan(findings_df):
    recommendations = []

    # Agrupamos por tipo de violação para não repetir recomendações
    unique_violations = findings_df["pattern_detected"].unique()

    for violation in unique_violations:
        if "CPF" in violation or "SSN" in violation:
            recommendations.append(
                {
                    "Violação": violation,
                    "Risco": "Identificação direta de pessoa natural (Alta Severidade)",
                    "Ação Recomendada": "Aplicar técnicas de Anonimização ou Hashing. Restringir acesso apenas a usuários com necessidade de negócio (Least Privilege).",
                    "Prioridade": "CRÍTICA",
                }
            )
        elif "EMAIL" in violation:
            recommendations.append(
                {
                    "Violação": violation,
                    "Risco": "Comunicação não autorizada ou vazamento de base de marketing",
                    "Ação Recomendada": "Criptografia da coluna de e-mail e revisão de logs de acesso (Auditoria).",
                    "Prioridade": "ALTA",
                }
            )
        elif "ML_DETECTED" in violation:
            recommendations.append(
                {
                    "Violação": "Identificado via Machine Learning",
                    "Risco": "Contexto sugere dados sensíveis não estruturados",
                    "Ação Recomendada": "Revisão manual por analista de privacidade e classificação formal do banco de dados.",
                    "Prioridade": "MÉDIA",
                }
            )

    return pd.DataFrame(recommendations)
