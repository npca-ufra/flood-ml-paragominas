"""Silhouette score of the K-Means stratification for k = 2-15 (Sect. 3.4.1): the maximum is at k = 2,
and k = 7, selected within [5, 10], is also the highest value for any k >= 4."""
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

from common import FEATS, load, results_dir

d = load()
Z = StandardScaler().fit_transform(d[FEATS])
s = pd.Series({k: silhouette_score(Z, KMeans(k, init="k-means++", random_state=42, n_init="auto").fit_predict(Z))
               for k in range(2, 16)}, name="silhouette")
s.to_csv(results_dir("results") / "14_silhouette_k2_15.csv")
print(s.round(4).to_string())
