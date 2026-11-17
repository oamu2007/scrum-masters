"""Pruebas de secuencias inventadas para modulo2.py (cada caracter = un frame).

  control: h local | a visitante | . balon oculto | t empate | w debil | u local sin datos
  parada : d evidencia de parada (control empatado)
  reanuda: 0 sin lado | 1 lado H | 2 lado A | z reanudacion debil | q parada y reanudacion

Corre con `python modulos/test_modulo2.py` o `python -m unittest discover -s tests -v`.
"""

import sys
from pathlib import Path
import unittest

import numpy as np

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from modulos.modulo2 import ConfigM2, modulo2

# (sh, sa, visible, h_disp, a_disp, dead_score, dead_av, restart_score, restart_av, side)
_FRAME = {
    'h': (.9, .1, 1, 1, 1, 0, 0, 0, 0, None), 'a': (.1, .9, 1, 1, 1, 0, 0, 0, 0, None),
    '.': (0, 0, 0, 0, 0, 0, 0, 0, 0, None), 't': (.5, .5, 1, 1, 1, 0, 0, 0, 0, None),
    'w': (.02, .01, 1, 1, 1, 0, 0, 0, 0, None), 'u': (0, .9, 1, 0, 1, 0, 0, 0, 0, None),
    'd': (.5, .5, 1, 1, 1, .8, 1, 0, 0, None),
    '0': (.5, .5, 1, 1, 1, 0, 0, .8, 1, None), '1': (.5, .5, 1, 1, 1, 0, 0, .8, 1, 'H'),
    '2': (.5, .5, 1, 1, 1, 0, 0, .8, 1, 'A'), 'z': (.5, .5, 1, 1, 1, 0, 0, .2, 1, None),
    'q': (.5, .5, 1, 1, 1, .8, 1, .8, 1, None),
}
_CFG = ConfigM2(confirm_frames=3, min_score=0.05, dead_confirm_frames=2, restart_confirm_frames=2)


def _corre(seq, bloques=None, cfg=_CFG):
    cols = list(zip(*[_FRAME[c] for c in seq]))
    return "".join(modulo2(*cols, half_blocks=bloques or [(1, 0, len(seq) - 1)], config=cfg))


def _base(n):
    ceros = [0] * n
    return dict(score_home=ceros, score_away=ceros, ball_visible=[1] * n, home_available=[1] * n,
                away_available=[1] * n, dead_score=ceros, dead_available=ceros,
                restart_score=ceros, restart_available=ceros, restart_side=[None] * n,
                half_blocks=[(1, 0, n - 1)])


class SequenceTests(unittest.TestCase):
    def test_pase_con_oclusion_y_desvio_breve_conservan_control(self):
        assert _corre("hhh..h") == "XXHHHH"
        assert _corre("hhhaahhh") == "XXHHHHHH"


    def test_control_visitante_sostenido_cambia_una_vez(self):
        assert _corre("hhhaaaaa") == "XXHHHAAA"


    def test_sin_datos_de_un_equipo_no_gana_la_comparacion(self):
        assert _corre("hhhuuuuuu") == "XXHHHHHHH"
        assert _corre("uuuuu") == "XXXXX"


    def test_empate_y_evidencia_debil_son_incertidumbre(self):
        assert _corre("hhhtttt") == "XXHHHHH"
        assert _corre("wwww") == "XXXX"


    def test_parada_requiere_confirmacion(self):
        assert _corre("hhhdhhh") == "XXHHHHH"


    def test_D_persiste_con_balon_oculto_y_cercania(self):
        assert _corre("hhhdd" + "a.ah.h") == "XXHHD" + "D" * 6


    def test_reanudacion_segun_lado(self):
        base = "hhhdd" + "a.a"
        assert _corre(base + "00" + "aaa") == "XXHHDDDDD" + "XXXA"   # sin lado: X hasta control creible
        assert _corre(base + "11" + "aaa") == "XXHHDDDDD" + "HHHA"   # lado conocido se conserva
        assert _corre(base + "22" + "aaa") == "XXHHDDDDD" + "AAAA"
        assert _corre(base + "12" + "aaa") == "XXHHDDDDD" + "XXXA"   # contradictorio: X, nunca A por defecto


    def test_reanudacion_debil_o_aislada_no_termina_D(self):
        assert _corre("hhhdd" + "zzzz" + "aaa") == "XXHHD" + "D" * 7
        assert _corre("hhhdd" + "0" + "aaaa") == "XXHHD" + "D" * 5


    def test_reanudacion_sin_D_no_cambia_nada(self):
        assert _corre("hhhh0000") == "XXHHHHHH"


    def test_prioridad_en_el_mismo_frame(self):
        assert _corre("hhhdd" + "qq" + "aaa") == "XXHHD" + "D" * 5
        cfg = ConfigM2(confirm_frames=3, min_score=0.05, dead_confirm_frames=2,
                       restart_confirm_frames=2, same_frame_priority="restart")
        assert _corre("hhhdd" + "qq" + "aaa", cfg=cfg) == "XXHHDDXXXA"


    def test_halves_independientes(self):
        seq = "hh" + "hhhdd.ah" + ".." + "hhhhhhhh" + "hh"
        completo = _corre(seq, [(1, 2, 9), (2, 12, 19)])
        solo_h2 = _corre(seq, [(2, 12, 19)])
        assert completo[:2] == "XX" and completo[2:10] == "XXHHDDDD"   # D no cruza al half 2
        assert completo[10:12] == "XX" and completo[20:] == "XX"
        assert completo[12:20] == solo_h2[12:20] == "XXHHHHHH"


    def test_validaciones(self):
        casos = [dict(score_home=[0, 0]), dict(score_home=[float("nan")] * 3),
                 dict(dead_score=[1.5] * 3), dict(restart_side=["Z", None, None]),
                 dict(half_blocks=[(1, 0, 1), (2, 1, 2)])]
        for cambio in casos:
            try:
                modulo2(**{**_base(3), **cambio})
            except ValueError:
                continue
            raise AssertionError("debio lanzar ValueError: {}".format(cambio))


    def test_etiqueta_legal_por_frame_con_datos_aleatorios(self):
        rng = np.random.default_rng(0)
        n = 400
        for _ in range(50):
            a = dict(score_home=rng.random(n), score_away=rng.random(n),
                     ball_visible=rng.random(n) > .3, home_available=rng.random(n) > .2,
                     away_available=rng.random(n) > .2,
                     dead_score=rng.random(n) * (rng.random(n) > .85), dead_available=rng.random(n) > .3,
                     restart_score=rng.random(n) * (rng.random(n) > .9), restart_available=rng.random(n) > .5,
                     restart_side=rng.choice(np.array(["H", "A", None], dtype=object), n))
            # Generate valid producer contracts; unavailable evidence remains zero.
            for side in ("home", "away"):
                a[side + "_available"] &= a["ball_visible"]
                a["score_" + side][~a[side + "_available"]] = 0
            a["dead_score"][~a["dead_available"]] = 0
            a["restart_score"][~a["restart_available"]] = 0
            full = modulo2(**a, half_blocks=[(1, 20, 180), (2, 220, 380)], config=_CFG)
            solo_h2 = modulo2(**a, half_blocks=[(2, 220, 380)], config=_CFG)
            assert len(full) == n and set(full) <= set("HADX")
            assert set(full[:20] + full[181:220] + full[381:]) == {"X"}
            assert full[220:381] == solo_h2[220:381]


if __name__ == "__main__":
    unittest.main()
