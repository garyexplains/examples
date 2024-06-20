// gcc -o struct3 struct3.c 

#include <stdio.h>

struct point {
    int x;
    int y;
};

int main() {
    struct point q = {12, 44};
    struct point p;

    p = q;

    printf("x is %d and y is %d\n", p.x, p.y);
}