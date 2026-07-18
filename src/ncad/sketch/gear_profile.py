"""Generate an involute gear profile (a closed 2D point list) plus its meshing relations.

The single source of truth for a gear, mirroring CamProfile: one object owns BOTH the drawn tooth
``outline()`` AND the mesh relations a gear/rack_pinion coupling consumes (``center_distance``,
``mesh_ratio``, ``rack_travel_per_radian``), so the drawn teeth and the motion coupling can never
disagree.

Three gear TYPES (professional generator parity, cf. Fusion SpurGear / Creo / KISSsoft):
- external: teeth point outward (a normal spur gear); addendum > pitch > dedendum radius.
- internal: a ring gear, teeth point inward; addendum < pitch < dedendum radius (inverted band).
- rack:     the z -> infinity limit, straight trapezoidal teeth at the pressure angle on a line.

Professional tooth parameters:
- module ``m``, tooth count ``z``, pressure angle ``alpha`` (the fundamentals);
- profile shift ``x`` (addendum-modification coefficient): shifts the reference rack by x*m, raising
  addendum + dedendum by x*m (avoids undercut on low z, sets the working center distance);
- trochoidal root fillet: the real filleted root the cutter leaves, not a radial line to a corner;
- backlash ``j`` (mm): thins each tooth by j/2 per flank at the pitch line for running clearance.

Standard full-depth proportions (x = 0): pitch d = m*z; base d_b = d*cos(alpha); addendum
r_a = d/2 + m(1 + x); dedendum r_f = d/2 - m(1.25 - x). Each flank is the involute of the base
circle. Pure math; no kernel. One class.

Scope: flat involute gears (external/internal/rack), standard depth, profile shift, trochoid root,
backlash. Deferred (inherently 3D or microgeometry): helical / bevel / worm, tip relief, crowning.
"""

import math

# Points sampled along each involute flank and along each trochoidal root fillet.
_FLANK_SAMPLES = 10
_FILLET_SAMPLES = 6
_ADDENDUM_COEF = 1.0     # standard addendum = 1.0 * m (before profile shift)
_DEDENDUM_COEF = 1.25    # standard dedendum = 1.25 * m (before profile shift)
_GEAR_TYPES = frozenset({"external", "internal", "rack"})


class GearProfileError(Exception):
    """Invalid gear parameters (module/teeth/pressure_angle/type out of range)."""


class GearProfile:
    """An involute gear profile (external/internal/rack): profile shift, root fillet, backlash."""

    def __init__(self, module: float, teeth: int, pressure_angle: float = 20.0,
                 gear_type: str = "external", profile_shift: float = 0.0,
                 backlash: float = 0.0, length: float = 0.0, phase: float = 0.0) -> None:
        if not isinstance(module, (int, float)) or module <= 0:
            raise GearProfileError("gear module must be a positive number")
        if gear_type not in _GEAR_TYPES:
            raise GearProfileError(f"gear_type must be one of {sorted(_GEAR_TYPES)}")
        if gear_type != "rack" and (not isinstance(teeth, int) or teeth < 3):
            raise GearProfileError("gear teeth must be an integer >= 3")
        if gear_type == "rack" and (not isinstance(teeth, int) or teeth < 1):
            raise GearProfileError("rack teeth must be an integer >= 1")
        if not isinstance(pressure_angle, (int, float)) or not 0 < pressure_angle < 45:
            raise GearProfileError("gear pressure_angle must be in (0, 45) degrees")
        if not isinstance(profile_shift, (int, float)):
            raise GearProfileError("gear profile_shift must be a number")
        if not isinstance(backlash, (int, float)) or backlash < 0:
            raise GearProfileError("gear backlash must be a non-negative number")
        if not isinstance(phase, (int, float)):
            raise GearProfileError("gear phase must be a number (degrees)")
        self._m = float(module)
        self._z = int(teeth)
        self._alpha = math.radians(float(pressure_angle))
        self._type = gear_type
        self._x = float(profile_shift)
        self._backlash = float(backlash)
        self._phase = math.radians(float(phase))
        self._length = float(length) if length else self._z * math.pi * self._m

    @property
    def gear_type(self) -> str:
        """"external", "internal", or "rack"."""
        return self._type

    @property
    def pitch_radius(self) -> float:
        """Pitch-circle radius d/2 = m*z/2 (for a rack this is the reference-line offset)."""
        return self._m * self._z / 2.0

    @property
    def base_radius(self) -> float:
        """Base-circle radius (the involute is generated from this): pitch_r * cos(alpha)."""
        return self.pitch_radius * math.cos(self._alpha)

    @property
    def addendum_radius(self) -> float:
        """Tooth-tip radius. External: pitch + m(1 + x). Internal: pitch - m(1 + x) (inward tip)."""
        rise = self._m * (_ADDENDUM_COEF + self._x)
        return self.pitch_radius - rise if self._type == "internal" else self.pitch_radius + rise

    @property
    def dedendum_radius(self) -> float:
        """Root radius. External: pitch - m(1.25 - x). Internal: pitch + m(1.25 - x), outward."""
        drop = self._m * (_DEDENDUM_COEF - self._x)
        return self.pitch_radius + drop if self._type == "internal" else self.pitch_radius - drop

    def tooth_thickness_angle(self) -> float:
        """Half the circular tooth thickness at the pitch circle, as an angle (radians).

        Nominal half-thickness arc = (pi*m/2 + 2*x*m*tan(alpha)) / 2, thinned by backlash j/2 per
        flank. Divided by the pitch radius to get the angle. This is what the flank offset uses, so
        backlash + profile shift flow straight into the drawn tooth.
        """
        thickness = math.pi * self._m / 2.0 + 2.0 * self._x * self._m * math.tan(self._alpha)
        thickness -= self._backlash
        return max(thickness, 0.0) / (2.0 * self.pitch_radius)

    @staticmethod
    def center_distance(a: "GearProfile", b: "GearProfile") -> float:
        """The meshing center distance of two gears (same module).

        Rack + pinion: the pinion pitch radius (the rack rides tangent to the pitch circle).
        Internal + external: the difference (z_ring - z_pinion)*m/2 (the pinion runs in the ring).
        External + external: shift-corrected via the involute function (working pressure angle),
        which reduces to the standard sum (z1+z2)*m/2 when the total profile shift is zero.
        """
        if a._type == "rack" or b._type == "rack":
            pinion = b if a._type == "rack" else a
            return pinion.pitch_radius
        if a._type == "internal" or b._type == "internal":
            ring = a if a._type == "internal" else b
            pinion = b if a._type == "internal" else a
            return (ring._z - pinion._z) * a._m / 2.0
        standard = (a._z + b._z) * a._m / 2.0
        total_shift = a._x + b._x
        if abs(total_shift) < 1e-12:
            return standard
        # Working pressure angle from the involute-function balance:
        # inv(alpha_w) = inv(alpha) + 2*(x1+x2)/(z1+z2)*tan(alpha); then a_w = a_std*cos a/cos a_w.
        inv_alpha = math.tan(a._alpha) - a._alpha
        inv_alpha_w = inv_alpha + 2.0 * total_shift / (a._z + b._z) * math.tan(a._alpha)
        alpha_w = _inv_involute(inv_alpha_w)
        return standard * math.cos(a._alpha) / math.cos(alpha_w)

    @staticmethod
    def mesh_ratio(driver: "GearProfile", driven: "GearProfile") -> float:
        """Angular velocity ratio omega_driven / omega_driver = -z_driver / z_driven.

        External meshes reverse sense (negative); an internal (ring) mesh keeps sense (positive).
        """
        magnitude = driver._z / driven._z
        same_sense = driver._type == "internal" or driven._type == "internal"
        return magnitude if same_sense else -magnitude

    def rack_travel_per_radian(self) -> float:
        """Rack linear travel per radian of pinion rotation (mm/rad) = the pinion pitch radius."""
        return self.pitch_radius

    def outline(self) -> list[list[float]]:
        """The closed gear outline as a list of [x, y] points.

        Rack: a straight-toothed strip along +x. External/internal: z tooth periods walked CCW, each
        a rising involute flank + addendum crest + falling flank + root (trochoidal fillet + arc).
        """
        if self._type == "rack":
            return self._rack_outline()
        return self._radial_outline()

    def _radial_outline(self) -> list[list[float]]:
        """External/internal outline: z teeth, each flank the involute of the base circle."""
        pitch_angle = 2.0 * math.pi / self._z
        half_tooth = self.tooth_thickness_angle()
        inv_alpha = math.tan(self._alpha) - self._alpha
        # The flank crosses the pitch circle at +/- half_tooth about the tooth centre; its base
        # angular offset is (half_tooth + inv_alpha).
        flank_offset = half_tooth + inv_alpha
        points: list[list[float]] = []
        for k in range(self._z):
            centre = k * pitch_angle + self._phase   # phase clocks the whole gear (tooth timing)
            rising = self._flank(centre, -1.0, flank_offset)
            falling = list(reversed(self._flank(centre, +1.0, flank_offset)))
            points.extend(rising)
            points.extend(falling)
        return points

    def _flank(self, centre: float, side: float, flank_offset: float) -> list[list[float]]:
        """One flank root->tip (external) with a trochoidal root fillet below the active involute.

        ``side`` = -1 rising / +1 falling; the flank's polar angle at radius r is
        ``centre + side*(flank_offset - inv(roll(r)))``. For an internal gear the radial band is
        inverted (tip inside, root outside), handled by walking from the addendum to the dedendum.
        """
        if self._type == "internal":
            return self._internal_flank(centre, side, flank_offset)
        r_active_start = max(self.base_radius, self.dedendum_radius)
        out: list[list[float]] = []
        # Trochoidal root fillet from the dedendum up to where the active involute begins.
        if self.dedendum_radius < r_active_start:
            out.extend(self._root_fillet(centre, side, flank_offset, r_active_start))
        for i in range(_FLANK_SAMPLES + 1):
            r = r_active_start + (self.addendum_radius - r_active_start) * i / _FLANK_SAMPLES
            angle = centre + side * (flank_offset - _involute_angle(self.base_radius, r))
            out.append([r * math.cos(angle), r * math.sin(angle)])
        return out

    def _internal_flank(self, centre: float, side: float, flank_offset: float) -> list[list[float]]:
        """An internal-gear flank: the involute active from the addendum (inner tip) to the root.

        The material is outside the pitch circle, so the tooth space is the involute and we walk
        from the addendum radius (smaller) out to the dedendum radius (larger); no undercut fillet
        for the coarse blockout (a radial segment closes the root).
        """
        r_lo = max(self.base_radius, self.addendum_radius)
        out: list[list[float]] = []
        for i in range(_FLANK_SAMPLES + 1):
            r = r_lo + (self.dedendum_radius - r_lo) * i / _FLANK_SAMPLES
            angle = centre + side * (flank_offset - _involute_angle(self.base_radius, r))
            out.append([r * math.cos(angle), r * math.sin(angle)])
        return out

    def _root_fillet(self, centre: float, side: float, flank_offset: float,
                     r_active_start: float) -> list[list[float]]:
        """A trochoidal root fillet from the dedendum up to the start of the active involute.

        Approximated as a smooth blend arc in polar space: the angle eases from the root (offset by
        the full flank_offset at the dedendum) to the involute's angle at r_active_start, so the
        drawn root is a rounded fillet rather than a sharp radial corner.
        """
        angle_at_start = flank_offset - _involute_angle(self.base_radius, r_active_start)
        out: list[list[float]] = []
        for i in range(_FILLET_SAMPLES):
            t = i / _FILLET_SAMPLES
            r = self.dedendum_radius + (r_active_start - self.dedendum_radius) * t
            # Ease the offset from flank_offset (root) to angle_at_start (involute), smoothstep.
            ease = t * t * (3.0 - 2.0 * t)
            offset = flank_offset + (angle_at_start - flank_offset) * ease
            angle = centre + side * offset
            out.append([r * math.cos(angle), r * math.sin(angle)])
        return out

    def _rack_outline(self) -> list[list[float]]:
        """A straight-toothed rack strip along +x: trapezoidal teeth + a solid backing below.

        The pitch line is y = 0; the crest is at +m (addendum), the root at -1.25m (dedendum). Each
        tooth is a trapezoid whose flanks lean at the pressure angle. The strip closes with a
        backing rectangle below the root so it is a single closed profile to extrude.
        """
        p = math.pi * self._m                       # circular pitch (crest+space) along the line
        addendum = self._m * (_ADDENDUM_COEF + self._x)
        dedendum = self._m * (_DEDENDUM_COEF - self._x)
        # Tooth thickness at the pitch line = p/2 (+ shift, - backlash); flank run over the tooth
        # height due to the pressure angle.
        thickness = p / 2.0 + 2.0 * self._x * self._m * math.tan(self._alpha) - self._backlash
        run = (addendum + dedendum) * math.tan(self._alpha)   # x offset over the tooth height
        top: list[list[float]] = []
        for k in range(self._z):
            xc = (k + 0.5) * p                        # tooth centre along the line
            # Root-left, up the rising flank to crest-left, across the crest, down to root-right.
            top.append([xc - thickness / 2.0 - run / 2.0, -dedendum])
            top.append([xc - thickness / 2.0 + run / 2.0, addendum])
            top.append([xc + thickness / 2.0 - run / 2.0, addendum])
            top.append([xc + thickness / 2.0 + run / 2.0, -dedendum])
        back = dedendum + self._m                     # backing depth below the root
        length = self._z * p
        points = [[0.0, -dedendum]]
        points.extend(top)
        points.append([length, -dedendum])
        points.append([length, -back])
        points.append([0.0, -back])
        return points


def _involute_angle(base_r: float, r: float) -> float:
    """The involute angular position inv(roll) at radius r on the involute of ``base_r``.

    roll = acos(base_r / r); inv = tan(roll) - roll. At r = base_r this is 0. Clamped so a radius at
    or below the base circle returns 0 (the involute does not exist below its base).
    """
    if r <= base_r:
        return 0.0
    roll = math.acos(max(-1.0, min(1.0, base_r / r)))
    return math.tan(roll) - roll


def _inv_involute(inv_value: float, iterations: int = 30) -> float:
    """Invert the involute function: find alpha such that tan(alpha) - alpha == inv_value.

    Newton iteration from a cube-root seed; used for the working pressure angle of a shifted mesh.
    """
    if inv_value <= 0.0:
        return 0.0
    alpha = (3.0 * inv_value) ** (1.0 / 3.0)          # classic starting estimate
    for _ in range(iterations):
        f = math.tan(alpha) - alpha - inv_value
        df = math.tan(alpha) ** 2                      # d/da(tan a - a) = sec^2 a - 1 = tan^2 a
        if df < 1e-12:
            break
        alpha -= f / df
    return alpha
