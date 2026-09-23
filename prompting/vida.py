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
