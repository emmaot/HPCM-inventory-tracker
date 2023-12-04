#!/usr/bin/bash
/opt/clmgr/bin/cm inventory -e -j > '/home/emma/HPCM-inventory-tracker/data/'$(date "+de-%Y%m%d%H%M")
