import os
import shutil
from typing import Optional, Tuple

def mover_arquivo_seguro(origem: str, pasta_destino: str) -> Tuple[str, Optional[str]]:
    """
    Move um arquivo para a pasta de destino evitando sobrescrever arquivos existentes.
    Se ja existir um arquivo com o mesmo nome, adiciona um sufixo numerico.
    Retorna (caminho_final, aviso_se_renomeado).
    """
    os.makedirs(pasta_destino, exist_ok=True)
    nome_arquivo = os.path.basename(origem)
    destino = os.path.join(pasta_destino, nome_arquivo)
    aviso = None

    if os.path.exists(destino):
        base, ext = os.path.splitext(nome_arquivo)
        contador = 1
        while True:
            novo_nome = f"{base}_{contador}{ext}"
            novo_destino = os.path.join(pasta_destino, novo_nome)
            if not os.path.exists(novo_destino):
                destino = novo_destino
                aviso = f"'{nome_arquivo}' ja existia no destino. Salvo como '{novo_nome}'."
                break
            contador += 1

    shutil.move(origem, destino)
    return destino, aviso