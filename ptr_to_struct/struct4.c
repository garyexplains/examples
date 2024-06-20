// gcc -o struct4 struct4.c 

#include <stdio.h>

typedef struct point {
    int x;
    int y;
} point_t;

int main() {
    point_t p = {13, 45};

    printf("x is %d and y is %d\n", p.x, p.y);
}