# Wow-Midnight: Herramientas de Conocimiento para WoW

Ecosistema de herramientas para aprender, analizar y mejorar en World of Warcraft,
construido desde la necesidad de **criterio frente al ruido**.

## Problema

Hay mucha información sobre WoW. Demasiada. Simuladores, guías, logs, vídeos,
opiniones disfrazadas de datos. Lo que falta es **orden, criterio y contexto**.

Este proyecto ataca eso en tres frentes:

### 1. Rosetta (`/rosetta`)
Puente idiomático español-inglés. Todo el theorycraft está en inglés, pero el
juego está en español. Aquí vive la tabla de traducción estructurada: stats,
clases, habilidades, términos de combate, jerga de simulación.

### 2. Análisis (`/analisis`)
Inventario crítico de fuentes de datos y herramientas disponibles:
- **Fuentes**: Blizzard API, Warcraft Logs, WarcraftLogsDPS, Wowhead, Archon, SimulationCraft
- **Herramientas**: Raidbots, WoWAnalyzer, simuladores locales
- Qué dice cada fuente, qué no dice, dónde se contradicen, cómo triangular

### 3. Conocimiento (`/conocimiento`)
Lo que vamos aprendiendo, organizado. No es lineal: cada descubrimiento
puede cambiar lo que creíamos saber antes. Aquí se documenta el proceso.

## Filosofía

- **Datos > opiniones**: Si no tiene números, es una opinión
- **Triangulación**: Una sola fuente no es suficiente
- **Contexto**: Un dato sin contexto es ruido
- **Iteración**: Todo es revisable, nada es definitivo

## Estructura

```
├── rosetta/              # Terminología ES/EN estructurada
│   ├── stats.json        # Estadísticas de personaje
│   ├── clases.json       # Clases y especializaciones
│   ├── combate.json      # Términos de combate y mecánicas
│   ├── equipo.json       # Equipamiento y ranuras
│   ├── contenido.json    # Mazmorras, bandas, modos de juego
│   └── simulacion.json   # Términos de theorycraft y simulación
├── analisis/
│   ├── fuentes/          # Qué fuentes existen y qué ofrecen
│   └── herramientas/     # Herramientas disponibles y cómo usarlas
└── conocimiento/
    └── fundamentos/      # Base teórica: stats, gearing, rotaciones
```
