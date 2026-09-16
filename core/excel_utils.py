import os
import shutil
import openpyxl
from typing import Optional, Tuple, Dict, Any, List

def limpar_coluna_observacao(aba, col_obs=3) -> int:
    """
    Configura o cabecalho 'OBSERVACAO' e limpa valores anteriores da coluna col_obs.
    Remove linhas residuais criadas em execucoes anteriores.
    Retorna a ultima linha de dados valida.
    """
    aba.cell(row=1, column=col_obs, value="OBSERVACAO")

    ultima_dados = 1
    for row in aba.iter_rows(min_row=2):
        if row[0].value is not None or (len(row) > 1 and row[1].value is not None):
            ultima_dados = max(ultima_dados, row[0].row)

    if aba.max_row > ultima_dados:
        aba.delete_rows(ultima_dados + 1, aba.max_row - ultima_dados)

    for r in range(2, ultima_dados + 1):
        aba.cell(row=r, column=col_obs).value = None

    return ultima_dados


def obter_caminho_planilha_base() -> str:
    """Retorna o caminho padrao da planilha guardada na pasta do projeto."""
    if getattr(sys := __import__("sys"), "frozen", False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        if os.path.basename(base_dir) == "core":
            base_dir = os.path.dirname(base_dir)
    return os.path.join(base_dir, "base_notas.xlsx")


def garantir_planilha_base_existe() -> str:
    """Garante que a planilha base existe e e valida. Se estiver corrompida ou vazia, recria."""
    caminho = "base_notas.xlsx"
    
    # Se o arquivo nao existe ou esta vazio (tamanho 0 bytes)
    if not os.path.exists(caminho) or os.path.getsize(caminho) == 0:
        _criar_planilha_nova(caminho)
        return caminho
        
    # Tenta abrir para testar se nao esta corrompido
    try:
        wb = openpyxl.load_workbook(caminho)
        # Verifica se as abas essenciais existem
        if "XML" not in wb.sheetnames or "PEDIDO" not in wb.sheetnames:
            wb.close()
            _criar_planilha_nova(caminho)
        else:
            wb.close()
    except Exception:
        # Se der qualquer erro ao ler (como BadZipFile), o arquivo esta corrompido, entao recria
        _criar_planilha_nova(caminho)
        
    return caminho

def _criar_planilha_nova(caminho: str):
    wb = openpyxl.Workbook()
    # Aba XML
    ws_xml = wb.active
    ws_xml.title = "XML"
    ws_xml.append(["Fatura", "Remessa", "Observacoes"])
    
    # Aba PEDIDO
    ws_pedido = wb.create_sheet(title="PEDIDO")
    ws_pedido.append(["Remessa", "Pedido", "Observacoes"])
    
    wb.save(caminho)
    wb.close()

def ler_dados_planilha(aba_nome: str) -> List[Dict[str, Any]]:
    """Lê todos os registros cadastrados em uma aba especifica ('XML' ou 'PEDIDO')."""
    caminho = garantir_planilha_base_existe()
    wb = openpyxl.load_workbook(caminho)
    
    if aba_nome not in wb.sheetnames:
        return []
        
    aba = wb[aba_nome]
    registros = []
    
    for row in aba.iter_rows(min_row=2):
        val_a, val_b, val_c = row[0].value, row[1].value, row[2].value
        if val_a is not None or val_b is not None:
            registros.append({
                "col_a": str(val_a) if val_a is not None else "",
                "col_b": str(val_b) if val_b is not None else "",
                "obs": str(val_c) if val_c is not None else "",
                "linha": row[0].row
            })
    return registros


def adicionar_registro_planilha(aba_nome: str, valor_a: str, valor_b: str):
    """Adiciona uma nova linha na planilha base com os valores informados."""
    caminho = garantir_planilha_base_existe()
    wb = openpyxl.load_workbook(caminho)
    
    if aba_nome in wb.sheetnames:
        aba = wb[aba_nome]
        # Acha a proxima linha vazia
        proxima_linha = aba.max_row + 1
        # Se max_row for 1 e estiver vazio, comeca na linha 2
        if proxima_linha == 2 and aba.cell(row=1, column=1).value is None:
            proxima_linha = 1
            
        aba.cell(row=proxima_linha, column=1, value=valor_a)
        aba.cell(row=proxima_linha, column=2, value=valor_b)
        wb.save(caminho)


def excluir_registro_planilha(aba_nome: str, linha: int):
    """Exclui uma linha especifica da planilha base."""
    caminho = garantir_planilha_base_existe()
    wb = openpyxl.load_workbook(caminho)
    
    if aba_nome in wb.sheetnames:
        aba = wb[aba_nome]
        aba.delete_rows(linha)
        wb.save(caminho)


def exportar_copia_planilha(destino_path: str) -> bool:
    """Exporta uma copia da planilha base atual para o caminho escolhido pelo usuario."""
    try:
        caminho_base = garantir_planilha_base_existe()
        shutil.copy(caminho_base, destino_path)
        return True
    except Exception:
        return False


def adicionar_registro_planilha_lote(aba_nome: str, pares: list[tuple[str, str]]):
    """Adiciona multiplas linhas de uma vez so na planilha base de forma otimizada."""
    caminho = garantir_planilha_base_existe()
    wb = openpyxl.load_workbook(caminho)
    
    if aba_nome in wb.sheetnames:
        aba = wb[aba_nome]
        proxima_linha = aba.max_row + 1
        if proxima_linha == 2 and aba.cell(row=1, column=1).value is None:
            proxima_linha = 1
            
        for val_a, val_b in pares:
            aba.cell(row=proxima_linha, column=1, value=val_a)
            aba.cell(row=proxima_linha, column=2, value=val_b)
            proxima_linha += 1
            
        wb.save(caminho)


def limpar_dados_planilha(aba_nome: str, tipo_limpeza: str):
    """
    Limpa dados da aba selecionada conforme o tipo:
    'col_a': apaga apenas a coluna 1 (preserva cabecalho)
    'col_b': apaga apenas a coluna 2 (preserva cabecalho)
    'tudo': apaga tudo mantendo apenas os cabecalhos da aba
    """
    caminho = garantir_planilha_base_existe()
    wb = openpyxl.load_workbook(caminho)
    if aba_nome in wb.sheetnames:
        aba = wb[aba_nome]
        max_r = aba.max_row
        if max_r > 1:
            for r in range(2, max_r + 1):
                if tipo_limpeza in ("col_a", "tudo"):
                    aba.cell(row=r, column=1, value=None)
                if tipo_limpeza in ("col_b", "tudo"):
                    aba.cell(row=r, column=2, value=None)
                if tipo_limpeza == "tudo":
                    aba.cell(row=r, column=3, value=None)
            wb.save(caminho)
    wb.close()


def excluir_e_recriar_planilha_base():
    """Exclui o arquivo da planilha base e o recria limpo do zero."""
    caminho = "base_notas.xlsx"
    if os.path.exists(caminho):
        try:
            os.remove(caminho)
        except Exception:
            pass
    _criar_planilha_nova(caminho)  