/* Equal point masses, massless rigid rods, no damping. Angles from downward vertical.
 * Equations: https://www.myphysicslab.com/pendulum/double-pendulum-en.html
 * Shared by numerical verification and script-free artwork generation. */
(function () {
  'use strict';
  const TAU = 2 * Math.PI;
  const STEP = 1 / 480;
  function derivatives(s, gravity = 9.81, l1 = 1, l2 = 1) {
    const [a, u, b, v] = s;
    const d = a - b, sn = Math.sin(d), cs = Math.cos(d);
    const den = 3 - Math.cos(2 * d);
    return [u,
      (-3 * gravity * Math.sin(a) - gravity * Math.sin(a - 2 * b)
        - 2 * sn * (v * v * l2 + u * u * l1 * cs)) / (l1 * den),
      v,
      2 * sn * (2 * u * u * l1 + 2 * gravity * Math.cos(a) + v * v * l2 * cs) / (l2 * den)];
  }
  function step(s, dt = STEP, gravity = 9.81, l1 = 1, l2 = 1) {
    const k1 = derivatives(s, gravity, l1, l2);
    const k2 = derivatives(s.map((x, i) => x + dt * k1[i] / 2), gravity, l1, l2);
    const k3 = derivatives(s.map((x, i) => x + dt * k2[i] / 2), gravity, l1, l2);
    const k4 = derivatives(s.map((x, i) => x + dt * k3[i]), gravity, l1, l2);
    return s.map((x, i) => x + dt * (k1[i] + 2 * k2[i] + 2 * k3[i] + k4[i]) / 6);
  }
  function energy(s, gravity = 9.81, l1 = 1, l2 = 1) {
    const [a, u, b, v] = s;
    return l1 * l1 * u * u + .5 * l2 * l2 * v * v
      + l1 * l2 * u * v * Math.cos(a - b)
      - gravity * (2 * l1 * Math.cos(a) + l2 * Math.cos(b));
  }
  function positions(s, l1 = 1, l2 = 1) {
    const x1 = l1 * Math.sin(s[0]), y1 = l1 * Math.cos(s[0]);
    return [x1, y1, x1 + l2 * Math.sin(s[2]), y1 + l2 * Math.cos(s[2])];
  }
  function ensemble(count = 128, degrees = 120, spread = 1e-6, lower = degrees) {
    const a = degrees * Math.PI / 180, b = lower * Math.PI / 180;
    return Array.from({length: count}, (_, i) => [a, 0, b + (i / Math.max(1, count - 1) - .5) * spread * Math.PI / 180, 0]);
  }
  function wrap(angle) { return ((angle + Math.PI) % TAU + TAU) % TAU - Math.PI; }
  const api = {STEP, derivatives, step, energy, positions, ensemble, wrap};
  module.exports = api;
})();
