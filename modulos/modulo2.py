"""Modulo 2 - posesion temporal: convierte evidencia en H / A / D / X por frame.

H = local controla, A = visitante controla, D = balon detenido, X = desconocido
o frame fuera de los halves. Devuelve una lista con UNA etiqueta legal por frame.

Entradas (arreglos por frame, indexados por frame tactico, precision completa):
    M1: score_home, score_away, ball_visible, home_available, away_available
    M4: dead_score, dead_available, restart_score, restart_available, restart_side
    half_blocks: OBLIGATORIO, triples (half, inicio, fin), limites INCLUSIVOS;
                 acepta directamente games.half_video_blocks(GAME).
                 Pares no se aceptan. [] deja todos los frames en X.
    config: ConfigM2.
Ejemplo en el runner:
    modulo2(**{k: m1[k] for k in ("score_home", "score_away", "ball_visible",
                                  "home_available", "away_available")},
            **m4, half_blocks=half_video_blocks(GAME))

Reglas de transicion
 1. Cada half se decodifica por separado con estado limpio (X, sin confirmaciones
    pendientes). Fuera de los halves se emite X. Nada se arrastra entre halves.
 2. Control creible de un lado: balon visible, home_available Y away_available,
    max(score) >= min_score y |sh - sa| > min_margin. Nunca se gana por comparar
    contra el 0 de un equipo sin datos.
 3. Un cambio H<->A, o X->H/A, exige confirm_frames frames creibles CONSECUTIVOS
    del mismo lado. Un frame no creible (balon oculto, sin datos, debil, empate) o
    creible para el lado ya establecido borra la confirmacion; mientras tanto se
    conserva el lado establecido (pases, desvios breves).
 4. D empieza tras dead_confirm_frames frames consecutivos con dead_available y
    dead_score >= dead_min_score. Es un estado persistente: balon oculto, cercania
    o ventanas de tag NO lo terminan.
 5. D termina solo tras restart_confirm_frames frames consecutivos con
    restart_available y restart_score >= restart_min_score. El lado es el unico
    restart_side conocido (H/A) visto durante esa confirmacion; si no hay lado o
    hay H y A, queda X hasta control creible. Nunca se asume A.
 6. Frame con evidencia de parada y de reanudacion a la vez: gana
    config.same_frame_priority ("dead" o "restart"); el otro lado no cuenta ese frame.
 7. Evidencia de reanudacion sin D activo no cambia nada.

Validacion y valores predeterminados: ver M2.md. Scores numericos reales [0,1],
flags Boolean o 0/1 numerico; nunca strings ni coercion por truthiness. Evidencia
no disponible debe tener score cero; disponibilidad M1 implica balon visible.
La reanudacion puede estar disponible sin jugadores visibles ni dead_available.
Los valores predeterminados son heuristicas justificadas con casos inventados,
no probabilidades de control ni parametros elegidos con etiquetas publicas.
"""

from dataclasses import dataclass
import math
from numbers import Real

import numpy as np

LADOS = ("H", "A")


@dataclass(frozen=True)
class ConfigM2:
    """Heuristicas de proximidad/tiempo; no prueban posesion controlada. Ver M2.md."""
    confirm_frames: int = 12         # 0.48 s nominales a 25 fps; confirma en frame 12
    min_score: float = 0.10          # exp(-d/3) >= .10 equivale a d <= 6.91 m
    min_margin: float = 0.05         # diferencia absoluta ESTRICTAMENTE mayor
    dead_min_score: float = 0.5      # soporte M4; no probabilidad calibrada
    dead_confirm_frames: int = 3
    restart_min_score: float = 0.5
    restart_confirm_frames: int = 3
    same_frame_priority: str = "dead"  # "dead" | "restart"


CONFIG_M2 = ConfigM2()


def _entero(valor, nombre):
    if isinstance(valor, (bool, np.bool_)) or not isinstance(valor, (int, np.integer)):
        raise ValueError("{} debe ser un entero".format(nombre))
    return int(valor)


def _vector(valores, nombre):
    try:
        arr = np.asarray(valores)
    except (ValueError, TypeError):
        raise ValueError("{} debe ser un arreglo 1-D regular".format(nombre)) from None
    if arr.ndim != 1:
        raise ValueError("{} debe ser un arreglo 1-D".format(nombre))
    return arr


def _scores(arr, nombre, original):
    # Inspect dtype before conversion: numeric strings/complex/bools are not scores.
    boolean_mixto = (isinstance(original, (list, tuple))
                     and any(isinstance(valor, (bool, np.bool_)) for valor in original))
    if arr.dtype.kind not in "iuf" or boolean_mixto:
        raise ValueError("{} debe contener scores numericos reales, sin strings ni Boolean".format(nombre))
    if not np.all(np.isfinite(arr)) or np.any(arr < 0) or np.any(arr > 1):
        raise ValueError("{} debe ser finito y estar en [0, 1]".format(nombre))
    # Integer 0/1 scores are legal, but unsigned subtraction must not wrap.
    return arr.astype(float) if arr.dtype.kind in "iu" else arr


def _flags(arr, nombre):
    if (arr.dtype.kind not in "biuf" or not np.all(np.isfinite(arr))
            or not np.all((arr == 0) | (arr == 1))):
        raise ValueError("{} solo admite Boolean o 0/1 numerico finito".format(nombre))
    return arr.astype(bool, copy=False)


def _validar_config(config):
    if not isinstance(config, ConfigM2):
        raise ValueError("config debe ser ConfigM2")
    for nombre in ("confirm_frames", "dead_confirm_frames", "restart_confirm_frames"):
        if _entero(getattr(config, nombre), nombre) < 1:
            raise ValueError("{} debe ser un entero positivo".format(nombre))
    for nombre in ("min_score", "min_margin", "dead_min_score", "restart_min_score"):
        valor = getattr(config, nombre)
        if (isinstance(valor, (bool, np.bool_)) or not isinstance(valor, Real)
                or not 0 <= valor <= 1 or not math.isfinite(valor)
                or (nombre in ("dead_min_score", "restart_min_score") and valor == 0)):
            intervalo = "[0, 1]" if nombre in ("min_score", "min_margin") else "(0, 1]"
            raise ValueError("{} debe ser un numero real finito en {}".format(nombre, intervalo))
    if (not isinstance(config.same_frame_priority, str)
            or config.same_frame_priority not in ("dead", "restart")):
        raise ValueError("same_frame_priority solo admite 'dead' o 'restart'")


def _bloques(half_blocks, n):
    if isinstance(half_blocks, (str, bytes, dict, set, frozenset)):
        raise ValueError("half_blocks debe contener triples (half, inicio, fin)")
    try:
        bloques_entrada = list(half_blocks)
    except TypeError:
        raise ValueError("half_blocks debe contener triples (half, inicio, fin)") from None
    bloques, previo_fin, previo_half = [], -1, 0
    for indice, bloque in enumerate(bloques_entrada):
        nombre = "half_blocks[{}]".format(indice)
        if isinstance(bloque, (str, bytes, dict, set, frozenset)):
            raise ValueError(nombre + " debe ser un triple (half, inicio, fin)")
        try:
            triple = tuple(bloque)
        except TypeError:
            raise ValueError(nombre + " debe ser un triple (half, inicio, fin)") from None
        if len(triple) != 3:
            raise ValueError(nombre + " debe tener exactamente 3 elementos (half, inicio, fin)")
        half, ini, fin = (_entero(valor, nombre + "." + campo)
                          for valor, campo in zip(triple, ("half", "inicio", "fin")))
        if half <= previo_half:
            raise ValueError(nombre + ".half debe ser positivo y estrictamente creciente")
        if not (0 <= ini <= fin < n) or ini <= previo_fin:
            raise ValueError(nombre + ": limites inclusivos, ordenados, sin solaparse y dentro de los arreglos")
        bloques.append((ini, fin))
        previo_fin, previo_half = fin, half
    return bloques


def _validar(entradas, half_blocks, config):
    _validar_config(config)
    arrays = {nombre: _vector(valores, nombre) for nombre, valores in entradas.items()}
    n = len(arrays["score_home"])
    for nombre, arr in arrays.items():
        if len(arr) != n:
            raise ValueError("{} debe tener {} elementos, como score_home".format(nombre, n))
    sh, sa, dead, restart = (_scores(arrays[nombre], nombre, entradas[nombre])
                             for nombre in ("score_home", "score_away", "dead_score", "restart_score"))
    visible, h_disp, a_disp, dead_disp, rest_disp = (
        _flags(arrays[nombre], nombre) for nombre in
        ("ball_visible", "home_available", "away_available", "dead_available", "restart_available"))
    lados = list(arrays["restart_side"])
    if any(l is not None and (not isinstance(l, str) or l not in LADOS) for l in lados):
        raise ValueError("restart_side solo admite 'H', 'A' o None")
    for nombre, disponible in (("home_available", h_disp), ("away_available", a_disp)):
        if np.any(disponible & ~visible):
            raise ValueError(nombre + " implica ball_visible")
    for nombre, score, disponible in (("score_home", sh, h_disp), ("score_away", sa, a_disp),
                                      ("dead_score", dead, dead_disp), ("restart_score", restart, rest_disp)):
        if np.any(score[~disponible] != 0):
            raise ValueError(nombre + " debe ser cero cuando su evidencia no esta disponible")
    bloques = _bloques(half_blocks, n)
    dead_ok = dead_disp & (dead >= config.dead_min_score)
    restart_ok = rest_disp & (restart >= config.restart_min_score)
    ambos = dead_ok & restart_ok
    if config.same_frame_priority == "dead":
        restart_ok = restart_ok & ~ambos
    else:
        dead_ok = dead_ok & ~ambos
    return n, bloques, sh, sa, visible, h_disp, a_disp, dead_ok, restart_ok, lados


def _decodificar_half(ini, fin, sh, sa, visible, h_disp, a_disp, dead_ok, restart_ok,
                      lados, config, etiquetas):
    estado = 'X'          # estado limpio al inicio de cada half
    pendiente, n_pend = None, 0
    n_dead, n_rest, lados_vistos = 0, 0, set()
    for i in range(ini, fin + 1):
        if estado != 'D':
            n_dead = n_dead + 1 if dead_ok[i] else 0
            if n_dead >= config.dead_confirm_frames:
                estado, pendiente, n_pend = 'D', None, 0
                n_dead, n_rest, lados_vistos = 0, 0, set()
        elif restart_ok[i]:
            n_rest += 1
            if lados[i] is not None:
                lados_vistos.add(lados[i])
            if n_rest >= config.restart_confirm_frames:
                estado = next(iter(lados_vistos)) if len(lados_vistos) == 1 else 'X'
                pendiente, n_pend = None, 0
                n_dead, n_rest, lados_vistos = 0, 0, set()
        else:
            n_rest, lados_vistos = 0, set()

        if estado == 'D':
            etiquetas[i] = 'D'
            continue

        creible = None
        if visible[i] and h_disp[i] and a_disp[i]:
            if max(sh[i], sa[i]) >= config.min_score and abs(sh[i] - sa[i]) > config.min_margin:
                creible = 'H' if sh[i] > sa[i] else 'A'

        if creible is None or creible == estado:
            pendiente, n_pend = None, 0          # se conserva el estado establecido
        else:
            n_pend = n_pend + 1 if pendiente == creible else 1
            pendiente = creible
            if n_pend >= config.confirm_frames:
                estado, pendiente, n_pend = creible, None, 0
        etiquetas[i] = estado


def modulo2(score_home, score_away, ball_visible, home_available, away_available,
            dead_score, dead_available, restart_score, restart_available, restart_side,
            half_blocks, config=CONFIG_M2):
    """Una etiqueta H/A/D/X por frame; valida todas las entradas antes de decodificar.

    half_blocks contiene triples inclusivos (half, inicio, fin), directamente de
    games.half_video_blocks(GAME). [] produce solo X; entradas vacias con [] dan [].
    Pares, bloques fuera de rango y evidencia/configuracion invalida dan ValueError
    con el nombre del campo. Nunca modifica los arreglos o bloques del llamador.
    """
    entradas = dict(score_home=score_home, score_away=score_away, ball_visible=ball_visible,
                    home_available=home_available, away_available=away_available,
                    dead_score=dead_score, dead_available=dead_available,
                    restart_score=restart_score, restart_available=restart_available,
                    restart_side=restart_side)
    (n, bloques, sh, sa, visible, h_disp, a_disp,
     dead_ok, restart_ok, lados) = _validar(entradas, half_blocks, config)
    etiquetas = ['X'] * n
    for ini, fin in bloques:
        _decodificar_half(ini, fin, sh, sa, visible, h_disp, a_disp, dead_ok,
                          restart_ok, lados, config, etiquetas)
    return etiquetas
