# Cómo obtener tu API Key de Blizzard (gratuita)

La API de Blizzard es gratuita y te da acceso a todos los datos del juego,
incluyendo los nombres oficiales en español que necesitamos para la Rosetta.

## Pasos

### 1. Ir al portal de desarrolladores
Abre: https://develop.battle.net/access/clients

### 2. Iniciar sesión
Usa tu cuenta normal de Battle.net (la misma del juego).

### 3. Crear un nuevo cliente
- Haz clic en **"Create Client"** (o "Crear Cliente")
- **Client Name**: Pon lo que quieras, por ejemplo "WoW Rosetta"
- **Redirect URLs**: Pon `http://localhost` (es obligatorio pero no lo usamos)
- **Intended Use**: Selecciona algo como "I am building a tool..."
- Acepta los términos y crea

### 4. Copiar las credenciales
Después de crear el cliente, verás dos valores:
- **Client ID**: Un código largo (público, no es secreto)
- **Client Secret**: Otro código largo (**este sí es privado, no lo compartas**)

### 5. Ejecutar el script

```bash
python3 scripts/rosetta-api.py \
  --client-id PEGA_TU_CLIENT_ID \
  --client-secret PEGA_TU_CLIENT_SECRET \
  --todo
```

O si prefieres no escribirlas cada vez:

```bash
export BLIZZARD_CLIENT_ID=tu_client_id
export BLIZZARD_CLIENT_SECRET=tu_client_secret
python3 scripts/rosetta-api.py --todo
```

## Qué descarga

Con `--todo` descarga:
- **Clases y habilidades**: Todas las clases, specs y sus habilidades en ES/EN
- **Mazmorras**: Nombres de mazmorras de M+ actuales
- **Bandas**: Nombres de raids
- **Estadísticas**: Nombres oficiales de recursos y stats

Los archivos se guardan en `rosetta/api/` como JSON.

## Seguridad

- El Client Secret es privado. No lo subas a GitHub.
- El archivo `.env` está en `.gitignore`, puedes guardar ahí tus credenciales.
- La API key es gratuita y no tiene límite práctico para nuestro uso.

## Límites

- La API permite ~36.000 peticiones/hora para datos de juego
- Nuestro script hace unas 50-100 peticiones en total
- No hay riesgo de exceder límites
