from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib.chart import Chart
from flatlib import const

print('House system constants in flatlib:')
for k, v in vars(const).items():
    if 'HOUSES_' in k:
        print(f'{k}: {v}')

print('\nTrying house systems directly:')
date = Datetime('1990/01/01', '12:00', '-04:00')
pos = GeoPos(40.7128, -74.0060)

house_systems = [
    const.HOUSES_PLACIDUS,
    const.HOUSES_KOCH,
    const.HOUSES_REGIOMONTANUS,
    const.HOUSES_CAMPANUS,
    const.HOUSES_EQUAL,
    const.HOUSES_WHOLE_SIGN,
    const.HOUSES_PORPHYRIUS,
    const.HOUSES_MORINUS,
    const.HOUSES_ALCABITUS
]

for hsys in house_systems:
    try:
        chart = Chart(date, pos, hsys=hsys)
        print(f'House system {hsys} works!')
    except Exception as e:
        print(f'House system {hsys} failed: {str(e)}')