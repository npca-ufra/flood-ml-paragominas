"""Sector-level views of two pooled recall values (Sects. 4.3 and 4.4, Table S7).

  * Recall of the 342 confirmed positives of the held-out test partition (notebook 3.1), with a 95% interval
    from resampling the CPRM/SGB sectors the test pixels belong to (nearest sector, as in protocol_lso).
  * Recall per withheld sector of the leave-sector-out benchmark (05_recall_per_held_out_sector.csv) with the
    number of positives per sector, and the unweighted mean and median across sectors.
"""
import numpy as np
import pandas as pd

from common import FEATS, load, protocol_5fold, protocol_lso, results_dir, rf

OUT = results_dir("results")
d = load()
Dstar, test, labels, _, _ = protocol_5fold(d)
sector = protocol_lso(d)[0].group                      # nearest sector of every sample (index of d)

# held-out partition: same model as notebook 3.1 (Random Forest on D* with the paper labels)
yhat = rf().fit(Dstar[FEATS], labels.loc[Dstar.index]).predict(test[FEATS])
pos = test.index[test.classes.values == 1]
hits = pd.Series(yhat[test.classes.values == 1], index=pos).groupby(sector.loc[pos].values)
n_per, k_per = hits.size(), hits.sum()
rng = np.random.default_rng(0)
boot = []
for _ in range(1000):
    pick = rng.choice(n_per.index, len(n_per), replace=True)
    boot.append(k_per.loc[pick].sum() / n_per.loc[pick].sum())
lo, hi = np.quantile(boot, [0.025, 0.975])
recall = k_per.sum() / n_per.sum()
pd.DataFrame([dict(n_positives=len(pos), n_sectors=len(n_per), recall=recall, lo=lo, hi=hi)]
             ).to_csv(OUT / "21_test_recall_sector_bootstrap.csv", index=False)
print(f"test partition: recall {recall:.3f} (95% sector bootstrap {lo:.2f}-{hi:.2f}); "
      f"{len(pos)} positives in {len(n_per)} sectors; positives per sector: {n_per.sort_values().tolist()}")

# leave-sector-out: recall per withheld sector with the number of positives it holds
rec = pd.read_csv(OUT / "05_recall_per_held_out_sector.csv").set_index("group")
n_pos = d[d.classes == 1].groupby(sector[d.classes == 1].values).size()
cols = ["PU-RF", "RF + random negatives (1:1)", "RF + random negatives (same number as PU reliable negatives)"]
tab = pd.DataFrame({"n_positives": n_pos, **{c: rec[c] for c in cols}}).loc[rec.index]
tab.index = tab.index.str.replace("PA_PARAGOM_", "").str.replace("_CPRM", "")
tab.index.name = "sector"
tab.to_csv(OUT / "22_recall_per_sector_table.csv")
for c in cols:
    print(f"{c}: pooled {np.average(tab[c], weights=tab.n_positives):.3f}, unweighted mean {tab[c].mean():.3f}, "
          f"median {tab[c].median():.3f}")
print(f"positives: {tab.n_positives.sum()}; largest sector {tab.n_positives.idxmax()} = {tab.n_positives.max()}")

# Table S7 (LaTeX)
pu, r11, rpu = cols
rows = "\n".join(f"{s} & {r.n_positives:.0f} & {r[pu]:.2f} & {r[r11]:.2f} & {r[rpu]:.2f} \\\\"
                 for s, r in tab.rename(index=lambda s: s.replace("_", "\\_")).iterrows())
summ = "\n".join(f"{name} & -- & {tab[pu].agg(fn):.2f} & {tab[r11].agg(fn):.2f} & {tab[rpu].agg(fn):.2f} \\\\"
                 for name, fn in (("Unweighted mean", "mean"), ("Median", "median")))
(OUT / "table_S7.tex").write_text(
    "\\begin{table}[!htb]\n"
    "\\caption{Recall of the withheld sector samples in the leave-sector-out benchmark, by sector (Sect.~3.4.4 and Table~5 of the "
    "main manuscript), with the number of positive samples assigned to each sector (nearest sector). The pooled values of Table~5 "
    "weight the sectors by their number of samples.}\\label{tab:S7}\n"
    "\\footnotesize\n\\begin{tabular*}{\\textwidth}{@{\\extracolsep{\\fill}}lcccc@{}}\n\\toprule\n"
    "Sector & Positives & PU-RF & Random negatives 1:1 & Random negatives (PU count) \\\\\n\\midrule\n"
    + rows + "\n\\midrule\n" + summ + "\n\\bottomrule\n\\end{tabular*}\n\\end{table}\n")
