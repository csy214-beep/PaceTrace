import math
import random


def random_point(lat: str, lng: str, radius: float = 100):
    angle = random.random() * 2 * math.pi
    r = math.sqrt(random.random()) * radius
    dx = r * math.cos(angle) / (111320 * math.cos(math.radians(float(lat))))
    dy = r * math.sin(angle) / 111320
    return str(float(lat) + dy), str(float(lng) + dx)


def route_distance(coords):
    d = 0
    for i in range(1, len(coords)):
        a, b = coords[i - 1], coords[i]
        dx = (b[1] - a[1]) * 111320 * math.cos(math.radians((a[0] + b[0]) / 2))
        dy = (b[0] - a[0]) * 111320
        d += math.sqrt(dx * dx + dy * dy)
    return int(d)


def build_track(coords, target_dist):
    full_d = route_distance(coords)
    if full_d <= 0:
        return coords
    n = len(coords)
    start = random.randint(0, n - 1)
    result = []
    i = start
    while route_distance(result) < target_dist:
        result.append(coords[i])
        i = (i + 1) % n
    return result
