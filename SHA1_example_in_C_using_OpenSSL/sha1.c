// SHA1 and SHA256 example in C using OpenSSL library

#include <openssl/err.h>
#include <openssl/evp.h>
#include <openssl/sha.h>
#include <stdio.h>

// Inspired from https://stackoverflow.com/questions/41109861/sha1-example-in-c-using-openssl-library
// The example given on the page above is broken as now EVP_MD_CTX_init and EVP_MD_CTX_cleanup are deprecated,
// in fact it looks like they have been removed from the OpenSSL library.
// I fixed the example to use EVP_MD_CTX_create and EVP_MD_CTX_destroy

// gcc -o sha1 sha1.c -lcrypto

int main(int argc, char **argv) {

  FILE *f;
  size_t len;
  unsigned char buffer[BUFSIZ];

  if (argc < 2) {
    fprintf(stderr, "usage: %s <file>\n", argv[0]);
    return 1;
  }

  f = fopen(argv[1], "r");

  if (!f) {
    fprintf(stderr, "couldn't open %s\n", argv[1]);
    return 1;
  }

  // makes all algorithms available to the EVP* routines
  OpenSSL_add_all_algorithms();
  // load the error strings for ERR_error_string
  ERR_load_crypto_strings();

  // const EVP_MD *hashctx;
  EVP_MD_CTX *hashctx;

  // const EVP_MD *hashptr = EVP_get_digestbyname("SHA256");
  const EVP_MD *hashptr = EVP_get_digestbyname("SHA1");

  // EVP_MD_CTX_init(&hashctx);
  hashctx = EVP_MD_CTX_create();
  EVP_DigestInit_ex(hashctx, hashptr, NULL);

  do {
    len = fread(buffer, 1, BUFSIZ, f);
    EVP_DigestUpdate(hashctx, buffer, len);
  } while (len == BUFSIZ);

  unsigned int outlen;
  EVP_DigestFinal_ex(hashctx, buffer, &outlen);
  // EVP_MD_CTX_cleanup(&hashctx);
  EVP_MD_CTX_destroy(hashctx);

  fclose(f);

  int i;
  for (i = 0; i < outlen; ++i)
    printf("%02x", buffer[i]);

  printf("\n");
  return 0;
}