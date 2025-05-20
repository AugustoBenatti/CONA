import os
import pandas as pd
import random
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

class GeradorLogs:
    def __init__(self, root):
        self.root = root
        self.root.title("Gerador de Logs de Transações (Offline)")
        self.root.geometry("800x600")
        
        self.df = None
        self.df_logs = None
        
        self.create_widgets()
        
    def create_widgets(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Controles
        control_frame = ttk.LabelFrame(main_frame, text="Controle")
        control_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(control_frame, text="Selecionar Arquivo CSV", command=self.load_dataset).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Gerar Logs", command=self.generate_logs).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Exportar Logs", command=self.export_logs).pack(side=tk.LEFT, padx=5)
        
        # Visualização dos logs
        log_frame = ttk.LabelFrame(main_frame, text="Logs Gerados")
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = tk.Text(log_frame, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Barra de status
        self.status_var = tk.StringVar()
        self.status_var.set("Pronto - Selecione o arquivo events.csv")
        ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN).pack(fill=tk.X)
    
    def load_dataset(self):
        file_path = filedialog.askopenfilename(
            title="Selecione o arquivo events.csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
            
        self.status_var.set("🔄 Carregando arquivo...")
        self.root.update()
        
        try:
            # Tenta várias codificações comuns
            encodings = ['utf-8', 'latin1', 'ISO-8859-1', 'cp1252']
            
            for encoding in encodings:
                try:
                    self.df = pd.read_csv(file_path, encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
            
            if self.df is None:
                raise ValueError("Não foi possível determinar a codificação do arquivo")
            
            self.status_var.set(f"✅ Arquivo carregado: {os.path.basename(file_path)}")
            self.log_text.insert(tk.END, "Dataset carregado:\n")
            self.log_text.insert(tk.END, str(self.df.head()) + "\n")
        except Exception as e:
            self.status_var.set(f"Erro: {str(e)}")
            messagebox.showerror("Erro", 
                f"Falha ao carregar arquivo: {str(e)}\n\n"
                "Certifique-se que:\n"
                "1. Você baixou o arquivo events.csv do dataset\n"
                "2. O arquivo não está corrompido\n"
                "3. Tentamos várias codificações de texto")

    def generate_logs(self):
        if self.df is None:
            messagebox.showwarning("Aviso", "Selecione o arquivo CSV primeiro!")
            return
        
        self.status_var.set("Gerando logs...")
        self.root.update()
        
        try:
            self.df_logs = self._gerar_logs_simulados(max_logs=30)
            self.log_text.delete(1.0, tk.END)
            
            for _, row in self.df_logs.iterrows():
                self.log_text.insert(tk.END, f"{row['timestamp']} - {row['nivel']} - {row['mensagem']}\n")
            
            self.status_var.set(f"✅ {len(self.df_logs)} logs gerados!")
        except Exception as e:
            self.status_var.set(f"Erro: {str(e)}")
            messagebox.showerror("Erro", f"Falha ao gerar logs: {str(e)}")
    
    def export_logs(self):
        if self.df_logs is None:
            messagebox.showwarning("Aviso", "Nenhum log para exportar!")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Salvar logs como CSV"
        )
        
        if file_path:
            try:
                self.df_logs.to_csv(file_path, index=False, encoding='utf-8')
                self.status_var.set(f"✅ Logs salvos em: {file_path}")
                messagebox.showinfo("Sucesso", "Logs exportados com sucesso!")
            except Exception as e:
                self.status_var.set(f"Erro: {str(e)}")
                messagebox.showerror("Erro", f"Falha ao exportar: {str(e)}")
    
    def _gerar_logs_simulados(self, max_logs=30):
        logs = []
        if "event" not in self.df.columns:
            raise ValueError("O arquivo CSV não contém a coluna 'event' necessária")
            
        df_transacoes = self.df[self.df["event"] == "transaction"].copy()

        mensagens_error = [
            "Erro ao processar pagamento com cartão de crédito.",
            "Timeout na API do gateway de pagamento.",
            "Discrepância nos valores da transação detectada.",
            "Falha ao validar dados bancários do cliente.",
            "Erro interno no sistema de pagamento.",
            "Transação duplicada identificada no sistema.",
            "Erro ao calcular total da compra com desconto aplicado."
        ]
        mensagens_info = [
            "Pagamento processado com sucesso.",
            "Transação concluída sem erros.",
            "Confirmação de pagamento recebida.",
            "Pedido finalizado com sucesso.",
        ]

        for _, row in df_transacoes.head(max_logs).iterrows():
            nivel = random.choices(["INFO", "ERROR"], weights=[0.7, 0.3])[0]
            mensagem = random.choice(mensagens_error) if nivel == "ERROR" else random.choice(mensagens_info)

            logs.append({
                "timestamp": pd.to_datetime(row["timestamp"], unit="ms").strftime('%Y-%m-%d %H:%M:%S'),
                "nivel": nivel,
                "mensagem": mensagem
            })

        return pd.DataFrame(logs)

if __name__ == "__main__":
    root = tk.Tk()
    app = GeradorLogs(root)
    root.mainloop()