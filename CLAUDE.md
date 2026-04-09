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

## Usuario: clase y specs
- **Clase**: Monje (Monk)
- **Main spec**: Maestro cervecero (Brewmaster) - TANK
- **Segundo foco**: Tejedor de niebla (Mistweaver) - HEALER
- **También**: Viajero del viento (Windwalker) - DPS
- **Contenido principal**: Mítica+ (M+)
- **Objetivo**: Aprender las tres specs, priorizando tank y heal

## Contexto del usuario como jugador
- Jugador veterano con mucho conocimiento del juego
- Fue top EU como Druid Balance en Wrath of the Lich King
- Su rol actual NO es competitivo personal - quiere hacer escuela
- Está mentorizando a un grupo de 8-10 personas en su guild
- Filosofía: no copiar rotaciones, entender POR QUÉ funciona lo que funciona
- Enfoque epistemológico: entender las condiciones que hacen efectiva una acción
- Ejemplo suyo: "No mires cuándo se tiran defensivos. Ponte a curar y tus
  ojos aprenderán cuándo entra el daño"
- El problema que ve: las guías copian al top 0.1% sin contexto, los jugadores
  copian sin entender, y cuando algo cambia no saben adaptarse
- El tank es el ejemplo más visible: el que más castiga el fallo, el que más
  fricción genera, y el que peores herramientas tiene para entender los bosses

## Modelo de trabajo
- Las herramientas son para uso del USUARIO, no para la guild directamente
- NO se expone IA a la guild - el usuario es el intermediario
- Flujo: usuario + Claude analizan datos → generan documentos legibles →
  el usuario los comparte como quiera (Discord, voz, docs)
- Los análisis deben ser consumibles por el usuario como "pizarra" de enseñanza
- La estructura debe poder escalar a addons propios en el futuro

## Estado del proyecto (última actualización: 2026-04-09)

### Completado
- Estructura base del repositorio
- Rosetta manual: 6 archivos en rosetta/ con ~140 términos curados
- Rosetta API funcionando:
  - rosetta/api/clases-habilidades.json (13 clases, todas las specs ES/EN)
  - rosetta/api/mazmorras.json (82 mazmorras ES/EN)
  - rosetta/api/instancias.json (todas las bandas/mazmorras por expansión ES/EN)
  - Blizzard API key configurada en GitHub Secrets
  - GitHub Action ejecutándose cada miércoles automáticamente
- Inventario de fuentes: analisis/fuentes/inventario.json
- Addons esenciales: analisis/herramientas/addons-esenciales.json
- Marco de aprendizaje: conocimiento/fundamentos/marco-aprendizaje.json
- Perfil del Monje: conocimiento/monje/perfil-clase.json
- Perfil SimC de Kymera (BrM, EU/Zul'jin, ~277 ilvl, 4p tier):
  - conocimiento/monje/perfiles/kymera-brewmaster-2026-04-09.simc
  - conocimiento/monje/perfiles/analisis-kymera-2026-04-09.json
- Script Warcraft Logs: scripts/wcl-analyzer.py (GraphQL v2)
- WCL API keys configuradas (WCL_CLIENT_SECRET en GitHub, falta WCL_CLIENT_ID)
- Pizarra visual creada (pizarra/):
  - index.html: panel de guild con tarjeta de Kymera
  - jugador.html: perfil detallado de equipo, enchants, mejoras
  - CSS tema oscuro con colores de clase WoW
  - JS vanilla + Chart.js CDN, sin frameworks
- Guild: Artic Penguins (posiblemente Sanguino EU)

### Pendiente
- Hacer repo público para activar GitHub Pages (pizarra web)
- Añadir WCL_CLIENT_ID a GitHub Secrets
- Descargar habilidades individuales por spec desde talent tree API
  (el endpoint spec_talent_tree existe pero hay que ajustar el parsing)
- Crear rotaciones detalladas para Maestro cervecero y Tejedor de niebla
- Primer análisis de logs reales con WCL API
- Ampliar pizarra: vista de boss (timeline de daño), comparar, mazmorra
- Añadir más jugadores de la guild al panel
- Verificar nombres de habilidades del Monje con datos de la API

### Próximos pasos sugeridos
1. Hacer repo público y activar GitHub Pages
2. Añadir WCL_CLIENT_ID y probar conexión con Warcraft Logs
3. Arreglar descarga de habilidades del talent tree
4. Vista de boss con timeline de daño (la más valiosa para el usuario)
5. Añadir jugadores de la guild al panel
