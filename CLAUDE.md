# Contexto del proyecto para asistencia AI

## Idioma
- El usuario es hispanohablante nativo
- El juego (WoW) está en español en su cliente
- La documentación del proyecto va en español
- Los archivos JSON de rosetta mapean ES <-> EN
- Cuando se referencien habilidades, stats o términos del juego, usar SIEMPRE
  el nombre español como primario y el inglés como referencia
- NUNCA inventar traducciones de habilidades del juego. Si no estás seguro,
  indicar que hay que verificar en rosetta/api/ o en el cliente del juego
- Las LLMs tienden a mezclar español latino con castellano o inventar nombres.
  Ejemplo real: "Tiger's Fury" es "Deseo del Tigre", NO "Furia del Tigre"

## Propósito
Herramientas de aprendizaje para WoW. No es un addon, no es una app web.
Es un repositorio de conocimiento estructurado + scripts de análisis.
El valor está en la personalización y la agencia que ofrece al usuario y
su grupo de amigos para jugar mejor juntos. No hay objetivo comercial.

## Usuario
No es programador. Explicar decisiones técnicas cuando sean relevantes.
Priorizar claridad sobre elegancia. Los archivos JSON se eligieron porque
son legibles por humanos y consumibles por scripts.

## Convenciones
- Nombres de archivo en español (excepto README.md, CLAUDE.md, LICENSE)
- JSON con indentación de 2 espacios
- Cada archivo JSON de rosetta tiene la misma estructura:
  {categoria, descripcion, terminos: [{es, en, contexto?, notas?}]}

## Estado del proyecto (última actualización: 2026-04-09)

### Completado
- Estructura base del repositorio creada
- Rosetta manual: 6 archivos en rosetta/ con ~140 términos curados
  (stats, clases, combate, equipo, contenido, simulación)
- Inventario de fuentes de datos: analisis/fuentes/inventario.json
  (Blizzard API, WCL, SimC, Raidbots, Archon, Wowhead, WoWAnalyzer, Subcreation)
- Addons esenciales documentados: analisis/herramientas/addons-esenciales.json
- Marco de aprendizaje: conocimiento/fundamentos/marco-aprendizaje.json
- Script rosetta-api.py para descargar datos ES/EN de Blizzard API
- GitHub Action configurada (.github/workflows/rosetta-api.yml)

### Pendiente
- Ejecutar rosetta-api.py por primera vez (necesita secrets en GitHub)
  - BLIZZARD_CLIENT_ID: aa3f940d04da479e96a92a7be57d9d34
  - BLIZZARD_CLIENT_SECRET: configurar en GitHub Settings > Secrets
- El usuario aún no ha indicado qué clase/spec juega
- Personalizar Rosetta con habilidades específicas de su clase
- Explorar integración con Warcraft Logs API y Raidbots
- Triangulación práctica con datos reales del usuario

### Próximos pasos sugeridos
1. Configurar secrets en GitHub y ejecutar la Action para poblar rosetta/api/
2. Elegir clase/spec y profundizar en su análisis
3. Primer ejercicio práctico: simular personaje y comparar con logs
