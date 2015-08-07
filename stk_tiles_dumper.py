#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright 2014 - Guillaume Beraudo
# License http://www.apache.org/licenses/LICENSE-2.0

import os
import sqlite3 as lite
import sys, getopt, errno
import json

con = None

def mkdir_p(path, mode):
    try:
        os.makedirs(path, mode)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else: raise

def test(con):
    cur = con.cursor()    
    cur.execute('SELECT SQLITE_VERSION()')
    data = cur.fetchone()
    print "SQLite version: %s" % data                
    

def dumpall(con, outputdir):
    cur = con.cursor()    
    cur.execute("select zoom_level, tile_row, tile_column, tile_data from tiles order by zoom_level,tile_column,tile_row")

    while True:
        row = cur.fetchone()
        if row == None:
            break
        zoom_level = row[0]
        tile_row = row[1]
        tile_column = row[2]
        tile_data = row[3]    
        print row[0], row[1], row[2]
        path = os.path.join(outputdir, str(zoom_level), str(tile_column))
        mkdir_p(path, 0755)
        tileFile = open (os.path.join(path, str(tile_row) + ".terrain"), "wb")
        dataByteArray = bytearray(tile_data)
        tileFile.write(dataByteArray)

    cur.execute("select zoom_level, start_row, start_column, end_row, end_column from availability order by zoom_level")
    available = []
    curzoom = 0
    curzoom_data = []
    while True:
        row = cur.fetchone()
        if row == None:
            if curzoom_data:
               available.append(curzoom_data)
            break
        zoom_level = row[0]
        start_row = row[1]
        start_column = row[2]
        end_row = row[3]
        end_column = row[4]
        print row[0], row[1], row[2], row[3], row[4]
        if curzoom != zoom_level:
           curzoom = zoom_level
           available.append(curzoom_data)
           curzoom_data = []

        curzoom_data.extend([
           {
               "startY" : start_row,
               "endX" : end_column,
               "startX" : start_column,
               "endY" : end_row
           }
       ])

    layerFile = open (os.path.join(outputdir, "layer.json"), "w")
    layerFile.write(json.dumps({
        'bounds': [-180, -90, 180, 90],
#        'name': 'something',
        'projection' : 'EPSG:4326',
        'format' : 'quantized-mesh-1.0',
        'version' : '3924.0.0',
        'tilejson' : '2.1.0',
        'minzoom' : 0,
        'attribution': 'Put something there',
        'scheme' : 'tms',
        'description':'Nice terrains',
        'tiles': ['{z}/{x}/{y}.terrain?v={version}'],
        'available': available
    }, sort_keys=True, indent=2))
#    json.dumps(data, separators=(',',':'))
#    layerFile.write(layerdata)



def main(argv):
   inputfile = ''
   outputfile = ''
   force = False

   try:
      opts, args = getopt.getopt(argv,"hi:o:f",["ifile=","odir=","force"])
   except getopt.GetoptError:
      print 'dumper -i <inputfile> -o <outputdir>'
      sys.exit(2)
   for opt, arg in opts:
      if opt == '-h':
         print 'dumper -i <inputfile> -o <outputdir>'
         sys.exit()
      elif opt in ("-i", "--ifile"):
         inputfile = arg
      elif opt in ("-o", "--odir"):
         outputdir = arg
      elif opt in ("-f", "--force"):
         force = True
   
   
   if not os.path.isfile(inputfile):
      print 'Input file does not exist ' + inputfile
      sys.exit(2)
   
   if os.path.exists(outputdir) and not force:
      print 'Output directory already exists ' + outputdir
      sys.exit(2)
   
   
   
   try:
       con = lite.connect(inputfile)
       test(con)
       dumpall(con, outputdir)
       
   except lite.Error, e:
       print "Error %s:" % e.args[0]
       sys.exit(1)
       
   finally:
       if con:
           con.close()

if __name__ == "__main__":
       main(sys.argv[1:])
