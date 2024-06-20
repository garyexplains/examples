// gcc -o struct8 struct8.c 

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct point {
    int x;
    int y;
    char desc64[64];
} point_t;

void point_add(point_t *a, const point_t *b) {
    a->x = a->x + b->x;
    a->y = a->y + b->y;
    // b->x = 0; /* No, as b is const */
}

int main() {
    point_t *p1 = (point_t *) malloc(sizeof(point_t));
    point_t p2 = {10, 20, "Another point"};

    p1->x = 14;
    p1->y = 46;
    strcpy(p1->desc64, "A point");

    point_add(p1, &p2);

    printf("x is %d and y is %d\n", p1->x, p1->y);

    free(p1);
}