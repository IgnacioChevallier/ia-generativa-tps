| Experimento | Encoder | Chunking | Metadatos | top-k | Umbral / margen | Context relevance | Recall | Precision | k medio | MRR |
|---|---|---|---|---|---|---|---|---|---|---|
| [bert-sec-k1](bert-sec-k1.jsonl.eval.json) | bert-base-multilingual-cased (promedio) | seccion | sí | 1 | — | **0.300** | 0.300 | 0.300 | 1.00 | 0.300 |
| [bert-par-k1](bert-par-k1.jsonl.eval.json) | bert-base-multilingual-cased (promedio) | parrafo | sí | 1 | — | **0.300** | 0.300 | 0.300 | 1.00 | 0.300 |
| [bert-v60-k1](bert-v60-k1.jsonl.eval.json) | bert-base-multilingual-cased (promedio) | ventana 60/20 | sí | 1 | — | **0.200** | 0.200 | 0.200 | 1.00 | 0.200 |
| [bert-v120-k1](bert-v120-k1.jsonl.eval.json) | bert-base-multilingual-cased (promedio) | ventana 120/40 | sí | 1 | — | **0.250** | 0.250 | 0.250 | 1.00 | 0.250 |
| [minilm-sec-k1](minilm-sec-k1.jsonl.eval.json) | paraphrase-multilingual-MiniLM-L12-v2 | seccion | sí | 1 | — | **0.800** | 0.800 | 0.800 | 1.00 | 0.800 |
| [minilm-par-k1](minilm-par-k1.jsonl.eval.json) | paraphrase-multilingual-MiniLM-L12-v2 | parrafo | sí | 1 | — | **0.850** | 0.850 | 0.850 | 1.00 | 0.850 |
| [minilm-v60-k1](minilm-v60-k1.jsonl.eval.json) | paraphrase-multilingual-MiniLM-L12-v2 | ventana 60/20 | sí | 1 | — | **0.750** | 0.750 | 0.750 | 1.00 | 0.750 |
| [minilm-v120-k1](minilm-v120-k1.jsonl.eval.json) | paraphrase-multilingual-MiniLM-L12-v2 | ventana 120/40 | sí | 1 | — | **0.700** | 0.700 | 0.700 | 1.00 | 0.700 |
| [e5s-sec-k1](e5s-sec-k1.jsonl.eval.json) | multilingual-e5-small | seccion | sí | 1 | — | **0.900** | 0.900 | 0.900 | 1.00 | 0.900 |
| [e5s-par-k1](e5s-par-k1.jsonl.eval.json) | multilingual-e5-small | parrafo | sí | 1 | — | **0.850** | 0.850 | 0.850 | 1.00 | 0.850 |
| [e5s-v60-k1](e5s-v60-k1.jsonl.eval.json) | multilingual-e5-small | ventana 60/20 | sí | 1 | — | **0.800** | 0.800 | 0.800 | 1.00 | 0.800 |
| [e5s-v120-k1](e5s-v120-k1.jsonl.eval.json) | multilingual-e5-small | ventana 120/40 | sí | 1 | — | **0.950** | 0.950 | 0.950 | 1.00 | 0.950 |
| [e5b-sec-k1](e5b-sec-k1.jsonl.eval.json) | multilingual-e5-base | seccion | sí | 1 | — | **1.000** | 1.000 | 1.000 | 1.00 | 1.000 |
| [e5b-par-k1](e5b-par-k1.jsonl.eval.json) | multilingual-e5-base | parrafo | sí | 1 | — | **0.950** | 0.950 | 0.950 | 1.00 | 0.950 |
| [e5b-v60-k1](e5b-v60-k1.jsonl.eval.json) | multilingual-e5-base | ventana 60/20 | sí | 1 | — | **0.800** | 0.800 | 0.800 | 1.00 | 0.800 |
| [e5b-v120-k1](e5b-v120-k1.jsonl.eval.json) | multilingual-e5-base | ventana 120/40 | sí | 1 | — | **0.900** | 0.900 | 0.900 | 1.00 | 0.900 |
| [bge-sec-k1](bge-sec-k1.jsonl.eval.json) | bge-m3 | seccion | sí | 1 | — | **1.000** | 1.000 | 1.000 | 1.00 | 1.000 |
| [bge-par-k1](bge-par-k1.jsonl.eval.json) | bge-m3 | parrafo | sí | 1 | — | **0.950** | 0.950 | 0.950 | 1.00 | 0.950 |
| [bge-v60-k1](bge-v60-k1.jsonl.eval.json) | bge-m3 | ventana 60/20 | sí | 1 | — | **0.800** | 0.800 | 0.800 | 1.00 | 0.800 |
| [bge-v120-k1](bge-v120-k1.jsonl.eval.json) | bge-m3 | ventana 120/40 | sí | 1 | — | **0.900** | 0.900 | 0.900 | 1.00 | 0.900 |
| [bert-sec-sinmeta-k1](bert-sec-sinmeta-k1.jsonl.eval.json) | bert-base-multilingual-cased (promedio) | seccion | no | 1 | — | **0.200** | 0.200 | 0.200 | 1.00 | 0.200 |
| [bert-par-sinmeta-k1](bert-par-sinmeta-k1.jsonl.eval.json) | bert-base-multilingual-cased (promedio) | parrafo | no | 1 | — | **0.250** | 0.250 | 0.250 | 1.00 | 0.250 |
| [minilm-sec-sinmeta-k1](minilm-sec-sinmeta-k1.jsonl.eval.json) | paraphrase-multilingual-MiniLM-L12-v2 | seccion | no | 1 | — | **0.800** | 0.800 | 0.800 | 1.00 | 0.800 |
| [minilm-par-sinmeta-k1](minilm-par-sinmeta-k1.jsonl.eval.json) | paraphrase-multilingual-MiniLM-L12-v2 | parrafo | no | 1 | — | **0.750** | 0.750 | 0.750 | 1.00 | 0.750 |
| [e5s-sec-sinmeta-k1](e5s-sec-sinmeta-k1.jsonl.eval.json) | multilingual-e5-small | seccion | no | 1 | — | **0.850** | 0.850 | 0.850 | 1.00 | 0.850 |
| [e5s-par-sinmeta-k1](e5s-par-sinmeta-k1.jsonl.eval.json) | multilingual-e5-small | parrafo | no | 1 | — | **0.800** | 0.800 | 0.800 | 1.00 | 0.800 |
| [e5b-sec-sinmeta-k1](e5b-sec-sinmeta-k1.jsonl.eval.json) | multilingual-e5-base | seccion | no | 1 | — | **0.950** | 0.950 | 0.950 | 1.00 | 0.950 |
| [e5b-par-sinmeta-k1](e5b-par-sinmeta-k1.jsonl.eval.json) | multilingual-e5-base | parrafo | no | 1 | — | **0.800** | 0.800 | 0.800 | 1.00 | 0.800 |
| [bge-sec-sinmeta-k1](bge-sec-sinmeta-k1.jsonl.eval.json) | bge-m3 | seccion | no | 1 | — | **1.000** | 1.000 | 1.000 | 1.00 | 1.000 |
| [bge-par-sinmeta-k1](bge-par-sinmeta-k1.jsonl.eval.json) | bge-m3 | parrafo | no | 1 | — | **0.900** | 0.900 | 0.900 | 1.00 | 0.900 |
| [bert-sec-k2](bert-sec-k2.jsonl.eval.json) | bert-base-multilingual-cased (promedio) | seccion | sí | 2 | — | **0.233** | 0.350 | 0.175 | 2.00 | 0.325 |
| [bert-sec-k3](bert-sec-k3.jsonl.eval.json) | bert-base-multilingual-cased (promedio) | seccion | sí | 3 | — | **0.200** | 0.400 | 0.133 | 3.00 | 0.342 |
| [bert-sec-k5](bert-sec-k5.jsonl.eval.json) | bert-base-multilingual-cased (promedio) | seccion | sí | 5 | — | **0.167** | 0.500 | 0.100 | 5.00 | 0.362 |
| [bert-sec-k3-u0.85](bert-sec-k3-u0.85.jsonl.eval.json) | bert-base-multilingual-cased (promedio) | seccion | sí | 3 | coseno ≥ 0.85 | **0.300** | 0.300 | 0.300 | 1.00 | 0.300 |
| [bert-sec-k3-u0.90](bert-sec-k3-u0.90.jsonl.eval.json) | bert-base-multilingual-cased (promedio) | seccion | sí | 3 | coseno ≥ 0.9 | **0.300** | 0.300 | 0.300 | 1.00 | 0.300 |
| [bert-sec-k3-m0.005](bert-sec-k3-m0.005.jsonl.eval.json) | bert-base-multilingual-cased (promedio) | seccion | sí | 3 | margen 0.005 | **0.300** | 0.300 | 0.300 | 1.45 | 0.300 |
| [bert-sec-k3-m0.01](bert-sec-k3-m0.01.jsonl.eval.json) | bert-base-multilingual-cased (promedio) | seccion | sí | 3 | margen 0.01 | **0.283** | 0.300 | 0.275 | 1.85 | 0.300 |
| [bert-sec-k3-m0.02](bert-sec-k3-m0.02.jsonl.eval.json) | bert-base-multilingual-cased (promedio) | seccion | sí | 3 | margen 0.02 | **0.317** | 0.400 | 0.283 | 2.35 | 0.342 |
| [bert-sec-k3-m0.05](bert-sec-k3-m0.05.jsonl.eval.json) | bert-base-multilingual-cased (promedio) | seccion | sí | 3 | margen 0.05 | **0.250** | 0.400 | 0.200 | 2.80 | 0.342 |
| [bert-par-k2](bert-par-k2.jsonl.eval.json) | bert-base-multilingual-cased (promedio) | parrafo | sí | 2 | — | **0.233** | 0.350 | 0.175 | 2.00 | 0.325 |
| [bert-par-k3](bert-par-k3.jsonl.eval.json) | bert-base-multilingual-cased (promedio) | parrafo | sí | 3 | — | **0.200** | 0.400 | 0.133 | 3.00 | 0.342 |
| [bert-par-k5](bert-par-k5.jsonl.eval.json) | bert-base-multilingual-cased (promedio) | parrafo | sí | 5 | — | **0.167** | 0.500 | 0.100 | 5.00 | 0.367 |
| [bert-par-k3-u0.85](bert-par-k3-u0.85.jsonl.eval.json) | bert-base-multilingual-cased (promedio) | parrafo | sí | 3 | coseno ≥ 0.85 | **0.300** | 0.300 | 0.300 | 1.00 | 0.300 |
| [bert-par-k3-u0.90](bert-par-k3-u0.90.jsonl.eval.json) | bert-base-multilingual-cased (promedio) | parrafo | sí | 3 | coseno ≥ 0.9 | **0.300** | 0.300 | 0.300 | 1.00 | 0.300 |
| [bert-par-k3-m0.005](bert-par-k3-m0.005.jsonl.eval.json) | bert-base-multilingual-cased (promedio) | parrafo | sí | 3 | margen 0.005 | **0.300** | 0.300 | 0.300 | 1.20 | 0.300 |
| [bert-par-k3-m0.01](bert-par-k3-m0.01.jsonl.eval.json) | bert-base-multilingual-cased (promedio) | parrafo | sí | 3 | margen 0.01 | **0.283** | 0.300 | 0.275 | 1.65 | 0.300 |
| [bert-par-k3-m0.02](bert-par-k3-m0.02.jsonl.eval.json) | bert-base-multilingual-cased (promedio) | parrafo | sí | 3 | margen 0.02 | **0.300** | 0.400 | 0.258 | 2.20 | 0.342 |
| [bert-par-k3-m0.05](bert-par-k3-m0.05.jsonl.eval.json) | bert-base-multilingual-cased (promedio) | parrafo | sí | 3 | margen 0.05 | **0.225** | 0.400 | 0.167 | 2.90 | 0.342 |
| [minilm-sec-k2](minilm-sec-k2.jsonl.eval.json) | paraphrase-multilingual-MiniLM-L12-v2 | seccion | sí | 2 | — | **0.667** | 1.000 | 0.500 | 2.00 | 0.900 |
| [minilm-sec-k3](minilm-sec-k3.jsonl.eval.json) | paraphrase-multilingual-MiniLM-L12-v2 | seccion | sí | 3 | — | **0.500** | 1.000 | 0.333 | 3.00 | 0.900 |
| [minilm-sec-k5](minilm-sec-k5.jsonl.eval.json) | paraphrase-multilingual-MiniLM-L12-v2 | seccion | sí | 5 | — | **0.333** | 1.000 | 0.200 | 5.00 | 0.900 |
| [minilm-sec-k3-u0.50](minilm-sec-k3-u0.50.jsonl.eval.json) | paraphrase-multilingual-MiniLM-L12-v2 | seccion | sí | 3 | coseno ≥ 0.5 | **0.700** | 0.900 | 0.625 | 1.75 | 0.850 |
| [minilm-sec-k3-u0.60](minilm-sec-k3-u0.60.jsonl.eval.json) | paraphrase-multilingual-MiniLM-L12-v2 | seccion | sí | 3 | coseno ≥ 0.6 | **0.767** | 0.850 | 0.733 | 1.30 | 0.825 |
| [minilm-sec-k3-m0.005](minilm-sec-k3-m0.005.jsonl.eval.json) | paraphrase-multilingual-MiniLM-L12-v2 | seccion | sí | 3 | margen 0.005 | **0.833** | 0.850 | 0.825 | 1.05 | 0.825 |
| [minilm-sec-k3-m0.01](minilm-sec-k3-m0.01.jsonl.eval.json) | paraphrase-multilingual-MiniLM-L12-v2 | seccion | sí | 3 | margen 0.01 | **0.817** | 0.850 | 0.800 | 1.10 | 0.825 |
| [minilm-sec-k3-m0.02](minilm-sec-k3-m0.02.jsonl.eval.json) | paraphrase-multilingual-MiniLM-L12-v2 | seccion | sí | 3 | margen 0.02 | **0.850** | 0.900 | 0.825 | 1.15 | 0.850 |
| [minilm-sec-k3-m0.05](minilm-sec-k3-m0.05.jsonl.eval.json) | paraphrase-multilingual-MiniLM-L12-v2 | seccion | sí | 3 | margen 0.05 | **0.850** | 0.950 | 0.808 | 1.35 | 0.875 |
| [minilm-par-k2](minilm-par-k2.jsonl.eval.json) | paraphrase-multilingual-MiniLM-L12-v2 | parrafo | sí | 2 | — | **0.667** | 1.000 | 0.500 | 2.00 | 0.925 |
| [minilm-par-k3](minilm-par-k3.jsonl.eval.json) | paraphrase-multilingual-MiniLM-L12-v2 | parrafo | sí | 3 | — | **0.500** | 1.000 | 0.333 | 3.00 | 0.925 |
| [minilm-par-k5](minilm-par-k5.jsonl.eval.json) | paraphrase-multilingual-MiniLM-L12-v2 | parrafo | sí | 5 | — | **0.333** | 1.000 | 0.200 | 5.00 | 0.925 |
| [minilm-par-k3-u0.50](minilm-par-k3-u0.50.jsonl.eval.json) | paraphrase-multilingual-MiniLM-L12-v2 | parrafo | sí | 3 | coseno ≥ 0.5 | **0.750** | 0.950 | 0.675 | 1.75 | 0.900 |
| [minilm-par-k3-u0.60](minilm-par-k3-u0.60.jsonl.eval.json) | paraphrase-multilingual-MiniLM-L12-v2 | parrafo | sí | 3 | coseno ≥ 0.6 | **0.817** | 0.900 | 0.783 | 1.30 | 0.875 |
| [minilm-par-k3-m0.005](minilm-par-k3-m0.005.jsonl.eval.json) | paraphrase-multilingual-MiniLM-L12-v2 | parrafo | sí | 3 | margen 0.005 | **0.883** | 0.900 | 0.875 | 1.05 | 0.875 |
| [minilm-par-k3-m0.01](minilm-par-k3-m0.01.jsonl.eval.json) | paraphrase-multilingual-MiniLM-L12-v2 | parrafo | sí | 3 | margen 0.01 | **0.867** | 0.900 | 0.850 | 1.10 | 0.875 |
| [minilm-par-k3-m0.02](minilm-par-k3-m0.02.jsonl.eval.json) | paraphrase-multilingual-MiniLM-L12-v2 | parrafo | sí | 3 | margen 0.02 | **0.867** | 0.900 | 0.850 | 1.10 | 0.875 |
| [minilm-par-k3-m0.05](minilm-par-k3-m0.05.jsonl.eval.json) | paraphrase-multilingual-MiniLM-L12-v2 | parrafo | sí | 3 | margen 0.05 | **0.817** | 0.950 | 0.758 | 1.45 | 0.900 |
| [e5s-sec-k2](e5s-sec-k2.jsonl.eval.json) | multilingual-e5-small | seccion | sí | 2 | — | **0.633** | 0.950 | 0.475 | 2.00 | 0.925 |
| [e5s-sec-k3](e5s-sec-k3.jsonl.eval.json) | multilingual-e5-small | seccion | sí | 3 | — | **0.500** | 1.000 | 0.333 | 3.00 | 0.942 |
| [e5s-sec-k5](e5s-sec-k5.jsonl.eval.json) | multilingual-e5-small | seccion | sí | 5 | — | **0.333** | 1.000 | 0.200 | 5.00 | 0.942 |
| [e5s-sec-k3-u0.85](e5s-sec-k3-u0.85.jsonl.eval.json) | multilingual-e5-small | seccion | sí | 3 | coseno ≥ 0.85 | **0.750** | 1.000 | 0.650 | 1.90 | 0.942 |
| [e5s-sec-k3-u0.88](e5s-sec-k3-u0.88.jsonl.eval.json) | multilingual-e5-small | seccion | sí | 3 | coseno ≥ 0.88 | **0.933** | 0.950 | 0.925 | 1.05 | 0.925 |
| [e5s-sec-k3-m0.005](e5s-sec-k3-m0.005.jsonl.eval.json) | multilingual-e5-small | seccion | sí | 3 | margen 0.005 | **0.908** | 0.950 | 0.892 | 1.15 | 0.925 |
| [e5s-sec-k3-m0.01](e5s-sec-k3-m0.01.jsonl.eval.json) | multilingual-e5-small | seccion | sí | 3 | margen 0.01 | **0.892** | 1.000 | 0.850 | 1.40 | 0.942 |
| [e5s-sec-k3-m0.02](e5s-sec-k3-m0.02.jsonl.eval.json) | multilingual-e5-small | seccion | sí | 3 | margen 0.02 | **0.850** | 1.000 | 0.792 | 1.55 | 0.942 |
| [e5s-sec-k3-m0.05](e5s-sec-k3-m0.05.jsonl.eval.json) | multilingual-e5-small | seccion | sí | 3 | margen 0.05 | **0.683** | 1.000 | 0.575 | 2.25 | 0.942 |
| [e5s-par-k2](e5s-par-k2.jsonl.eval.json) | multilingual-e5-small | parrafo | sí | 2 | — | **0.600** | 0.900 | 0.450 | 2.00 | 0.875 |
| [e5s-par-k3](e5s-par-k3.jsonl.eval.json) | multilingual-e5-small | parrafo | sí | 3 | — | **0.500** | 1.000 | 0.333 | 3.00 | 0.908 |
| [e5s-par-k5](e5s-par-k5.jsonl.eval.json) | multilingual-e5-small | parrafo | sí | 5 | — | **0.333** | 1.000 | 0.200 | 5.00 | 0.908 |
| [e5s-par-k3-u0.85](e5s-par-k3-u0.85.jsonl.eval.json) | multilingual-e5-small | parrafo | sí | 3 | coseno ≥ 0.85 | **0.717** | 1.000 | 0.608 | 2.05 | 0.908 |
| [e5s-par-k3-u0.88](e5s-par-k3-u0.88.jsonl.eval.json) | multilingual-e5-small | parrafo | sí | 3 | coseno ≥ 0.88 | **0.908** | 0.950 | 0.892 | 1.15 | 0.892 |
| [e5s-par-k3-m0.005](e5s-par-k3-m0.005.jsonl.eval.json) | multilingual-e5-small | parrafo | sí | 3 | margen 0.005 | **0.858** | 0.900 | 0.842 | 1.15 | 0.875 |
| [e5s-par-k3-m0.01](e5s-par-k3-m0.01.jsonl.eval.json) | multilingual-e5-small | parrafo | sí | 3 | margen 0.01 | **0.867** | 1.000 | 0.817 | 1.50 | 0.908 |
| [e5s-par-k3-m0.02](e5s-par-k3-m0.02.jsonl.eval.json) | multilingual-e5-small | parrafo | sí | 3 | margen 0.02 | **0.817** | 1.000 | 0.750 | 1.70 | 0.908 |
| [e5s-par-k3-m0.05](e5s-par-k3-m0.05.jsonl.eval.json) | multilingual-e5-small | parrafo | sí | 3 | margen 0.05 | **0.650** | 1.000 | 0.525 | 2.35 | 0.908 |
| [e5b-sec-k2](e5b-sec-k2.jsonl.eval.json) | multilingual-e5-base | seccion | sí | 2 | — | **0.667** | 1.000 | 0.500 | 2.00 | 1.000 |
| [e5b-sec-k3](e5b-sec-k3.jsonl.eval.json) | multilingual-e5-base | seccion | sí | 3 | — | **0.500** | 1.000 | 0.333 | 3.00 | 1.000 |
| [e5b-sec-k5](e5b-sec-k5.jsonl.eval.json) | multilingual-e5-base | seccion | sí | 5 | — | **0.333** | 1.000 | 0.200 | 5.00 | 1.000 |
| [e5b-sec-k3-u0.85](e5b-sec-k3-u0.85.jsonl.eval.json) | multilingual-e5-base | seccion | sí | 3 | coseno ≥ 0.85 | **0.858** | 1.000 | 0.800 | 1.50 | 1.000 |
| [e5b-sec-k3-u0.88](e5b-sec-k3-u0.88.jsonl.eval.json) | multilingual-e5-base | seccion | sí | 3 | coseno ≥ 0.88 | **0.983** | 1.000 | 0.975 | 1.05 | 1.000 |
| [e5b-sec-k3-m0.005](e5b-sec-k3-m0.005.jsonl.eval.json) | multilingual-e5-base | seccion | sí | 3 | margen 0.005 | **0.967** | 1.000 | 0.950 | 1.10 | 1.000 |
| [e5b-sec-k3-m0.01](e5b-sec-k3-m0.01.jsonl.eval.json) | multilingual-e5-base | seccion | sí | 3 | margen 0.01 | **0.942** | 1.000 | 0.917 | 1.20 | 1.000 |
| [e5b-sec-k3-m0.02](e5b-sec-k3-m0.02.jsonl.eval.json) | multilingual-e5-base | seccion | sí | 3 | margen 0.02 | **0.875** | 1.000 | 0.825 | 1.45 | 1.000 |
| [e5b-sec-k3-m0.05](e5b-sec-k3-m0.05.jsonl.eval.json) | multilingual-e5-base | seccion | sí | 3 | margen 0.05 | **0.692** | 1.000 | 0.583 | 2.20 | 1.000 |
| [e5b-par-k2](e5b-par-k2.jsonl.eval.json) | multilingual-e5-base | parrafo | sí | 2 | — | **0.633** | 0.950 | 0.475 | 2.00 | 0.950 |
| [e5b-par-k3](e5b-par-k3.jsonl.eval.json) | multilingual-e5-base | parrafo | sí | 3 | — | **0.500** | 1.000 | 0.333 | 3.00 | 0.967 |
| [e5b-par-k5](e5b-par-k5.jsonl.eval.json) | multilingual-e5-base | parrafo | sí | 5 | — | **0.333** | 1.000 | 0.200 | 5.00 | 0.967 |
| [e5b-par-k3-u0.85](e5b-par-k3-u0.85.jsonl.eval.json) | multilingual-e5-base | parrafo | sí | 3 | coseno ≥ 0.85 | **0.825** | 1.000 | 0.750 | 1.60 | 0.967 |
| [e5b-par-k3-u0.88](e5b-par-k3-u0.88.jsonl.eval.json) | multilingual-e5-base | parrafo | sí | 3 | coseno ≥ 0.88 | **0.933** | 0.950 | 0.925 | 1.05 | 0.950 |
| [e5b-par-k3-m0.005](e5b-par-k3-m0.005.jsonl.eval.json) | multilingual-e5-base | parrafo | sí | 3 | margen 0.005 | **0.933** | 0.950 | 0.925 | 1.05 | 0.950 |
| [e5b-par-k3-m0.01](e5b-par-k3-m0.01.jsonl.eval.json) | multilingual-e5-base | parrafo | sí | 3 | margen 0.01 | **0.933** | 1.000 | 0.908 | 1.25 | 0.967 |
| [e5b-par-k3-m0.02](e5b-par-k3-m0.02.jsonl.eval.json) | multilingual-e5-base | parrafo | sí | 3 | margen 0.02 | **0.875** | 1.000 | 0.825 | 1.45 | 0.967 |
| [e5b-par-k3-m0.05](e5b-par-k3-m0.05.jsonl.eval.json) | multilingual-e5-base | parrafo | sí | 3 | margen 0.05 | **0.642** | 1.000 | 0.517 | 2.40 | 0.967 |
| [bge-sec-k2](bge-sec-k2.jsonl.eval.json) | bge-m3 | seccion | sí | 2 | — | **0.667** | 1.000 | 0.500 | 2.00 | 1.000 |
| [bge-sec-k3](bge-sec-k3.jsonl.eval.json) | bge-m3 | seccion | sí | 3 | — | **0.500** | 1.000 | 0.333 | 3.00 | 1.000 |
| [bge-sec-k5](bge-sec-k5.jsonl.eval.json) | bge-m3 | seccion | sí | 5 | — | **0.333** | 1.000 | 0.200 | 5.00 | 1.000 |
| [bge-sec-k3-u0.50](bge-sec-k3-u0.50.jsonl.eval.json) | bge-m3 | seccion | sí | 3 | coseno ≥ 0.5 | **0.617** | 1.000 | 0.475 | 2.45 | 1.000 |
| [bge-sec-k3-u0.60](bge-sec-k3-u0.60.jsonl.eval.json) | bge-m3 | seccion | sí | 3 | coseno ≥ 0.6 | **0.850** | 1.000 | 0.800 | 1.60 | 1.000 |
| [bge-sec-k3-m0.005](bge-sec-k3-m0.005.jsonl.eval.json) | bge-m3 | seccion | sí | 3 | margen 0.005 | **1.000** | 1.000 | 1.000 | 1.00 | 1.000 |
| [bge-sec-k3-m0.01](bge-sec-k3-m0.01.jsonl.eval.json) | bge-m3 | seccion | sí | 3 | margen 0.01 | **1.000** | 1.000 | 1.000 | 1.00 | 1.000 |
| [bge-sec-k3-m0.02](bge-sec-k3-m0.02.jsonl.eval.json) | bge-m3 | seccion | sí | 3 | margen 0.02 | **0.983** | 1.000 | 0.975 | 1.05 | 1.000 |
| [bge-sec-k3-m0.05](bge-sec-k3-m0.05.jsonl.eval.json) | bge-m3 | seccion | sí | 3 | margen 0.05 | **0.908** | 1.000 | 0.867 | 1.30 | 1.000 |
| [bge-par-k2](bge-par-k2.jsonl.eval.json) | bge-m3 | parrafo | sí | 2 | — | **0.667** | 1.000 | 0.500 | 2.00 | 0.975 |
| [bge-par-k3](bge-par-k3.jsonl.eval.json) | bge-m3 | parrafo | sí | 3 | — | **0.500** | 1.000 | 0.333 | 3.00 | 0.975 |
| [bge-par-k5](bge-par-k5.jsonl.eval.json) | bge-m3 | parrafo | sí | 5 | — | **0.333** | 1.000 | 0.200 | 5.00 | 0.975 |
| [bge-par-k3-u0.50](bge-par-k3-u0.50.jsonl.eval.json) | bge-m3 | parrafo | sí | 3 | coseno ≥ 0.5 | **0.592** | 1.000 | 0.442 | 2.55 | 0.975 |
| [bge-par-k3-u0.60](bge-par-k3-u0.60.jsonl.eval.json) | bge-m3 | parrafo | sí | 3 | coseno ≥ 0.6 | **0.808** | 1.000 | 0.742 | 1.75 | 0.975 |
| [bge-par-k3-m0.005](bge-par-k3-m0.005.jsonl.eval.json) | bge-m3 | parrafo | sí | 3 | margen 0.005 | **0.950** | 0.950 | 0.950 | 1.00 | 0.950 |
| [bge-par-k3-m0.01](bge-par-k3-m0.01.jsonl.eval.json) | bge-m3 | parrafo | sí | 3 | margen 0.01 | **0.950** | 0.950 | 0.950 | 1.00 | 0.950 |
| [bge-par-k3-m0.02](bge-par-k3-m0.02.jsonl.eval.json) | bge-m3 | parrafo | sí | 3 | margen 0.02 | **0.933** | 0.950 | 0.925 | 1.05 | 0.950 |
| [bge-par-k3-m0.05](bge-par-k3-m0.05.jsonl.eval.json) | bge-m3 | parrafo | sí | 3 | margen 0.05 | **0.875** | 0.950 | 0.842 | 1.25 | 0.950 |
