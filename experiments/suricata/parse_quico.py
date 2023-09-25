
import json
import csv
import argparse

EVE_FILE = "./eve.json"
CSV_FILE = "./parsed.csv"

EVE_STRUCTURE = {
    "uptime": "key",
    "capture": {
      "packets": "avg",
      "dpdk" : {
          "ierrors" : "avg"
      }
    },
    "decoder": {
      "pkts": "avg",
      "bytes": "avg",
    },
    "detect": {
      "alert": "avg",
    }
}

class EveParser:

    def __init__(self):
        pass


    def parse_stat(self, d):
        data_key = None
        data_value = dict()
        for key, role in EVE_STRUCTURE.items():
            if role == 'key':
                data_key = str(d[key])
            elif isinstance(role, dict):
                for subkey, subrole in role.items():
                    if subkey in d[key]:
                        data_value['%s.%s' % (key, subkey)] = d[key][subkey]
        return data_key, data_value

    def parse(self, eve_path):
        data = dict()
        with open(eve_path, 'r') as f:
            for line in f:
                if 'stats' in line:
                    ev = json.loads(line)
                    if ev['event_type'] == 'stats':
                        key, val = self.parse_stat(ev['stats'])
                        data[key] = val
        return data

    def parse_to_csv(self, json_string, output_csv_file):
        # Parse the JSON string into a Python data structure (dictionary)
        data = json.loads(json_string)


    # Open the CSV file for writing
        with open(output_csv_file, 'w', newline='') as csv_file:
            # Create a CSV writer
            csv_writer = csv.writer(csv_file)

        # Write the header row (column names)
            header = ["Uptime", "Capture Packets", "Capture DPDK iMissed", "Capture DPDK No MBUFs", "Capture DPDK iErrors", "Decoder PKTS", "Decoder Bytes", "Detect Alert"]
            csv_writer.writerow(header)

        # Iterate through the JSON data and write each row to the CSV file
            for key, values in data.items():
                row = [
                    key,
                    values["capture.packets"],
                    values["capture.dpdk"]["imissed"],
                    values["capture.dpdk"]["no_mbufs"],
                    values["capture.dpdk"]["ierrors"],
                    values["decoder.pkts"],
                    values["decoder.bytes"],
#                     values["decoder.alert"]
                ]
                csv_writer.writerow(row)

        print(f"JSON data has been written to {output_csv_file}")
    

    def parse_to_csv2(self, data, output_csv_file):

        #lter out non-dictionary elements (e.g., integers)

        header = data.keys()

        with open(output_csv_file, 'w', newline='') as csv_file:
            csv_writer = csv.DictWriter(csv_file, fieldnames=header)

            # Write the header
            csv_writer.writeheader()

            # Write the data
            try:
                csv_writer.writerows(data)
            except:
                pass



def main():


    # Create an ArgumentParser object
    parser = argparse.ArgumentParser(description='A simple Python script with command-line arguments.')

    # Add arguments
    parser.add_argument('--input_file', '-i', type=str, default=EVE_FILE, help='Input file path')
    parser.add_argument('--output', '-o', type=str, default=CSV_FILE, help='Output file path (default: output.txt)')

    # Parse the command-line arguments
    args = parser.parse_args()

    # Access and use the parsed arguments
    input_file = args.input_file
    output_file = args.output



    parser = EveParser()
    data = parser.parse(input_file)
    str_data = json.dumps(data, indent=4)

    parser.parse_to_csv(str_data, output_file)







if __name__ == "__main__":
    main()
