import customtkinter as ctk
from .styles import (
    COR_FUNDO, COR_BORDA, COR_CARD_BG, COR_HEADER_BG, 
    COR_HEADER_TEXT, COR_ITEM_TEXT, COR_SEM_ITENS, 
    COR_BTN_PROC, COR_BTN_PROC_H, COR_TOPO, COR_STATUS_TEXT
)

class CardResumo(ctk.CTkFrame):
    """Card para exibir contadores numéricos dos resultados da analise."""
    def __init__(self, master, titulo, cor, **kwargs):
        super().__init__(master, fg_color=COR_CARD_BG, corner_radius=10,
                         border_width=2, border_color=cor, **kwargs)
        ctk.CTkLabel(self, text=titulo, font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=cor).pack(pady=(10, 2))
        self._valor = ctk.CTkLabel(self, text="—", font=ctk.CTkFont(size=26, weight="bold"),
                                   text_color=cor)
        self._valor.pack(pady=(0, 10))

    def atualizar(self, valor: int):
        self._valor.configure(text=str(valor))


class SecaoLog(ctk.CTkFrame):
    """Secao expansivel para detalhar os itens encontrados em cada categoria."""
    def __init__(self, master, titulo, cor, **kwargs):
        super().__init__(master, fg_color=COR_FUNDO, corner_radius=8,
                         border_width=1, border_color=COR_BORDA, **kwargs)
        self._expandido = False
        header = ctk.CTkFrame(self, fg_color=cor, corner_radius=6)
        header.pack(fill="x", padx=1, pady=(1, 0))
        header.bind("<Button-1>", self._toggle)
        
        self._lbl_titulo = ctk.CTkLabel(header, text=titulo,
                                        font=ctk.CTkFont(size=12, weight="bold"),
                                        text_color="white", anchor="w")
        self._lbl_titulo.pack(side="left", padx=12, pady=8)
        self._lbl_titulo.bind("<Button-1>", self._toggle)
        
        self._lbl_seta = ctk.CTkLabel(header, text="▼", text_color="white",
                                      font=ctk.CTkFont(size=11))
        self._lbl_seta.pack(side="right", padx=12)
        self._lbl_seta.bind("<Button-1>", self._toggle)
        
        self._corpo = ctk.CTkFrame(self, fg_color=COR_FUNDO, corner_radius=0)

    def _toggle(self, _=None):
        self._expandido = not self._expandido
        if self._expandido:
            self._corpo.pack(fill="x", padx=1, pady=(0, 1))
            self._lbl_seta.configure(text="▲")
        else:
            self._corpo.pack_forget()
            self._lbl_seta.configure(text="▼")

    def atualizar_titulo(self, titulo):
        self._lbl_titulo.configure(text=titulo)

    def popular(self, linhas: list[str]):
        for w in self._corpo.winfo_children():
            w.destroy()
        if not linhas:
            ctk.CTkLabel(self._corpo, text="Nenhum item nesta categoria.",
                         font=ctk.CTkFont(size=11), text_color=COR_SEM_ITENS,
                         anchor="w").pack(anchor="w", padx=14, pady=6)
            return
        for linha in linhas:
            ctk.CTkLabel(self._corpo, text=linha, font=ctk.CTkFont(size=11),
                         text_color=COR_ITEM_TEXT, anchor="w",
                         wraplength=820).pack(anchor="w", padx=14, pady=2)


class CampoArquivo(ctk.CTkFrame):
    """Campo de entrada para selecionar pastas ou arquivos com botao de procurar."""
    def __init__(self, master, label, modo="pasta", callback_mudanca=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._callback = callback_mudanca
        ctk.CTkLabel(self, text=label, font=ctk.CTkFont(size=12),
                     width=220, anchor="w").pack(side="left")
        self._var = ctk.StringVar()
        self._var.trace_add("write", self._on_change)
        
        ctk.CTkEntry(self, textvariable=self._var, width=420,
                     font=ctk.CTkFont(size=11)).pack(side="left", padx=(0, 8))
        
        cmd = self._selecionar_arquivo if modo == "arquivo" else self._selecionar_pasta
        ctk.CTkButton(self, text="Procurar", width=80, command=cmd,
                      fg_color=COR_BTN_PROC, hover_color=COR_BTN_PROC_H).pack(side="left")

    def _selecionar_pasta(self):
        if p := ctk.filedialog.askdirectory():
            self._var.set(p)

    def _selecionar_arquivo(self):
        if p := ctk.filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx")]):
            self._var.set(p)

    def _on_change(self, *_):
        if self._callback:
            self._callback()

    def get(self) -> str:
        return self._var.get().strip()

    def set(self, valor: str):
        self._var.set(valor)


class MenuCard(ctk.CTkFrame):
    """Card em formato de bloco com icone grande e descricao para o menu inicial."""
    def __init__(self, master, icone: str, titulo: str, descricao: str, comando, **kwargs):
        super().__init__(master, fg_color=COR_CARD_BG, corner_radius=12,
                         border_width=2, border_color=COR_BORDA, **kwargs)
        
        # Torna o card clicavel
        self.bind("<Button-1>", lambda e: comando())
        
        # Icone grande centralizado
        lbl_icone = ctk.CTkLabel(self, text=icone, font=ctk.CTkFont(size=40))
        lbl_icone.pack(pady=(24, 8))
        lbl_icone.bind("<Button-1>", lambda e: comando())
        
        # Titulo
        lbl_titulo = ctk.CTkLabel(self, text=titulo, font=ctk.CTkFont(size=16, weight="bold"),
                                  text_color=COR_TOPO)
        lbl_titulo.pack(pady=(0, 4))
        lbl_titulo.bind("<Button-1>", lambda e: comando())
        
        # Descricao
        lbl_desc = ctk.CTkLabel(self, text=descricao, font=ctk.CTkFont(size=11),
                                text_color=COR_STATUS_TEXT, wraplength=220, justify="center")
        lbl_desc.pack(pady=(0, 24), padx=16)
        lbl_desc.bind("<Button-1>", lambda e: comando())