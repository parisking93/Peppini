import torch
import sys
import os

# Aggiungi il path del progetto per gli import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading.RLReward import PnlRewardManager

def test_pnl_reward():
    manager = PnlRewardManager(pnl_scale=2.0, win_bonus=0.5, loss_penalty=1.0)

    # Test 1: Profitto senza chiusura
    r1 = manager.calculate_reward(pnl_delta=0.1, is_closed=False)
    print(f"Test 1 (Profit, open): {r1} (Expected: 0.2)")
    assert abs(r1 - 0.2) < 1e-6

    # Test 2: Perdita senza chiusura
    r2 = manager.calculate_reward(pnl_delta=-0.05, is_closed=False)
    print(f"Test 2 (Loss, open): {r2} (Expected: -0.1)")
    assert abs(r2 - (-0.1)) < 1e-6

    # Test 3: Chiusura in profitto
    r3 = manager.calculate_reward(pnl_delta=0.2, is_closed=True, total_pnl=1.0)
    print(f"Test 3 (Win, closed): {r3} (Expected: 0.2*2 + 0.5 = 0.9)")
    assert abs(r3 - 0.9) < 1e-6

    # Test 4: Chiusura in perdita
    r4 = manager.calculate_reward(pnl_delta=-0.1, is_closed=True, total_pnl=-0.5)
    print(f"Test 4 (Loss, closed): {r4} (Expected: -0.1*2 - 1.0 = -1.2)")
    assert abs(r4 - (-1.2)) < 1e-6

    # Test 5: Halt penalty
    r5 = manager.get_halt_penalty(trend_strength=0.05, side_prediction=2)
    print(f"Test 5 (Halt penalty): {r5} (Expected: -0.05 * 0.05 = -0.0025)")
    assert abs(r5 - (-0.0025)) < 1e-6

    print("\n[OK] Tutti i test sui reward passati!")

if __name__ == "__main__":
    test_pnl_reward()
