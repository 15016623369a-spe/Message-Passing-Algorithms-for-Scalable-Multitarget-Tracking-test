"""Python translation of Florian Meyer's particle BP multitarget-tracking example.

Based on the experimental code associated with:
Meyer F, Braca P, Willett P, Hlawatsch F. A Scalable Algorithm for Tracking an Unknown Number of Targets Using Multiple Sensors[J]. IEEE Transactions on Signal Processing, 2017, 65(13): 3478–3493. DOI: 10.1109/TSP.2017.2688966.

Original MATLAB author: Florian Meyer, 2017, 2020.
Source: https://github.com/meyer-ucsd/MTT-PIEEE-18
Source commit: d2e02df90d85aca5ad1120d80f8ba66946e903ca
Unofficial Python port; OSPA and diagnostics are added evaluation features.
NumPy and MATLAB random streams differ; this is not bitwise MATLAB parity.
See README.md and THIRD_PARTY_NOTICES.md for attribution and scope.
"""
from dataclasses import dataclass, asdict
from time import perf_counter
import warnings
import numpy as np


@dataclass
class Parameters:
    num_steps: int = 200
    num_particles: int = 10_000
    num_sensors: int = 2
    driving_noise_variance: float = 0.010
    survival_probability: float = 0.999
    measurement_variance_range: float = 25.0**2
    measurement_variance_bearing: float = 0.5**2
    detection_probability: float = 0.9
    measurement_range: float = 6000.0
    mean_clutter: float = 5.0
    detection_threshold: float = 0.5
    threshold_pruning: float = 1e-4
    minimum_track_length: int = 1
    unknown_number: float = 0.01
    bp_check_every: int = 20
    bp_tolerance: float = 1e-5
    bp_max_iterations: int = 100_000

    def __post_init__(self):
        if self.num_steps < 1 or self.num_particles < 1 or self.num_sensors < 1:
            raise ValueError('Steps, particles and sensors must be positive.')
        if not 0 <= self.detection_probability < 1:
            raise ValueError('This original example requires 0 <= P_D < 1.')
        if not 0 <= self.survival_probability <= 1 or self.mean_clutter <= 0:
            raise ValueError('Invalid survival probability or clutter intensity.')
        if self.bp_check_every < 1 or self.bp_max_iterations < 1:
            raise ValueError('BP iteration settings must be positive.')
        self.surveillance_region = np.array([[-3000., -3000.], [3000., 3000.]])
        self.prior_velocity_covariance = np.diag([100., 100.])
        self.length_steps = np.ones(self.num_steps)
        self.clutter_distribution = 1 / (360 * self.measurement_range)
        self.sensor_positions = get_sensor_positions(self.num_sensors, 5000.)
        self.target_start_states = get_start_states(5, 1000., 10.)
        self.target_appearance_from_to = np.array([[5, 10, 15, 20, 25],
                                                  [155, 160, 165, 170, 175]])


def transition_matrices(scan_time):
    A = np.eye(4)
    A[0, 2] = A[1, 3] = scan_time
    W = np.array([[0.5*scan_time**2, 0.], [0., 0.5*scan_time**2],
                  [scan_time, 0.], [0., scan_time]])
    return A, W


def get_sensor_positions(num_sensors, radius):
    angles = np.arange(num_sensors) * 2*np.pi/num_sensors
    return radius * np.vstack([np.sin(angles), np.cos(angles)])


def get_start_states(num_targets, radius, speed):
    if num_targets == 1:
        return np.array([[0.], [0.], [speed], [0.]])
    angles = np.arange(num_targets) * 2*np.pi/num_targets
    return np.vstack([radius*np.sin(angles), radius*np.cos(angles),
                      -speed*np.sin(angles), -speed*np.cos(angles)])


def wrap_to_180(angle):
    angle = np.asarray(angle)
    wrapped = (angle + 180.) % 360. - 180.
    return np.where((wrapped == -180.) & (angle > 0), 180., wrapped)


def generate_true_tracks(p, rng):
    num_targets = p.target_start_states.shape[1]
    tracks = np.full((4, num_targets, p.num_steps), np.nan)
    for target in range(num_targets):
        state = p.target_start_states[:, target].copy()
        # MATLAB loop is 2:numSteps; step 1 is intentionally left absent.
        for k in range(1, p.num_steps):
            A, W = transition_matrices(p.length_steps[k])
            state = A @ state + W @ (np.sqrt(p.driving_noise_variance)*rng.standard_normal(2))
            start, stop = p.target_appearance_from_to[:, target]
            if start <= k + 1 <= stop:
                tracks[:, target, k] = state
    return tracks


def generate_true_measurements(target_trajectory, p, rng):
    num_targets = target_trajectory.shape[1]
    measurements = np.empty((2, num_targets, p.num_sensors))
    for sensor in range(p.num_sensors):
        delta = target_trajectory[:2] - p.sensor_positions[:, sensor, None]
        measurements[0, :, sensor] = np.hypot(*delta) + np.sqrt(p.measurement_variance_range)*rng.standard_normal(num_targets)
        # Original bearing: atan2d(delta_x, delta_y), measured from +y.
        measurements[1, :, sensor] = np.rad2deg(np.arctan2(delta[0], delta[1])) + np.sqrt(p.measurement_variance_bearing)*rng.standard_normal(num_targets)
    return measurements


def generate_cluttered_measurements(track_measurements, p, rng):
    all_measurements = []
    num_targets = track_measurements.shape[1]
    for sensor in range(p.num_sensors):
        exists = np.isfinite(track_measurements[0, :, sensor])
        detected = rng.random(num_targets) < p.detection_probability
        true_detections = track_measurements[:, exists & detected, sensor]
        n_clutter = rng.poisson(p.mean_clutter)
        clutter = np.vstack([p.measurement_range*rng.random(n_clutter),
                             360*rng.random(n_clutter)-180])
        values = np.concatenate([clutter, true_detections], axis=1)
        all_measurements.append(values[:, rng.permutation(values.shape[1])])
    return all_measurements


def perform_prediction(particles, existences, scan_time, p, rng):
    A, W = transition_matrices(scan_time)
    predicted = particles.copy()
    for target in range(particles.shape[2]):
        noise = rng.standard_normal((2, particles.shape[1]))
        predicted[:, :, target] = A @ particles[:, :, target] + W @ (np.sqrt(p.driving_noise_variance)*noise)
    return predicted, p.survival_probability*existences


def calculate_constants_uniform(sensor_position, measurements, particles, p):
    delta = particles - sensor_position[:, None]
    predicted_range = np.hypot(*delta)
    predicted_bearing = np.rad2deg(np.arctan2(delta[0], delta[1]))
    dr = measurements[0, :, None] - predicted_range
    # Deliberately no wrap here: matches calculateConstantsUniform in source.
    db = measurements[1, :, None] - predicted_bearing
    norm = 1/(2*np.pi*np.sqrt(p.measurement_variance_bearing*p.measurement_variance_range))
    likelihood = norm*np.exp(-0.5*(dr**2/p.measurement_variance_range + db**2/p.measurement_variance_bearing))
    area = np.prod(p.surveillance_region[1] - p.surveillance_region[0])
    return area*likelihood.mean(axis=1)


def sample_from_likelihood(measurement, sensor, p, rng):
    ranges = measurement[0] + np.sqrt(p.measurement_variance_range)*rng.standard_normal(p.num_particles)
    bearings = np.deg2rad(measurement[1] + np.sqrt(p.measurement_variance_bearing)*rng.standard_normal(p.num_particles))
    samples = np.empty((4, p.num_particles))
    samples[0] = p.sensor_positions[0, sensor] + ranges*np.sin(bearings)
    samples[1] = p.sensor_positions[1, sensor] + ranges*np.cos(bearings)
    # Original covariance is diagonal; Cholesky equals its principal square root.
    samples[2:] = np.linalg.cholesky(p.prior_velocity_covariance) @ rng.standard_normal((2, p.num_particles))
    return samples


def introduce_new_pts(measurements, sensor, step, unknown_particles, p, rng):
    m = measurements.shape[1]
    particles = np.empty((4, p.num_particles, m))
    labels = np.empty((3, m), dtype=int)
    area = np.prod(p.surveillance_region[1] - p.surveillance_region[0])
    unknown_intensity = p.unknown_number/area*(1-p.detection_probability)**sensor
    constants = calculate_constants_uniform(p.sensor_positions[:, sensor], measurements, unknown_particles, p)
    xi = 1 + constants*unknown_intensity*p.detection_probability/(p.mean_clutter*p.clutter_distribution)
    for j in range(m):
        particles[:, :, j] = sample_from_likelihood(measurements[:, j], sensor, p, rng)
        labels[:, j] = [step, sensor+1, j+1]  # Keep MATLAB's 1-based labels.
    return particles, labels, xi-1, xi


def evaluate_measurements(alphas, existence, measurements, p, sensor):
    m, t, n = measurements.shape[1], alphas.shape[2], p.num_particles
    v = np.zeros((m+1, t, n))
    beta = np.zeros((m+1, t))
    if t:
        v[0] = 1-p.detection_probability
        normalizer = p.detection_probability/(p.mean_clutter*p.clutter_distribution*2*np.pi*np.sqrt(p.measurement_variance_range*p.measurement_variance_bearing))
        for target in range(t):
            delta = alphas[:2, :, target] - p.sensor_positions[:, sensor, None]
            ranges = np.hypot(*delta)
            bearings = np.rad2deg(np.arctan2(delta[0], delta[1]))
            dr = measurements[0, :, None] - ranges
            db = wrap_to_180(measurements[1, :, None] - bearings)
            v[1:, target] = normalizer*np.exp(-0.5*(dr**2/p.measurement_variance_range + db**2/p.measurement_variance_bearing))
        beta = existence[None, :]*v.mean(axis=2)
        beta[0] += 1-existence
    return beta, v


def perform_data_association_bp(beta, xi, check_every=20, tolerance=1e-5, max_iterations=100_000):
    m, t = beta.shape[0]-1, beta.shape[1]
    kappas = np.ones((m, t))
    if not m or not t:
        return kappas, np.ones(m), {'iterations': 0, 'converged': True, 'residual': 0.}
    tiny = np.finfo(float).tiny
    residual, converged = np.inf, False
    for iteration in range(1, max_iterations+1):
        old = kappas
        product = kappas*beta[1:]
        denominator = beta[0]+product.sum(axis=0)-product
        messages = beta[1:]/np.maximum(denominator, tiny)
        denominator = xi[:, None]+messages.sum(axis=1, keepdims=True)-messages
        kappas = 1/np.maximum(denominator, tiny)
        if iteration % check_every == 0 or iteration == max_iterations:
            residual = float(np.max(np.abs(np.log(kappas)-np.log(old))))
            if residual < tolerance:
                converged = True
                break
    iotas = 1/(1+messages.sum(axis=1))
    if not converged:
        warnings.warn(f'BP did not converge in {iteration} iterations (residual={residual:.3g}).', RuntimeWarning)
    return kappas, iotas, {'iterations': iteration, 'converged': converged, 'residual': residual}


def resample_systematic(weights, rng):
    weights = np.asarray(weights, dtype=float)
    if weights.ndim != 1 or not np.all(np.isfinite(weights)) or np.any(weights < 0) or weights.sum() <= 0:
        raise ValueError('Resampling weights must be finite, nonnegative and have positive sum.')
    n = weights.size
    cumulative = np.cumsum(weights/weights.sum())
    cumulative[-1] = 1.0
    grid = np.arange(n)/n + rng.random()/n
    return np.searchsorted(cumulative, grid, side='right')


def update_pts(kappas, iotas, particles, new_particles, existence, new_existence, labels, new_labels, v, rng):
    updated, probabilities = particles.copy(), existence.copy()
    ess = []
    for target in range(particles.shape[2]):
        weights = v[0, target] + np.sum(kappas[:, target, None]*v[1:, target], axis=0)
        total = weights.sum()
        alive = existence[target]*total/particles.shape[1]
        probabilities[target] = alive/(alive+1-existence[target])
        if total > 0:
            normalized = weights/total
            ess.append(float(1/np.sum(normalized**2)))
            updated[:, :, target] = particles[:, resample_systematic(normalized, rng), target]
    new_probability = iotas*new_existence
    new_probability = new_probability/(new_probability+1)
    return (np.concatenate([updated, new_particles], axis=2),
            np.concatenate([probabilities, new_probability]),
            np.concatenate([labels, new_labels], axis=1), ess)


def tracker_bp(measurements, particles, existence, labels, unknown_particles, step, p, rng):
    particles, existence = perform_prediction(particles, existence, p.length_steps[step-1], p, rng)
    diagnostics = []
    for sensor in range(p.num_sensors):
        values = measurements[sensor]
        new, new_labels, new_existence, xi = introduce_new_pts(values, sensor, step, unknown_particles, p, rng)
        beta, v = evaluate_measurements(particles, existence, values, p, sensor)
        kappas, iotas, diag = perform_data_association_bp(beta, xi, p.bp_check_every, p.bp_tolerance, p.bp_max_iterations)
        particles, existence, labels, ess = update_pts(kappas, iotas, particles, new, existence, new_existence, labels, new_labels, v, rng)
        keep = existence >= p.threshold_pruning
        particles, existence, labels = particles[:, :, keep], existence[keep], labels[:, keep]
        if not np.all(np.isfinite(particles)) or not np.all(np.isfinite(existence)):
            raise FloatingPointError('Nonfinite particle states or existence probabilities.')
        if np.any((existence < 0) | (existence > 1)):
            raise FloatingPointError('Existence probability outside [0, 1].')
        diag.update(sensor=sensor+1, measurement_count=values.shape[1],
                    potential_targets=existence.size, mean_ess=float(np.mean(ess)) if ess else np.nan)
        diagnostics.append(diag)
    detected = existence > p.detection_threshold
    estimates = {'state': particles[:, :, detected].mean(axis=1), 'label': labels[:, detected].copy()}
    return estimates, existence.sum(), particles, existence, labels, diagnostics


def track_formation(estimates, minimum_track_length=1):
    label_set = sorted({tuple(label) for item in estimates for label in item['label'].T})
    lookup = {label: j for j, label in enumerate(label_set)}
    tracks = np.full((4, len(label_set), len(estimates)), np.nan)
    for k, item in enumerate(estimates):
        for j, label in enumerate(item['label'].T):
            tracks[:, lookup[tuple(label)], k] = item['state'][:, j]
    keep = np.isfinite(tracks[0]).sum(axis=1) >= minimum_track_length
    return tracks[:, keep], np.asarray(label_set, dtype=int).reshape(-1, 3)[keep]


def run_experiment(p=None, seed=1, progress_every=25):
    p = Parameters() if p is None else p
    rng = np.random.default_rng(seed)
    start = perf_counter()
    truth = generate_true_tracks(p, rng)
    # Fixed uniform unknown-target particles, as in main.m.
    unknown = p.surveillance_region[0, :, None] + (p.surveillance_region[1]-p.surveillance_region[0])[:, None]*rng.random((2, p.num_particles))
    particles = np.empty((4, p.num_particles, 0))
    existence, labels = np.empty(0), np.empty((3, 0), dtype=int)
    estimates, measurements, diagnostics = [], [], []
    cardinality = np.zeros(p.num_steps)
    step_times = np.zeros(p.num_steps)
    for k in range(p.num_steps):
        step_start = perf_counter()
        values = generate_cluttered_measurements(generate_true_measurements(truth[:, :, k], p, rng), p, rng)
        estimate, cardinality[k], particles, existence, labels, diag = tracker_bp(values, particles, existence, labels, unknown, k+1, p, rng)
        estimates.append(estimate)
        measurements.append(values)
        diagnostics.append(diag)
        step_times[k] = perf_counter()-step_start
        if progress_every and ((k+1) % progress_every == 0 or k+1 == p.num_steps):
            print(f'{k+1:3d}/{p.num_steps} | E[N]={cardinality[k]:.2f} | detected={estimate["state"].shape[1]} | elapsed={perf_counter()-start:.1f}s', flush=True)
    tracks, track_labels = track_formation(estimates, p.minimum_track_length)
    return {'parameters': p, 'seed': seed, 'truth': truth, 'tracks': tracks,
            'track_labels': track_labels, 'estimates': estimates, 'measurements': measurements,
            'cardinality': cardinality, 'diagnostics': diagnostics, 'step_times': step_times,
            'runtime_seconds': perf_counter()-start}


def ospa_distance(truth_xy, estimated_xy, cutoff=200., order=2):
    """Supplementary position-only OSPA; not supplied by original MATLAB demo."""
    from scipy.optimize import linear_sum_assignment
    m, n = truth_xy.shape[1], estimated_xy.shape[1]
    if max(m, n) == 0:
        return 0.
    if min(m, n) == 0:
        return float(cutoff)
    cost = np.minimum(np.linalg.norm(truth_xy[:, :, None]-estimated_xy[:, None, :], axis=0), cutoff)**order
    rows, columns = linear_sum_assignment(cost)
    return float(((cost[rows, columns].sum()+abs(m-n)*cutoff**order)/max(m, n))**(1/order))


def result_table(result):
    import pandas as pd
    p = result['parameters']
    true_count = np.isfinite(result['truth'][0]).sum(axis=0)
    detected = np.array([item['state'].shape[1] for item in result['estimates']])
    ospa = []
    for k, item in enumerate(result['estimates']):
        present = np.isfinite(result['truth'][0, :, k])
        ospa.append(ospa_distance(result['truth'][:2, present, k], item['state'][:2]))
    return pd.DataFrame({'step': np.arange(1, p.num_steps+1), 'true_count': true_count,
                         'expected_count': result['cardinality'], 'detected_count': detected,
                         'ospa_position_m': ospa, 'runtime_seconds': result['step_times'],
                         'max_bp_iterations': [max(d['iterations'] for d in step) for step in result['diagnostics']],
                         'bp_converged': [all(d['converged'] for d in step) for step in result['diagnostics']]})
