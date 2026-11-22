"""The live conveyor rule reads fixed-BRL exits (b3/config/exit_brl.json) as the research does (owner 2026-11-21)."""
import numpy as np

from b3 import esteira as es
from b3 import esteira_live as el
from b3 import p026_lab as lab
from b3.markets import market


def test_brl_exit_distances_match_the_research():
    fam = es.load_families()[0]
    p = fam.variants()[0]
    st = el.build(fam.id, fam.markets[0], fam.timeframes[0], p, "B1")()
    inst = market(fam.markets[0]).instrument()
    research = lab.distances(el.EXITS["B1"], np.array([170000.0]), np.array([np.nan]), np.array([np.nan]),
                             np.array([0.001]), inst.point_value_brl, inst.tick_size)
    assert st._dist("stop", 0.001, 170000.0) == research["stop"][0]
    assert st._dist("target", 0.001, 170000.0) == research["target"][0]
    assert set(el.EXITS) >= {"S1", "S2", "S3", "S4", "B1", "B2", "B3", "B4", "B5"}
