import customtkinter as ctk
from ui.styles import COR_FUNDO, COR_TOPO, COR_ITEM_TEXT, COR_HEADER_BG
from ui.components import MenuCard
from ui.tab_documentos import TabDocumentos
from ui.tab_pedido import TabPedido
from ui.tab_base_manager import TabBaseManager

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Separador de Notas Fiscais e Pedidos")
        self.geometry("1020x820")
        self.minsize(950, 700)
        self.configure(fg_color=COR_FUNDO)

        # Topo fixo da aplicacao
        self._topo = ctk.CTkFrame(self, fg_color=COR_TOPO, corner_radius=0, height=70)
        self._topo.pack(fill="x")
        self._topo.pack_propagate(False)
        
        self._lbl_titulo = ctk.CTkLabel(self._topo, text="Separador de Notas Fiscais",
                                        font=ctk.CTkFont(size=20, weight="bold"),
                                        text_color="white")
        self._lbl_titulo.pack(side="left", padx=24, pady=18)

        # Botao para voltar ao menu (inicalmente oculto)
        self._btn_voltar = ctk.CTkButton(self._topo, text="Voltar ao Menu", width=120,
                                         fg_color="#ffffff", text_color=COR_TOPO,
                                         hover_color="#eceff1", command=self.mostrar_menu)

        # Container principal onde as telas serao alternadas
        self._container = ctk.CTkFrame(self, fg_color=COR_FUNDO, corner_radius=0)
        self._container.pack(fill="both", expand=True)

        self.tela_atual = None
        self.mostrar_menu()

    def limpar_container(self):
        """Remove a tela atual do container."""
        if self.tela_atual is not None:
            self.tela_atual.destroy()
            self.tela_atual = None

    def mostrar_menu(self):
        """Exibe o menu principal com os icones grandes."""
        self.limpar_container()
        self._btn_voltar.pack_forget()
        self._lbl_titulo.configure(text="Separador de Notas Fiscais e Pedidos")

        # Frame central do menu
        menu_frame = ctk.CTkScrollableFrame(self._container, fg_color=COR_FUNDO, corner_radius=0)
        menu_frame.pack(fill="both", expand=True, padx=40, pady=40)
        self.tela_atual = menu_frame

        # Titulo e subtitulo do menu
        ctk.CTkLabel(menu_frame, text="Escolha uma opcao abaixo:",
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=COR_ITEM_TEXT).pack(anchor="w", pady=(0, 20))

        # Grid de cards com icones grandes
        grid = ctk.CTkFrame(menu_frame, fg_color="transparent")
        grid.pack(fill="both", expand=True)

        # Card 1: XML
        MenuCard(grid, icone="📄", titulo="Notas XML",
                 descricao="Organize e separe arquivos XML de Fatura e Remessa cruzando com a planilha.",
                 comando=lambda: self.abrir_tela_documentos(".xml", "XML Fatura", "xml", "Processamento de Notas XML")
                 ).pack(side="left", expand=True, fill="both", padx=10, pady=10)

        # Card 2: PDF
        MenuCard(grid, icone="📑", titulo="Notas PDF",
                 descricao="Organize e separe arquivos PDF de Fatura e Remessa cruzando com a planilha.",
                 comando=lambda: self.abrir_tela_documentos(".pdf", "PDF Fatura", "pdf", "Processamento de Notas PDF")
                 ).pack(side="left", expand=True, fill="both", padx=10, pady=10)

        # Card 3: Pedidos
        MenuCard(grid, icone="📦", titulo="Pedidos / Remessas",
                 descricao="Direcione remessas em PDF para ETI ou PROPAG com base na planilha de pedidos.",
                 comando=self.abrir_tela_pedido
                 ).pack(side="left", expand=True, fill="both", padx=10, pady=10)

        # Segunda linha do grid (Gerenciador da Planilha Base)
        grid_2 = ctk.CTkFrame(menu_frame, fg_color="transparent")
        grid_2.pack(fill="both", expand=True, pady=(10, 0))

        MenuCard(grid_2, icone="📊", titulo="Gerenciar Planilha Base",
                 descricao="Cadastre notas direto pelo aplicativo, visualize registros ou baixe copias atualizadas.",
                 comando=self.abrir_gerenciador_base
                 ).pack(side="left", expand=True, fill="both", padx=10, pady=10, ipadx=100)

    def preparar_troca_tela(self, titulo_topo: str):
        self.limpar_container()
        self._lbl_titulo.configure(text=titulo_topo)
        self._btn_voltar.pack(side="right", padx=24, pady=14)

    def abrir_tela_documentos(self, extensao, label_origem, chave_config, titulo_janela):
        self.preparar_troca_tela(titulo_janela)
        self.tela_atual = TabDocumentos(self._container, extensao=extensao, label_origem=label_origem, chave_config=chave_config)
        self.tela_atual.pack(fill="both", expand=True)

    def abrir_tela_pedido(self):
        self.preparar_troca_tela("Processamento de Pedidos e Remessas")
        self.tela_atual = TabPedido(self._container, chave_config="pedido")
        self.tela_atual.pack(fill="both", expand=True)

    def abrir_gerenciador_base(self):
        self.preparar_troca_tela("Gerenciador da Planilha Base")
        self.tela_atual = TabBaseManager(self._container)
        self.tela_atual.pack(fill="both", expand=True)


if __name__ == "__main__":
    app = App()
    app.mainloop()