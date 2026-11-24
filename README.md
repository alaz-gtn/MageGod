# MageGod

Addon de mejoras para magos en WoW Forever, hermano de HunterGod y con la misma ventana de opciones en azul de mago. De momento hace esto:

- Recuerda los bufos que te faltan: la armadura (escarcha, hielo o mago), Intelecto Arcano (vale también Luminosidad Arcana) y, si quieres, Amortiguar o Amplificar magia. Los muestra en gris cuando no los llevas y en color, con lo que les queda, en sus últimos minutos.
- Recuerda conjurar la gema de maná del rango más alto que sabes hacer, o todas si lo pides. Solo fuera de combate.
- Haciendo clic en un recordatorio se lanza ese bufo en ti (o se conjura la gema). Solo fuera de combate: en combate el juego no deja a los addons tocar esos botones.
- Una barra con lo que le queda a tu Barrera de hielo o Escudo de maná, del ancho y alto que quieras, para ponerla encima de las barras del juego. Va con el mismo estilo que la del MP5: plana, con borde negro de un píxel, letra fina y el icono del escudo en su etiqueta a la izquierda; el color se elige en las opciones. Forever esconde cuánto absorbe un escudo, pero deja pasárselo a la barra y a su número, que los rellena el propio juego.
- Una barra para la regla de los 5 segundos: un hechizo que gasta maná corta la regeneración del Espíritu 5 segundos (la varita no). Gris y vaciándose mientras esperas; azul cuando el maná vuelve, llenándose hasta cada tick, que llega cada 2 segundos, con lo que te dio el último. A su izquierda pone MP5, en gris mientras esperas y en verde mientras regeneras. Se esconde con el maná lleno y, si no dices lo contrario, fuera de combate. Los dos colores de la barra se cambian en las opciones.
- Un aviso pequeño cuando no llevas Bien alimentado, que en Forever da +5% de experiencia por muerte. No sale en combate ni a nivel máximo.
- Junto al de la comida, los pergaminos de Comprensión que llevas y no has usado: Imbuir (para el arma que llevas en la mano) y Familiar. Haciendo clic se usa el pergamino. Se da por usado cuando sale de las bolsas (no si lo vendes, lo mandas o lo guardas en el banco) y no vuelve a avisar en una hora; el de imbuir tampoco avisa si el arma ya lleva un encantamiento temporal. Los IDs salen de la tabla de Method (beta, hasta nivel 30).
- La distancia al objetivo: rojo a melee (5 yd), amarillo al alcance de Nova (10 yd), verde a tiro de tu hechizo principal y azul brillante en sus últimas 5 yardas. El hechizo principal es el último que lanzaste de Descarga de escarcha, Bola de fuego y Proyectiles Arcanos, o el que elijas.
- Rayos morados a los dos lados de tu personaje mientras dura Missile Barrage (el proc de Proyectiles Arcanos: tus próximos Proyectiles Arcanos no gastan maná y van más rápidos), con un gran relámpago al salir el proc que a los segundos se calma (más transparente y más lento) mientras dura, y debajo, centrados, los segundos que le quedan. Forever esconde los bufos en combate, así que los dibuja el propio juego: un contenedor de auras vigila ese bufo y el juego reproduce las animaciones de los rayos mientras dura, como hace ForeverAuras. Tamaño, posición, separación, intensidad del relámpago y de después, y color en las opciones (pestaña Procs); `/magegod rayos` los prueba. Vigila los IDs de Missile Barrage de Forever (400589, 401736 y 467409) y, fuera de combate, aprende otro si el bufo sale con otro número o quita uno que no se acaba nunca (un pasivo).
- Cada vez que vuelve Traslación, su icono sale en grande en el centro de la pantalla con un destello detrás y se desvanece en menos de un segundo. En combate Forever esconde cuánto le falta a un hechizo, pero no si está en reutilización: el aviso salta cuando Traslación pasa de en reutilización a lista. Si en combate no sabe si era su reutilización o la global, cuenta como suya si duró más de 2,5 s. Tamaño, intensidad y color en la pestaña Procs; `/magegod traslacion` lo prueba y se mueve con Mover avisos.
- El aviso de agro en grupo: AGRO 92% antes de quitárselo al tanque, y ¡TIENES EL AGRO! cuando se lo quitas.

## Carpetas

- `MageGod/`: el addon tal como se instala en `_forever_\Interface\AddOns`. En este PC esa carpeta es una unión (junction) a esta, así que los cambios llegan al juego sin copiar nada: con `/reload` basta, salvo los archivos nuevos, que piden reiniciar el juego.
- `tools/`: `test_addon.py` (pruebas con lupa), `make_logo.py` (logo e icono), `make_lightning.py` (las texturas de los rayos; estos dos necesitan pillow), `build_zip.py` (el zip) y `publish.py` (la subida a CurseForge).
- `curseforge/`: el logo, la descripción de la página y las notas de cada versión.
- `release/`: los zips, que no van al repositorio.

## Probar

`python -I tools/test_addon.py MageGod enUS` y lo mismo con `esES`.

## Sacar una versión nueva

1. Cambia `## Version:` en `MageGod/MageGod.toc` y añade su entrada en `curseforge/changelog.md`.
2. Pasa las pruebas en los dos idiomas.
3. Haz commit, crea la etiqueta `v<versión>` y súbela (`git push origin main v<versión>`). GitHub Actions (`.github/workflows/release.yml`) prueba el addon y lo sube a CurseForge con su nota de cambios (`tools/publish.py`, con la clave de CurseForge en el secreto `CF_API_KEY` del repositorio y el proyecto en `## X-Curse-Project-ID` del TOC). Para ver el zip sin subirlo: `python -I tools/build_zip.py` o `python -I tools/publish.py --dry-run`.

La descripción de la página de CurseForge (`curseforge/description.md`) no la sube `publish.py`: se pega a mano.

## En Forever

Forever esconde los bufos a los addons en combate. Por eso los tiempos se leen fuera de combate y en combate se siguen por lo que lanzas. Lo que lanzas en combate se da por puesto en ti.

En el juego, `/magegod bufos` dice lo que el addon ve y `/magegod rango` qué dice cada comprobación de distancia.
