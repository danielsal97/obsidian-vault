# Pointers

A pointer is a variable that holds a memory address. Understanding pointers deeply is the foundation of C and systems programming.

---

## What a Pointer Is

```c
int x = 5;
int* p = &x;   // p holds the address of x (e.g. 0x7ffd1234)
*p = 10;       // dereference: follow the address and write 10 there
               // now x == 10
```

Memory picture:
```
Address     Value
0x7ffd1234  5       ← x lives here
0x7ffd1238  0x7ffd1234  ← p lives here, holds address of x
```

`&` = "address of" — gives you the pointer  
`*` = "dereference" — follows the pointer to the value

---

## Pointer Types

The type of a pointer tells the compiler how many bytes to read/write at the address, and how pointer arithmetic works.

```c
char*   p;   // reads 1 byte at *p
int*    p;   // reads 4 bytes at *p
double* p;   // reads 8 bytes at *p
void*   p;   // no type — cannot dereference, must cast first
```

---

## Pointer Arithmetic

```c
int arr[] = {10, 20, 30, 40};
int* p = arr;   // points to arr[0]

p + 1;   // address + sizeof(int) = next element
p++;     // p now points to arr[1]
p[2];    // same as *(p + 2) — element 2 from current position

// Distance between two pointers (same array):
int* end = arr + 4;
ptrdiff_t n = end - arr;   // = 4 (elements, not bytes)
```

Arithmetic is in units of the pointed-to type — `int* p; p++` moves 4 bytes, not 1.

---

## Arrays and Pointers

An array name decays to a pointer to its first element in most contexts:

```c
int arr[5];
int* p = arr;        // arr decays to &arr[0]
arr[i] == *(arr+i)   // always true — indexing IS pointer arithmetic

// Exception: sizeof does NOT decay
sizeof(arr)  // 20 (5 * sizeof(int))
sizeof(p)    // 8 (pointer size on 64-bit)
```

---

## Double Pointers

A pointer to a pointer. Used when a function needs to modify the caller's pointer.

```c
void allocate(int** pp, int size) {
    *pp = malloc(size * sizeof(int));   // modify the caller's pointer
}

int* arr = NULL;
allocate(&arr, 10);   // pass address of the pointer
// now arr points to allocated memory
```

Also used for arrays of strings (`char** argv`) — array of pointers to char arrays.

---

## Function Pointers

A pointer to executable code. Enables callbacks and runtime dispatch.

```c
// Declare: return_type (*name)(param_types)
int (*compare)(int, int);

int less_than(int a, int b) { return a < b; }
compare = less_than;
compare(3, 5);   // calls less_than(3, 5)

// typedef makes it readable:
typedef int (*Comparator)(int, int);
Comparator cmp = less_than;

// Array of function pointers (dispatch table):
void (*handlers[4])(int) = { on_read, on_write, on_flush, on_disconnect };
handlers[op](fd);   // runtime dispatch by op code
```

---

## const and Pointers

Four combinations — read right to left:

```c
int* p;               // pointer to int — both mutable
const int* p;         // pointer to const int — can't modify *p
int* const p;         // const pointer to int — can't change p itself
const int* const p;   // const pointer to const int — nothing mutable
```

---

## Null Pointer

```c
int* p = NULL;   // or 0, or (void*)0 in C
                 // nullptr in C++

if (p != NULL) { *p = 5; }   // always check before dereference
```

Dereferencing NULL is undefined behavior — usually a segfault on modern systems, but not guaranteed.

---

## Pointer Pitfalls

**Dangling pointer** — pointing to memory that has been freed or gone out of scope:
```c
int* bad() {
    int x = 5;
    return &x;   // x is gone after return — dangling pointer
}

int* p = malloc(4);
free(p);
*p = 5;   // use-after-free — undefined behavior
```

**Wild pointer** — uninitialized pointer:
```c
int* p;    // contains garbage address
*p = 5;   // writes to random memory — undefined behavior
// Fix: always initialize: int* p = NULL;
```

**Buffer overflow** — pointer arithmetic past array bounds:
```c
int arr[5];
int* p = arr + 10;
*p = 5;   // writes 10 elements past array — undefined behavior
```

---

## void* — Generic Pointer

`void*` can hold any pointer type. Used for generic functions (like `malloc`, `memcpy`, `qsort`).

```c
void* malloc(size_t n);   // returns void* — caller casts to desired type

void memcpy(void* dst, const void* src, size_t n);   // works for any type

// qsort comparator receives void* — you cast:
int cmp(const void* a, const void* b) {
    return *(int*)a - *(int*)b;
}
qsort(arr, n, sizeof(int), cmp);
```

In C++, `void*` is replaced by templates — type safety without casting.

---

## Pointer Size

On 64-bit systems: all pointers are 8 bytes regardless of what they point to.  
On 32-bit systems: 4 bytes.

```c
sizeof(int*)    // 8 on 64-bit
sizeof(char*)   // 8 on 64-bit — same as int*
sizeof(void*)   // 8 on 64-bit
```
