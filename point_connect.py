#######################################################################
## POINT CONNECT ##
#######################################################################

import math
import os

import numpy as np
## KNIZNICE
from matplotlib.style import use
from osgeo import gdal, ogr, osr

#######################################################################
## CESTY
point_layer_path = r"D:\Praca\SAHI\Kosice\geodezia\plan_pre_mirku\data\L1_points.shp"   #cesta k bodovej vrstve
output_folder = r"D:\Praca\SAHI\Kosice\geodezia\plan_pre_mirku\data\script_outds"  #cesta k priecinku, kde sa ulozi vysledok
output_file = r"connected_points"   #nazov vystupneho suboru

## NASTAVENIA
feature_type = 1 #typ vysledku, 0 = linia, 1 = polygon
line_ring = 1 #uzavretie linie, 1 = ano, 0 = nie (nepouzitelne pri polygone)
feature_description = 1 #precitanie kodu bodu a jeho pridelenie vytvorenemu prvku, 1 = ano, 0 = nie
keep_point_crs = 0 #vystupna vrstva ma suradnicovy system ako vstupna bodova, ano = 1, nie, nastavim EPSG noveho SS = 0
EPSG = 5514 #EPSG kod (suradnicovy system) vystupnej vrstvy

## PREMENNE
include_features = ('OBJ','obj','Obj')   #zadanie retazcov kodov/casti kodov prvkov, ktore budu vo vystupe
exclude_features = ('VB','kera','FTG')   #zadanie retazcov kodov/casti kodov prvkov, ktore nebudu vo vystupe
code_position = 5   #cislo atributu s kodmi bodov podla poradia


#############################################################################
## VYPOCET

# import bodovej vrstvy
point_ds = ogr.Open(point_layer_path, 0) #1 = editing, 0 = read only. Datasource
# bodova vrstva
point_layer = point_ds.GetLayer()
# ziskanie poctu bodov vo vrstve
point_count = point_layer.GetFeatureCount()


#definicia vystupnej vrstvy, zdroja, CRS
driver = ogr.GetDriverByName("ESRI Shapefile")
outds = driver.CreateDataSource(output_folder + "\\" + output_file + ".shp")

# definicia referencneho systemu
srs = osr.SpatialReference()
if keep_point_crs == 0:
    srs.ImportFromEPSG(EPSG)    
elif keep_point_crs == 1:
    srs = point_layer.GetSpatialRef()
else:
    print("Zle nastavena hodnota keep_point_crs.")
    throwshed_outds = None
    exit()
outlayer = outds.CreateLayer(output_file, srs)


#poradie bodu v linii/polygone
feature_point_count = 0
#cyklus citania atributov kazdeho bodu
for point_number in range(0,point_count):
    # ziskanie konkretneho bodu
    point_feature = point_layer.GetFeature(point_number)
    # ziskanie geometrie bodu, X a Y suradnice (odpovedajuce smeru a orientacii osi v QGISe)
    point_geom = point_feature.GetGeometryRef()
    X_coor_point = point_geom.GetX()
    Y_coor_point = point_geom.GetY()
    #ziskanie kodu bodu
    point_code = point_feature.GetField(code_position-1)
    include_count = 0
    exclude_count = 0

    #prijatie bodu na zaklade najdeneho zelaneho retazca v kode
    for inclusion in include_features:
        if point_code.find(inclusion) != -1:
            include_count += 1
    
    #vyradenie bodu na zaklade najdeneho nezelaneho retazca v kode
    for exclusion in exclude_features:
        if point_code.find(exclusion) != -1:
            exclude_count += 1

    #podla poziadaviek sa vyhodnoti bod za vhodny na cerpanie suradnic
    if exclude_count == 0 and include_count > 0 or include_features == ():
        feature_point_count += 1    #pocitanie poradia bodu v jednom prvku
        # vytvorenie novej geometrie
        if feature_point_count == 1:
            if feature_type == 0:
                feature_ring = ogr.Geometry(ogr.wkbLineString)  #pre liniu
            elif feature_type == 1:
                feature_ring = ogr.Geometry(ogr.wkbLinearRing)  #pre polygon (najprv ring)
            
        #priradenie suradnice
        feature_ring.AddPoint(X_coor_point, Y_coor_point)
        #ulozenie suradnice prveho bodu pre neskorsie uzavretie
        if line_ring == 1 and feature_point_count == 1:
            end_ring_X = X_coor_point
            end_ring_Y = Y_coor_point

        #rozpoznanie posledneho bodu prvku
        if point_code != point_layer.GetFeature(point_number+1).GetField(code_position-1):

            #uzavretie ring
            if line_ring == 1:
                feature_ring.AddPoint(end_ring_X, end_ring_Y)
            # vytvorenie linie
            if feature_type == 0:
                # pridanie polygonu do feature a jeho ulozenie do vystupnej vrstvy
                feature = ogr.Feature(outlayer.GetLayerDefn())
                feature.SetGeometry(feature_ring)
                outlayer.CreateFeature(feature)
                feature_ring = feature = None
            
            # vytvorenie polygonu
            if feature_type == 1:
                feature_polygon = ogr.Geometry(ogr.wkbPolygon)
                feature_polygon.AddGeometry(feature_ring)
                # pridanie polygonu do feature a jeho ulozenie do vystupnej vrstvy
                feature = ogr.Feature(outlayer.GetLayerDefn())
                feature.SetGeometry(feature_polygon)
                outlayer.CreateFeature(feature)
                feature_polygon = feature = None
            feature_point_count = 0


#zavretie suboru
outds = outlayer = None
