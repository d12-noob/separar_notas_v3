import os
import threading
from typing import Optional
import customtkinter as ctk
from tkinter import messagebox
from core.config import carregar_config, salvar_config
from core.models import ResultadoPedido
from core.processor_pedido import analisar_pedido, mover_pedido
from .styles import (
    COR_FUNDO, COR_BORDA, COR_TOPO, COR_HEADER_BG, 
    COR_HEADER_TEXT, COR_ITEM_TEXT, COR_STATUS_TEXT,
    COR_PROPAG, COR_ETI, COR_NAO_LISTADO, COR_NAO_ACHADO, COR_CONFLITO,
    COR_BTN_MOVER, COR_BTN_MOVER_H
)
from .components import CardResumo, SecaoLog, CampoArquivo

class TabPedido(ctk.CTkFrame):
    """Tela para processar a separacao de remessas entre ETI e PROPAG."""
    def __init__(self, master, chave_config: str = "pedido", **kwargs):
        super().__init__(master, fg_color=COR_FUNDO, **kwargs)
        self._chave_config = chave_config
        self._resultado = None
        self._config_expandida = True

        self._scroll = ctk.CTkScrollableFrame(self, fg_color=COR_FUNDO, corner_radius=0)
        self._scroll.pack(fill="both", expand=True)

        outer = ctk.CTkFrame(self._scroll, fg_color=COR_FUNDO, corner_radius=10,
                             border_width=1, border_color=COR_BORDA)
        outer.pack(fill="x", padx=20, pady=(16, 8))
        
        # Header de configuracao
        header = ctk.CTkFrame(outer, fg_color=COR_HEADER_BG, corner_radius=8)
        header.pack(fill="x", padx=1, pady=1)
        header.bind("<Button-1>", self._toggle_config)
        
        ctk.CTkLabel(header, text="Configuracao de Caminhos (Pedidos)",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=COR_HEADER_TEXT, anchor="w").pack(side="left", padx=14, pady=10)
        
        self._seta_config = ctk.CTkLabel(header, text="▲", text_color=COR_HEADER_TEXT, font=ctk.CTkFont(size=11))
        self._seta_config.pack(side="right", padx=14)
        
        corpo = ctk.CTkFrame(outer, fg_color=COR_FUNDO, corner_radius=0)
        corpo.pack(fill="x", padx=16, pady=12)
        self._frame_config_corpo = corpo

        self._campo_origem = CampoArquivo(corpo, "Pasta origem (remessas):", callback_mudanca=self._on_config_mudou)
        self._campo_eti    = CampoArquivo(corpo, "Pasta destino ETI:",       callback_mudanca=self._on_config_mudou)
        self._campo_propag = CampoArquivo(corpo, "Pasta destino PROPAG:",    callback_mudanca=self._on_config_mudou)
        self._campo_excel  = CampoArquivo(corpo, "Arquivo Excel (Opcional):",  modo="arquivo", callback_mudanca=self._on_config_mudou)
        
        for c in [self._campo_origem, self._campo_eti, self._campo_propag, self._campo_excel]:
            c.pack(fill="x", pady=5)

        self._carregar_campos_config()
        self._construir_botoes()
        
        self._construir_secoes([
            ("_card_propag",      "_sec_propag",      "PROPAG",                   COR_PROPAG),
            ("_card_eti",         "_sec_eti",          "ETI",                      COR_ETI),
            ("_card_sem_destino", "_sec_sem_destino",  "SEM DESTINO",              COR_CONFLITO),
            ("_card_nao_listado", "_sec_nao_listado",  "NAO LISTADO\nNA PLANILHA", COR_NAO_LISTADO),
            ("_card_nao_achado",  "_sec_nao_achado",   "NAO ENCONTRADO\nNA PASTA", COR_NAO_ACHADO),
        ])
        self._construir_status()

    def _construir_botoes(self):
        frame = ctk.CTkFrame(self._scroll, fg_color="transparent")
        frame.pack(fill="x", padx=20, pady=8)
        
        self._btn_analisar = ctk.CTkButton(
            frame, text="Analisar Pedidos", width=180, height=42,
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
        
        ctk.CTkLabel(self._scroll, text="Resultado da Analise de Pedidos",
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
        self._lbl_status = ctk.CTkLabel(frame, text="Pronto para analisar pedidos.",
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

    def _carregar_campos_config(self):
        cfg = carregar_config().get(self._chave_config, {})
        if "origem" in cfg: self._campo_origem.set(cfg["origem"])
        if "eti" in cfg:    self._campo_eti.set(cfg["eti"])
        if "propag" in cfg: self._campo_propag.set(cfg["propag"])
        
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
            "eti": self._campo_eti.get(),
            "propag": self._campo_propag.get(),
            "excel": self._campo_excel.get(),
        }
        salvar_config(self._chave_config, dados)

    def _on_config_mudou(self):
        if self._resultado is not None:
            self._resultado = None
            self._btn_mover.configure(state="disabled")
            self._set_status("Configuracao alterada. Execute a analise novamente.")
        self._salvar_campos_config()

    def _validar_campos(self, incluir_destinos=True) -> Optional[str]:
        campos = [
            (self._campo_origem.get(), "Pasta origem", os.path.isdir),
        ]
        if incluir_destinos:
            campos += [
                (self._campo_eti.get(),    "Pasta destino ETI",    os.path.isdir),
                (self._campo_propag.get(), "Pasta destino PROPAG", os.path.isdir),
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
        self._set_status("Analisando remessas...")

        def tarefa():
            try:
                r = analisar_pedido(self._campo_origem.get(), self._campo_excel.get() or None)
                self.after(0, lambda: self._exibir_resultado(r))
            except PermissionError:
                self.after(0, lambda: self._erro_analise("O arquivo Excel esta aberto. Feche-o e tente novamente."))
            except Exception as e:
                self.after(0, lambda: self._erro_analise(str(e)))

        threading.Thread(target=tarefa, daemon=True).start()

    def _erro_analise(self, msg: str):
        self._btn_analisar.configure(state="normal", text="Analisar Pedidos")
        self._set_status("Erro durante a analise.")
        messagebox.showerror("Erro na analise", msg)

    def _exibir_resultado(self, r: ResultadoPedido):
        self._resultado = r
        ls = lambda itens: [f"  {n}   →   {arq}" for n, arq in itens]
        
        self._atualizar_secoes([
            (self._card_propag,      self._sec_propag,      "Arquivos → PROPAG",                    ls(r.propag)),
            (self._card_eti,         self._sec_eti,          "Arquivos → ETI",                       ls(r.eti)),
            (self._card_sem_destino, self._sec_sem_destino,  "Sem destino",                          ls(r.sem_destino)),
            (self._card_nao_listado, self._sec_nao_listado,  "Na pasta e nao listados na planilha",  ls(r.nao_listado)),
            (self._card_nao_achado,  self._sec_nao_achado,   "Na planilha e nao encontrados na pasta",
             [f"  {n}   (linha {ln})" for n, ln in r.nao_achado]),
        ])
        
        self._btn_analisar.configure(state="normal", text="Analisar Pedidos")
        self._btn_mover.configure(state="normal")
        self._set_status("Analise concluida. Confira os resultados.")

    def _atualizar_secoes(self, pares):
        for card, sec, titulo, linhas in pares:
            card.atualizar(len(linhas))
            sec.atualizar_titulo(f"{titulo}  ({len(linhas)})")
            sec.popular(linhas)

    def _confirmar_mover(self):
        if erro := self._validar_campos(incluir_destinos=True):
            messagebox.showwarning("Campo invalido", erro)
            return
            
        ne, np_ = len(self._resultado.eti), len(self._resultado.propag)
        if not messagebox.askyesno("Confirmar movimentacao",
                f"Foram identificados {ne} arquivo(s) para ETI e {np_} para PROPAG.\n\nDeseja mover agora?"):
            return
            
        self._btn_mover.configure(state="disabled", text="Movendo...")
        self._btn_analisar.configure(state="disabled")
        self._set_status("Movendo arquivos...")

        def tarefa():
            erros_log = []
            mover_pedido(
                self._campo_origem.get(), self._campo_eti.get(), self._campo_propag.get(),
                self._campo_excel.get() or None,
                self._resultado,
                lambda msg: erros_log.append(msg),
                lambda me, mp, e: self.after(0, lambda: self._finalizar_mover(me, mp, e, erros_log)),
            )

        threading.Thread(target=tarefa, daemon=True).start()

    def _finalizar_mover(self, me, mp, erros, erros_log):
        self._resultado = None
        self._btn_mover.configure(state="disabled", text="Mover Arquivos")
        self._btn_analisar.configure(state="normal")
        status = f"Concluido. {me} movido(s) para ETI, {mp} movido(s) para PROPAG, {erros} erro(s)."
        self._set_status(status)
        messagebox.showinfo("Movimentacao concluida",
                            f"{status}\n\nDetalhes:\n" + ("\n".join(erros_log) if erros_log else "Nenhum erro."))