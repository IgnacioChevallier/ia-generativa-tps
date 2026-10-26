# Costumbres del hospital

Descubiertas en `historial/historial.csv` (2.000 admisiones). Una costumbre es algo que las normas escritas no dicen
y que casi todos los operadores hacen igual. Este archivo lo genera `uv run python -m curado.costumbres`, que mide
cada número desde el historial; no hay valores escritos a mano. Las normas escritas que los operadores violan
(los errores) están en `curado/detalle_clasificacion.jsonl` y en el informe, no acá.

Los operadores son 20. Para cada costumbre se midió cuántos la cumplen en **todas** sus filas y cuántos
no. En las dos, los operadores que la siguen son los mismos 17 y los que se apartan son
OP-04, OP-11, OP-17.

## 1. Aviso al voluntariado: pacientes de 75 años o más que llegan sin acompañante

**Qué es.** La ficha tiene un campo, `aviso_al_voluntariado`, que ninguna norma menciona (ninguna de las 20 secciones
nombra al voluntariado). El hospital lo resuelve así: **se avisa al voluntariado si y solo si el paciente tiene
75 años o más y no tiene acompañante en la guardia.** Es independiente del nivel de triage, del motivo, de
la cobertura y de cómo llegó.

**Evidencia.** Entre los 17 operadores que la siguen (1674 filas) no hay ninguna excepción: avisan en las
185 filas de pacientes de 75+ sin acompañante, y no avisan en ninguna de las demás. El umbral se
midió probando todas las edades de 18 a 89 y quedándose con la que explica más filas. El corte es nítido (pacientes sin
acompañante de esos operadores, avisos sobre total de cada edad):
73 años: 0/16, 74 años: 0/13, 75 años: 8/8, 76 años: 13/13.

No cambia con las normas: las fichas esperadas de `practica/` con las normas original, b y c tienen el mismo
`aviso_al_voluntariado` para los 50 casos, aunque los parámetros de edad y de nivel (P-ADM-1 a P-ADM-3) sean otros. Por
eso el umbral es parte del oráculo y no de `parametros.yaml`. Los 226 pacientes de 75+ sin acompañante del
historial pasan por 20 de los 20 operadores.

**Filas que la respaldan** (avisos de los operadores que la siguen, 185 filas):

H-0013, H-0016, H-0036, H-0044, H-0045, H-0063, H-0088, H-0094, H-0100, H-0114, H-0146, H-0171, H-0194,
H-0210, H-0213, H-0216, H-0217, H-0221, H-0230, H-0233, H-0277, H-0338, H-0344, H-0347, H-0364, H-0380,
H-0385, H-0393, H-0395, H-0397, H-0413, H-0424, H-0426, H-0446, H-0451, H-0459, H-0465, H-0484, H-0486,
H-0507, H-0534, H-0535, H-0571, H-0573, H-0579, H-0596, H-0602, H-0611, H-0620, H-0624, H-0632, H-0636,
H-0639, H-0646, H-0648, H-0659, H-0667, H-0674, H-0680, H-0685, H-0701, H-0718, H-0726, H-0739, H-0743,
H-0752, H-0769, H-0787, H-0793, H-0794, H-0796, H-0816, H-0817, H-0823, H-0825, H-0861, H-0888, H-0901,
H-0903, H-0919, H-0927, H-0939, H-0943, H-0950, H-0951, H-0973, H-0982, H-0989, H-1002, H-1048, H-1074,
H-1076, H-1082, H-1085, H-1101, H-1119, H-1121, H-1130, H-1134, H-1152, H-1154, H-1163, H-1164, H-1172,
H-1183, H-1191, H-1194, H-1197, H-1204, H-1206, H-1212, H-1226, H-1231, H-1237, H-1238, H-1244, H-1254,
H-1262, H-1272, H-1279, H-1285, H-1319, H-1336, H-1346, H-1348, H-1351, H-1356, H-1381, H-1383, H-1393,
H-1420, H-1421, H-1432, H-1433, H-1459, H-1468, H-1470, H-1471, H-1487, H-1501, H-1504, H-1511, H-1526,
H-1533, H-1537, H-1548, H-1556, H-1562, H-1574, H-1578, H-1583, H-1592, H-1593, H-1596, H-1602, H-1613,
H-1616, H-1643, H-1649, H-1654, H-1658, H-1672, H-1676, H-1677, H-1683, H-1691, H-1693, H-1711, H-1712,
H-1720, H-1739, H-1770, H-1776, H-1786, H-1787, H-1824, H-1833, H-1838, H-1846, H-1848, H-1859, H-1878,
H-1963, H-1965, H-1970

**Quiénes se apartan.** OP-04, OP-11, OP-17 avisan sin ese criterio: su aviso no se explica ni por la edad ni
por el acompañante (cumplen la regla en OP-04 55/93, OP-11 51/111, OP-17 69/122
de sus filas; avisan en el 47 % de sus filas sea cual sea la edad o el acompañante). Las 151 filas en que se apartan son **ruido**:

H-0005, H-0006, H-0009, H-0053, H-0056, H-0067, H-0077, H-0093, H-0108, H-0110, H-0127, H-0140, H-0142,
H-0150, H-0163, H-0182, H-0188, H-0196, H-0231, H-0241, H-0245, H-0255, H-0265, H-0288, H-0306, H-0322,
H-0340, H-0353, H-0357, H-0386, H-0398, H-0399, H-0416, H-0443, H-0444, H-0445, H-0449, H-0450, H-0463,
H-0489, H-0497, H-0515, H-0525, H-0537, H-0542, H-0562, H-0575, H-0597, H-0607, H-0610, H-0612, H-0617,
H-0619, H-0622, H-0626, H-0627, H-0630, H-0644, H-0652, H-0653, H-0710, H-0717, H-0741, H-0748, H-0749,
H-0756, H-0761, H-0770, H-0778, H-0786, H-0808, H-0827, H-0856, H-0875, H-0883, H-0898, H-0904, H-0907,
H-0925, H-0933, H-0936, H-0954, H-0958, H-0966, H-0970, H-0980, H-1020, H-1031, H-1040, H-1046, H-1052,
H-1088, H-1091, H-1093, H-1102, H-1116, H-1126, H-1143, H-1173, H-1234, H-1257, H-1258, H-1276, H-1283,
H-1295, H-1313, H-1382, H-1391, H-1416, H-1427, H-1428, H-1434, H-1443, H-1452, H-1466, H-1496, H-1549,
H-1554, H-1564, H-1568, H-1582, H-1584, H-1641, H-1644, H-1665, H-1666, H-1669, H-1682, H-1702, H-1708,
H-1709, H-1722, H-1724, H-1742, H-1752, H-1758, H-1778, H-1794, H-1800, H-1812, H-1821, H-1831, H-1834,
H-1843, H-1856, H-1860, H-1905, H-1909, H-1947, H-1973, H-1976

## 2. Con dos credenciales, vale la prepaga

**Qué es.** NOR-COB-01 §4 dice que la credencial reemplaza la consulta, pero no dice qué hacer si el paciente presenta
**dos** credenciales, una de obra social y otra de prepaga. La costumbre es **verificar y notificar la prepaga**, y no
verificar la obra social, sin importar el orden en que figuran las credenciales ni cuál esté activa.

**Evidencia.** En las filas con dos credenciales (sin accidente de trabajo), los 17 operadores que siguen la costumbre
verificaron la prepaga el 100 % de las veces (154 filas).
Los casos de práctica de la cátedra coinciden: en los 5 con dos credenciales la verificación requerida es la prepaga y la
obra social figura como prohibida, también cuando la prepaga está inactiva y la obra social activa.

**Filas que la respaldan** (184 filas con dos credenciales en que se verificó la prepaga):

H-0010, H-0011, H-0021, H-0052, H-0056, H-0075, H-0086, H-0087, H-0088, H-0099, H-0114, H-0125, H-0153,
H-0157, H-0161, H-0167, H-0178, H-0197, H-0209, H-0219, H-0246, H-0256, H-0275, H-0282, H-0300, H-0324,
H-0326, H-0338, H-0341, H-0349, H-0356, H-0360, H-0387, H-0388, H-0390, H-0395, H-0410, H-0417, H-0423,
H-0429, H-0433, H-0451, H-0465, H-0472, H-0474, H-0478, H-0497, H-0513, H-0520, H-0523, H-0526, H-0530,
H-0531, H-0554, H-0564, H-0575, H-0590, H-0624, H-0627, H-0628, H-0630, H-0631, H-0640, H-0649, H-0656,
H-0677, H-0681, H-0683, H-0690, H-0692, H-0699, H-0702, H-0704, H-0737, H-0740, H-0741, H-0753, H-0791,
H-0809, H-0834, H-0839, H-0857, H-0858, H-0864, H-0867, H-0886, H-0891, H-0905, H-0920, H-0921, H-0929,
H-0946, H-0948, H-0961, H-0985, H-1002, H-1004, H-1012, H-1036, H-1039, H-1044, H-1054, H-1074, H-1079,
H-1082, H-1089, H-1092, H-1096, H-1102, H-1104, H-1110, H-1129, H-1137, H-1149, H-1152, H-1167, H-1169,
H-1171, H-1203, H-1222, H-1248, H-1254, H-1255, H-1260, H-1261, H-1263, H-1265, H-1275, H-1286, H-1321,
H-1328, H-1331, H-1376, H-1379, H-1385, H-1400, H-1401, H-1407, H-1417, H-1481, H-1484, H-1491, H-1498,
H-1506, H-1517, H-1539, H-1555, H-1562, H-1569, H-1572, H-1579, H-1621, H-1629, H-1648, H-1655, H-1656,
H-1664, H-1693, H-1697, H-1701, H-1702, H-1726, H-1739, H-1745, H-1751, H-1767, H-1776, H-1779, H-1792,
H-1799, H-1800, H-1844, H-1847, H-1876, H-1878, H-1893, H-1898, H-1900, H-1914, H-1928, H-1968, H-1970,
H-1975, H-1979

**Quiénes se apartan.** OP-04, OP-11, OP-17 verificaron la obra social en 9 filas. Son **ruido** (si esas
filas no violan además una norma escrita):

H-0334, H-0404, H-0408, H-0480, H-0792, H-0881, H-1190, H-1467, H-1520

## Operadores que se apartan: resumen

Las dos costumbres las rompen exactamente los mismos operadores, OP-04, OP-11, OP-17, y nadie más. Sus filas
son ruido en 160 casos; en el resto de sus filas hacen lo mismo que todos. Esto sugiere que son
operadores que "hacen las cosas a su manera" y no una tercera costumbre: su aviso al voluntariado (47 % de
sus filas) no se relaciona con ningún dato de la fila.

## Lo que se miró y no es una costumbre

Los desvíos de las demás reglas no forman un patrón de operador sino un porcentaje parejo de incumplimientos de una
norma escrita, repartido entre los 20 operadores, y por eso se clasifican como **error**: el plazo de un circuito en
ambulancia sin restar los minutos de NOR-TDE-04, el registro definitivo con pasaporte o cédula en un nivel urgente
(NOR-ADM-03), el paciente mayor que no se ubica en el box antes del registro (NOR-ADM-02) y la cobertura de un número de
afiliado con la terminación reservada de NOR-COB-04.
