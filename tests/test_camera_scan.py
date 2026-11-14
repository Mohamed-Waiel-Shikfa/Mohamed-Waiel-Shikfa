import math
import re
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from mechanical_scenes import (
    CAMERA_SCAN_SECONDS, CameraBlueprint,
    ScanJointBlueprint, camera_scan_angles, scan_gimbal,
)


class CameraScanTests(unittest.TestCase):
    def test_sweep_is_periodic_and_has_no_holds(self):
        for i in range(180):
            t=i/10
            at=camera_scan_angles(t)
            after=camera_scan_angles(t+.001)
            loop=camera_scan_angles(t+CAMERA_SCAN_SECONDS)
            self.assertGreater(math.dist(at,after), 1e-7)
            for a,b in zip(at,loop):
                self.assertAlmostEqual(a,b)
            self.assertLessEqual(abs(at[0]), .42)
            self.assertEqual(at[1], 0.)
            self.assertLessEqual(abs(at[2]), .24)

    def test_pitch_keeps_both_trunnions_registered(self):
        b = CameraBlueprint(0, 0, 1700)
        for yaw in (-.42, 0., .42):
            yoke = ScanJointBlueprint(b, (0, 0, 0), (yaw, 0., 0.), 2)
            for pitch in (-.24, 0., .24):
                camera = ScanJointBlueprint(b, (0, 0, 0), (yaw, 0., pitch), 3)
                for y in (-.026, .026):
                    self.assertEqual(camera.p((0, y, -.059)), yoke.p((0, y, -.059)))

    def test_geometry_topology_and_mount_stay_fixed(self):
        b = CameraBlueprint(848, 221, 1700)
        reference = None
        for i in range(89):
            root = ET.fromstring('<svg>'+scan_gimbal(b, camera_scan_angles(i/88*CAMERA_SCAN_SECONDS))+'</svg>')
            signature = [(el.tag, len(el.get('points', '').split()),
                          re.findall('[a-zA-Z]', el.get('d', ''))) for el in root]
            mount = [ET.tostring(el) for el in list(root)[-16:]]
            if reference is None:
                reference, fixed_mount = signature, mount
            self.assertEqual(signature, reference)
            self.assertEqual(mount, fixed_mount)
            for el in root:
                for number in re.findall(r'-?\d+(?:\.\d+)?', el.get('points', '')+el.get('d', '')):
                    self.assertTrue(math.isfinite(float(number)))


if __name__ == '__main__':
    unittest.main()
