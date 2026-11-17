"""Modulo 2 - posesion temporal: convierte evidencia en H / A / D / X por frame.

H = local controla, A = visitante controla, D = balon detenido, X = desconocido
o frame fuera de los halves. Devuelve una lista con UNA etiqueta legal por frame.

Entradas (arreglos por frame, indexados por frame tactico, precision completa):
    M1: score_home, score_away, ball_visible, home_available, away_available
    M4: dead_score, dead_available, restart_score, restart_available, restart_side
    half_blocks: OBLIGATORIO, lista de (inicio, fin) INCLUSIVOS; el runner pasa
                 half_video_blocks(GAME) (11185-90651 y 110808-190197).
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
"""

from dataclasses import dataclass

import numpy as np

LADOS = ("H", "A")


@dataclass(frozen=True)
class ConfigM2:
    """VALORES PROVISIONALES: umbrales, duraciones y prioridad los acuerda el equipo."""
    confirm_frames: int = 5          # cambio de control: frames creibles consecutivos
    min_score: float = 0.0           # magnitud minima del score maximo
    min_margin: float = 0.0          # |sh - sa| debe ser ESTRICTAMENTE mayor
    dead_min_score: float = 0.5      # igual a pause_anchor_score de M4
    dead_confirm_frames: int = 3
    restart_min_score: float = 0.5
    restart_confirm_frames: int = 3
    same_frame_priority: str = "dead"  # "dead" | "restart"


CONFIG_M2 = ConfigM2()


def _entero(valor, nombre):
    if isinstance(valor, bool) or not isinstance(valor, (int, np.integer)):
        raise ValueError("{} debe ser un entero".format(nombre))
    return int(valor)


def _scores(valores, nombre):
    arr = np.asarray(valores, dtype=float)
    if not np.all(np.isfinite(arr)) or np.any(arr < 0) or np.any(arr > 1):
        raise ValueError("{} debe ser finito y estar en [0, 1]".format(nombre))
    return arr


def _validar(entradas, half_blocks, config):
    if (_entero(config.confirm_frames, "confirm_frames") < 1
            or _entero(config.dead_confirm_frames, "dead_confirm_frames") < 1
            or _entero(config.restart_confirm_frames, "restart_confirm_frames") < 1
            or config.min_score < 0 or config.min_margin < 0
            or not 0 < config.dead_min_score <= 1 or not 0 < config.restart_min_score <= 1
            or config.same_frame_priority not in ("dead", "restart")):
        raise ValueError("ConfigM2 invalida")
    n = len(entradas["score_home"])
    for nombre, valores in entradas.items():
        if np.ndim(valores) != 1 or len(valores) != n:
            raise ValueError("{} debe ser 1-D con {} elementos".format(nombre, n))
    lados = list(entradas["restart_side"])
    if any(l is not None and l not in LADOS for l in lados):
        raise ValueError("restart_side solo admite 'H', 'A' o None")

    bloques, previo_fin = [], -1
    for bloque in half_blocks:
        ini, fin = _entero(bloque[0], "inicio de half"), _entero(bloque[1], "fin de half")
        if not (0 <= ini <= fin < n) or ini <= previo_fin:
            raise ValueError("half_blocks: inclusivos, ordenados, sin solaparse y dentro de los arreglos")
        bloques.append((ini, fin))
        previo_fin = fin

    sh, sa = _scores(entradas["score_home"], "score_home"), _scores(entradas["score_away"], "score_away")
    dead = _scores(entradas["dead_score"], "dead_score")
    restart = _scores(entradas["restart_score"], "restart_score")
    visible = np.asarray(entradas["ball_visible"]).astype(bool)
    h_disp = np.asarray(entradas["home_available"]).astype(bool)
    a_disp = np.asarray(entradas["away_available"]).astype(bool)
    dead_ok = np.asarray(entradas["dead_available"]).astype(bool) & (dead >= config.dead_min_score)
    restart_ok = np.asarray(entradas["restart_available"]).astype(bool) & (restart >= config.restart_min_score)
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
    """Regresa la lista de etiquetas ('H','A','D','X'), una por frame de entrada."""
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