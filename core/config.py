import os
import sys
import json
from typing import Dict, Any

def obter_caminho_config() -> str:
    """Retorna o caminho absoluto para o arquivo config.json."""
    if getattr(sys, "frozen", False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        if os.path.basename(base_dir) == "core":
            base_dir = os.path.dirname(base_dir)
    return os.path.join(base_dir, "config.json")

def carregar_config() -> Dict[str, Any]:
    """Carrega as configuracoes salvas no arquivo JSON."""
    caminho = obter_caminho_config()
    if os.path.exists(caminho):
        try:
            with open(caminho, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def salvar_config(chave: str, dados: dict):
    """Salva um bloco de configuracao especifico associado a uma chave."""
    caminho = obter_caminho_config()
    try:
        cfg = carregar_config()
        cfg[chave] = dados
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception:
        pass