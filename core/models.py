from dataclasses import dataclass, field
from typing import List, Tuple, Optional

@dataclass
class ResultadoPedido:
    propag:      List[Tuple[str, str]] = field(default_factory=list)
    eti:         List[Tuple[str, str]] = field(default_factory=list)
    sem_destino: List[Tuple[str, str]] = field(default_factory=list)
    nao_listado: List[Tuple[str, str]] = field(default_factory=list)
    nao_achado:  List[Tuple[str, str]] = field(default_factory=list)

@dataclass
class ResultadoAnalise:
    fatura:      List[Tuple[str, str]] = field(default_factory=list)
    remessa:     List[Tuple[str, str]] = field(default_factory=list)
    nao_achado:  List[Tuple[str, str]] = field(default_factory=list)
    nao_listado: List[Tuple[str, str]] = field(default_factory=list)
    conflito:    List[Tuple[str, int, int]] = field(default_factory=list)