#!/usr/bin/env python3
import datetime
import json
import os
import sqlite3
import argparse
from prettytable import from_db_cursor

# todo: update this after testing is complete
PATH = '/Users/emma/Github/data'
DBPATH = '/Users/emma/Github/de-inventory-tracker'

# PATH = '/home/emma/de-inventory-tracker/'
# DBPATH = '/home/emma/de-inventory-tracker/data/'

def load_json(input_file):
    """
    todo: write docstring
    """
    with open(input_file, encoding='utf-8') as f:
        loaded = json.load(f)

    return loaded

def test_compare_dictionaries():
    """
    Test compare_dictionaries()
    """
    old = {'dec0001': {'cpu.PO.Manufacturer': 'AMD', 'mac.mgmt': '02:03:eb:05:32:00', 'fru.Name': 'Node0'},
           'dec0002': {},
           'dec0003': {'cpu.PO.Manufacturer': 'AMD', 'mac.mgmt': '02:03:eb:05:32:00'},
           'dec0004': {'cpu.PO.Manufacturer': 'AMD'}, 
           'deg0001 ': {'gpu.model': 'A100 PCIe 40GB', 'gpu.vendor': 'NVIDA'},
           'deg0082': {'gpu.vendor': 'NVIDIA'}} # only in old but not in new

    new = {'dec0001': {'cpu.PO.Manufacturer': 'AMD', 'mac.mgmt': '02:03:eb:05:32:00'}, # missing key
           'dec0002': {'chassis.Type': 'Rack Mount Chassis'}, # new key
           'dec0003': {'cpu.PO.Manufacturer': 'AMD', 'mac.mgmt': '09:09:eb:09:99:99'}, # changed values
           'dec0004': {'cpu.PO.Manufacturer': 'AMD'}, # same
           'deg0001': {}, # keys disappeared
           'dec2450': {'cpu.Proc 2.Core Count': '32'}} # not in old but in new

    expected = {'dec0001': {('fru.Name', 'Node0')},
                'dec0002': {('chassis.Type', 'Rack Mount Chassis')},
                'dec0003': {('mac.mgmt', '02:03:eb:05:32:00'), ('mac.mgmt', '09:09:eb:09:99:99')},
                'deg0001': {('gpu.model', 'A100 PCIe 40GB'), ('gpu.vendor', 'NVIDIA')},
                'deg0082': {('gpu.vendor', 'NVIDIA')},
                'dec2450': {('cpu.Proc 2.Core Count', '32')}}

    actual = compare_dictionaries(old, new)
    assert actual == expected


def compare_items(dict1, dict2):
    set1 = set(dict1.items())
    set2 = set(dict2.items())
    # symmetric set difference
    diffs = set2 ^ set1

    return diffs


def compare_dictionaries(old_inventory, new_inventory): # pylint: disable=redefined-outer-name
    """
    todo: write docstring
    """
    all_nodes = sorted(set(list(old_inventory.keys()) + list(new_inventory.keys())))
    diffs = {}
    for node in all_nodes:
        present_in_old = node in old_inventory
        present_in_new = node in new_inventory
        if present_in_old and present_in_new:
            # check for diffs are normal
            diff = compare_items(dict1=old_inventory[node], dict2=new_inventory[node])
            if diff:
                # only add a record if there is a change
                diffs[node] = diff
        elif present_in_new:
            diffs[node] = compare_items(dict1={}, dict2=new_inventory[node])
        elif present_in_old:
            diffs[node] = compare_items(dict1=old_inventory[node], dict2={})
    return diffs

def extract_serial_numbers(diffs):
	"""
	Extra all serial number fields from a dictionary of differences.
	:param diffs: A dictionary of differences
	"""
	serials = []
	for node, differences in diffs.items():
		for item in differences:
			if 'Serial Number' in item[0]:
				serials.append((node, item[0], item[1]))

	return serials

def builddb(db: str = 'inventory.sqlite'):
    """
    todo
    """
    con = sqlite3.connect(DBPATH + '/' + db)
    with con:
        cur = con.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS changes(
                       id INTEGER PRIMARY KEY,
                       timestamp TEXT NOT NULL,
                       node TEXT NOT NULL,
                       serial_name TEXT NOT NULL,
                       serial_number TEXT NOT NULL)''')
        con.commit()

def write_to_db(serials, timestamp): # pylint: disable=redefined-outer-name
    """
    """
    with sqlite3.connect("inventory.sqlite") as con:
        cur = con.cursor()
        for item in serials:
            data = ('INSERT INTO changes (timestamp, node, serial_name, serial_number) VALUES '
                    f'("{timestamp}", "{item[0]}", "{item[1]}", "{item[2]}")')
            print(data)
            cur.execute(data)
        con.commit()
 
def view_changes() -> None:
    """
    shows changes inserted to the table
    """
    con = sqlite3.connect(r"/Users/emma/Github/de-inventory-tracker/inventory.sqlite")
    with con:
        cur = con.cursor()
        cur.execute("SELECT id, timestamp, node, serial_name, serial_number FROM changes")
        data = from_db_cursor(cur)
        print(data)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='inventory_tracker.py')
    subparser = parser.add_subparsers(title='subcommand', dest='subcommand')
    view_parser = subparser.add_parser('view', help="View the changes")
    args = parser.parse_args()
    builddb()

    if args.subcommand == 'view':
        view_changes()
    else:
        timestamp = datetime.datetime.now()
        files = [obj for obj in os.listdir(PATH) if obj.startswith('de')]
        assert len(files) >= 2
        new_file = files[-1]
        old_file = files[-2]
        old_inventory = load_json(PATH + '/' + old_file)
        new_inventory = load_json(PATH + '/' + new_file)
        differences = compare_dictionaries(old_inventory=old_inventory, new_inventory=new_inventory)
        serial_differences = extract_serial_numbers(diffs=differences)

        # write results to DB
        # builddb()
        write_to_db(serials=serial_differences, timestamp=timestamp)
        #print(f'Inserted {len(differences)} records')