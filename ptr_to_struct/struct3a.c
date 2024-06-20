// gcc -o struct3a struct3a.c 

#include <stdio.h>

struct point {
    int x;
    int y;
};

int main() {
    struct point q = {12, 44};
    struct point p;

    p = q;
    p.x = p.x + 1;
    p.y = p.y + 1;

    printf("q: x is %d and y is %d\n", q.x, q.y);
    printf("p: x is %d and y is %d\n", p.x, p.y);
}