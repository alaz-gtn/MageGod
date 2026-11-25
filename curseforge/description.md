# MageGod

*Quality of life for mages in WoW Forever · Mejoras para magos en WoW Forever*

### At a glance

- 💜 **Purple lightning on Missile Barrage**: a big strike when it procs, calmer lightning while it lasts and the seconds it has left underneath
- ✨ **Blink is back**: its icon pops up big in the middle of the screen every time it's ready again
- 🛡️ **Buff reminders**: your armor, Arcane Intellect, mana gem and Well Fed (+5% XP from kills in Forever). Click one to cast it
- 📜 **Comprehension scrolls**: Imbue and Familiar, one click to use them; one click to decipher the scrolls you carry and to open your Bundle of Scrolls
- 🧊 **Ice Barrier and Mana Shield bar**: what's left of your shield
- 💧 **Five-second rule bar (MP5)**: when your Spirit gives mana back, and each tick
- 📏 **Range to your target**: melee, Frost Nova, in range of your main spell, at the edge of it or out of range, on the target's nameplate
- ⚠️ **Aggro warning** in a group, before you pull it off the tank
- 💰 **Talent reset price**: at your trainer, when the price of resetting your talents drops

### De un vistazo

- 💜 **Rayos morados con Missile Barrage** (el proc de Proyectiles Arcanos): un gran relámpago al salir, rayos más tranquilos mientras dura y debajo los segundos que le quedan
- ✨ **Traslación lista**: su icono sale en grande en el centro de la pantalla cada vez que vuelve
- 🛡️ **Recordatorios de bufos**: tu armadura, Intelecto Arcano, la gema de maná y Bien alimentado (+5% de experiencia por muerte en Forever). Con un clic se lanza
- 📜 **Pergaminos de Comprensión**: Imbuir y Familiar, con un clic se usan; con un clic se descifran los que llevas y se abre el paquete de pergaminos
- 🧊 **Barra de Barrera de hielo y Escudo de maná**: lo que le queda a tu escudo
- 💧 **Barra de la regla de los 5 segundos (MP5)**: cuándo te devuelve maná el Espíritu, y cada tick
- 📏 **Distancia al objetivo**: cuerpo a cuerpo, Nova de Escarcha, a tiro de tu hechizo principal, al límite o fuera de alcance, en la placa del objetivo
- ⚠️ **Aviso de agro** en grupo, antes de quitárselo al tanque
- 💰 **Precio de reiniciar talentos**: en tu instructor, cuándo baja el precio de reiniciar los talentos

Everything is set up from the **minimap button** or `/magegod`. English and Spanish.
Todo se configura desde el **botón del minimapa** o con `/magegod`. En inglés y en español.

---

## In combat too

Forever hides your buffs, your cooldowns and what your shield absorbs from addons during a fight. MageGod has the game itself draw them: the lightning, its countdown, the shield bar and the Blink pulse all work in combat.

## In detail

- **Missile Barrage**: two columns of lightning at your sides. Size, position, the space between them, how strong the strike and the calm lightning are, their colour and the countdown, all in the Procs tab. `/magegod lightning` shows it.
- **Blink**: its icon pops in, holds for a moment and fades in under a second as it grows. It ignores the global cooldown of your other spells. Size, strength and the colour of the shine behind it in the Procs tab; `/magegod blink` shows it.
- **Reminders**: grey when a buff is missing, in colour with its time left in its last minutes. Frost, Ice or Mage Armor (the last one you cast, or the one you choose), Arcane Intellect (Arcane Brilliance counts too) and, if you want, Dampen or Amplify Magic. Conjure the highest mana gem you know. Clicking a reminder casts it on you, out of combat.
- **Food and scrolls**: a small reminder when you're not Well Fed (not in combat, not at max level), and the Comprehension scrolls you carry and haven't used: Imbue for the weapon in your hand and Familiar. Carrying scrolls you haven't deciphered? A click casts Comprehend Scroll on the easiest one your Comprehension can read (it can backfire and turn you into a sheep for 8 seconds; the scroll isn't lost). Carrying a Bundle of Scrolls? A click opens it.
- **Shield bar**: as wide and tall as you want, to sit on top of the game's bars. Flat, with a one-pixel black edge and the shield's icon on its left.
- **MP5 bar**: grey and emptying for the five seconds after a spell that costs mana (not your wand), blue and filling up to each tick when your mana comes back, with what the last tick gave you. It hides with your mana full and, unless you say otherwise, out of combat.
- **Range**: red in melee (5 yd), yellow in Frost Nova range (10 yd), green in range of your main spell and light blue in its last 5 yards. Your main spell is the last one you cast of Frostbolt, Fireball and Arcane Missiles, or the one you choose. In yards or metres.
- **Aggro**: AGGRO 92% before you take it off the tank, and YOU HAVE AGGRO! when you do. Only in a group.
- **At your trainer**: a note under its window says when you last reset your talents, what it costs now, and when the price drops and to what; it shows under the trainer's price too. The game doesn't tell addons when you last reset or when the price drops, so MageGod writes down each reset you pay for from now on and counts from there: a step up with each reset (1, 5, 10, then 5 g more up to 50 g) and a step down for each week since the last one, as players report it. The price the trainer asks always wins. Class and legacy talents, each with its own price.
- Drag any display where you want it with **Move displays** (or `/magegod unlock`).

## Commands

- `/magegod` (or `/mago`): the options
- `/magegod unlock` · `lock`: move the displays
- `/magegod lightning` · `rayos`: try the Missile Barrage lightning
- `/magegod blink` · `traslacion`: try the Blink pulse
- `/magegod buffs` · `bufos`: what the addon sees of your buffs
- `/magegod range` · `rango`: what each range check says about your target
- `/magegod respec` · `talentos`: when the talent reset price drops

## License

GPLv3. The Fredoka One and Changa fonts are SIL Open Font License 1.1.
