/**
 * Deterministic seeded PRNG for the sim core (spec: "PCG32 or similar").
 * sfc32 (Chris Doty-Humphrey's Small Fast Counting RNG): 128-bit state, uint32 ops
 * only, identical output on every JS engine. No Math.random anywhere in the sim.
 */
export class Rng {
  private a: number;
  private b: number;
  private c: number;
  private d: number;

  constructor(seed: number) {
    // seed expansion via splitmix32
    let h = seed >>> 0;
    const next = () => {
      h = (h + 0x9e3779b9) >>> 0;
      let z = h;
      z = Math.imul(z ^ (z >>> 16), 0x21f0aaad);
      z = Math.imul(z ^ (z >>> 15), 0x735a2d97);
      return (z ^ (z >>> 15)) >>> 0;
    };
    this.a = next();
    this.b = next();
    this.c = next();
    this.d = next();
    for (let i = 0; i < 12; i++) this.nextU32(); // warm up
  }

  nextU32(): number {
    const t = (this.a + this.b + this.d) >>> 0;
    this.d = (this.d + 1) >>> 0;
    this.a = this.b ^ (this.b >>> 9);
    this.b = (this.c + (this.c << 3)) >>> 0;
    this.c = ((this.c << 21) | (this.c >>> 11)) >>> 0;
    this.c = (this.c + t) >>> 0;
    return t;
  }

  /** float in [0, 1) */
  next(): number {
    return this.nextU32() / 4294967296;
  }

  /** int in [0, n) */
  nextInt(n: number): number {
    return Math.floor(this.next() * n);
  }

  /** uniform in [lo, hi) */
  range(lo: number, hi: number): number {
    return lo + (hi - lo) * this.next();
  }

  /** pick index by weights (assumes some weight > 0) */
  weighted(weights: number[]): number {
    let sum = 0;
    for (const w of weights) sum += w;
    if (sum <= 0) return 0;
    let r = this.next() * sum;
    for (let i = 0; i < weights.length; i++) {
      r -= weights[i]!;
      if (r <= 0) return i;
    }
    return weights.length - 1;
  }
}
