#include <stdio.h>
#include <time.h>

int main() {
    clock_t inicio, fin;
    double tiempo;
    long long resultado = 0;

    inicio = clock();

    for(long long i = 0; i < 50000000; i++) {
        resultado += i * i;
    }

    fin = clock();

    tiempo = (double)(fin - inicio) / CLOCKS_PER_SEC;

    printf("Resultado: %lld\n", resultado);
    printf("Tiempo en C: %f segundos\n", tiempo);

    FILE *archivo = fopen("resultados.txt", "a");

    if(archivo != NULL){
        fprintf(archivo, "C: %f segundos\n", tiempo);
        fclose(archivo);
    }

    return 0;
}
