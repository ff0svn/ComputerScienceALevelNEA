#ifndef BCRYPT
#define BCRYPT

#include <stdint.h>

struct charArr{
    char* data;
    int size;
};

struct state{
    uint32_t P[18]; // Array of 18 32 bit integers
    uint32_t S[4][256]; // Arrays of 256 32-bit integers
};

char* bcrypt(uint_least8_t cost, char salt[16],  struct charArr* password);
struct state eksBlowfishSetup(uint_least8_t cost, char salt[16], struct charArr key);
struct state expandKey(struct state state, char salt[16], struct charArr key);
uint64_t blowfishEncrypt(struct state state, uint64_t input);
uint32_t f(struct state state, uint32_t x);
char* concatenate(uint_least8_t cost, char salt[16], char* ctext);
char* threeBytesToB64(char* input);
struct state initState();

#endif