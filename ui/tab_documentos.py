import os
import threading
from typing import Optional
import customtkinter as ctk
from tkinter import messagebox
from core.config import carregar_config, salvar_config
from core.models import ResultadoAnalise
from core.processor_doc import analisar_documentos, mover_documentos
from .styles import (
    COR_FUNDO, COR_BORDA, COR_TOPO, COR_HEADER_BG, 
    COR_HEADER_TEXT, COR_ITEM_TEXT, COR_STATUS_TEXT,
    COR_FATURA, COR_REMESSA, COR_NAO_ACHADO, COR_NAO_LISTADO, COR_CONFLITO,
    COR_BTN_MOVER, COR_BTN_MOVER_H
)
from .components import CardResumo, SecaoLog, CampoArquivo

class _AbaBaseDoc(ctk.CTkFrame):
    """Classe base compartilhada para a estrutura visual de analise."""
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=COR_FUNDO, **kwargs)
        self._resultado = None
        self._config_expandida = True
        self._scroll = ctk.CTkScrollableFrame(self, fg_color=COR_FUNDO, corner_radius=0)
        self._scroll.pack(fill="both", expand=True)

    def _construir_header_config(self, outer):
        header = ctk.CTkFrame(outer, fg_color=COR_HEADER_BG, corner_radius=8)
        header.pack(fill="x", padx=1, pady=1)
        header.bind("<Button-1>", self._toggle_config)
        
        ctk.CTkLabel(header, text="Configuracao de Caminhos",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=COR_HEADER_TEXT, anchor="w").pack(side="left", padx=14, pady=10)
        
        self._seta_config = ctk.CTkLabel(header, text="▲", text_color=COR_HEADER_TEXT,
                                         font=ctk.CTkFont(size=11))
        self._seta_config.pack(side="right", padx=14)
        
        self._frame_config_corpo = ctk.CTkFrame(outer, fg_color=COR_FUNDO, corner_radius=0)
        self._frame_config_corpo.pack(fill="x", padx=16, pady=12)
        return self._frame_config_corpo

    def _construir_botoes(self):
        frame = ctk.CTkFrame(self._scroll, fg_color="transparent")
        frame.pack(fill="x", padx=20, pady=8)
        
        self._btn_analisar = ctk.CTkButton(
            frame, text="Analisar", width=180, height=42,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=COR_TOPO, hover_color="#0d47a1", command=self._iniciar_analise)
        self._btn_analisar.pack(side="left", padx=(0, 12))
        
        self._btn_mover = ctk.CTkButton(
            frame, text="Mover Arquivos", width=180, height=42,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=COR_BTN_MOVER, hover_color=COR_BTN_MOVER_H,
            state="disabled", command=self._confirmar_mover)
        self._btn_mover.pack(side="left")

    def _construir_secoes(self, definicoes):
        frame = ctk.CTkFrame(self._scroll, fg_color="transparent")
        frame.pack(fill="x", padx=20, pady=(8, 4))
        
        ctk.CTkLabel(self._scroll, text="Resultado da Analise",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=COR_ITEM_TEXT, anchor="w").pack(anchor="w", padx=20, pady=(12, 4))
                     
        for attr_card, attr_sec, titulo, cor in definicoes:
            card = CardResumo(frame, titulo, cor)
            card.pack(side="left", expand=True, fill="x", padx=4)
            setattr(self, attr_card, card)
            
            sec = SecaoLog(self._scroll, titulo, cor)
            sec.pack(fill="x", padx=20, pady=4)
            setattr(self, attr_sec, sec)

    def _construir_status(self):
        frame = ctk.CTkFrame(self, fg_color=COR_HEADER_BG, corner_radius=0, height=36)
        frame.pack(fill="x", side="bottom")
        frame.pack_propagate(False)
        self._lbl_status = ctk.CTkLabel(frame, text="Pronto para analisar.",
                                        font=ctk.CTkFont(size=11),
                                        text_color=COR_STATUS_TEXT, anchor="w")
        self._lbl_status.pack(side="left", padx=16)

    def _set_status(self, texto: str):
        self._lbl_status.configure(text=texto)

    def _toggle_config(self, _=None):
        self._config_expandida = not self._config_expandida
        if self._config_expandida:
            self._frame_config_corpo.pack(fill="x", padx=16, pady=12)
            self._seta_config.configure(text="▲")
        else:
            self._frame_config_corpo.pack_forget()
            self._seta_config.configure(text="▼")

    def _on_config_mudou(self):
        if self._resultado is not None:
            self._resultado = None
            self._btn_mover.configure(state="disabled")
            self._set_status("Configuracao alterada. Execute a analise novamente.")

    def _erro_analise(self, msg: str):
        self._btn_analisar.configure(state="normal", text="Analisar")
        self._set_status("Erro durante a analise.")
        messagebox.showerror("Erro na analise", msg)

    def _rodar_em_thread(self, fn):
        threading.Thread(target=fn, daemon=True).start()

    def _atualizar_secoes(self, pares):
        for card, sec, titulo, linhas in pares:
            card.atualizar(len(linhas))
            sec.atualizar_titulo(f"{titulo}  ({len(linhas)})")
            sec.popular(linhas)


class TabDocumentos(_AbaBaseDoc):
    """Tela unica reutilizavel para processar arquivos XML ou PDF (Fatura e Remessa)."""
    def __init__(self, master, extensao: str = ".xml", label_origem: str = "Pasta de origem:", chave_config: str = "xml", **kwargs):
        super().__init__(master, **kwargs)
        self._extensao = extensao
        self._chave_config = chave_config

        outer = ctk.CTkFrame(self._scroll, fg_color=COR_FUNDO, corner_radius=10,
                             border_width=1, border_color=COR_BORDA)
        outer.pack(fill="x", padx=20, pady=(16, 8))
        corpo = self._construir_header_config(outer)

        self._campo_origem  = CampoArquivo(corpo, label_origem,             callback_mudanca=self._on_config_mudou)
        self._campo_fatura  = CampoArquivo(corpo, "Pasta destino FATURA:",  callback_mudanca=self._on_config_mudou)
        self._campo_remessa = CampoArquivo(corpo, "Pasta destino REMESSA:", callback_mudanca=self._on_config_mudou)
        self._campo_excel   = CampoArquivo(corpo, "Arquivo Excel (Opcional):", modo="arquivo", callback_mudanca=self._on_config_mudou)
        
        for c in [self._campo_origem, self._campo_fatura, self._campo_remessa, self._campo_excel]:
            c.pack(fill="x", pady=5)

        self._carregar_campos_config()
        self._construir_botoes()
        
        self._construir_secoes([
            ("_card_fatura",      "_sec_fatura",      "FATURA",                   COR_FATURA),
            ("_card_remessa",     "_sec_remessa",      "REMESSA",                  COR_REMESSA),
            ("_card_nao_achado",  "_sec_nao_achado",   "NAO ENCONTRADO\nNA PASTA", COR_NAO_ACHADO),
            ("_card_nao_listado", "_sec_nao_listado",  "NAO LISTADO\nNA PLANILHA", COR_NAO_LISTADO),
            ("_card_conflito",    "_sec_conflito",     "CONFLITO",                 COR_CONFLITO),
        ])
        self._construir_status()

    def _carregar_campos_config(self):
        cfg = carregar_config().get(self._chave_config, {})
        if "origem" in cfg:  self._campo_origem.set(cfg["origem"])
        if "fatura" in cfg:  self._campo_fatura.set(cfg["fatura"])
        if "remessa" in cfg: self._campo_remessa.set(cfg["remessa"])
        
        # Se ja tiver salvo nas configuracoes, usa. Senao, tenta usar a base padrao do projeto se existir
        if "excel" in cfg and cfg["excel"]:
            self._campo_excel.set(cfg["excel"])
        else:
            caminho_padrao = os.path.abspath("base_notas.xlsx")
            if os.path.exists(caminho_padrao):
                self._campo_excel.set(caminho_padrao)           

    def _salvar_campos_config(self):
        dados = {
            "origem": self._campo_origem.get(),
            "fatura": self._campo_fatura.get(),
            "remessa": self._campo_remessa.get(),
            "excel": self._campo_excel.get(),
        }
        salvar_config(self._chave_config, dados)

    def _on_config_mudou(self):
        super()._on_config_mudou()
        self._salvar_campos_config()

    def _validar_campos(self, incluir_destinos=True) -> Optional[str]:
        campos = [
            (self._campo_origem.get(), "Pasta de origem", os.path.isdir),
        ]
        if incluir_destinos:
            campos += [
                (self._campo_fatura.get(),  "Pasta de destino FATURA",  os.path.isdir),
                (self._campo_remessa.get(), "Pasta de destino REMESSA", os.path.isdir),
            ]
        for valor, nome, verificar in campos:
            if not valor:
                return f"O campo '{nome}' esta vazio."
            if not verificar(valor):
                return f"{nome} nao encontrado:\n{valor}"
        return None

    def _iniciar_analise(self):
        if erro := self._validar_campos(incluir_destinos=False):
            messagebox.showwarning("Campo invalido", erro)
            return
            
        self._btn_analisar.configure(state="disabled", text="Analisando...")
        self._btn_mover.configure(state="disabled")
        self._set_status("Analisando arquivos...")

        def tarefa():
            try:
                r = analisar_documentos(self._campo_origem.get(), self._campo_excel.get() or None, self._extensao)
                self.after(0, lambda: self._exibir_resultado(r))
            except PermissionError:
                self.after(0, lambda: self._erro_analise("O arquivo Excel esta aberto. Feche-o e tente novamente."))
            except Exception as e:
                self.after(0, lambda: self._erro_analise(str(e)))

        self._rodar_em_thread(tarefa)

    def _exibir_resultado(self, r: ResultadoAnalise):
        self._resultado = r
        ls = lambda itens: [f"  {c}   →   {n}" for c, n in itens]
        
        self._atualizar_secoes([
            (self._card_fatura,      self._sec_fatura,      "Arquivos de FATURA",                    ls(r.fatura)),
            (self._card_remessa,     self._sec_remessa,      "Arquivos de REMESSA",                   ls(r.remessa)),
            (self._card_nao_achado,  self._sec_nao_achado,   "Na planilha e nao encontrados na pasta",
             [f"  {c}   (planilha coluna {col}, linha {ln})" for c, col, ln in r.nao_achado]),
            (self._card_nao_listado, self._sec_nao_listado,  "Na pasta e nao listados na planilha",   ls(r.nao_listado)),
            (self._card_conflito,    self._sec_conflito,     "Conflitos",
             [f"  {c}   (linha A={la}, linha B={lb})" for c, la, lb in r.conflito]),
        ])
        
        self._btn_analisar.configure(state="normal", text="Analisar")
        self._btn_mover.configure(state="normal")
        self._set_status("Analise concluida. Confira os resultados.")

    def _confirmar_mover(self):
        if erro := self._validar_campos(incluir_destinos=True):
            messagebox.showwarning("Campo invalido", erro)
            return
            
        nf, nr = len(self._resultado.fatura), len(self._resultado.remessa)
        if not messagebox.askyesno("Confirmar movimentacao",
                f"Foram identificados {nf} arquivo(s) de FATURA e {nr} de REMESSA.\n\nDeseja mover agora?"):
            return
            
        self._btn_mover.configure(state="disabled", text="Movendo...")
        self._btn_analisar.configure(state="disabled")
        self._set_status("Movendo arquivos...")

        def tarefa():
            erros_log = []
            mover_documentos(
                self._campo_origem.get(), self._campo_fatura.get(),
                self._campo_remessa.get(), self._campo_excel.get() or None,
                self._resultado,
                lambda msg: erros_log.append(msg),
                lambda mf, mr, e: self.after(0, lambda: self._finalizar_mover(mf, mr, e, erros_log)),
                self._extensao,
            )

        self._rodar_em_thread(tarefa)

    def _finalizar_mover(self, mf, mr, erros, erros_log):
        self._resultado = None
        self._btn_mover.configure(state="disabled", text="Mover Arquivos")
        self._btn_analisar.configure(state="normal")
        status = f"Concluido. {mf} movido(s) para FATURA, {mr} movido(s) para REMESSA, {erros} erro(s)."
        self._set_status(status)
        messagebox.showinfo("Movimentacao concluida",
                            f"{status}\n\nDetalhes:\n" + ("\n".join(erros_log) if erros_log else "Nenhum erro."))