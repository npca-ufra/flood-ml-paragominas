"""Expected contamination of the Spy labels (Reviewer 3, comment 4), indicative only because SCAR does not hold.

The Elkan-Noto label frequency c = P(s=1 | y=1) is estimated on D* with the same Random Forest estimator used in
the benchmark (out-of-bag probabilities of the labeled samples). Hidden positives in the unlabeled pool:
H = n_labeled (1 - c) / c. The share of spies below the threshold estimates the share of hidden positives that
fall among the reliable negatives."""
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

from common import FEATS, load, protocol_5fold, results_dir, spy_scores, threshold

OUT = results_dir("results")
d = load()
Dstar, _, labels, _, _ = protocol_5fold(d)
m = RandomForestClassifier(100, random_state=42, n_jobs=-1, oob_score=True, min_samples_leaf=5).fit(Dstar[FEATS], Dstar.classes)
c = m.oob_decision_function_[Dstar.classes.values == 1, 1].mean()
n_pos, n_unl = int((Dstar.classes == 1).sum()), int((Dstar.classes == 0).sum())
hidden = n_pos * (1 - c) / c
pos, unl = Dstar[Dstar.classes == 1], Dstar[Dstar.classes == 0]
p_spy, p_unl = spy_scores(pos[FEATS].values, unl[FEATS].values)
rows = []
for name, rule in [("first quartile (paper)", "paper"), ("mu-sigma", "musigma"), ("10th percentile", 0.10)]:
    tau = threshold(p_spy, rule)
    below = (p_spy < tau).mean()
    rn, promoted = int((p_unl < tau).sum()), int((p_unl >= tau).sum())
    hid_rn = below * hidden
    hid_prom = hidden - hid_rn
    rows.append(dict(rule=name, tau=tau, spies_below=below, reliable_negatives=rn, promoted=promoted,
                     hidden_positives_in_U=hidden, expected_positives_in_RN=hid_rn, RN_contamination=hid_rn / rn,
                     expected_true_positives_among_promoted=hid_prom, expected_negatives_among_promoted=promoted - hid_prom,
                     share_of_Dstar_positives_likely_negative=(promoted - hid_prom) / (n_pos + promoted)))
res = pd.DataFrame(rows)
res.insert(0, "label_frequency_c", c)
res.to_csv(OUT / "13_label_contamination.csv", index=False)
print(f"c = {c:.3f}; hidden positives in U = {hidden:.0f} of {n_unl} ({hidden / n_unl:.1%})")
print(res.round(3).to_string(index=False))
