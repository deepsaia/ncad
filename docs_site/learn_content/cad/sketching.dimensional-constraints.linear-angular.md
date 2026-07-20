**Dimensional constraints** fix the *size* of sketch geometry with a numeric value: **linear**
(distance), **radial/diametral** (radius or diameter), and **angular** (the angle between two
lines).

- A **linear** dimension pins the distance between two points, or a point and a line (a horizontal,
  vertical, or aligned distance).
- A **radius** or **diameter** dimension fixes an arc or circle's size.
- An **angular** dimension fixes the angle between two lines (a draft angle, a chamfer, a
  spoke spacing).

<figure markdown="span">
<svg viewBox="0 0 320 130" width="340" role="img" aria-label="Linear and angular dimensions" xmlns="http://www.w3.org/2000/svg" fill="none" stroke="currentColor" stroke-width="1.6">
  <line x1="30" y1="40" x2="150" y2="40" stroke-width="2"/>
  <line x1="30" y1="30" x2="30" y2="60"/>
  <line x1="150" y1="30" x2="150" y2="60"/>
  <text x="78" y="30" fill="currentColor" stroke="none" font-size="12">60</text>
  <line x1="210" y1="110" x2="300" y2="110" stroke-width="2"/>
  <line x1="210" y1="110" x2="285" y2="55" stroke-width="2"/>
  <path d="M 250 110 A 40 40 0 0 0 240 82" />
  <text x="250" y="100" fill="currentColor" stroke="none" font-size="12">30&#176;</text>
</svg>
<figcaption>A linear distance dimension (left) and an angular dimension between two lines (right).</figcaption>
</figure>

## Value and expression

A dimension's value can be a literal (60 mm) or an **expression** referencing a parameter
(`2 * width + 5`). Expression-driven dimensions are what turn a sketch into a parametric family: one
named parameter propagates through every dimension that references it. Each dimension removes one
degree of freedom; together with geometric constraints, enough dimensions bring the sketch to
**fully defined**, the state where every entity has a unique solved position.
