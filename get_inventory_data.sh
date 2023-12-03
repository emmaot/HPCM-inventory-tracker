#!/usr/bin/bash
/opt/clmgr/bin/cm inventory -e -j > '/home/emma/de-inventory-tracker/data/'$(date "+de-%Y%m%d%H%M")
