# Type Casting

C++ has four named casts. Each has a specific purpose — always use the most restrictive one that works.

---

## static_cast — Compile-Time Cast

Safe conversions between related types. Checked at compile time only.

```cpp
// Numeric conversions:
int i = static_cast<int>(3.14);         // double → int (truncates)
double d = static_cast<double>(5) / 2;  // 2.5 not 2

// Pointer up/down cast (no runtime check):
Base* b = new Derived();
Derived* d = static_cast<Derived*>(b);  // OK if b really is Derived
                                         // UB if b is actually a different derived type

// void* to typed pointer:
void* p = malloc(sizeof(int));
int* ip = static_cast<int*>(p);

// Enum to int:
int val = static_cast<int>(MyEnum::Value);
```

**Use when:** you know the conversion is valid. No runtime cost.

---

## dynamic_cast — Runtime-Checked Downcast

Safe downcast in an inheritance hierarchy. Requires virtual functions (RTTI).

```cpp
Animal* a = new Dog("Rex");

Dog* d = dynamic_cast<Dog*>(a);   // succeeds — a is actually Dog
if (d) { d->fetch(); }

Cat* c = dynamic_cast<Cat*>(a);   // fails — a is not Cat
if (!c) { /* handle null */ }

// With references (throws std::bad_cast on failure):
Dog& d = dynamic_cast<Dog&>(*a);  // throws if *a is not Dog
```

**Use when:** you need to check the actual runtime type. Has overhead (RTTI lookup).

**Don't overuse:** needing `dynamic_cast` often means your interface design is wrong — rethink the class hierarchy.

---

## const_cast — Add/Remove const

The only cast that can add or remove `const`. Use sparingly.

```cpp
void legacy_api(char* p);   // old API doesn't take const
const char* msg = "hello";
legacy_api(const_cast<char*>(msg));   // OK as long as legacy_api doesn't modify it

// Adding const (always safe):
int x = 5;
const int& cr = const_cast<const int&>(x);

// Removing const then modifying — UB if object was originally const:
const int n = 5;
int* p = const_cast<int*>(&n);
*p = 10;   // UNDEFINED BEHAVIOR — n was declared const
```

**Legitimate uses:** calling legacy C APIs that take non-const pointers but don't modify.  
**Never:** cast away const to actually modify the object.

---

## reinterpret_cast — Raw Bit Reinterpretation

Tells the compiler "treat these bits as a different type." Almost never safe. No conversion performed.

```cpp
// Pointer to integer and back:
int* p = new int(42);
uintptr_t addr = reinterpret_cast<uintptr_t>(p);   // store address as integer
int* p2 = reinterpret_cast<int*>(addr);             // restore

// Function pointer cast (platform-specific):
void* handle = dlopen("lib.so", RTLD_LAZY);
typedef void (*FnPtr)();
FnPtr fn = reinterpret_cast<FnPtr>(dlsym(handle, "func"));

// Type punning (read float as int — use union instead):
float f = 3.14f;
int bits = *reinterpret_cast<int*>(&f);  // technically UB — use memcpy or union
```

**Use only for:** low-level system code, `dlsym` casts, hardware register access.

---

## C-Style Cast — Avoid

```cpp
int x = (int)3.14;   // C-style cast
```

C-style cast tries `static_cast`, then `const_cast`, then `reinterpret_cast` in order — does whatever works. Dangerous because it silently does the wrong thing.

In C++, always use named casts. They're explicit about intent and easier to search for in code.

---

## Summary — Which Cast to Use

| Situation | Cast |
|---|---|
| Numeric conversion (double→int) | `static_cast` |
| Downcast when you're sure of type | `static_cast` |
| Downcast when unsure of type | `dynamic_cast` |
| Remove const for legacy API | `const_cast` |
| Raw pointer ↔ integer | `reinterpret_cast` |
| Never in modern C++ | C-style cast `(T)` |

---

## Implicit Conversions

Conversions the compiler does automatically:

```cpp
int i = 3.14;       // double → int (narrowing — use -Wconversion to catch)
double d = 5;        // int → double (safe widening)
Base* b = new Derived(); // implicit upcast — always safe
```

**`explicit` constructor/conversion prevents implicit conversion:**
```cpp
class MyInt {
public:
    explicit MyInt(int val);  // explicit — prevents: MyInt x = 5;
};

void f(MyInt x);
f(5);                // ERROR — implicit conversion not allowed
f(MyInt(5));         // OK — explicit
f(static_cast<MyInt>(5)); // OK — explicit cast
```
