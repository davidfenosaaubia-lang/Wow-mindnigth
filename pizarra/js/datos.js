/**
 * Cargador de datos - Lee JSON del repositorio para la pizarra.
 * Cachea en memoria para no hacer fetch repetidos.
 */
const cache = {};

async function cargarJSON(ruta) {
  if (cache[ruta]) return cache[ruta];
  try {
    const resp = await fetch(ruta);
    if (!resp.ok) throw new Error(`${resp.status} ${resp.statusText}`);
    const datos = await resp.json();
    cache[ruta] = datos;
    return datos;
  } catch (e) {
    console.error(`Error cargando ${ruta}:`, e);
    return null;
  }
}

// Rutas relativas desde pizarra/
const RUTAS = {
  analisisKymera: '../conocimiento/monje/perfiles/analisis-kymera-2026-04-09.json',
  perfilMonje: '../conocimiento/monje/perfil-clase.json',
  clases: '../rosetta/api/clases-habilidades.json',
  mazmorras: '../rosetta/api/mazmorras.json',
  instancias: '../rosetta/api/instancias.json',
  rosettaStats: '../rosetta/stats.json',
  rosettaCombate: '../rosetta/combate.json',
};

// Colores de clase por nombre ES
const COLORES_CLASE = {
  'Guerrero': 'var(--clase-guerrero)',
  'Paladín': 'var(--clase-paladin)',
  'Cazador': 'var(--clase-cazador)',
  'Pícaro': 'var(--clase-picaro)',
  'Sacerdote': 'var(--clase-sacerdote)',
  'Caballero de la Muerte': 'var(--clase-dk)',
  'Chamán': 'var(--clase-chaman)',
  'Mago': 'var(--clase-mago)',
  'Brujo': 'var(--clase-brujo)',
  'Monje': 'var(--clase-monje)',
  'Druida': 'var(--clase-druida)',
  'Cazador de demonios': 'var(--clase-dh)',
  'Evocador': 'var(--clase-evocador)',
};

function colorClase(nombreES) {
  return COLORES_CLASE[nombreES] || 'var(--text-secondary)';
}

function claseIlvl(ilvl) {
  if (ilvl >= 285) return 'ilvl-alto';
  if (ilvl >= 272) return 'ilvl-medio';
  return 'ilvl-bajo';
}
