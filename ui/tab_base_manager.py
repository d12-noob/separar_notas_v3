import os
import threading
import customtkinter as ctk
from tkinter import messagebox, filedialog
from core.excel_utils import (
    ler_dados_planilha, 
    adicionar_registro_planilha_lote, 
    excluir_registro_planilha, 
    exportar_copia_planilha,
    limpar_dados_planilha,
    excluir_e_recriar_planilha_base
)
from .styles import (
    COR_FUNDO, COR_TOPO, COR_HEADER_BG, COR_HEADER_TEXT, 
    COR_ITEM_TEXT, COR_STATUS_TEXT, COR_BORDA, COR_CARD_BG
)

class TabBaseManager(ctk.CTkFrame):
    """Tela para gerenciar a base com lotes, limpeza e secoes minimizaveis independentes por aba."""
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=COR_FUNDO, **kwargs)
        
        header = ctk.CTkFrame(self, fg_color=COR_TOPO, corner_radius=0, height=50)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(header, text="Gerenciador da Planilha Base",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color="white").pack(side="left", padx=20, pady=10)
        
        self._scroll = ctk.CTkScrollableFrame(self, fg_color=COR_FUNDO, corner_radius=0)
        self._scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        self._construir_painel_adicao()
        self._construir_painel_listagem()
        self._carregar_dados()

    def _construir_painel_adicao(self):
        frame_add = ctk.CTkFrame(self._scroll, fg_color=COR_CARD_BG, corner_radius=8,
                                 border_width=1, border_color=COR_BORDA)
        frame_add.pack(fill="x", padx=10, pady=(10, 20))
        
        ctk.CTkLabel(frame_add, text="Adicionar Registros em Lote (Cole suas notas abaixo)",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=COR_HEADER_TEXT).pack(anchor="w", padx=16, pady=(12, 8))
        
        f_aba = ctk.CTkFrame(frame_add, fg_color="transparent")
        f_aba.pack(fill="x", padx=16, pady=4)
        ctk.CTkLabel(f_aba, text="Tipo de Dados:", width=120, anchor="w").pack(side="left")
        self._tipo_var = ctk.StringVar(value="XML")
        ctk.CTkRadioButton(f_aba, text="XML (Fatura / Remessa)", variable=self._tipo_var, value="XML").pack(side="left", padx=(0, 20))
        ctk.CTkRadioButton(f_aba, text="Pedido (Remessa / Pedido)", variable=self._tipo_var, value="PEDIDO").pack(side="left")
        
        lbl_info = ctk.CTkLabel(frame_add, text="Dica: Voce pode colar milhares de linhas de uma vez. Cada linha sera inserida sequencialmente na planilha.",
                                font=ctk.CTkFont(size=11), text_color=COR_STATUS_TEXT)
        lbl_info.pack(anchor="w", padx=16, pady=(4, 8))

        f_txts = ctk.CTkFrame(frame_add, fg_color="transparent")
        f_txts.pack(fill="x", padx=16, pady=4)
        
        f_col_a = ctk.CTkFrame(f_txts, fg_color="transparent")
        f_col_a.pack(side="left", expand=True, fill="x", padx=(0, 10))
        self._lbl_a = ctk.CTkLabel(f_col_a, text="Coluna A (XML Fatura):", anchor="w")
        self._lbl_a.pack(anchor="w", pady=(0, 4))
        self._text_a = ctk.CTkTextbox(f_col_a, height=120, font=ctk.CTkFont(size=11))
        self._text_a.pack(fill="x")
        
        f_col_b = ctk.CTkFrame(f_txts, fg_color="transparent")
        f_col_b.pack(side="left", expand=True, fill="x", padx=(10, 0))
        self._lbl_b = ctk.CTkLabel(f_col_b, text="Coluna B (XML Remessa):", anchor="w")
        self._lbl_b.pack(anchor="w", pady=(0, 4))
        self._text_b = ctk.CTkTextbox(f_col_b, height=120, font=ctk.CTkFont(size=11))
        self._text_b.pack(fill="x")
        
        self._tipo_var.trace_add("write", self._atualizar_rotulos)
        
        f_btn = ctk.CTkFrame(frame_add, fg_color="transparent")
        f_btn.pack(fill="x", padx=16, pady=(12, 16))
        
        self._btn_salvar = ctk.CTkButton(f_btn, text="Processar e Salvar Lote", fg_color=COR_TOPO, height=36,
                                         command=self._iniciar_salvamento_lote)
        self._btn_salvar.pack(side="left", padx=(0, 8))

        ctk.CTkButton(f_btn, text="Limpar Planilha...", fg_color="#d32f2f", hover_color="#c62828", height=36,
                      command=self._abrir_modal_limpeza).pack(side="left", padx=(0, 8))

        ctk.CTkButton(f_btn, text="Excluir Planilha Base", fg_color="#b71c1c", hover_color="#7f0000", height=36,
                      command=self._excluir_planilha_completa).pack(side="left", padx=(0, 8))
        
        ctk.CTkButton(f_btn, text="Baixar Copia...", fg_color="#455a64", height=36,
                      command=self._exportar_copia).pack(side="right")

    def _atualizar_rotulos(self, *_):
        if self._tipo_var.get() == "XML":
            self._lbl_a.configure(text="Coluna A (XML Fatura):")
            self._lbl_b.configure(text="Coluna B (XML Remessa):")
        else:
            self._lbl_a.configure(text="Coluna A (Remessa):")
            self._lbl_b.configure(text="Coluna B (Pedido):")

    def _construir_painel_listagem(self):
        """Cria os blocos minimizaveis separados para cada aba."""
        self._container_listas = ctk.CTkFrame(self._scroll, fg_color="transparent")
        self._container_listas.pack(fill="x", padx=10, pady=(0, 20))

        # Dicionario para controlar o estado e widgets de cada aba
        self._secoes_abas = {}
        for aba_nome in ["XML", "PEDIDO"]:
            self._secoes_abas[aba_nome] = self._criar_bloco_minimizavel(self._container_listas, aba_nome)

    def _criar_bloco_minimizavel(self, parent, aba_nome):
        outer = ctk.CTkFrame(parent, fg_color=COR_CARD_BG, corner_radius=8,
                             border_width=1, border_color=COR_BORDA)
        outer.pack(fill="x", pady=6)
        
        header = ctk.CTkFrame(outer, fg_color=COR_HEADER_BG, corner_radius=6)
        header.pack(fill="x", padx=1, pady=1)
        
        lbl_titulo = ctk.CTkLabel(header, text=f"Aba: {aba_nome} (Carregando...)",
                                  font=ctk.CTkFont(size=12, weight="bold"),
                                  text_color=COR_HEADER_TEXT, anchor="w")
        lbl_titulo.pack(side="left", padx=14, pady=10)
        
        seta = ctk.CTkLabel(header, text="▼", text_color=COR_HEADER_TEXT, font=ctk.CTkFont(size=11))
        seta.pack(side="right", padx=14)
        
        corpo = ctk.CTkFrame(outer, fg_color=COR_FUNDO, corner_radius=0)
        # Inicia oculto (minimizado por padrao)
        expandida = False
        
        def toggle(_=None):
            nonlocal expandida
            expandida = not expandida
            if expandida:
                corpo.pack(fill="both", expand=True, padx=10, pady=10)
                seta.configure(text="▲")
            else:
                corpo.pack_forget()
                seta.configure(text="▼")

        header.bind("<Button-1>", toggle)
        lbl_titulo.bind("<Button-1>", toggle)
        seta.bind("<Button-1>", toggle)
        
        return {"corpo": corpo, "lbl_titulo": lbl_titulo}

    def _carregar_dados(self):
        for aba_nome, dados in self._secoes_abas.items():
            corpo = dados["corpo"]
            lbl_titulo = dados["lbl_titulo"]
            
            for w in corpo.winfo_children():
                w.destroy()
                
            registros = ler_dados_planilha(aba_nome)
            total = len(registros)
            lbl_titulo.configure(text=f"Aba: {aba_nome}  |  Total de linhas preenchidas: {total}")
            
            if not registros:
                ctk.CTkLabel(corpo, text="Nenhum registro cadastrado.",
                             font=ctk.CTkFont(size=11), text_color=COR_STATUS_TEXT).pack(anchor="w", padx=10, pady=2)
                continue
                
            max_exibir = 100
            registros_para_mostrar = registros[-max_exibir:]
            
            if total > max_exibir:
                ctk.CTkLabel(corpo, text=f"Mostrando os ultimos {max_exibir} registros (de um total de {total}):",
                             font=ctk.CTkFont(size=10, slant="italic"), text_color=COR_STATUS_TEXT).pack(anchor="w", padx=10)

            for reg in registros_para_mostrar:
                f_item = ctk.CTkFrame(corpo, fg_color=COR_HEADER_BG, corner_radius=6)
                f_item.pack(fill="x", pady=2, padx=5)
                
                texto = f"Coluna A: {reg['col_a']}   |   Coluna B: {reg['col_b']}   |   Obs: {reg['obs'] or 'Nenhuma'}"
                ctk.CTkLabel(f_item, text=texto, font=ctk.CTkFont(size=11), text_color=COR_ITEM_TEXT).pack(side="left", padx=10, pady=6)
                
                btn_del = ctk.CTkButton(f_item, text="Excluir", width=60, height=24,
                                        fg_color="#c62828", hover_color="#b71c1c",
                                        command=lambda a=aba_nome, l=reg['linha']: self._excluir(a, l))
                btn_del.pack(side="right", padx=10)

    def _abrir_modal_limpeza(self):
        modal = ctk.CTkToplevel(self)
        modal.title("Limpar Planilha")
        modal.geometry("400x280")
        modal.resizable(False, False)
        modal.grab_set()
        
        ctk.CTkLabel(modal, text="O que voce deseja limpar?", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(20, 10))
        
        f_aba = ctk.CTkFrame(modal, fg_color="transparent")
        f_aba.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(f_aba, text="Aba:", width=60, anchor="w").pack(side="left")
        aba_var = ctk.StringVar(value="XML")
        ctk.CTkRadioButton(f_aba, text="XML", variable=aba_var, value="XML").pack(side="left", padx=10)
        ctk.CTkRadioButton(f_aba, text="PEDIDO", variable=aba_var, value="PEDIDO").pack(side="left", padx=10)
        
        f_tipo = ctk.CTkFrame(modal, fg_color="transparent")
        f_tipo.pack(fill="x", padx=20, pady=10)
        tipo_var = ctk.StringVar(value="tudo")
        ctk.CTkRadioButton(f_tipo, text="Toda a aba selecionada", variable=tipo_var, value="tudo").pack(anchor="w", pady=2)
        ctk.CTkRadioButton(f_tipo, text="Apenas a Coluna A", variable=tipo_var, value="col_a").pack(anchor="w", pady=2)
        ctk.CTkRadioButton(f_tipo, text="Apenas a Coluna B", variable=tipo_var, value="col_b").pack(anchor="w", pady=2)
        
        def executar_limpeza():
            aba = aba_var.get()
            tipo = tipo_var.get()
            if messagebox.askyesno("Confirmar Limpeza", f"Deseja realmente limpar ({tipo}) na aba {aba}?", parent=modal):
                limpar_dados_planilha(aba, tipo)
                self._carregar_dados()
                modal.destroy()
                messagebox.showinfo("Sucesso", "Limpeza realizada com sucesso!")

        ctk.CTkButton(modal, text="Confirmar Limpeza", fg_color="#d32f2f", hover_color="#c62828",
                      command=executar_limpeza).pack(pady=15)

    def _excluir_planilha_completa(self):
        if messagebox.askyesno("Atencao - Excluir Planilha", 
                               "Isso vai apagar completamente o arquivo atual da base de dados e criar um novo arquivo limpo do zero.\n\nDeseja continuar?"):
            excluir_e_recriar_planilha_base()
            self._carregar_dados()
            messagebox.showinfo("Sucesso", "Planilha base foi reiniciada com sucesso!")

    def _iniciar_salvamento_lote(self):
        linhas_a = [l.strip() for l in self._text_a.get("1.0", "end").splitlines() if l.strip()]
        linhas_b = [l.strip() for l in self._text_b.get("1.0", "end").splitlines() if l.strip()]
        
        if not linhas_a and not linhas_b:
            messagebox.showwarning("Aviso", "Cole pelo menos alguns dados nas caixas de texto.")
            return
            
        self._btn_salvar.configure(state="disabled", text="Salvando lote...")
        aba_nome = self._tipo_var.get()

        def tarefa():
            try:
                total_linhas = max(len(linhas_a), len(linhas_b))
                pares = []
                for i in range(total_linhas):
                    val_a = linhas_a[i] if i < len(linhas_a) else ""
                    val_b = linhas_b[i] if i < len(linhas_b) else ""
                    if val_a or val_b:
                        pares.append((val_a, val_b))
                
                adicionar_registro_planilha_lote(aba_nome, pares)
                self.after(0, lambda: self._finalizar_sucesso(aba_nome, len(pares)))
            except Exception as e:
                self.after(0, lambda: self._finalizar_erro(str(e)))

        threading.Thread(target=tarefa, daemon=True).start()

    def _finalizar_sucesso(self, aba_nome, qtd):
        self._btn_salvar.configure(state="normal", text="Processar e Salvar Lote")
        self._text_a.delete("1.0", "end")
        self._text_b.delete("1.0", "end")
        self._carregar_dados()
        messagebox.showinfo("Sucesso", f"{qtd} registros adicionados com sucesso na aba {aba_nome}!")

    def _finalizar_erro(self, erro):
        self._btn_salvar.configure(state="normal", text="Processar e Salvar Lote")
        messagebox.showerror("Erro", f"Ocorreu um erro ao salvar o lote:\n{erro}")

    def _excluir(self, aba_nome: str, linha: int):
        if messagebox.askyesno("Confirmar", "Deseja realmente excluir este registro?"):
            excluir_registro_planilha(aba_nome, linha)
            self._carregar_dados()

    def _exportar_copia(self):
        arquivo = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")],
            initialfile="copia_notas.xlsx"
        )
        if arquivo:
            if exportar_copia_planilha(arquivo):
                messagebox.showinfo("Sucesso", f"Copia exportada com sucesso para:\n{arquivo}")
            else:
                messagebox.showerror("Erro", "Nao foi possivel exportar a copia da planilha.")