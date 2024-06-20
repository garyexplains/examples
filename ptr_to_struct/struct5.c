// gcc -o struct5 struct5.c 

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct point {
    int x;
    int y;
    char desc64[64];
} point_t;

int main() {
    point_t *p = (point_t *) malloc(sizeof(point_t));

    p->x = 14;
    p->y = 46;
    strcpy(p->desc64, "A point");

    printf("x is %d and y is %d and it is a '%s' and its size is %d\n",
                            p->x, p->y, p->desc64, (int) sizeof(point_t));

    free(p);
}