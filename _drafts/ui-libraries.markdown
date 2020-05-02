---
layout: post
title:  "Why UI Programming Sucks, and How to Make It Better"
date:   2018-10-02 16:30:00 +0200
categories: climbing
---

# UI Programming Sucks

Explain **that** it sucks.

# Why?

UI programming is, similarly to all other kinds of programming programming, mostly about composition. In UI, we compose what is known as *widgets*, or *components*. These are the elements displayed on the screen, which can be interacted with by the user. This means that widgets typically have multiple responsibilities:

 * Display on the screen,
 * Reaction to user events,
 * Reaction to internal application state.

 It turns out that widget composition is quite involved, as it must correctly weave together all of the responsibilities above. To solve the problem, we must carefully analyze composition itself.

The simplest kind of widget composition is **composition in space**. It is typically hierarchical: widget may be a container, or a window, which contains and manages child widgets. Alternatively, the structure may be flat, such that a list of sibling widgets is manipulated by the UI framework.

There is another kind of composition: **composition in time**. It involves creating, deleting, or modifying widgets in response to user interaction with other widgets. Whereas composition in space is unordered, and the widgets can be conceptually specified in any order, composition in time is inherently ordered. We must know the result of the interaction with past widgets to create future widgets.

Most UI frameworks treat both composition types very differently, and one of them tends to be neglected by the framework and exceptionally hard to get right. Let me show on some examples.

If you don't care about some of the frameworks, feel free to skip the respective sections. I will be listing a lot of negatives, but that doesn't mean that there aren't any positives. They are just not very interesting in the context of identifying UI framefork problems.

## Traditional UI Frameworks

<!-- Traditionally, UI frameworks leverage the object-oriented paradigm. Widgets are objects, and they have methods which are called in reaction to user events. These methods in turn modify state. State itself is both centralized ("model"), and distributed among widgets ("view"). This dichotomy forces the programmer to synchronize view and model manually ("controller"), which is laborious and error-prone. -->

Examples of traditional UI frameworks are abundant: Qt, GTK, C# WinForms(?), Android SDK(?), etc.

**Composition in space** is done using normal language constructs. Widgets can be constructed and passed as arguments to container widgets. Language features can be leveraged there: list widgets can be populated in a loop, etc. To make the process of creating widget layout easier, design tools can be used, which generate the required code from configuration files, and/or in a WYSIWYG editor.

Much has been done to streamline composition in space. The same cannot be said for **composition in time**, however. To modify the widget tree in reaction to user interaction, modification is performed from the respective event handler. New widgets are be designed manually, without the assistance of design tools. Current state of the UI may need to be stored inside the model, which leads to model-view synchronization issues. This frequently leads to proliferation of state machines in event handlers and bugs around unhandled corner cases. Composition in time ends up being an ad-hoc decentralized mess.

Due to these difficulties, composition in time is often avoided. User interfaces tend to be static and non-responsive. Most changes are confirmed by "OK" buttons, which brings at least a bit of centralization of update logic. There is a lot of boilerplate because widgets are objects, and because the model-view redundancy.

ToDo list:
* [x] C#, WinForms?, GTK, Android UIs
* [ ] Retained mode, traditional, desktop
* [x] Event driven user interaction
* [x] Fractured state, MVC approach
* [x] Composition in time is implicit, hard, threaded through state. Therefore, it is rarely done, interfaces tend not to be reactive

## Functional Reactive programming

Functional Reactive Programming (FRP) tries to make composition in time, and management of time-varying values generally, explicit and principled.  

ToDo list:
* [ ] Meta-language for widget specification. Time is treated in a point-free style. Widgets are transformers of the state.
* [ ] Composition in time is HARD.

## React, Redux

React improves upon traditional UI frameworks in two important ways:

1. State is no longer split between model and view. View is now stateless. This requires some magic behind the scenes, but it works great in practice and seems to be *the* way to do it.
2. Information flow is restricted to one direction: parent -> child. Message passing must be used in the other direction. This makes event handling much easier to reason about.

TODO: join the paragraphs together.

Redux can be used to centralize state handling. In Redux, all state changes happen in the same way, and in the same place.

Composition in time can be handled by creating a state-machine.

* React alone uses nested components. The components manage their state. It is extremely verbose, event-driven
* Redux makes composition in time explicit.
* Similar to Elm architecture? Designers do not need to shy away from composition in time.

## Immediate mode UI

* Here, composition in space is achieved by normal language constructs, including if, while, etc.
* Composition in time is implicit, carried over by state variables

# Solution

Be honest about composition. The simplest case is, just treat both composition kinds explicitly.

## Composition in space

```haskell
-- Chain siblings together
orr :: [Widget] -> Widget

-- Nest widgets
window :: Parameters -> Widget -> Widget
```


## Concur UI

* Composition in time, and composition in space are explicit
* Time compomsition uses normal language constructs, with all the power they bring
* Space composition uses builder functions and lists of widgets (a DSL).
* This is the sweet spot in the design space
* But state must be propagated upwards to guarantee state persistance.

## Composition in Time

```haskell
>>= :: Widget
```
