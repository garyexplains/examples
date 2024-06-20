// gcc -o struct1 struct1.c 

#include <stdio.h>

struct point {
    int x;
    int y;
};

int main() {
    struct point p;

    p.x = 10;
    p.y = 42;

    printf("x is %d and y is %d\n", p.x, p.y);
}