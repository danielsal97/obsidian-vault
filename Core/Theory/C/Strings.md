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

---

## Understanding Check

> [!question]- Why does `strncpy` fail to guarantee null termination, and what is the correct safe-copy pattern?
> `strncpy` was designed to pad fixed-width fields, not to be a safe `strcpy`. When the source is longer than `n`, it copies exactly `n` bytes and stops — without writing a `'\0'`. The destination buffer has no terminator, so any subsequent string function will run past the end looking for one. The correct pattern is `strncpy(buf, src, sizeof(buf) - 1); buf[sizeof(buf) - 1] = '\0';` — always force the final byte to zero regardless of what `strncpy` wrote.

> [!question]- What goes wrong if you compare two C strings with `==` instead of `strcmp`?
> `==` compares the pointer values (addresses), not the contents. Two separate arrays containing "hello" have different addresses, so `s1 == s2` is false even when the strings are identical. The reverse is also tricky: two `const char*` pointing to the same string literal may compare equal with `==` because the compiler can coalesce literals — but this is implementation-specific and cannot be relied on. Always use `strcmp` (or `strncmp` for bounded comparison) to test string equality.

> [!question]- Why is modifying a string literal undefined behavior, even though the pointer type `char*` technically allows writes?
> String literals are placed by the linker in a read-only data segment (`.rodata`). The `char*` type does not convey this — it is a historical remnant from before `const` existed in C. Writing through that pointer attempts to modify read-only memory, which on modern systems triggers a segfault (write to a read-protected page). The fix is to always declare string literals as `const char*` so the compiler catches accidental write attempts at compile time.

> [!question]- In LDS, if you build a command string with `snprintf` to send over TCP and the buffer is too small, what happens to the serialized message?
> `snprintf` always null-terminates (when `size > 0`) and returns the number of characters that *would* have been written. If that return value is `>= size`, the output was truncated — the buffer holds a partial string ending in `'\0'`. If you then transmit `strlen(buf)` bytes, the receiver gets a truncated message. The correct pattern is to check the return value: if `ret >= sizeof(buf)`, either allocate a larger buffer or treat it as an error before sending anything.

> [!question]- `strlen` is O(n) — it scans until it finds '\0'. Why can this be a hidden performance problem, and how do you avoid it?
> Every call to `strlen` walks the entire string. If you call it inside a loop (e.g., `for (i = 0; i < strlen(s); i++)`) the loop becomes O(n²). A similar trap is passing `strlen(s)` as an argument to multiple functions on the same string, causing repeated scans. The fix is to compute `strlen` once, store it in a `size_t len` variable, and reuse that value. For dynamic strings where the length is known at construction time (e.g., after `snprintf`), cache the return value directly.
```
