SHA1 and SHA256 example in C using OpenSSL library

Inspired from https://stackoverflow.com/questions/41109861/sha1-example-in-c-using-openssl-library
The example given on the page above is broken as now EVP_MD_CTX_init and EVP_MD_CTX_cleanup are deprecated, in fact it looks like they have been removed from the OpenSSL library. I fixed the example to use EVP_MD_CTX_create and EVP_MD_CTX_destroy

Compile with:
gcc -o sha1 sha1.c -lcrypto
