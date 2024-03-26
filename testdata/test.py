with open('measurements.xml', 'r') as file:
    meter_r = file.read()


import xmltodict
test = str(meter_r)
print(meter_r)

print(test)

meter_data = xmltodict.parse(test)
print(meter_data)

print (meter_data['root']['Device']['@Serial'])

voltage = meter_data['root']['Device']['Measurements']['Measurement'][0]['@Value']
parsed_voltage = float(voltage) 
print(parsed_voltage)

x = meter_data['root']['Device']['Measurements']['Measurement'][1]
current = 0
if "@Value" in x:
    current = x['@Value']
    
print(current)

import json

with open('test.json', 'w') as file:
    json.dump(meter_data, file)


with open('yields.json', 'r') as file:
    meter_r = file.read()
    historic_data = json.loads(meter_r)
    print(historic_data)

    energy = 0
      # sum up all Wh values from yields.json datasets in produced 
    for x in historic_data['TotalCurves']['Datasets'][0]['Data']:
        energy += x['Data']

    print(energy)