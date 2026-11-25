# COSMONIAN - Proyecto final

Juego de naves con las mecánicas de *Bosconian* (versión Sharp X68000), hecho con Pygame y
Esper siguiendo la arquitectura ECS.

- **Jugar en el navegador:** https://juan-jerez.itch.io/cosmonian
- **Documento de arquitectura y post-mortem:** [docs/arquitectura_y_postmortem.pdf](docs/arquitectura_y_postmortem.pdf)
- **Post-mortem individual:** [docs/postmortem_individual.pdf](docs/postmortem_individual.pdf)

## Estructura

- **Escenas** (`src/engine/scenes/scene.py`): cada pantalla es una escena con su propio mundo de
  esper. El motor (`src/engine/game_engine.py`) solo crea, actualiza, dibuja y cambia la escena
  actual; el cambio se aplica al terminar el cuadro.
  - `IntroScene`: intro animada; cualquier tecla o botón la salta.
  - `TitleScene`: título y menú (Jugar, Niveles, Instrucciones, Créditos). Tras 15 s sin tocar
    nada empieza el modo atractor.
  - `AttractScene` y `AttractInfoScene`: modo atractor. Una ronda que juega sola un piloto
    automático (`system_autopilot`: esquiva lo que tiene delante, persigue enemigos cercanos y
    ataca las torretas), con su propio estado de partida para no tocar el puntaje real; después,
    las instrucciones. Cualquier tecla o botón vuelve al título. Tiempos y ronda en el bloque
    `attract` de `interface.json`.
  - `LevelSelectScene`: selección de ronda (lista en `assets/cfg/levels.json`).
  - `InfoScene`: instrucciones y créditos.
  - `PlayScene`: el juego. Empieza con un despegue ("BLAST OFF!", sin poder moverse) y tiene
    pausa con el mismo menú del título.
  - `VictoryScene`, `DefeatScene` (continuar en 5 s: vidas completas y puntaje a 0) y
    `HiScoreScene` (celebración si se superó el récord).
- **Service Locator** (`src/engine/service_locator.py`): acceso único a imágenes (y recortes de
  la hoja de sprites), sonidos, fuentes y archivos JSON.
- **Configuración** en `assets/cfg/`: ventana, interfaz y textos (`interface.json`), controles
  (`input.json`), recortes de la hoja de sprites (`sprites.json`), niveles, jugador, enemigos...
- **Interfaz**: las entidades con `CTagUI` se dibujan en coordenadas de pantalla, sin cámara y
  encima del mundo.
- **Nave del jugador** (`system_player_ship`): nunca se detiene; arranca quieta y acelera poco a
  poco hasta su velocidad máxima. Las flechas eligen una de 8 direcciones y la nave gira hacia ella
  pasando por las intermedias. `system_directional_sprite` muestra la imagen girada que toca
  según hacia dónde se mueve. Z dispara una bala hacia delante y otra hacia atrás; si el nivel
  tiene `"triple_shot": true`, salen tres hacia delante y se anuncia al empezar la ronda.
- **Colisiones**: AABB con el componente `CHitBox` (rectángulo centrado en la entidad, de tamaño
  propio en el JSON, independiente de la imagen); funcionan también a través de los bordes del
  mundo. Toda colisión crea una explosión; las de los enemigos conservan su velocidad. Si un
  enemigo toca al jugador mueren los dos: la nave deja una ráfaga de explosiones y reaparece en el
  punto de partida. Los enemigos que chocan entre sí rebotan. F2 muestra las hitboxes.
- **Bases** (`assets/cfg/base.json`, posiciones y orientación en cada nivel): un cuerpo
  decorativo, seis torretas y un núcleo. Las torretas se abren y disparan al jugador cuando está
  cerca, cada una a su ritmo; sus balas también matan a los enemigos. El núcleo se abre y se cierra
  (o está siempre abierto, según `base_behavior` del nivel). La base cae al destruir sus seis
  torretas o con un disparo recto que entre por la abertura del núcleo abierto: de arriba o abajo
  en las verticales, de lado en las horizontales. Sin bases en pie se pasa a la siguiente ronda.
- **Obstáculos** (`assets/cfg/obstacles.json`, cantidades en cada nivel; se reparten al azar lejos
  del jugador y de las bases): rocas estáticas, minas con luces que parpadean y rocas
  indestructibles (doradas) que se mueven en línea recta. Una bala, el jugador o un enemigo que
  toca una roca o una mina la destruye y muere con ella. La explosión de una mina es verde y letal:
  mata al jugador y a los enemigos cercanos y hace estallar otras minas. Las rocas indestructibles
  destruyen balas, jugador y enemigos, y rebotan contra las bases.
- **Enemigos** (`assets/cfg/enemies.json`; ritmo, máximo, tipos y precisión en cada nivel):
  aparecen al azar desde cualquier dirección, justo fuera de la pantalla, y se mueven con
  steering behaviours (`src/ecs/utils/steering.py`: seek, flee y wander), siempre algo más rápido
  que el jugador. Tipo I (50): persigue un rato y luego huye. Tipo P (60): persigue poco y luego
  vaga al azar. Tipo E (70): va recto y rápido; también sale del núcleo de las bases al abrirse si
  el nivel tiene `spawn_e`. Con menos precisión (`accuracy`) apuntan a un punto más alejado del
  jugador. Los que dejan de perseguir desaparecen al alejarse.
- **Condición de alerta** (`assets/cfg/alert.json`; tiempos en `alert` de cada nivel): todos los
  niveles empiezan en VERDE (sin enemigos) y poco después pasan a AMARILLO. Destruir una base
  devuelve a VERDE un rato. Pasa a ROJO, sin vuelta atrás, si el nivel se alarga o si escapa un
  espía: los enemigos salen al doble de ritmo, más rápidos y en mayor número. Cada cambio suena.
- **Espía** (`SPY` en `enemies.json`): aparece cada cierto tiempo en AMARILLO o ROJO y cruza la
  pantalla. La primera vez que llega a un borde rebota; la segunda escapa y la condición pasa a
  ROJO. Mientras se ve, el panel parpadea "¡ESPIA!".
- **Formaciones** (`assets/cfg/formations.json`; ritmo, figuras y tipos en cada nivel): en AMARILLO
  o ROJO sale cada cierto tiempo de una base una formación de cuatro enemigos y su capitán (de
  otro color), en línea (I), en V, en X o en cruz (+). Vuela como un grupo directo hacia el
  jugador, más rápido que él, y se ve en el radar. Si cae el capitán, el resto huye.
- **Puntaje y vidas** (`assets/cfg/score.json`): cada entidad que se puede destruir lleva
  `CPoints`; el jugador suma esos puntos solo si la destruyó él (con una bala, chocando o con una
  mina que hizo estallar). El espía vale 200, 400, 800 o 1600 según la distancia; derribar una
  formación entera da 1500 más. 1UP y HI-SCORE (20.000 al empezar) se actualizan a la vez. Hay 4
  vidas (la reserva se ve como iconos bajo el radar; con 0 se juega la última) y se gana una a los
  50.000, a los 100.000 y luego cada 100.000; si no caben los iconos se muestra el total. El
  récord, el puntaje y las vidas pasan de una ronda a otra (`src/engine/game_state.py`).
- **Escudo** (tecla X, `assets/cfg/shield.json`): la segunda habilidad especial. Cada carga
  protege 3 s: los enemigos rebotan contra la nave (sin morir ni dar puntos), las balas enemigas
  se pierden y la nave atraviesa rocas, minas y bases sin romperlas. Se empieza con 1 carga
  (máximo 3) y se consiguen más recogiendo un ítem que aparece cada cierto tiempo con cierta
  probabilidad (`shield_item` de cada nivel), se ve en el radar y desaparece si no se recoge.
- **Niveles y rondas** (`assets/cfg/levels/level_01.json` … `level_10.json`, en orden en
  `levels.json`; acceso en `src/game/levels.py`): 10 niveles de 3 rondas cada uno. El JSON de un
  nivel tiene lo común a sus rondas (disparo triple, mundo, obstáculos, alerta, espía, ítem de
  escudo) y una lista `rounds` con lo propio de cada ronda (bases, comportamiento de las bases,
  enemigos y formaciones), que se combina con lo común al jugarla. La dificultad sube a lo largo
  de las 30 rondas: de 2 a 7 bases, núcleos siempre abiertos al principio y que lanzan enemigos E
  después, enemigos más frecuentes, numerosos y precisos, más formaciones y obstáculos y ROJO
  antes. El disparo triple está en los niveles 4, 7 y 10. El panel muestra la ronda global
  (ROUND 1 a 30) y al empezar se anuncia "NIVEL n - RONDA m". Tras la última ronda del nivel 10,
  victoria; continuar tras perder repite la misma ronda.
- **Jefe** (`assets/cfg/boss.json`, nivel `level_jefe.json` tras el nivel 10): una nave grande
  en un mundo propio (más pequeño, con estrellas rojizas y sin bases) que se acerca despacio al
  jugador y, cada pocos segundos, ataca: se queda quieta 2 s cargando (parpadea) y lanza anillos
  de balas en todas direcciones; lanza una bala que persigue al jugador y aguanta 3 disparos; o
  despliega dos alineaciones, una a cada lado. Tiene 60 de vida (barra en la parte superior) y
  da 10000 puntos; al derrotarlo llega la victoria.
- **Modo trampa** (tecla T en el juego; se mantiene entre rondas): el jugador es invencible y
  hay atajos para observar el juego: N pasa a la siguiente ronda, 1 cambia la condición de alerta,
  2 hace aparecer un espía, 3 una formación y 4 da una carga de escudo.
- **Editor de niveles** (`src/game/editor_scene.py`; E o Back/Select del mando durante el juego
  para entrar y salir): edita la ronda que se estaba jugando. La cámara se mueve libremente
  (flechas, cruceta o stick; Shift o RB más rápido) y una mira en el centro indica dónde se actúa:
  Z/A coloca una base, X/B la borra, R/Y la gira (o cambia la orientación de las nuevas) y S/X del
  mando mueve el punto de partida; no deja poner bases encimadas ni sobre el inicio. Con O o Start
  se abre el menú de opciones: nivel y ronda que se editan, dificultad (1 a 10, aplica los ajustes
  de `difficulty.json` a enemigos, bases y formaciones), música de fondo, disparo triple, ítems de
  escudo, guardar el nivel en su JSON, volver a cargarlo del disco (descarta lo no guardado) y
  jugar. Al salir, la ronda se juega con los cambios aunque no se hayan guardado. En la versión web
  lo guardado se pierde al recargar la página (el navegador no deja escribir en los archivos).
- **Rendimiento**: las colisiones con obstáculos y bases usan una cuadrícula espacial
  (`src/ecs/utils/spatial_grid.py`) que tiene en cuenta que el mundo da la vuelta.
- **Estrellas**: colores al azar y brillo que sube y baja de 0 a 255 al mismo ritmo pero
  desfasado; en el juego tres capas con paralaje, en los menús caen de arriba hacia abajo.

## Controles

Teclado y mando funcionan a la vez; las asignaciones están en `assets/cfg/input.json`.

| Teclado | Mando | Menús | Juego |
|---|---|---|---|
| Flechas | Cruceta o stick izquierdo | Mover el cursor | Cambiar la dirección de la nave |
| Z / Enter | A (o X para disparar) | Aceptar | Disparar |
| X | B (o Y para el escudo) | Volver | Escudo |
| P / Esc | Start | | Pausa |
| F2 | | | Mostrar u ocultar las hitboxes |
| T | | | Modo trampa (N, 1, 2, 3, 4: atajos) |
| E | Back / Select | | Entrar y salir del editor de niveles |

El mando se detecta aunque se conecte con el juego abierto. En el navegador hay que pulsar un
botón del mando para que el navegador lo reconozca. La numeración de botones cambia según el
mando y el sistema: Start es el botón 7 en escritorio (mandos tipo Xbox) y el 9 en el navegador,
y la cruceta llega como "hat" o como los botones 12-15; ambos casos están asignados.

## Ejecución

```
pip install -r requirements.txt
python main.py
```

## Versión web

Desde la carpeta que contiene el proyecto:

```
pygbag --build <carpeta_del_proyecto>
```

El resultado queda en `build/web`; para itch.io se sube un `.zip` con su contenido.

## Créditos

- Imágenes (`naves.png`, `titulo.png`): Diana Pacheco, CC-BY-4.0.
- Música: "n-Dimensions (Main Theme - Retro Ver.)" y, en el jefe final, "Orbital Colossus", de
  Matthew Pablo (www.matthewpablo.com), CC-BY 3.0.
- Fuente Press Start 2P: CodeMan38, SIL Open Font License 1.1.
- Sonidos de la alerta, del espía, del despegue, de la fanfarria y de GAME OVER: generados para
  este proyecto con ffmpeg.
- Nave del jefe (`assets/img/jefe.png`, original "DurrrSpaceShip.png"): Tummyache, dominio público.
- Detalle de licencias en `assets/LICENCIAS.txt`.
- Sonido del motor: "Rocket Engine" de freesound_community (Pixabay).
