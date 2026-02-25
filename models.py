#Define que es un gasto

from dataclasses import dataclass
from datetime import date

@dataclass  #Crea la clase sin el __init__()
class Gasto:
    fecha: date
    categoria: str
    descripcion: str
    monto: float

