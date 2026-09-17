# Conversación — deepseek/deepseek-v4-flash-0731

_Inicio: 2026-09-16T21:18:21_

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

def leer_grilla(ruta):
    with open(ruta, 'r') as f:
        lineas = f.read().splitlines()
    return lineas

def contar_vecinos_vivos(grilla, fila, col):
    filas = len(grilla)
    cols = len(grilla[0]) if filas > 0 else 0
    count = 0
    for i in [-1, 0, 1]:
        for j in [-1, 0, 1]:
            if i == 0 and j == 0:
                continue
            ni = fila + i
            nj = col + j
            if 0 <= ni < filas and 0 <= nj < cols:
                if grilla[ni][nj] == '#':
                    count += 1
    return count

def siguiente_generacion(grilla):
    filas = len(grilla)
    if filas == 0:
        return []
    cols = len(grilla[0])
    nueva = []
    for i in range(filas):
        fila_nueva = []
        for j in range(cols):
            vecinos = contar_vecinos_vivos(grilla, i, j)
            celda = grilla[i][j]
            if celda == '#':
                if vecinos in (2, 3):
                    fila_nueva.append('#')
                else:
                    fila_nueva.append('.')
            else:
                if vecinos == 3:
                    fila_nueva.append('#')
                else:
                    fila_nueva.append('.')
        nueva.append(''.join(fila_nueva))
    return nueva

def main():
    if len(sys.argv) != 3:
        print("Uso: python3 vida.py <archivo_estado_inicial> <generaciones>", file=sys.stderr)
        sys.exit(1)
    
    ruta = sys.argv[1]
    try:
        generaciones = int(sys.argv[2])
    except ValueError:
        print("Error: generaciones debe ser un entero", file=sys.stderr)
        sys.exit(1)
    
    if generaciones < 0:
        print("Error: generaciones debe ser no negativo", file=sys.stderr)
        sys.exit(1)
    
    grilla = leer_grilla(ruta)
    
    for _ in range(generaciones):
        grilla = siguiente_generacion(grilla)
    
    print('\n'.join(grilla))

if __name__ == '__main__':
    main()
```

**Usage:** prompt=813 completion=1699 cached=0 reasoning=1071 cost=$0.000355

