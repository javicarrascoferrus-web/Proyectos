import time

inicio = time.time()

resultado = 0

for i in range(50000000):
    resultado += i * i

fin = time.time()

tiempo = fin - inicio

print("Resultado:", resultado)
print("Tiempo en Python:", tiempo, "segundos")

with open("resultados.txt", "a") as archivo:
    archivo.write(f"Python: {tiempo} segundos\n")
