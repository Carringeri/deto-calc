import math

def kamlet_jacobs(rho: float, Q: float, N: float, M: float):
    phi = N * math.sqrt(M * Q)
    D = 1.01 * math.sqrt(phi) * (1 + 1.30 * rho)
    P = 15.58 * rho**2 * phi
    return D, P

def tnt_equivalent(mass_kg: float, Q: float, Q_tnt: float = 1090.0) -> float:
    return mass_kg * Q / Q_tnt