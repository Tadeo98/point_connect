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
point_layer_path = r"D:\Praca\SAHI\Kosice\geodezia\plan_pre_mirku\data\L1_points2.shp"   #cesta k bodovej vrstve
output_folder = r"D:\Praca\SAHI\Kosice\geodezia\plan_pre_mirku\data\script_outds"  #cesta k priecinku, kde sa ulozi vysledok
output_file = r"connected_points"   #nazov vystupneho suboru

## NASTAVENIA
feature_type = 1 #typ vysledku, 0 = linia, 1 = polygon
line_ring = 1 #uzavretie linie, 1 = ano, 0 = nie (nepouzitelne pri polygone)
feature_description = 1 #precitanie kodu bodu a jeho pridelenie vytvorenemu prvku, 1 = ano, 0 = nie
keep_point_crs = 0 #vystupna vrstva ma suradnicovy system ako vstupna bodova, ano = 1, nie, nastavim EPSG noveho SS = 0
EPSG = 5514 #EPSG kod (suradnicovy system) vystupnej vrstvy
duplicite_feature = 2   #duplicitne prvky s totoznym kodom, 0 = ponechat vsetky duplicitne prvky, 1 = ponechanie iba prvych vyhodnotenych duplicitnych prvkov, 2 = nahradit skorsie vyhodnotene duplicitne prvky neskorsimi

## PREMENNE
include_features = ('OBJ','obj','Obj','H')   #zadanie retazcov kodov/casti kodov prvkov, ktore budu vo vystupe
exclude_features = ('VB','kera','FTG','SHL','PROF')   #zadanie retazcov kodov/casti kodov prvkov, ktore nebudu vo vystupe
code_position = 5   #cislo atributu s kodmi bodov podla poradia
new_field_name = "Kod"  #nazov noveho pola s popisom/kodom prvku


#############################################################################
## VYPOCET

#uistenie sa, ze v pripade polygonov je nastavene uzavretie linie
if feature_type == 1:
    line_ring = 1


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

#vytvorenie noveho atributoveho pola s popisom prvku
if feature_description == 1:
    new_field = ogr.FieldDefn(new_field_name, ogr.OFTString)
    new_field.SetWidth(32)
    outlayer.CreateField(new_field)

#zoznam kodov pre kontrolu duplicity
code_register = []
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
            #kontrola poctu bodov pre novovytvarane prvky
            if feature_point_count == 2 and line_ring == 1:
                print("Prvok ", point_code, " pozostava len z 2 bodov. Uzavrety prvok vytvoreny nebol.")
                feature_ring = None
                feature_point_count = 0
                continue
            if feature_point_count == 1:
                print("Prvok ", point_code, " pozostava len z 1 bodu. Prvok vytvoreny nebol.")
                feature_ring = None
                feature_point_count = 0
                continue

            #pridanie kodu do zoznamu
            code_register.append(point_code)

            #uzavretie ring
            if line_ring == 1:
                feature_ring.AddPoint(end_ring_X, end_ring_Y)
            # vytvorenie linie
            if feature_type == 0:
                # pridanie polygonu do feature a jeho ulozenie do vystupnej vrstvy
                feature = ogr.Feature(outlayer.GetLayerDefn())
                feature.SetGeometry(feature_ring)
                outlayer.CreateFeature(feature)
                if feature_description == 1:
                    feature.SetField(new_field_name, point_code)   #priradenie kodu prvku
                    outlayer.SetFeature(feature)    #update prvku vo vrstve
                feature_ring = feature = None
            
            # vytvorenie polygonu
            if feature_type == 1:
                feature_polygon = ogr.Geometry(ogr.wkbPolygon)
                feature_polygon.AddGeometry(feature_ring)
                # pridanie polygonu do feature a jeho ulozenie do vystupnej vrstvy
                feature = ogr.Feature(outlayer.GetLayerDefn())
                feature.SetGeometry(feature_polygon)
                outlayer.CreateFeature(feature)
                if feature_description == 1:
                    feature.SetField(new_field_name, point_code)   #priradenie kodu prvku
                    outlayer.SetFeature(feature)    #update prvku vo vrstve
                feature_polygon = feature = None
            feature_point_count = 0


#DUPLICITA
#spocitanie prvkov s rovnakym kodom a vytvorenie matice s nazvami kodov a ich poctom (opakujuce sa)
codes_count = [code_register,[]]
for code in code_register:
    codes_count[1].append(code_register.count(code))

#Vysporiadanie sa s duplicitou
#duplicita sa ponecha, no oznami sa pocet duplicit
if duplicite_feature == 0:
    i = 0
    repeating_codes = []
    for code in codes_count[0]:
        if codes_count[1][i] > 1:
            if code in repeating_codes: #kotrola ci uz kod nebol spomenuty ako duplicitny (inak by sa spomenul tolkokrat, kolkokrat sa kod vyskytuje)
                i += 1
                continue
            print("Prvok s kodom", code, "sa vyskytuje", codes_count[1][i], "krat.")
            repeating_codes.append(code)
        i += 1

#Mazanie neskorsich duplicitnych prvkov
elif duplicite_feature == 1:
    not_first_time_codes = [[],[]]   #vektor so zoznamom kodov a vyskytov prvkov po prvom opakovani
    duplicite_rows = [] #vektor s poradiami prvkov, ktore sa vymazu
    #pridelenie hodnot vektoru
    for i in range(0,len(codes_count[1])):
        if codes_count[1][i] > 1:
            if codes_count[0][i] in not_first_time_codes[0]:
                duplicite_rows.append(i)
            elif codes_count[0][i] not in not_first_time_codes[0]:
                not_first_time_codes[0].append(codes_count[0][i])
                not_first_time_codes[1].append(codes_count[1][i])
    #mazanie prvkov
    for row in duplicite_rows:
        outlayer.DeleteFeature(row)
    for i in range(0,len(not_first_time_codes[0])): #vypisanie spravy o vymazanych duplicitnych prvkoch iba raz
        print("Neskorsie duplicitne prvky s kodom", not_first_time_codes[0][i],"boli vymazane", not_first_time_codes[1][i]-1,"krat.")

#Mazanie skorsich duplicitnych prvkov a ponechanie posledneho
elif duplicite_feature == 2:
    last_time_code = [[],[]]   #vektor so zoznamom kodov a vyskytov prvkov pred poslednym opakovanim
    first_time_codes = []
    duplicite_rows = [] #vektor s poradiami prvkov, ktore sa vymazu
    #pridelenie hodnot vektoru
    for i in range(0,len(codes_count[1])):
        if codes_count[1][i] > 1:
            if codes_count[0][i] not in last_time_code[0]:
                duplicite_rows.append(i)
                first_time_codes.append(codes_count[0][i])
                if codes_count[1][i] == (first_time_codes.count(codes_count[0][i])+1):
                    last_time_code[0].append(codes_count[0][i])
                    last_time_code[1].append(codes_count[1][i])
            else:
                continue
    #mazanie prvkov
    for row in duplicite_rows:
        outlayer.DeleteFeature(row)
    for i in range(0,len(last_time_code[0])): #vypisanie spravy o vymazanych duplicitnych prvkoch iba raz
        print("Skorsie duplicitne prvky s kodom", last_time_code[0][i],"boli vymazane", last_time_code[1][i]-1,"krat.")


#zavretie suboru
outds = outlayer = None