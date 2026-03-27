#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

/*
 * hash_int
 *
 * This is the simplest possible hash for an integer key. It uses the modulo
 * operator to fold a potentially large integer into the range
 * [0, table_size - 1].
 *
 * Example with table_size = 100:
 *   12345 % 100 = 45
 *
 * Why it works:
 * - A hash table needs an array index, not an arbitrary large integer.
 * - Taking the remainder after division by the table size guarantees the
 *   result fits inside the table.
 *
 * Limitations:
 * - This only works reasonably well when input integers are already spread out.
 * - If many keys share the same pattern in their lower bits or their last
 *   digits, collisions can be common.
 * - It is useful for teaching because the idea is easy to see, but by itself
 *   it is not a strong general-purpose hash function.
 */
int hash_int(int key, int table_size) {
    return key % table_size;
}

/*
 * hash_string
 *
 * This function builds a hash by adding together the numeric value of every
 * character in the string, then reducing that total with modulo table_size.
 *
 * Example for "abc":
 *   'a' + 'b' + 'c' = 97 + 98 + 99 = 294
 *   294 % table_size gives the final table index
 *
 * Why it works:
 * - Every character contributes something to the final total.
 * - The modulo operation converts the total into a valid table index.
 *
 * Limitations:
 * - Character order does not matter here. "abc" and "cba" produce the same sum.
 * - Many unrelated strings can easily collide.
 * - This makes it a good teaching example for "a hash exists", but also for
 *   showing why better string hash functions are needed.
 */
int hash_string(const char *str, int table_size) {
    int sum = 0;
    while (*str) {
        sum += *str;
        str++;
    }
    return sum % table_size;
}

/*
 * hash_poly
 *
 * This is a polynomial rolling hash. Instead of just adding characters, it
 * repeatedly multiplies the current hash by a small prime and then adds the
 * next character:
 *
 *   hash = hash * 31 + current_character
 *
 * Why it works:
 * - Earlier characters are "shifted" by multiplication before later
 *   characters are added.
 * - That means character order matters. "abc" and "cba" produce different
 *   values.
 * - The small prime 31 is a common teaching and practical choice because it
 *   is cheap to compute and tends to distribute many text inputs better than
 *   a simple character sum.
 *
 * Important note:
 * - This function returns the full computed hash value, not a table index.
 * - In a hash table, you would usually reduce the result with modulo
 *   table_size afterward.
 */
unsigned int hash_poly(const char *str) {
    unsigned int hash = 0;
    int prime = 31;

    while (*str) {
        hash = hash * prime + (*str);
        str++;
    }

    return hash;
}

/*
 * hash_djb2
 *
 * DJB2 is a classic string hash often attributed to Daniel J. Bernstein. It
 * starts from the seed value 5381 and for each character performs:
 *
 *   hash = hash * 33 + c
 *
 * In this implementation, hash * 33 is written as:
 *
 *   ((hash << 5) + hash)
 *
 * because shifting left by 5 multiplies by 32, and adding the original hash
 * gives 33 * hash.
 *
 * Why it works:
 * - Each character affects all later states of the hash.
 * - Multiplying by 33 mixes old state with new input at each step.
 * - It is compact, fast, and historically popular for text keys.
 *
 * Teaching value:
 * - Students can compare it directly with the naive sum-based hash and see how
 *   preserving character order and repeatedly mixing state improves behavior.
 */
unsigned long hash_djb2(const char *str) {
    unsigned long hash = 5381;
    int c;

    while ((c = *str++)) {
        hash = ((hash << 5) + hash) + c; // hash * 33 + c
    }

    return hash;
}

/*
 * hash_sdbm
 *
 * SDBM is another classic string hash. For each character, it updates the
 * current state with:
 *
 *   hash = c + (hash << 6) + (hash << 16) - hash
 *
 * This can also be viewed as:
 *
 *   hash = c + hash * 65599
 *
 * because:
 *   (hash << 6)  = hash * 64
 *   (hash << 16) = hash * 65536
 *   64 + 65536 - 1 = 65599
 *
 * Why it works:
 * - The old hash is strongly mixed before the new character is added.
 * - Character order matters.
 * - The large multiplier helps spread out similar strings.
 *
 * Teaching value:
 * - This is useful to contrast with DJB2. Both are iterative string hashes,
 *   but they use different mixing constants and therefore produce different
 *   distributions.
 */
static unsigned long hash_sdbm(const unsigned char *str) {
    unsigned long hash = 0;
    int c;

    while ((c = *str++)) {
        hash = c + (hash << 6) + (hash << 16) - hash;
    }

    return hash;
}

/*
 * md5_hash
 *
 * MD5 is a cryptographic hash algorithm that processes data in 512-bit
 * (64-byte) blocks and produces a 128-bit (16-byte) digest. Even though MD5 is
 * no longer considered secure for modern cryptographic use, it remains a very
 * useful teaching example because it shows how a structured hash algorithm can
 * repeatedly mix internal state with bitwise operations, rotations, constants,
 * and padding rules.
 *
 * High-level process:
 * - Copy the input and pad it so the total length is 64 bytes short of a
 *   multiple of 64.
 * - Append the original message length in bits as a 64-bit value.
 * - Process each 64-byte chunk through 64 rounds of mixing.
 * - Output the four 32-bit state words as a 16-byte digest.
 *
 * Teaching note:
 * - This implementation is written directly in C and does not rely on external
 *   libraries.
 * - It is suitable for demonstration and experimentation, but MD5 should not
 *   be used for passwords, signatures, or collision-resistant security work.
 */
static uint32_t md5_left_rotate(uint32_t value, uint32_t shift) {
    return (value << shift) | (value >> (32 - shift));
}

static void md5_hash(const unsigned char *initial_msg, size_t initial_len,
                     unsigned char digest[16]) {
    static const uint32_t shift_amounts[64] = {
        7, 12, 17, 22, 7, 12, 17, 22, 7, 12, 17, 22, 7, 12, 17, 22,
        5, 9, 14, 20, 5, 9, 14, 20, 5, 9, 14, 20, 5, 9, 14, 20,
        4, 11, 16, 23, 4, 11, 16, 23, 4, 11, 16, 23, 4, 11, 16, 23,
        6, 10, 15, 21, 6, 10, 15, 21, 6, 10, 15, 21, 6, 10, 15, 21
    };
    static const uint32_t table[64] = {
        0xd76aa478, 0xe8c7b756, 0x242070db, 0xc1bdceee,
        0xf57c0faf, 0x4787c62a, 0xa8304613, 0xfd469501,
        0x698098d8, 0x8b44f7af, 0xffff5bb1, 0x895cd7be,
        0x6b901122, 0xfd987193, 0xa679438e, 0x49b40821,
        0xf61e2562, 0xc040b340, 0x265e5a51, 0xe9b6c7aa,
        0xd62f105d, 0x02441453, 0xd8a1e681, 0xe7d3fbc8,
        0x21e1cde6, 0xc33707d6, 0xf4d50d87, 0x455a14ed,
        0xa9e3e905, 0xfcefa3f8, 0x676f02d9, 0x8d2a4c8a,
        0xfffa3942, 0x8771f681, 0x6d9d6122, 0xfde5380c,
        0xa4beea44, 0x4bdecfa9, 0xf6bb4b60, 0xbebfbc70,
        0x289b7ec6, 0xeaa127fa, 0xd4ef3085, 0x04881d05,
        0xd9d4d039, 0xe6db99e5, 0x1fa27cf8, 0xc4ac5665,
        0xf4292244, 0x432aff97, 0xab9423a7, 0xfc93a039,
        0x655b59c3, 0x8f0ccc92, 0xffeff47d, 0x85845dd1,
        0x6fa87e4f, 0xfe2ce6e0, 0xa3014314, 0x4e0811a1,
        0xf7537e82, 0xbd3af235, 0x2ad7d2bb, 0xeb86d391
    };
    uint32_t a0 = 0x67452301;
    uint32_t b0 = 0xefcdab89;
    uint32_t c0 = 0x98badcfe;
    uint32_t d0 = 0x10325476;
    uint64_t bit_len = (uint64_t)initial_len * 8;
    size_t new_len = initial_len + 1;
    unsigned char *msg;
    size_t offset;

    while ((new_len % 64) != 56) {
        new_len++;
    }

    msg = (unsigned char *)calloc(new_len + 8, 1);
    if (msg == NULL) {
        fprintf(stderr, "error: failed to allocate memory for MD5\n");
        exit(1);
    }

    memcpy(msg, initial_msg, initial_len);
    msg[initial_len] = 0x80;
    memcpy(msg + new_len, &bit_len, sizeof(bit_len));

    for (offset = 0; offset < new_len; offset += 64) {
        uint32_t words[16];
        uint32_t a = a0;
        uint32_t b = b0;
        uint32_t c = c0;
        uint32_t d = d0;
        int i;

        for (i = 0; i < 16; i++) {
            words[i] =
                (uint32_t)msg[offset + i * 4] |
                ((uint32_t)msg[offset + i * 4 + 1] << 8) |
                ((uint32_t)msg[offset + i * 4 + 2] << 16) |
                ((uint32_t)msg[offset + i * 4 + 3] << 24);
        }

        for (i = 0; i < 64; i++) {
            uint32_t f;
            uint32_t g;

            if (i < 16) {
                f = (b & c) | ((~b) & d);
                g = (uint32_t)i;
            } else if (i < 32) {
                f = (d & b) | ((~d) & c);
                g = (uint32_t)((5 * i + 1) % 16);
            } else if (i < 48) {
                f = b ^ c ^ d;
                g = (uint32_t)((3 * i + 5) % 16);
            } else {
                f = c ^ (b | (~d));
                g = (uint32_t)((7 * i) % 16);
            }

            {
                uint32_t temp = d;
                d = c;
                c = b;
                b = b + md5_left_rotate(a + f + table[i] + words[g],
                                        shift_amounts[i]);
                a = temp;
            }
        }

        a0 += a;
        b0 += b;
        c0 += c;
        d0 += d;
    }

    free(msg);

    digest[0] = (unsigned char)(a0 & 0xff);
    digest[1] = (unsigned char)((a0 >> 8) & 0xff);
    digest[2] = (unsigned char)((a0 >> 16) & 0xff);
    digest[3] = (unsigned char)((a0 >> 24) & 0xff);
    digest[4] = (unsigned char)(b0 & 0xff);
    digest[5] = (unsigned char)((b0 >> 8) & 0xff);
    digest[6] = (unsigned char)((b0 >> 16) & 0xff);
    digest[7] = (unsigned char)((b0 >> 24) & 0xff);
    digest[8] = (unsigned char)(c0 & 0xff);
    digest[9] = (unsigned char)((c0 >> 8) & 0xff);
    digest[10] = (unsigned char)((c0 >> 16) & 0xff);
    digest[11] = (unsigned char)((c0 >> 24) & 0xff);
    digest[12] = (unsigned char)(d0 & 0xff);
    digest[13] = (unsigned char)((d0 >> 8) & 0xff);
    digest[14] = (unsigned char)((d0 >> 16) & 0xff);
    digest[15] = (unsigned char)((d0 >> 24) & 0xff);
}

static void print_md5_digest(const unsigned char digest[16]) {
    int i;

    for (i = 0; i < 16; i++) {
        printf("%02x", digest[i]);
    }
}

static void print_usage(const char *prog_name) {
    printf("Usage: %s [--int] [--sum] [--poly] [--djb2] [--sdbm] [--md5] [-s STRING]\n",
           prog_name);
    printf("  -s STRING  Set the input string for the string-based hash functions\n");
    printf("  --int      Run the integer modulo hash example\n");
    printf("  --sum      Run the simple character-sum string hash\n");
    printf("  --poly     Run the polynomial rolling hash\n");
    printf("  --djb2     Run the DJB2 hash\n");
    printf("  --sdbm     Run the SDBM hash\n");
    printf("  --md5      Run the MD5 hash and print the 128-bit digest in hex\n");
    printf("If no hash flag is provided, the program runs all examples.\n");
}

int main(int argc, char *argv[]) {
    const char *input = "Hello, World!";
    int run_int = 0;
    int run_sum = 0;
    int run_poly = 0;
    int run_djb2_flag = 0;
    int run_sdbm_flag = 0;
    int run_md5_flag = 0;
    int selected_any = 0;
    unsigned char md5_digest[16];
    unsigned long hl;
    unsigned h;
    int i;

    for (i = 1; i < argc; i++) {
        if (strcmp(argv[i], "-s") == 0) {
            if (i + 1 >= argc) {
                fprintf(stderr, "error: -s requires a string argument\n");
                print_usage(argv[0]);
                return 1;
            }
            input = argv[++i];
        } else if (strcmp(argv[i], "--int") == 0) {
            run_int = 1;
            selected_any = 1;
        } else if (strcmp(argv[i], "--sum") == 0) {
            run_sum = 1;
            selected_any = 1;
        } else if (strcmp(argv[i], "--poly") == 0) {
            run_poly = 1;
            selected_any = 1;
        } else if (strcmp(argv[i], "--djb2") == 0) {
            run_djb2_flag = 1;
            selected_any = 1;
        } else if (strcmp(argv[i], "--sdbm") == 0) {
            run_sdbm_flag = 1;
            selected_any = 1;
        } else if (strcmp(argv[i], "--md5") == 0) {
            run_md5_flag = 1;
            selected_any = 1;
        } else if (strcmp(argv[i], "--help") == 0 || strcmp(argv[i], "-h") == 0) {
            print_usage(argv[0]);
            return 0;
        } else {
            fprintf(stderr, "error: unknown argument '%s'\n", argv[i]);
            print_usage(argv[0]);
            return 1;
        }
    }

    if (!selected_any) {
        run_int = 1;
        run_sum = 1;
        run_poly = 1;
        run_djb2_flag = 1;
        run_sdbm_flag = 1;
        run_md5_flag = 1;
    }

    if (run_int) {
        h = hash_int(12345, 100);
        printf("Hash of integer 12345: %d\n", h);
    }

    if (run_sum) {
        h = hash_string(input, 100);
        printf("Hash of string \"%s\": %d\n", input, h);
    }

    if (run_poly) {
        h = hash_poly(input);
        printf("Polynomial rolling hash of string \"%s\": %u\n", input, h);
    }

    if (run_djb2_flag) {
        hl = hash_djb2(input);
        printf("DJB2 hash of string \"%s\": %lu\n", input, hl);
    }

    if (run_sdbm_flag) {
        hl = hash_sdbm((const unsigned char *)input);
        printf("SDBM hash of string \"%s\": %lu\n", input, hl);
    }

    if (run_md5_flag) {
        md5_hash((const unsigned char *)input, strlen(input), md5_digest);
        printf("MD5 hash of string \"%s\": ", input);
        print_md5_digest(md5_digest);
        printf("\n");
    }

    return 0;
}
