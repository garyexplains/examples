/* stringtool_simple: a minimal LLM-callable string tool.
 *
 * One operation: reverse.
 *
 *   stringtool_simple reverse "hello"      ->  olleh
 *   echo hello | stringtool_simple reverse - ->  olleh
 *
 * That's it. No JSON, no schema, no dependencies. This is the smallest
 * useful example of "a command-line program an LLM host can shell out to".
 */

#include <stdio.h>
#include <string.h>

int main(int argc, char **argv) {
    if (argc != 3 || strcmp(argv[1], "reverse") != 0) {
        fprintf(stderr, "usage: %s reverse \"<string>\"\n", argv[0]);
        return 2;
    }

    const char *s = argv[2];
    for (size_t i = strlen(s); i > 0; i--) putchar(s[i - 1]);
    putchar('\n');
    return 0;
}