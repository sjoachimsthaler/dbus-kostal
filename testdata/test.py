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
print(meter_data['root']['Device']['Measurements']['Measurement'][0]['@Value'])

import json

with open('test.json', 'w') as file:
    json.dump(meter_data, file)