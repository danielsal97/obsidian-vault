# Strings in C

A string in C is a null-terminated array of `char`. There is no string type — just a convention.

---

## The Null Terminator

```c
char s[] = "hello";
// stored as: ['h','e','l','l','o','\0']
// indices:     0    1    2    3    4   5
```

`'\0'` is byte value 0. Every C string function relies on it to find the end.

```c
strlen("hello")  // = 5 — counts bytes until '\0', not including it
sizeof("hello")  // = 6 — includes '\0'
```

If you forget the null terminator, every string function runs past the end of your buffer until it finds a zero byte — buffer overread, undefined behavior.

---

## String Literals vs char Arrays

```c
char* p = "hello";    // string literal — stored in read-only memory
p[0] = 'H';           // UNDEFINED BEHAVIOR — cannot modify literal

char s[] = "hello";   // copy into stack array — mutable
s[0] = 'H';           // fine — s = "Hello"
```

Always use `const char*` for string literals:
```c
const char* msg = "hello";   // compiler warns if you try to modify it
```

---

## Key String Functions

```c
#include <string.h>

strlen(s)              // length (not counting '\0')
strcpy(dst, src)       // copy src into dst — UNSAFE, no bounds check
strncpy(dst, src, n)   // copy at most n bytes — does NOT guarantee '\0'
strcat(dst, src)       // append src to dst — UNSAFE
strncat(dst, src, n)   // append at most n bytes — safer
strcmp(a, b)           // 0 if equal, <0 if a<b, >0 if a>b
strncmp(a, b, n)       // compare at most n bytes
strchr(s, c)           // find first occurrence of char c — returns pointer or NULL
strstr(haystack, needle) // find first occurrence of substring
```

**Safe copy pattern:**
```c
char buf[64];
strncpy(buf, src, sizeof(buf) - 1);
buf[sizeof(buf) - 1] = '\0';   // strncpy does NOT guarantee null termination
```

---

## sprintf / snprintf

```c
char buf[64];
sprintf(buf, "x=%d y=%d", x, y);    // UNSAFE — no bounds check
snprintf(buf, sizeof(buf), "x=%d", x);  // safe — always use this
```

`snprintf` always null-terminates as long as `size > 0`.

---

## String to Number Conversions

```c
int n = atoi("42");        // string → int, no error checking
long n = strtol("42", NULL, 10);  // base 10, with error checking
double d = strtod("3.14", NULL);
```

`strtol` is safer — it sets `errno` on overflow and lets you detect invalid input via the end pointer.

---

## Dynamic Strings

C has no `std::string`. Dynamic strings are char arrays on the heap:

```c
char* dup = malloc(strlen(src) + 1);  // +1 for '\0'
strcpy(dup, src);
// ... use dup ...
free(dup);

// Or use strdup (POSIX):
char* dup = strdup(src);  // malloc + strcpy in one call
free(dup);
```

---

## Common Bugs

**Off-by-one — forgetting '\0':**
```c
char buf[5];
strcpy(buf, "hello");   // writes 6 bytes into 5-byte buffer — overflow
// Fix: char buf[6] or strncpy with n-1
```

**Comparing strings with ==:**
```c
if (s1 == s2)         // compares ADDRESSES — always false for different arrays
if (strcmp(s1, s2) == 0)  // correct — compares contents
```

**Returning pointer to local array:**
```c
char* bad() {
    char buf[32];
    snprintf(buf, sizeof(buf), "result");
    return buf;   // buf is gone after return — dangling pointer
}
// Fix: pass buffer as parameter, or malloc it (caller must free)
```
