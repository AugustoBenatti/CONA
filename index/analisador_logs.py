import pandas as pd
import re
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from sklearn.svm import OneClassSVM
from sklearn.feature_extraction.text import TfidfVectorizer
import seaborn as sns
from datetime import datetime

class AnalisadorLogs:
    def __init__(self, root):
        self.root = root
        self.root.title("Analisador de Logs Avançado")
        self.root.geometry("1200x900")
        
        self.df_logs = None
        self.erros_detectados = None
        
        self.create_widgets()
    
    def create_widgets(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Controles
        control_frame = ttk.LabelFrame(main_frame, text="Controle")
        control_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(control_frame, text="Carregar Logs", command=self.load_logs).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Analisar Logs", command=self.analyze_logs).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Mostrar Dashboard", command=self.show_dashboard).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Exportar Relatório", command=self.export_report).pack(side=tk.LEFT, padx=5)
        
        # Abas
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Aba de logs
        self.log_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.log_tab, text="Logs")
        
        self.log_text = tk.Text(self.log_tab, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(self.log_tab, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Aba de resultados
        self.result_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.result_tab, text="Resultados")
        
        self.result_text = tk.Text(self.result_tab, wrap=tk.WORD)
        scrollbar_result = ttk.Scrollbar(self.result_tab, orient="vertical", command=self.result_text.yview)
        self.result_text.configure(yscrollcommand=scrollbar_result.set)
        
        scrollbar_result.pack(side="right", fill="y")
        self.result_text.pack(fill=tk.BOTH, expand=True)
        
        # Aba de dashboard
        self.dashboard_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.dashboard_tab, text="Dashboard")
        
        # Barra de status
        self.status_var = tk.StringVar()
        self.status_var.set("Pronto")
        ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN).pack(fill=tk.X)
    
    def load_logs(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv"), ("Text files", "*.txt"), ("All files", "*.*")],
            title="Selecione o arquivo de logs"
        )
        
        if file_path:
            try:
                self.df_logs = pd.read_csv(file_path)
                self.status_var.set(f"✅ Logs carregados: {file_path}")
                
                # Pré-processamento básico
                self.df_logs['timestamp'] = pd.to_datetime(self.df_logs['timestamp'], errors='coerce')
                self.df_logs = self.df_logs.dropna(subset=['timestamp'])
                
                self.log_text.delete(1.0, tk.END)
                sample_logs = self.df_logs.sample(min(100, len(self.df_logs)))  # Mostra apenas uma amostra para performance
                for _, row in sample_logs.iterrows():
                    self.log_text.insert(tk.END, f"{row['timestamp']} - {row['nivel']} - {row['mensagem']}\n")
                
                self.log_text.insert(tk.END, f"\n\nTotal de logs carregados: {len(self.df_logs):,}")
            except Exception as e:
                self.status_var.set(f"Erro: {str(e)}")
                messagebox.showerror("Erro", f"Falha ao carregar logs: {str(e)}")
    
    def analyze_logs(self):
        if self.df_logs is None:
            messagebox.showwarning("Aviso", "Carregue os logs primeiro!")
            return
        
        self.status_var.set("Analisando logs...")
        self.root.update()
        
        try:
            self.erros_detectados = self._detectar_erros()
            self.result_text.delete(1.0, tk.END)
            
            if not self.erros_detectados.empty:
                # Estatísticas básicas
                total_erros = len(self.erros_detectados)
                percentual = (total_erros / len(self.df_logs)) * 100
                
                self.result_text.insert(tk.END, "⚠️ RESUMO DE ERROS DETECTADOS ⚠️\n\n")
                self.result_text.insert(tk.END, f"Total de erros: {total_erros:,}\n")
                self.result_text.insert(tk.END, f"Percentual sobre total: {percentual:.2f}%\n")
                self.result_text.insert(tk.END, f"Primeira ocorrência: {self.erros_detectados['timestamp'].min()}\n")
                self.result_text.insert(tk.END, f"Última ocorrência: {self.erros_detectados['timestamp'].max()}\n\n")
                
                # Erros por tipo
                self.result_text.insert(tk.END, "📊 DISTRIBUIÇÃO DE ERROS POR TIPO:\n\n")
                padroes = {
                    'Pagamento': self.erros_detectados['mensagem'].str.contains('pagamento|cartão|bancário', case=False).sum(),
                    'Timeout': self.erros_detectados['mensagem'].str.contains('timeout', case=False).sum(),
                    'Valores': self.erros_detectados['mensagem'].str.contains('valor|desconto|total', case=False).sum(),
                    'Duplicada': self.erros_detectados['mensagem'].str.contains('duplicada', case=False).sum(),
                    'Conexão': self.erros_detectados['mensagem'].str.contains('conexão|conectar|timeout', case=False).sum()
                }
                
                for tipo, qtd in padroes.items():
                    if qtd > 0:
                        self.result_text.insert(tk.END, f"• {tipo}: {qtd} ocorrências\n")
                
                # Mostra os primeiros 50 erros para não sobrecarregar
                self.result_text.insert(tk.END, "\n🔍 PRINCIPAIS ERROS DETECTADOS:\n\n")
                for _, row in self.erros_detectados.head(50).iterrows():
                    self.result_text.insert(tk.END, f"[{row['timestamp']}] {row['nivel']}: {row['mensagem']}\n")
                
                self.status_var.set(f"⚠️ {total_erros} erros encontrados!")
            else:
                self.result_text.insert(tk.END, "✅ Nenhum erro grave detectado.")
                self.status_var.set("✅ Análise concluída!")
        except Exception as e:
            self.status_var.set(f"Erro: {str(e)}")
            messagebox.showerror("Erro", f"Falha na análise: {str(e)}")
    
    def show_dashboard(self):
        if self.df_logs is None:
            messagebox.showwarning("Aviso", "Carregue os logs primeiro!")
            return
        
        self.status_var.set("Gerando dashboard...")
        self.root.update()
        
        try:
            # Limpa a aba do dashboard
            for widget in self.dashboard_tab.winfo_children():
                widget.destroy()
            
            # Cria um frame com scroll para o dashboard
            dashboard_canvas = tk.Canvas(self.dashboard_tab)
            scrollbar = ttk.Scrollbar(self.dashboard_tab, orient="vertical", command=dashboard_canvas.yview)
            scrollable_frame = ttk.Frame(dashboard_canvas)
            
            scrollable_frame.bind(
                "<Configure>",
                lambda e: dashboard_canvas.configure(
                    scrollregion=dashboard_canvas.bbox("all")
                )
            )
            
            dashboard_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            dashboard_canvas.configure(yscrollcommand=scrollbar.set)
            
            scrollbar.pack(side="right", fill="y")
            dashboard_canvas.pack(side="left", fill="both", expand=True)
            
            # Cabeçalho do dashboard
            header_frame = ttk.Frame(scrollable_frame)
            header_frame.pack(fill=tk.X, pady=10)
            
            ttk.Label(header_frame, 
                     text="DASHBOARD DE ANÁLISE DE LOGS",
                     font=('Helvetica', 14, 'bold')).pack()
            
            # Estatísticas gerais
            stats_frame = ttk.LabelFrame(scrollable_frame, text="📊 Estatísticas Gerais")
            stats_frame.pack(fill=tk.X, padx=10, pady=5)
            
            # Calcula estatísticas
            total_logs = len(self.df_logs)
            start_date = self.df_logs['timestamp'].min()
            end_date = self.df_logs['timestamp'].max()
            error_count = len(self.erros_detectados) if self.erros_detectados is not None else 0
            error_percent = (error_count / total_logs) * 100 if total_logs > 0 else 0
            
            stats_text = (f"• Total de logs: {total_logs:,}\n"
                         f"• Período analisado: {start_date} até {end_date}\n"
                         f"• Erros detectados: {error_count:,} ({error_percent:.2f}% do total)\n"
                         f"• Nível mais frequente: {self.df_logs['nivel'].value_counts().idxmax()}")
            
            ttk.Label(stats_frame, text=stats_text, justify=tk.LEFT).pack(anchor=tk.W)
            
            # Cria os gráficos em uma grade 2x2
            fig_frame = ttk.Frame(scrollable_frame)
            fig_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Gráfico 1: Distribuição de níveis (melhorado)
            fig1 = Figure(figsize=(6, 4), dpi=100)
            ax1 = fig1.add_subplot(111)
            nivel_counts = self.df_logs['nivel'].value_counts()
            colors = ['#4CAF50' if nivel != 'ERROR' else '#F44336' for nivel in nivel_counts.index]
            nivel_counts.plot(kind='bar', ax=ax1, color=colors)
            ax1.set_title('Distribuição de Níveis de Log', pad=10)
            ax1.set_ylabel('Quantidade')
            ax1.grid(axis='y', linestyle='--', alpha=0.7)
            
            for p in ax1.patches:
                ax1.annotate(f"{int(p.get_height())}", 
                            (p.get_x() + p.get_width() / 2., p.get_height()),
                            ha='center', va='center', xytext=(0, 5), textcoords='offset points')
            
            canvas1 = FigureCanvasTkAgg(fig1, master=fig_frame)
            canvas1.draw()
            canvas1.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # Gráfico 2: Logs por hora (melhorado)
            fig2 = Figure(figsize=(6, 4), dpi=100)
            ax2 = fig2.add_subplot(111)
            
            self.df_logs['hora'] = self.df_logs['timestamp'].dt.hour
            hora_counts = self.df_logs['hora'].value_counts().sort_index()
            
            sns.lineplot(x=hora_counts.index, y=hora_counts.values, ax=ax2, 
                        marker='o', color='#2196F3', linewidth=2.5)
            
            ax2.set_title('Logs por Hora do Dia', pad=10)
            ax2.set_xlabel('Hora')
            ax2.set_ylabel('Quantidade')
            ax2.grid(axis='both', linestyle='--', alpha=0.7)
            ax2.set_xticks(range(0, 24))
            ax2.fill_between(hora_counts.index, hora_counts.values, color='#2196F3', alpha=0.2)
            
            canvas2 = FigureCanvasTkAgg(fig2, master=fig_frame)
            canvas2.draw()
            canvas2.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # Segunda linha de gráficos
            fig_frame2 = ttk.Frame(scrollable_frame)
            fig_frame2.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Gráfico 3: Tipos de erros (se houver)
            fig3 = Figure(figsize=(6, 4), dpi=100)
            ax3 = fig3.add_subplot(111)
            
            if 'ERROR' in self.df_logs['nivel'].values:
                erros = self.df_logs[self.df_logs['nivel'] == 'ERROR']
                padroes = {
                    'Pagamento': erros['mensagem'].str.contains('pagamento|cartão|bancário', case=False).sum(),
                    'Timeout': erros['mensagem'].str.contains('timeout', case=False).sum(),
                    'Valores': erros['mensagem'].str.contains('valor|desconto|total', case=False).sum(),
                    'Duplicada': erros['mensagem'].str.contains('duplicada', case=False).sum(),
                    'Conexão': erros['mensagem'].str.contains('conexão|conectar', case=False).sum(),
                    'Outros': len(erros) - sum([
                        erros['mensagem'].str.contains('pagamento|cartão|bancário', case=False).sum(),
                        erros['mensagem'].str.contains('timeout', case=False).sum(),
                        erros['mensagem'].str.contains('valor|desconto|total', case=False).sum(),
                        erros['mensagem'].str.contains('duplicada', case=False).sum(),
                        erros['mensagem'].str.contains('conexão|conectar', case=False).sum()
                    ])
                }
                
                # Remove categorias com zero ocorrências
                padroes = {k: v for k, v in padroes.items() if v > 0}
                
                if padroes:
                    colors = sns.color_palette("Reds_r", len(padroes))
                    wedges, texts, autotexts = ax3.pie(
                        padroes.values(), 
                        labels=padroes.keys(), 
                        autopct='%1.1f%%',
                        startangle=90,
                        colors=colors,
                        wedgeprops={'linewidth': 1, 'edgecolor': 'white'},
                        textprops={'fontsize': 8}
                    )
                    
                    for autotext in autotexts:
                        autotext.set_color('white')
                        autotext.set_fontweight('bold')
                    
                    ax3.set_title('Distribuição de Tipos de Erros', pad=10)
                    ax3.axis('equal')
                else:
                    ax3.text(0.5, 0.5, 'Nenhum erro categorizado', ha='center', va='center')
                    ax3.set_title('Distribuição de Tipos de Erros', pad=10)
            else:
                ax3.text(0.5, 0.5, 'Nenhum erro encontrado', ha='center', va='center')
                ax3.set_title('Distribuição de Tipos de Erros', pad=10)
            
            canvas3 = FigureCanvasTkAgg(fig3, master=fig_frame2)
            canvas3.draw()
            canvas3.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # Gráfico 4: Tendência temporal de erros
            fig4 = Figure(figsize=(6, 4), dpi=100)
            ax4 = fig4.add_subplot(111)
            
            if self.erros_detectados is not None and not self.erros_detectados.empty:
                erros_por_dia = self.erros_detectados.set_index('timestamp').resample('D').size()
                
                sns.lineplot(
                    x=erros_por_dia.index, 
                    y=erros_por_dia.values, 
                    ax=ax4, 
                    color='#F44336',
                    linewidth=2.5,
                    marker='o'
                )
                
                ax4.set_title('Tendência de Erros ao Longo do Tempo', pad=10)
                ax4.set_xlabel('Data')
                ax4.set_ylabel('Erros por dia')
                ax4.grid(axis='both', linestyle='--', alpha=0.7)
                
                # Formatação da data
                ax4.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%d/%m'))
                
                # Adiciona média móvel
                if len(erros_por_dia) > 7:
                    media_movel = erros_por_dia.rolling(7).mean()
                    ax4.plot(media_movel.index, media_movel.values, '--', color='#9C27B0', label='Média 7 dias')
                    ax4.legend()
            else:
                ax4.text(0.5, 0.5, 'Nenhuma anomalia detectada', ha='center', va='center')
                ax4.set_title('Tendência de Erros ao Longo do Tempo', pad=10)
            
            canvas4 = FigureCanvasTkAgg(fig4, master=fig_frame2)
            canvas4.draw()
            canvas4.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # Seção de erros mais frequentes
            if self.erros_detectados is not None and not self.erros_detectados.empty:
                errors_frame = ttk.LabelFrame(scrollable_frame, text="🔍 Erros Mais Frequentes")
                errors_frame.pack(fill=tk.BOTH, padx=10, pady=10)
                
                top_errors = self.erros_detectados['mensagem'].value_counts().head(5)
                
                for i, (error_msg, count) in enumerate(top_errors.items(), 1):
                    error_frame = ttk.Frame(errors_frame)
                    error_frame.pack(fill=tk.X, padx=5, pady=2)
                    
                    ttk.Label(error_frame, text=f"{i}.", width=3).pack(side=tk.LEFT)
                    ttk.Label(error_frame, text=f"({count}x)").pack(side=tk.LEFT, padx=5)
                    
                    msg_label = ttk.Label(error_frame, text=error_msg[:150] + ("..." if len(error_msg) > 150 else ""), 
                                         wraplength=800, justify=tk.LEFT)
                    msg_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            self.status_var.set("✅ Dashboard gerado!")
        except Exception as e:
            self.status_var.set(f"Erro: {str(e)}")
            messagebox.showerror("Erro", f"Falha ao gerar dashboard: {str(e)}")
            raise e
    
    def export_report(self):
        if self.df_logs is None:
            messagebox.showwarning("Aviso", "Carregue os logs primeiro!")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="Salvar relatório de análise"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("RELATÓRIO DE ANÁLISE DE LOGS\n")
                    f.write("="*40 + "\n\n")
                    
                    # Informações gerais
                    f.write(f"Data da análise: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
                    f.write(f"Total de logs analisados: {len(self.df_logs):,}\n")
                    f.write(f"Período coberto: {self.df_logs['timestamp'].min()} a {self.df_logs['timestamp'].max()}\n\n")
                    
                    # Erros detectados
                    if self.erros_detectados is not None and not self.erros_detectados.empty:
                        f.write(f"ERROS DETECTADOS: {len(self.erros_detectados):,}\n")
                        f.write("="*40 + "\n\n")
                        
                        for _, row in self.erros_detectados.iterrows():
                            f.write(f"[{row['timestamp']}] {row['nivel']}: {row['mensagem']}\n")
                    else:
                        f.write("NENHUM ERRO GRAVE DETECTADO\n")
                
                self.status_var.set(f"✅ Relatório salvo em: {file_path}")
                messagebox.showinfo("Sucesso", "Relatório exportado com sucesso!")
            except Exception as e:
                self.status_var.set(f"Erro: {str(e)}")
                messagebox.showerror("Erro", f"Falha ao exportar relatório: {str(e)}")
    
    def _detectar_erros(self):
        # Detecção por regras
        padrao = r"\berro\b|\bfalha\b|\btimeout\b|\bduplicada\b|\binválido\b|\bdiscrepância\b|\bexception\b"
        por_regras = self.df_logs[self.df_logs['mensagem'].str.contains(padrao, flags=re.IGNORECASE, regex=True)]
        
        # Detecção por IA (One-Class SVM)
        df_erros = self.df_logs[self.df_logs['nivel'] == 'ERROR'].copy()
        if not df_erros.empty:
            vectorizer = TfidfVectorizer(max_features=1000)
            X = vectorizer.fit_transform(df_erros['mensagem']).toarray()
            
            modelo = OneClassSVM(gamma='auto', nu=0.1)
            df_erros['anomalia'] = modelo.fit_predict(X)
            por_ia = df_erros[df_erros['anomalia'] == -1]
        else:
            por_ia = pd.DataFrame()
        
        # Combina resultados e remove duplicatas
        erros_combinados = pd.concat([por_regras, por_ia]).drop_duplicates()
        
        # Adiciona severidade baseada em regras
        def calcular_severidade(mensagem):
            if re.search(r"\bcritico\b|\bfatal\b", mensagem, re.IGNORECASE):
                return "Alta"
            elif re.search(r"\berro\b|\bfalha\b", mensagem, re.IGNORECASE):
                return "Média"
            else:
                return "Baixa"
        
        if not erros_combinados.empty:
            erros_combinados['severidade'] = erros_combinados['mensagem'].apply(calcular_severidade)
        
        return erros_combinados

if __name__ == "__main__":
    root = tk.Tk()
    app = AnalisadorLogs(root)
    root.mainloop()