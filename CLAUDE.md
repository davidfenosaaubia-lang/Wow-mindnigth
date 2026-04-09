# Contexto del proyecto para asistencia AI

## Idioma
- El usuario es hispanohablante nativo
- El juego (WoW) está en español en su cliente
- La documentación del proyecto va en español
- Los archivos JSON de rosetta mapean ES <-> EN
- Cuando se referencien habilidades, stats o términos del juego, usar SIEMPRE
  el nombre español como primario y el inglés como referencia

## Propósito
Herramientas de aprendizaje para WoW. No es un addon, no es una app web.
Es un repositorio de conocimiento estructurado + scripts de análisis.

## Usuario
No es programador. Explicar decisiones técnicas cuando sean relevantes.
Priorizar claridad sobre elegancia. Los archivos JSON se eligieron porque
son legibles por humanos y consumibles por scripts.

## Convenciones
- Nombres de archivo en español (excepto README.md, CLAUDE.md, LICENSE)
- JSON con indentación de 2 espacios
- Cada archivo JSON de rosetta tiene la misma estructura:
  {categoria, descripcion, terminos: [{es, en, contexto?, notas?}]}
