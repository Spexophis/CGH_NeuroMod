# -*- coding: utf-8 -*-
# Copyright (c) 2025 Ruizhe Lin
# Licensed under the MIT License.


from dataclasses import dataclass
from typing import Tuple, List

import numpy as np
from PIL import Image

from cgh_neuromod import logger


@dataclass
class ImagingGeometry:
    pixel_size_cam: float  # camera pixel size
    mag_total: float  # imaging magnification to camera
    flip_x: int = 1  # +1 or -1 to account for horizontal flips
    flip_y: int = 1  # +1 or -1 to account for vertical flips
    u0: int = 600  # center of the field in pixel coordinates.
    v0: int = 395

    def pixels_to_sample(self, u: float, v: float) -> Tuple[float, float]:
        """
        Convert camera pixel coordinates (u,v) to sample-plane coordinates (x0,y0) in [m].
        """
        du = (u - self.u0) * self.pixel_size_cam / self.mag_total
        dv = (v - self.v0) * self.pixel_size_cam / self.mag_total
        # apply flips if the axes are inverted
        x0 = self.flip_x * du
        y0 = self.flip_y * dv
        return x0, y0


@dataclass
class MicroscopeSLMSystem:
    wavelength: float = 473e-9  # laser wavelength
    n_medium: float = 1.33  # water
    NA_obj: float = 1.0  # objective NA
    M_obj: float = 20.0  # objective magnification
    f_tube: float = 180e-3  # tube lens focal length
    f_fresnel: float = 150e-3  # tube lens focal length
    pupil_mag: float = 1

    @property
    def f_obj(self) -> float:
        """Objective focal length, from tube lens and magnification."""
        return self.f_tube / self.M_obj

    @property
    def pupil_magnification(self) -> float:
        """
        Pupil magnification from objective pupil to SLM.
        """
        return self.pupil_mag

    @property
    def pupil_radius_obj(self) -> float:
        """
        Objective pupil radius (meters) at the objective back aperture.
        """
        n = self.n_medium
        f = self.f_obj
        na_rel = self.NA_obj / n
        if na_rel >= 1.0:
            na_rel = 0.999999
        r_max = f * na_rel / np.sqrt(1.0 - na_rel ** 2)
        return r_max

    @property
    def pupil_radius_slm(self) -> float:
        """Pupil radius (meters) at the SLM plane."""
        return self.pupil_radius_obj * self.pupil_magnification

    @property
    def k(self) -> float:
        """Vacuum wave number."""
        return 2 * np.pi / self.wavelength


@dataclass
class SLMDevice:
    slm_pixel_pitch: float = 12.5e-6  # SLM pixel size
    slm_nx: int = 1024  # number of pixels in x
    slm_ny: int = 1272  # number of pixels in y
    correction_pattern: np.ndarray = None
    correction_value: int = 137

    def slm_coordinates(self):
        """
        Return SLM coordinate grids X, Y (meters), centered at (0,0).
        Shape: (slm_ny, slm_nx).
        """
        x = (np.arange(self.slm_nx) - self.slm_nx / 2 + 0.5) * self.slm_pixel_pitch
        y = (np.arange(self.slm_ny) - self.slm_ny / 2 + 0.5) * self.slm_pixel_pitch
        X, Y = np.meshgrid(x, y)
        return X, Y


def phase_to_uint(phase_0_2pi: np.ndarray, levels) -> np.ndarray:
    out = np.round((levels * phase_0_2pi / (2.0 * np.pi)))
    return out.astype(np.uint8)


def save_to_bmp(fn, data):
    img = Image.fromarray(data, mode='L')
    img.save(fn + r"_8bit.bmp", format='BMP')


class CGH:

    def __init__(self, logg=None):
        self.logg = logg or logger.setup_logging()
        self.system = MicroscopeSLMSystem(
            wavelength=473e-9,
            NA_obj=1.0,
            n_medium=1.33,
            M_obj=20.0,
            f_tube=180e-3,
            f_fresnel=150e-3
        )
        self.device = SLMDevice(
            slm_pixel_pitch=12.5e-6,
            slm_nx=1272,
            slm_ny=1024,
            correction_pattern=np.zeros((1024, 1272), dtype=np.uint8),
            correction_value=137
        )
        self.geom = ImagingGeometry(
            pixel_size_cam=6.5e-6,
            mag_total=20.0,
            flip_x=1,
            flip_y=1,
            u0 = 600,
            v0 = 395
        )
        self.mask = None
        self.spots_xy = None
        self.itn = 64
        self.phase_spots = None
        self.phase_total = None
        self.phase_slm = None

    def load_correction_pattern(self, file):
        correct_pattern = Image.open(file)
        self.device.correction_pattern = np.array(correct_pattern, dtype=np.uint8)

    def update_parameters(self, itn, mag, fl, cnt):
        self.itn = itn
        self.geom.mag_total = mag
        self.system.f_fresnel = fl
        self.geom.u0, self.geom.v0 = cnt

    def load_mask(self, fnd):
        img = Image.open(fnd)
        if img.mode != "1":
            img = img.convert("L")
        self.mask = np.asarray(img)

    def load_spots_picked(self, spots_picked):
        self.spots_xy = spots_picked

    def compute_cgh(self):
        spots_sample = []
        for (u, v) in self.spots_xy:
            x0, y0 = self.geom.pixels_to_sample(u, v)
            spots_sample.append((x0, y0, 0.0))
        phase_init = self.generate_cgh(spots_sample, include_defocus=False)
        sigma_spot = 0.1e-6
        target_amp = self.build_target_amp_from_spots(spots_sample, sigma=sigma_spot, amp_per_spot=1.0)
        self.phase_spots = self.gerchberg_saxton_with_target(target_amp, n_iters=128,
                                                             phase_init=phase_init, use_pupil_mask=True)
        phase_fresnel_lens = self.generate_fresnel_lens_phase()
        self.phase_total = (self.phase_spots + phase_fresnel_lens) % (2.0 * np.pi)
        self.phase_slm = self.device.correction_pattern + phase_to_uint(self.phase_total, self.device.correction_value)

    def save_cgh(self, fnd):
        save_to_bmp(fnd, self.phase_slm)

    def generate_cgh(self, spots_sample: List[Tuple[float, float, float]], weights: List[complex] = None,
                     include_defocus: bool = True):
        """
        Compute a phase-only CGH for multiple spots in the sample.

        Parameters
        ----------
        spots_sample : list of (x0, y0, z0)
            Target spot coordinates in sample space.
        weights : list of complex, optional
            Complex weights for each spot (default 1+0j).
        include_defocus : bool
            If True, add paraxial quadratic defocus term.

        Returns
        -------
        phase : ndarray (slm_ny, slm_nx)
            Phase hologram [rad], in [0, 2π).
        """
        X_slm, Y_slm = self.device.slm_coordinates()

        # Map SLM coordinates back to objective pupil
        M_pupil = self.system.pupil_magnification
        x_pupil = X_slm / M_pupil
        y_pupil = Y_slm / M_pupil
        r2_pupil = x_pupil ** 2 + y_pupil ** 2

        # Pupil aperture mask
        r_slm = np.sqrt(X_slm ** 2 + Y_slm ** 2)
        pupil_mask = (r_slm <= self.system.pupil_radius_slm).astype(np.float32)

        k = self.system.k
        f_obj = self.system.f_obj

        if weights is None:
            weights = [1.0] * len(spots_sample)

        field = np.zeros_like(X_slm, dtype=np.complex64)

        for (x0, y0, z0), w in zip(spots_sample, weights):
            phi = k * (x0 * x_pupil + y0 * y_pupil) / f_obj

            if include_defocus and np.abs(z0) > 0:
                phi += -k * z0 * r2_pupil / (2.0 * f_obj ** 2)

            field += w * np.exp(1j * phi)

        field *= pupil_mask
        phase = np.angle(field)
        phase = (phase + 2.0 * np.pi) % (2.0 * np.pi)
        return phase

    def sample_plane_coordinates_fft_grid(self):
        """
        Sample-plane coordinates (x_s, y_s) corresponding to the FFT grid

        Returns
        -------
        Xs, Ys : 2D arrays [m]
            Coordinates in the sample plane at nominal focus (z=0).
            Shape = (slm_ny, slm_nx)
        """
        ny, nx = self.device.slm_ny, self.device.slm_nx
        dx_slm = self.device.slm_pixel_pitch

        fx = np.fft.fftfreq(nx, d=dx_slm)
        fy = np.fft.fftfreq(ny, d=dx_slm)
        fx = np.fft.fftshift(fx)
        fy = np.fft.fftshift(fy)

        FX, FY = np.meshgrid(fx, fy)
        Xs = self.system.wavelength * self.system.f_obj * FX
        Ys = self.system.wavelength * self.system.f_obj * FY
        return Xs, Ys

    def build_target_amp_from_spots(self, spots_sample, sigma=None, amp_per_spot=1.0):
        """
        Build a target amplitude pattern in the sample plane
        (FFT domain of the SLM pupil) for a list of spots.

        Parameters
        ----------
        spots_sample : list of (x0, y0, z0) [m]
            Target positions in the sample (z0 is currently ignored here).
        sigma : float or None
            If None: each spot is a single pixel.
            If float: Gaussian radius in meters (in sample plane).
        amp_per_spot : float
            Amplitude per spot before normalization.

        Returns
        -------
        target_amp : 2D array, shape (slm_ny, slm_nx)
            Normalized amplitudes in [0,1].
        """
        ny, nx = self.device.slm_ny, self.device.slm_nx
        Xs, Ys = self.sample_plane_coordinates_fft_grid()

        target_amp = np.zeros((ny, nx), dtype=np.float32)

        for (x0, y0, z0) in spots_sample:
            if sigma is None:
                # find nearest pixel on the sample grid
                dist2 = (Xs - x0) ** 2 + (Ys - y0) ** 2
                iy, ix = np.unravel_index(np.argmin(dist2), dist2.shape)
                target_amp[iy, ix] += amp_per_spot
            else:
                # Gaussian blob around the desired position
                target_amp += amp_per_spot * np.exp(
                    -((Xs - x0) ** 2 + (Ys - y0) ** 2) / (2.0 * sigma ** 2)
                )

        max_val = target_amp.max()
        if max_val > 0:
            target_amp /= max_val
        return target_amp

    def gerchberg_saxton_with_target(self, target_amp, n_iters=50, phase_init=None, use_pupil_mask=True):
        """
        Gerchberg–Saxton phase retrieval

        Parameters
        ----------
        target_amp : 2D array (slm_ny, slm_nx)
            Desired amplitude pattern
        n_iters : int
            Number of GS iterations.
        phase_init : 2D array or None
            Optional initial phase
        use_pupil_mask : bool
            If True, enforce the objective pupil aperture on the SLM.

        Returns
        -------
        phase_slm : 2D array
            Final SLM phase [rad], wrapped to [0, 2π).
        """
        ny, nx = self.device.slm_ny, self.device.slm_nx
        assert target_amp.shape == (ny, nx), "target_amp must match SLM size"

        if use_pupil_mask:
            X_slm, Y_slm = self.device.slm_coordinates()
            r2 = X_slm ** 2 + Y_slm ** 2
            pupil_mask = (r2 <= self.system.pupil_radius_slm ** 2).astype(np.float32)
        else:
            pupil_mask = np.ones((ny, nx), dtype=np.float32)

        if phase_init is None:
            phase_slm = 2.0 * np.pi * np.random.rand(ny, nx)
        else:
            phase_slm = np.mod(phase_init, 2.0 * np.pi)

        field_slm = np.exp(1j * phase_slm) * pupil_mask

        for _ in range(n_iters):
            field_focal = np.fft.fft2(field_slm)
            field_focal = np.fft.fftshift(field_focal)

            phase_focal = np.angle(field_focal)
            field_focal = target_amp * np.exp(1j * phase_focal)

            field_focal = np.fft.ifftshift(field_focal)
            field_slm = np.fft.ifft2(field_focal)

            phase_slm = np.angle(field_slm)
            field_slm = np.exp(1j * phase_slm) * pupil_mask

        phase_slm = (phase_slm + 2.0 * np.pi) % (2.0 * np.pi)
        return phase_slm

    def generate_fresnel_lens_phase(self):
        """
        Generate a Fresnel lens phase pattern

        Returns
        -------
        phase : 2D np.ndarray
            Phase map in radians, wrapped to [0, 2π)
        """

        x = (np.arange(self.device.slm_nx) - self.device.slm_nx / 2 + 0.5) * self.device.slm_pixel_pitch
        y = (np.arange(self.device.slm_ny) - self.device.slm_ny / 2 + 0.5) * self.device.slm_pixel_pitch
        X, Y = np.meshgrid(x, y)

        k = 2.0 * np.pi / self.system.wavelength
        phi = -k * (X ** 2 + Y ** 2) / (2.0 * self.system.f_fresnel)
        phase = np.mod(phi, 2.0 * np.pi)
        return phase
