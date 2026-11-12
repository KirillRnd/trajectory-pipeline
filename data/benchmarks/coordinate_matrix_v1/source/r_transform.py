"""Local orbital charts and paired transport of vectors and costates."""
import numpy as np


def orbital_frame(state, kind='legacy'):
    """Return frame rows from a dimensionless [r,v] at any trajectory node."""
    state = np.asarray(state, dtype=float)
    if state.shape != (6,) or not np.isfinite(state).all():
        raise ValueError('A finite dimensionless [r,v] is required')
    r, v = state[:3], state[3:]
    normal = np.cross(r, v)
    radius, speed, momentum = map(np.linalg.norm, (r, v, normal))
    if radius == 0 or speed == 0 or momentum <= 1e-12 * radius * speed:
        raise ValueError('An orbital frame requires non-collinear position and velocity')
    if kind == 'legacy':
        frame = np.array([r, v, normal])
    elif kind == 'angular':
        # Isolate the angle between r and v from row scaling.
        frame = np.array([r / radius, v / speed, normal / momentum])
    elif kind == 'rtn':
        radial, perpendicular = r / radius, normal / momentum
        frame = np.array([radial, np.cross(perpendicular, radial), perpendicular])
    else:
        raise ValueError(f'Unknown orbital frame: {kind}')
    if np.linalg.cond(frame) > 1e12:
        raise ValueError('Orbital frame is ill-conditioned')
    return frame


def transport_matrix(reference, target, kind='legacy'):
    """Map reference costates to target costates, in one common set of units."""
    return np.linalg.solve(orbital_frame(target, kind), orbital_frame(reference, kind))


def transport_costates(costates, transform):
    """Map [p_r,p_v] or [p_r,p_v,p_m], with unchanged scalar p_m."""
    costates = np.asarray(costates, dtype=float)
    if costates.shape not in ((6,), (7,)):
        raise ValueError('Expected [p_r,p_v] or [p_r,p_v,p_m]')
    result = costates.copy()
    result[:6] = (costates[:6].reshape(2, 3) @ transform.T).ravel()
    return result


def transport_vector(vector, transform):
    """Transport the dual vector so its pairing with the costate is preserved."""
    return np.linalg.solve(transform.T, vector)


def costate_chart(frame, *, size=6, blocks=2):
    """Return A in p=A z, leaving scalars, velocity and switch variables unchanged.

    The independent spatial costate triples must come first. For a reduced
    free-departure shooting problem use blocks=1, since p_v(0)=0.
    """
    if blocks not in (1, 2) or size < 3 * blocks:
        raise ValueError('Invalid shooting layout for the costate chart')
    matrix = np.eye(size)
    if frame is not None:
        inverse = np.linalg.solve(frame, np.eye(3))
        for start in range(0, 3 * blocks, 3):
            matrix[start:start + 3, start:start + 3] = inverse
    return matrix
