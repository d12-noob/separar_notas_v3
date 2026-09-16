# Separador de Notas Fiscais e Pedidos

Sistema modular desenvolvido em **Python** utilizando **CustomTkinter** para automatizar a organizacao, o cruzamento de dados e a movimentacao de arquivos (XML, PDF, Faturas, Remessas e Pedidos) com base em uma planilha centralizada.

## Funcionalidades

- **Menu Principal Moderno:** Interface visual limpa baseada em icones e blocos de selecao direta.
- **Processamento de Notas (XML e PDF):** Analisa e separa arquivos de Fatura e Remessa cruzando os dados com a base local.
- **Processamento de Pedidos:** Direciona remessas em PDF para as pastas de destino (`ETI` ou `PROPAG`) com base na aba de pedidos.
- **Gerenciador da Planilha Base Integrado:** 
  - Suporte a **colagem em lote massivo** (permite colar milhares de linhas copiadas de outra planilha de uma vez so, processando em segundo plano sem travar).
  - Listagem separada por abas (`XML` e `PEDIDO`) com blocos minimizaveis independentes para economia de processamento.
  - Opcoes de limpeza seletiva (colunas especificas ou aba inteira) e recriacao de base.
  - Exportacao rapida de copias atualizadas.
- **Carregamento Inteligente de Caminhos:** O sistema detecta automaticamente a `base_notas.xlsx` presente na pasta do projeto e memoriza os ultimos caminhos utilizados.

---

## Estrutura do Projeto

separador_notas/
│
├── core/
│   ├── config.py
│   ├── excel_utils.py
│   ├── file_utils.py
│   ├── models.py
│   ├── processor_doc.py
│   └── processor_pedido.py
│
├── ui/ 
│   ├── components.py
│   ├── styles.py
│   ├── tab_base_manager.py
│   ├── tab_documentos.py
│   └── tab_pedido.py
│
├── base_notas.xlsx (se criado)
├── config.json
└── main.py
└── README.md

---

## Como Executar

1. Certifique-se de ter o Python instalado em sua maquina.

2. Instale as dependencias necessarias (como customtkinter e openpyxl):

Bash
pip install customtkinter openpyxl

3. Execute o script principal na raiz do projeto:

Bash
python main.py

---

## Autor

Desenvolvido por d.
GitHub: github.com/d12-noob