# Conversación — deepseek/deepseek-v4-flash-0731

_Inicio: 2026-09-16T21:23:00_

## user

ROL
Sos un ingeniero de software en Python senior, especializado en implementar
especificaciones exactas sin salirte del contrato ni agregar nada por tu cuenta.

CONTEXTO
Necesito un script de Python que implemente el juego de la vida de Conway para
correr contra una batería de tests automatizados. Los tests invocan el script
por línea de comandos y comparan la salida por stdout carácter por carácter, así
que el formato tiene que ser exacto.

INSTRUCCIONES (el contrato, no negociable)
- Uso: python3 vida.py <archivo_estado_inicial> <generaciones>
- El archivo de estado es una grilla rectangular: una línea por fila, '#' célula
  viva, '.' célula muerta.
- El mundo es FINITO, del tamaño exacto de la grilla leída del archivo: todo lo
  que está fuera de esos bordes se considera muerto. NO hay wrap-around (no es
  un toroide).
- Reglas estándar de Conway: una célula viva con 2 o 3 vecinas vivas (de las 8
  adyacentes) sobrevive; con menos de 2 muere por soledad; con más de 3 muere
  por sobrepoblación. Una célula muerta con exactamente 3 vecinas vivas nace.
- El script imprime por stdout la grilla resultante tras N generaciones, en el
  mismo formato (una línea por fila, mismo ancho que la grilla original).
- Con generaciones = 0, imprime el estado inicial tal cual, sin modificarlo.

RESTRICCIONES
- Un solo archivo, vida.py, sin dependencias externas: solo biblioteca estándar
  de Python.
- No imprimas nada además de la grilla resultante: sin mensajes de debug, sin
  prompts, sin líneas en blanco extra al principio o al final.
- El script tiene que terminar con código de salida 0 si todo sale bien.
- Los argumentos son sys.argv[1] (ruta al archivo) y sys.argv[2] (generaciones,
  entero no negativo).

EJEMPLOS
1) Oscilador (blinker), vertical -> horizontal en 1 generación:
   Entrada:          Tras 1 generación:
   .....             .....
   ..#..             .....
   ..#..     ->      .###.
   ..#..             .....
   .....             .....

2) Naturaleza muerta (bloque), no cambia nunca:
   .##.
   .##.
   (con cualquier número de generaciones, queda igual)

3) Muerte por soledad (célula aislada, sin vecinas vivas):
   ...               ...
   .#.       ->      ...
   ...               ...

4) Nacimiento por 3 vecinas:
   Entrada:          Tras 1 generación:
   ....              ....
   .##.      ->      .##.
   .#..              .##.
   ....              ....

5) Sin wrap-around: un patrón pegado al borde superior NO interactúa con "el
   otro lado" de la grilla. Todo lo que está fuera de la grilla leída está
   muerto, sin excepción:
   Entrada:          Tras 1 generación:
   ###               .#.
   ...      ->       .#.
   ...               ...

INPUT
Generá el archivo vida.py completo y listo para ejecutar. Respondé solo con el
código, en un único bloque de código Python, sin explicaciones antes ni después.

## assistant

```python
import sys

def contar_vecinos(grid, r, c, H, W):
    vivos = 0
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            nr = r + dr
            nc = c + dc
            if 0 <= nr < H and 0 <= nc < W and grid[nr][nc] == '#':
                vivos += 1
    return vivos


def siguiente_generacion(grid):
    H = len(grid)
    if H == 0:
        return []

    W = len(grid[0])
    nueva = []

    for r in range(H):
        fila = []
        for c in range(W):
            vecinas = contar_vecinos(grid, r, c, H, W)
            if grid[r][c] == '#':
                fila.append('#' if vecinas in (2, 3) else '.')
            else:
                fila.append('#' if vecinas == 3 else '.')
        nueva.append(''.join(fila))

    return nueva


def main():
    archivo = sys.argv[1]
    generaciones = int(sys.argv[2])

    with open(archivo, 'r') as f:
        grid = f.read().splitlines()

    for _ in range(generaciones):
        grid = siguiente_generacion(grid)

    if grid:
        sys.stdout.write('\n'.join(grid) + '\n')


if __name__ == '__main__':
    main()
```

**Usage:** prompt=892 completion=14699 cached=0 reasoning=14356 cost=$0.005093

