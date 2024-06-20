// gcc -o struct7 struct7.c 

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct point {
    int x;
    int y;
    char desc64[64];
} point_t;

void point_factor2(point_t *apoint) {
    apoint->x = apoint->x * 2;
    apoint->y = apoint->y * 2;
}

int main() {
    point_t *p = (point_t *) malloc(sizeof(point_t));

    p->x = 14;
    p->y = 46;
    strcpy(p->desc64, "A point");

    point_factor2(p);

    printf("x is %d and y is %d\n", p->x, p->y);

    free(p);
}