#!/usr/bin/env python3
"""
Point d'entrée de Nuru Workplan Manager.

Usage :
    python run_app.py

C'est aussi le script pointé par PyInstaller pour générer le .exe
(voir .github/workflows/build-exe.yml).
"""

from app.main import run_safely

if __name__ == "__main__":
    run_safely()
