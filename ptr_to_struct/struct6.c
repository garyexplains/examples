// gcc -o struct6 struct6.c 

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
    point_t *q;

    p->x = 14;
    p->y = 46;
    strcpy(p->desc64, "A point");

    printf("x is %d and y is %d and it is a '%s' and its size is %d\n",
                            p->x, p->y, p->desc64, (int) sizeof(point_t));

    q = p;

    q->x = 15;
    q->y = 47;

    printf("x is %d and y is %d\n", p->x, p->y);

    free(p);
    // free(q) /* NO */
}