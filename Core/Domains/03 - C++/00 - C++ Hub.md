# C++ — Hub

Resource management, object lifetime, and zero-cost abstractions.

## The Machine

- [[01 - RAII — The Machine]] — destructor call order, stack unwind sequence
- [[02 - Smart Pointers — The Machine]] — unique_ptr vs shared_ptr control block
- [[22 - shared_ptr — The Machine]] — refcount layout, atomic decrement, deleter call
- [[25 - weak_ptr — The Machine]] — weak count, lock() CAS, cycle breaking
- [[21 - Move Semantics — The Machine (deep)]] — moved-from state, noexcept fast path
- [[18 - VTables — The Machine]] — vptr at offset 0, vtable in .rodata, three-instruction dispatch
- [[20 - Exception Unwinding — The Machine]] — .eh_frame lookup, __cxa_throw, destructor per frame
- [[17 - std::vector — The Machine]] — 2x growth, move_if_noexcept, iterator invalidation

## Theory

- [[01 - RAII]] — destructor timing, stack unwinding, why resources can't leak
- [[02 - Smart Pointers]] — unique_ptr, shared_ptr, weak_ptr ownership models
- [[03 - Move Semantics]] — lvalue/rvalue, move constructor, Rule of Five
- [[06 - Virtual Functions]] — vtable layout, override, pure virtual, slicing danger
- [[04 - Templates]] — function/class templates, specialization, SFINAE
- [[09 - Exception Handling]] — throw/catch, exception safety levels, noexcept

## Interview Q&A

- [[01 - C++ Language Q&A]] — RAII, move semantics, vtables, templates, smart pointers, Rule of Five, noexcept

## Glossary

[[11 - RAII]] · [[18 - shared_ptr]] · [[13 - Templates]]
