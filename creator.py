from datetime import datetime
from geopy import Nominatim
from astral.geocoder import database, lookup
from pytz import timezone, utc
import matplotlib.pyplot as plt
from skyfield.api import Star, load, wgs84
from skyfield.data import hipparcos
from skyfield.projections import build_stereographic_projection
import numpy as np

# ----------------------------
# 1. Load ephemeris and star catalog
# ----------------------------
eph = load('de421.bsp')
with load.open(hipparcos.URL) as f:
    stars = hipparcos.load_dataframe(f)

# ----------------------------
# 2. Input location and time
# ----------------------------
location_name = 'London'  # Must match Astral database
time_str = '20-08-2025 01:00'  # DD-MM-YYYY HH:MM

# Geocode location
locator = Nominatim(user_agent='myGeocoder')
loc = locator.geocode(location_name)
lat, lon = loc.latitude, loc.longitude

# ----------------------------
# 3. Timezone using Astral
# ----------------------------
city = lookup(location_name, database())
tz = timezone(city.timezone)

# Parse datetime and localize
dateTime = datetime.strptime(time_str, '%d-%m-%Y %H:%M')
localDateTime = tz.localize(dateTime)
utcDateTime = localDateTime.astimezone(utc)

# ----------------------------
# 4. Skyfield observer and time
# ----------------------------
timescale = load.timescale()
t = timescale.from_datetime(utcDateTime)

# Observer at location
observer = wgs84.latlon(latitude_degrees=lat, longitude_degrees=lon)
topos_at_time = observer.at(t)

# RA/Dec of zenith
ra, dec, distance = topos_at_time.radec()

# Create a Star at zenith
zenith_star = Star(ra_hours=ra.hours, dec_degrees=dec.degrees)

# Observe from Earth to get Geocentric position
center = load('de421.bsp')['earth'].at(t).observe(zenith_star)

# Build stereographic projection
projection = build_stereographic_projection(center)

# ----------------------------
# 5. Filter stars by magnitude
# ----------------------------
limitMag = 6  # visible stars
stars = stars[stars.magnitude <= limitMag]

# ----------------------------
# 6. Project stars
# ----------------------------
x_list = []
y_list = []

for index, row in stars.iterrows():
    # Convert RA from degrees to hours
    star = Star(ra_hours=row['ra_degrees'] / 15.0, dec_degrees=row['dec_degrees'])
    pos = load('de421.bsp')['earth'].at(t).observe(star)
    x, y = projection(pos)
    x_list.append(x)
    y_list.append(y)

stars['x'] = x_list
stars['y'] = y_list

# ----------------------------
# 7. Plot stars
# ----------------------------
chartSize = 10
starSizeMax = 100

# Marker size scaling
markerSize = starSizeMax * 10 ** (stars['magnitude'] / -2.5)

# Create figure
fig, ax = plt.subplots(figsize=(chartSize, chartSize))
# Background circle (sky)
border = plt.Circle((0, 0), 1, color='navy', fill=True)
ax.add_patch(border)

# Plot stars
ax.scatter(
    stars['x'],
    stars['y'],
    s=markerSize,
    color='white',
    marker='.',
    linewidths=0,
    zorder=2
)

# Set plot limits and remove axes
ax.set_xlim(-1, 1)
ax.set_ylim(-1, 1)
plt.axis('off')
plt.show()
