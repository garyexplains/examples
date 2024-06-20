// gcc -o struct2 struct2.c 

#include <stdio.h>

struct point {
    int x;
    int y;
};

int main() {
    struct point p = {11, 43};

    printf("x is %d and y is %d\n", p.x, p.y);
}