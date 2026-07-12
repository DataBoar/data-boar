import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

from report.excel_sanitizer import excel_safe_dataframe


class ReportGenerator:
    def __init__(self, data):
        self.data = data

    def generate_report(self, output_path="report.xlsx"):
        df = pd.DataFrame(self.data)
        excel_safe_dataframe(df).to_excel(output_path, index=False)

        # Heatmap de sensibilidade
        plt.figure(figsize=(10, 6))
        sns.heatmap(
            df.pivot_table(
                index="table_name", columns="column_name", values="sensitivity_score"
            ),
            annot=True,
        )
        plt.title("Heatmap de Sensibilidade dos Dados")
        plt.savefig("heatmap.png")
