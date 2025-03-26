from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib import const

# Create chart
date = Datetime('1990/01/01', '12:00', '-04:00')
pos = GeoPos(40.7128, -74.0060)
chart = Chart(date, pos)

# Get sun
sun = chart.getObject('Sun')
print("Sun data:", sun.id, sun.sign, sun.lon)

# Try getting the house for a planet using the correct method
print("\nUsing getObjectHouse method to find house for planets:")
for planet_id in const.LIST_OBJECTS:
    try:
        obj = chart.getObject(planet_id)
        house = chart.houses.getObjectHouse(obj)
        print(f"{obj.id} is in house {house.id}, sign {house.sign}")
    except Exception as e:
        print(f"Error with {planet_id}: {str(e)}")

# Show house names
print("\nGetting all house objects:")
for house_id in const.LIST_HOUSES:
    try:
        house = chart.getHouse(house_id)
        print(f"House {house_id}: sign {house.sign}, longitude {house.lon}")
    except Exception as e:
        print(f"Error with house {house_id}: {str(e)}")

# Print all available constants related to houses
print("\nHouse-related constants:")
for name in dir(const):
    if "HOUSE" in name:
        value = getattr(const, name)
        print(f"{name}: {value}")