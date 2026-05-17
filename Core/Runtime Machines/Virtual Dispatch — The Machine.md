# Virtual Dispatch — The Machine

## The Model

A virtual function call is three machine instructions: load the vptr from the object, index into the vtable to get the function pointer, call through it. The overhead is one extra memory load and one indirect branch. The real costs are not the instructions — they are the cache miss on the vtable (first call, cold), and the indirect branch misprediction (branch predictor cannot reliably predict indirect targets).

---

## How It Moves — Construction Sets the vptr

```cpp
struct Animal {
    virtual void speak();    // vtable slot 0
    virtual void move();     // vtable slot 1
};
struct Dog : Animal {
    void speak() override;   // replaces slot 0
    void move() override;    // replaces slot 1
};

Dog d;
```

```
Animal constructor runs first:
  → writes Animal's vtable address into d.vptr
  → if Animal::Animal() calls speak(): calls Animal::speak() — NOT Dog::speak()
    (vptr points to Animal's vtable while Animal ctor is running)

Dog constructor runs second:
  → overwrites d.vptr with Dog's vtable address
  → now d.vptr → Dog's vtable

After construction: d.vptr → Dog::vtable → [Dog::speak, Dog::move]
```

**Danger zone:** calling virtual functions in a base constructor always calls the base version — the derived vptr has not been written yet.

---

## How It Moves — The Dispatch

```cpp
Animal* a = &d;
a->speak();
```

```
CPU executes:
  mov rax, [a]               ; load a (pointer to Dog object)
  mov rax, [rax]             ; load vptr (first 8 bytes of Dog object)
  mov rax, [rax + 0]         ; load vtable slot 0 (speak)
  call rax                   ; indirect call to Dog::speak

Assembly from the compiler:
  48 8b 07        mov rax, [rdi]      ; rdi = this = a
  48 8b 00        mov rax, [rax]      ; vptr
  ff 10           call [rax]          ; vtable[0]
```

Three instructions instead of one direct `call` for a non-virtual function. The cost comes from the two memory loads (object → vptr → vtable entry).

---

## How It Moves — Cache Behavior

```
vtable lives in .rodata (read-only data segment), NOT near the object.

Cold scenario (first call to this vtable in this run):
  load vptr:       object is hot in L1 → 1 cycle
  load vtable[0]:  vtable in .rodata, cold → L3 miss → 35 cycles

Hot scenario (vtable recently used):
  load vptr:       L1 hit → 1 cycle
  load vtable[0]:  L1 hit → 1 cycle
  Total: 2 extra cycles vs direct call
```

For a tight loop calling the same virtual function on the same type: vtable will be in L1 after first call — overhead is ~2 cycles. For a polymorphic container (Animal* array, mixed Dog/Cat/Bird): different vtable per type, cache thrash on every element.

---

## How It Moves — Object Slicing (the silent bug)

```cpp
Animal a = d;     // copies only the Animal subobject — vptr becomes Animal's
a.speak();        // calls Animal::speak(), NOT Dog::speak()
```

```
Copy assigns: copy Animal's fields from d into a
vptr in a:        Animal's vtable (set by Animal's copy constructor)
d.vptr:           Dog's vtable (unchanged)

a.speak() dispatches through Animal's vtable → Animal::speak()
```

Slicing loses the runtime type. Virtual dispatch only works through a pointer or reference — never through a value.

---

## How It Moves — Devirtualization

```cpp
Dog d;
d.speak();        // compiler knows exact type: devirtualized → direct call
```

```
Compiler sees: d is a Dog (not through a pointer/reference)
Replaces:      indirect call through vtable
With:           direct call to Dog::speak
Cost:           same as a non-virtual call
```

`final` keyword enables devirtualization through pointers:

```cpp
struct Dog final : Animal { void speak() override; };
Animal* a = new Dog();
a->speak();   // compiler: Dog is final, no subclass possible → devirtualize
```

---

## How It Moves — dynamic_cast

```cpp
Animal* a = new Dog();
Dog* d = dynamic_cast<Dog*>(a);
```

```
dynamic_cast at runtime:
  → load typeinfo pointer from vtable (slot before slot 0)
  → walk RTTI (run-time type information) hierarchy
  → check if Dog is in Animal's type chain
  → if yes: adjust pointer + return
  → if no: return nullptr (for pointer cast)
Cost: ~50-200ns depending on hierarchy depth
```

RTTI lives in .rodata alongside the vtable. `dynamic_cast` is the only virtual operation with non-trivial overhead — avoid in hot paths.

---

## Hidden Costs

| Operation | Cost |
|---|---|
| Virtual call, vtable hot (L1) | +2 cycles vs direct call |
| Virtual call, vtable cold (L3 miss) | +35 cycles |
| Virtual call, vtable in DRAM | +200 cycles |
| Indirect branch mispredict | +15-20 cycles |
| `dynamic_cast` (pointer) | 50-200ns |
| Object slicing | Silent — wrong function called, no error |
| Virtual call in base constructor | Silent — base version called, not derived |

---

## Links

→ [[18 - VTables — The Machine]]
→ [[19 - Object Layout — The Machine]]
→ [[09 - Cache Hierarchy — The Machine (deep)]]
→ [[06 - Virtual Functions]]
→ [[C++ Object Lifetime — The Machine]]
