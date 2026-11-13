# Retarget to Empties (Blender Addon)

Un complemento de producción para **Blender** diseñado para asistir en flujos de trabajo de animación mediante *retargeting* bidireccional asistido por objetos `Empty`. 

Su objetivo principal es **aislar canales de movimiento** (traslación y rotación), limpiar curvas innecesarias y retransferir la animación de forma limpia de vuelta a un Rig. Es una herramienta ideal para **combinar animaciones incompatibles en el Non-Linear Animation (NLA) Editor** y para **extraer *Root Motion* limpio** listo para motores de videojuegos (Unreal Engine, Unity, Godot, etc.).

---

## ⚠️ Alcance y Compatibilidad de Rigging

* **Diseñado para cadenas IK:** Este flujo de trabajo opera transfiriendo transformaciones en espacio mundial (*World Space*). Por ello, está pensado exclusivamente para **controladores IK**, extremidades y puntos de pivote globales. **No está diseñado para cadenas FK jerárquicas puras.**
* **Versión de Blender:** Optimizado para la arquitectura moderna de animación (compatible con sistemas de *Action Layers / Channelbags* de Blender 4.x / 5.x).

---

## ✨ Características Principales

* **Aislamiento Estricto (*Source Armature*):** Requiere designar explícitamente el esqueleto de origen. Cada `Empty` generado guarda metadatos de propietario, evitando interferir o corromper otros rigs en escenas complejas.
* **Organización Automática:** Todos los proxies se agrupan automáticamente dentro de una colección dedicada (`RETARGET_Empties`) para mantener el *Outliner* limpio.
* **Limpieza Selectiva de Curvas:** Al finalizar el proceso, distingue automáticamente entre:
  * **Extremidades** (*Hands, Feet, Torso*): Conservan sus curvas de *Location* y *Rotation*.
  * **Articulaciones / Pole Targets** (*Chest, Head, Elbows, Knees*): Purga automáticamente las curvas residuales de *Location*, manteniendo únicamente la rotación necesaria.

---

## 🔄 Flujo de Trabajo (Workflow)

El panel se encuentra en la barra lateral de la vista 3D: **`N Sidebar > Retarget`**.

### Preparación
1. Selecciona tu esqueleto en el campo **Source Armature (Required)**.
2. Despliega los slots de las extremidades y articulaciones que necesites (puedes usar el gotero para capturar el hueso activo en *Pose Mode* o buscarlo por nombre).

### Parte 1: Rig → Empties (Extracción y Aislamiento)
1. Haz clic en **Create All Empties** para generar los proxies vinculados en el espacio mundial.
2. Haz clic en **Auto-Select Empties & Bake** para seleccionar automáticamente todos los proxies y abrir el menú de *Bake* (asegúrate de activar *Visual Keying*).
3. Haz clic en **Clear Empties Constraints** para liberar los `Empties` de las restricciones del Rig original. *(En este punto puedes editar los proxies, ajustar trayectorias o reorientar el movimiento raíz).*

### Parte 2: Empties → Rig (Retransferencia y Limpieza)
1. Haz clic en **Empties → Rig (Apply Retarget)** para vincular los controladores de tu Rig a los `Empties` editados.
2. Haz clic en **Select Rig & Bake** (el addon activará automáticamente el esqueleto en *Pose Mode* y abrirá el menú de *Bake*).
3. Finalmente, haz clic en **Clean Curves and Empties**:
   * Elimina las restricciones temporales del Rig.
   * Borra las *F-Curves* de traslación (*Location*) en las articulaciones.
   * Elimina todos los `Empties` y purga la colección temporal si queda vacía.

---

## 📦 Instalación

1. Descarga el archivo `Retarget_to_Empties.py` desde la sección de [Releases](../../releases) o directamente desde este repositorio.
2. Abre Blender y ve a **`Edit > Preferences > Add-ons`**.
3. Haz clic en **`Install...`** (o *Install from Disk*) y selecciona el archivo `.py`.
4. Activa la casilla junto a **Animation: Retarget to Empties**.

---

## 📄 Licencia

Distribuido bajo la licencia MIT. Siéntete libre de usarlo, modificarlo y adaptarlo a tu pipeline de producción.