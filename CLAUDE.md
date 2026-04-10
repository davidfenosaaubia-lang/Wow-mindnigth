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

## Arquitectura de datos: 3 pilares

### Fuentes primarias (de donde salen los datos)
1. **Blizzard API** - La fuente madre. Datos del juego: personajes, items
   (nombre ES/EN, icono, stats, calidad, procedencia), clases, habilidades,
   mazmorras, bandas, rankings M+, imagen render del personaje.
   TODO lo visual viene de aquí.
2. **Warcraft Logs (WCL)** - Rendimiento real. Se alimenta del combat log
   del juego. DPS, HPS, timeline de daño, uso de habilidades, parses.
   Todo lo que pasó en un combate real.
3. **SimulationCraft (SimC)** - Rendimiento teórico. Simula combates con
   juego perfecto. Stat weights, comparación de equipo/talentos.

### Derivados (capas sobre las primarias, NO fuentes propias)
- WoWAnalyzer = diagnóstico sobre datos de WCL
- Raidbots = interfaz web para SimC
- Archon = agrega datos de WCL + Blizzard API
- Raider.IO = originalmente sobre Blizzard API, ahora redundante con M+ Rating
- Wowhead = base de datos del juego, NO la usamos como fuente (Blizzard API
  tiene lo mismo directo). Solo como referencia de diseño.

### Regla: NO usar Wowhead como fuente de datos
Todo lo que necesitamos (iconos, nombres, stats, procedencia de items)
viene de la Blizzard API directamente. Wowhead, WoWAnalyzer, Raidbots y
Archon son referencias de DISEÑO (cómo presentar la info), no fuentes.

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

## Estado del proyecto (última actualización: 2026-04-10)

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
- WCL API keys configuradas en GitHub Secrets (4 secrets: Blizzard + WCL)
- Pizarra visual (pizarra/):
  - index.html: panel de guild con tarjeta de Kymera y stats del ecosistema
  - jugador.html: perfil rediseñado con avatar, gráfica de ilvl, stats, mecánicas
  - wowanalyzer.html: módulos de análisis BrM mapeados de WoWAnalyzer
    - Core: Stagger, DamageTaken, HealingDone, BrewCDR, MajorDefensives
    - Habilidades: PurifyingBrew, CelestialBrew, KegSmash, BreathOfFire,
      TigerPalm, Shuffle, GiftOfTheOx, HighTolerance
    - APL Check con prioridad básica BrM
  - CSS tema oscuro con colores de clase WoW, stagger, parse colors
  - JS vanilla + Chart.js CDN, sin frameworks
- GitHub Actions:
  - rosetta-api.yml: actualiza Rosetta cada miércoles
  - wcl-analisis.yml: consulta logs de WCL por personaje (manual)
  - simc-simular.yml: ejecuta SimC con perfil del repo (manual)
- Repo público, GitHub Pages activado
- Guild: Artic Penguins (posiblemente Sanguino EU)

### Pendiente
- Lanzar Action de WCL para obtener primeros logs reales
- Lanzar Action de SimC para primera simulación
- Descargar habilidades individuales por spec desde talent tree API
  (el endpoint spec_talent_tree existe pero hay que ajustar el parsing)
- Poblar la pizarra de WoWAnalyzer con datos reales de logs
- Vista de boss con timeline de daño (la más valiosa para el usuario)
- Vista de mazmorra con análisis de M+
- Añadir más jugadores de la guild al panel
- Verificar nombres de habilidades del Monje con datos de la API

### Próximos pasos sugeridos
1. Lanzar Actions de WCL y SimC para tener datos reales
2. Poblar módulos de WoWAnalyzer con datos de logs
3. Arreglar descarga de habilidades del talent tree
4. Vista de boss con timeline de daño
5. Añadir jugadores de la guild al panel
