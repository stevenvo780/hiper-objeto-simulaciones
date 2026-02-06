# Guía de Reproducibilidad (INSTALL.md)

Este documento detalla los pasos para replicar las simulaciones y validaciones presentadas en la tesis.

## 1. Requisitos del Sistema
*   **Lenguaje:** Python 3.8 o superior.
*   **Dependencias:** `numpy`, `pandas`, `meteostat`, `yfinance`, `scipy`.

## 2. Instalación
Clone el repositorio y ejecute la instalación de dependencias:
```bash
git clone https://github.com/stevenvo780/SimulacionClimatica.git
cd SimulacionClimatica
pip install -r 02_Modelado_Simulacion/caso_clima/requirements.txt
```

## 3. Ejecución de Validaciones
Para replicar el **Caso Clima (Éxito)**:
```bash
python3 02_Modelado_Simulacion/caso_clima/src/validate.py
```
El sistema generará `outputs/metrics.json` y `outputs/report.md` con los valores de EDI y CR presentados en la tesis.

Para replicar el **Caso Finanzas (Fallo)**:
```bash
python3 02_Modelado_Simulacion/caso_finanzas/src/validate.py
```

## 4. Control de Determinismo
Todos los scripts utilizan semillas aleatorias fijas (ej. `seed=42`) declaradas en los archivos `validate.py`. Los resultados son 100% deterministas en entornos Linux/Unix.
