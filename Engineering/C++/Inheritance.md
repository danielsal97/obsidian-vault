# Inheritance

---

## Basics

```cpp
class Animal {
protected:
    std::string m_name;
public:
    Animal(const std::string& name) : m_name(name) {}
    virtual void speak() const { std::cout << "...\n"; }
    virtual ~Animal() = default;
};

class Dog : public Animal {
public:
    Dog(const std::string& name) : Animal(name) {}
    void speak() const override { std::cout << m_name << ": Woof!\n"; }
};
```

---

## Access Specifiers in Inheritance

```cpp
class Derived : public Base    // public members of Base → public in Derived
class Derived : protected Base // public members of Base → protected in Derived
class Derived : private Base   // all Base members → private in Derived
```

`public` inheritance = "is-a" relationship. Most common.  
`private` inheritance = "implemented-in-terms-of". Rare.

---

## Member Access

| In Base | public inheritance | protected inheritance | private inheritance |
|---|---|---|---|
| `public` | public | protected | private |
| `protected` | protected | protected | private |
| `private` | not accessible | not accessible | not accessible |

```cpp
class Base {
public:    int pub;
protected: int prot;
private:   int priv;
};

class Derived : public Base {
    void f() {
        pub = 1;    // OK
        prot = 2;   // OK
        priv = 3;   // ERROR — private, not accessible
    }
};
```

---

## Constructor Chain

Derived constructor must explicitly call base constructor (if base has no default constructor):

```cpp
class Shape {
    std::string m_color;
public:
    Shape(const std::string& color) : m_color(color) {}
};

class Circle : public Shape {
    double m_radius;
public:
    Circle(double r, const std::string& color)
        : Shape(color)       // base constructor called first
        , m_radius(r) {}
};
```

Base is always constructed before derived. Destroyed in reverse order.

---

## Abstract Class vs Interface

**Abstract class:** has at least one pure virtual function. Cannot instantiate. May have data members and non-pure virtual functions.

```cpp
class IStorage {
public:
    virtual void Read(DriverData* d) = 0;    // pure virtual
    virtual void Write(DriverData* d) = 0;
    virtual ~IStorage() = default;
};

// IStorage s;   // ERROR — abstract
```

**Concrete class:** implements all pure virtuals.

```cpp
class LocalStorage : public IStorage {
    std::vector<char> m_buf;
public:
    void Read(DriverData* d) override { ... }
    void Write(DriverData* d) override { ... }
};
```

---

## Multiple Inheritance

A class can inherit from more than one base:

```cpp
class Flyable  { public: virtual void fly() = 0; };
class Swimmable{ public: virtual void swim() = 0; };

class Duck : public Flyable, public Swimmable {
public:
    void fly()  override { std::cout << "flying\n"; }
    void swim() override { std::cout << "swimming\n"; }
};
```

---

## Diamond Problem

```
        Animal
       /      \
    Dog        Cat
       \      /
        DogCat   ← has TWO copies of Animal?
```

```cpp
class Animal { public: int m_age; };
class Dog    : public Animal {};
class Cat    : public Animal {};
class DogCat : public Dog, public Cat {};

DogCat dc;
dc.m_age;        // ERROR — ambiguous: Dog::Animal::m_age or Cat::Animal::m_age?
dc.Dog::m_age;   // explicit — OK but ugly
```

**Solution: virtual inheritance**

```cpp
class Dog : virtual public Animal {};
class Cat : virtual public Animal {};
class DogCat : public Dog, public Cat {};

DogCat dc;
dc.m_age;   // OK — only one Animal subobject
```

Virtual inheritance adds overhead — use only when the diamond is intentional.

---

## Calling Base Class Methods

```cpp
class Derived : public Base {
    void f() override {
        Base::f();    // call base version explicitly
        // then do derived-specific work
    }
};
```

---

## Object Slicing

Copying a derived object into a base value loses the derived part:

```cpp
Dog dog("Rex");
Animal a = dog;   // sliced — only Animal part copied, Dog's data gone
a.speak();        // calls Animal::speak, not Dog::speak — vtable is gone

// Always use pointer or reference for polymorphism:
Animal& ref = dog;
ref.speak();      // calls Dog::speak — correct
```

---

## Casting in Inheritance

```cpp
Animal* a = new Dog("Rex");

// Down-cast — base pointer to derived pointer:
Dog* d = dynamic_cast<Dog*>(a);   // safe — returns nullptr if wrong type
if (d) { d->fetch(); }

Cat* c = dynamic_cast<Cat*>(a);   // a is Dog, not Cat → returns nullptr

// static_cast — no runtime check, undefined behavior if wrong:
Dog* d = static_cast<Dog*>(a);    // dangerous if a is actually Cat
```

`dynamic_cast` requires at least one virtual function in the class (uses RTTI — Run-Time Type Information).

---

## Preventing Inheritance

```cpp
class Leaf final : public Base { ... };  // no class can inherit from Leaf

class Base {
    virtual void f() final;  // no class can override this specific function
};
```

---

## When to Use Inheritance

**Use inheritance for:**
- True "is-a" relationships (`Dog` is an `Animal`)
- Polymorphic interfaces (`IStorage` → `LocalStorage`)
- Sharing implementation across related classes

**Prefer composition over inheritance when:**
- The relationship is "has-a" or "uses-a"
- You only need some behaviors, not the full interface
- The base class has many virtual functions you don't need

```cpp
// Composition — Logger has a FileWriter, not IS-A FileWriter:
class Logger {
    FileWriter m_writer;   // composition
public:
    void log(const std::string& msg) { m_writer.write(msg); }
};

---

## Understanding Check

> [!question]- Why does base class construction always happen before derived construction, and what would go wrong if it were the other way around?
> Base class members are part of the derived object's memory layout — they must exist before the derived constructor can use them. If derived were constructed first, any base method called from the derived constructor would access uninitialized base fields. Destruction follows the reverse order for the same reason: the derived destructor may call base methods, so the base must still be valid. Reverse construction order would mean the base's destructor runs while derived fields still exist, creating a window where derived's destructor could access an already-destroyed base.

> [!question]- What goes wrong if you use `private` inheritance when you actually need the `is-a` relationship for polymorphism?
> With `private` inheritance, public members of the base become private in the derived class and — critically — a `Derived*` cannot be implicitly converted to a `Base*`. Code that expects a `Base*` (e.g., a factory storing `IStorage*`) will not accept a `Derived` object. `private` inheritance means "implemented-in-terms-of", not "is-a" — it provides the base's implementation without exposing the interface. For polymorphic use through base pointers, you always need `public` inheritance.

> [!question]- What is the diamond problem in multiple inheritance and why does `virtual` inheritance solve it?
> Without `virtual` inheritance, `DogCat : Dog, Cat` where both inherit from `Animal` results in two separate `Animal` subobjects embedded in `DogCat`. Accessing `dc.m_age` is ambiguous: which `Animal`'s field? With `virtual` inheritance, `Dog` and `Cat` each carry a virtual base pointer instead of an embedded `Animal`; the actual `Animal` subobject is shared and constructed once by the most-derived class. The overhead is a pointer indirection per base access, which is why virtual inheritance should only be used when the diamond is genuinely intentional.

> [!question]- In LDS, `LocalStorage` publicly inherits `IStorage`. What would break if someone accidentally passed a `LocalStorage` object by value to a function taking `IStorage`?
> Object slicing would occur: only the `IStorage` base subobject is copied, losing all of `LocalStorage`'s data members (`m_buf`, the mutex, etc.). The `vptr` is set to `IStorage`'s vtable, so `Read()` and `Write()` would dispatch to the pure-virtual base — calling them is undefined behavior (or an immediate abort if the vtable slot is a null thunk). The LDS `InputMediator` correctly stores `IStorage*` (pointer), avoiding slicing entirely.

> [!question]- Why is "prefer composition over inheritance" advice for the `has-a` case, and how do you decide between the two in practice?
> Inheritance couples the derived class to the base's entire interface and implementation — changes to the base ripple into all subclasses. Composition couples only to the member's public interface, which you can also replace or mock independently. The decision rule: if you need polymorphic substitutability (caller holds a `Base*` and must be able to substitute `Derived`), use inheritance. If you just need the behavior of another class internally and don't need external callers to treat your object as that type, use composition. For example, `Reactor` uses a socket — it "has a" socket, not "is a" socket — so composition is correct.
```
