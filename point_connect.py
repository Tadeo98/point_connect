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
##FUNKCIE
def identity_check(feature,identic_points_check,identic_points_distance,feature_code,feature_type): #funkcia celkom zbytocna a mal som to dat dolu do skriptu, neva
    points = []
    identity_count = 0
    geom = feature.GetGeometryRef()
    if feature_type == 1:
        for geom1 in geom:
            geom = geom1
    feature = None
    for i in range(0, geom.GetPointCount()-1):
        points.append(geom.GetPoint(i))
    if identic_points_check == 1:
        #hladanie identickosti medzi vsetkymi moznymi dvojicami bodov, okrem samych so sebou
        for i in range(0,len(points)-1):
            for j in range(i+1,len(points)):
                if np.sqrt((points[i][0]-points[j][0])**2+(points[i][1]-points[j][1])**2+(points[i][2]-points[j][2])**2) < identic_points_distance:
                    identity_count += 1
        if identity_count == 1 and feature_code != None:
            print("V prvku s kodom", feature_code,"sa v tesnej blizkosti nachadza", identity_count, "dvojica bodov.")
        elif identity_count > 1 and identity_count < 5 and feature_code != None:
            print("V prvku s kodom", feature_code,"sa v tesnej blizkosti nachadzaju", identity_count, "dvojice bodov.")
        elif identity_count > 4 and feature_code != None:
            print("V prvku s kodom", feature_code,"sa v tesnej blizkosti nachadza", identity_count, "dvojic bodov.")
        elif identity_count > 0 and feature_code == None:
            print("V prvku zistena identickost bodov. Zapni zapis kodov pre zistenie, o ktory prvok sa jedna.")
        feature_ring = None
    elif identic_points_check == 2:
        feature_ring = None
        for i in range(0,len(points)-1):
            for j in range(i+1,len(points)):
                if np.sqrt((points[i][0]-points[j][0])**2+(points[i][1]-points[j][1])**2+(points[i][2]-points[j][2])**2) < identic_points_distance:
                    identity_count += 1
                    points[i] = []
                    break
        if identity_count == 1 and feature_code != None:
            print("V prvku s kodom", feature_code,"sa vymazal", identity_count, "bod.")
        elif identity_count > 1 and identity_count < 5 and feature_code != None:
            print("V prvku s kodom", feature_code,"sa vymazali", identity_count, "body.")
        elif identity_count > 4 and feature_code != None:
            print("V prvku s kodom", feature_code,"sa vymazalo", identity_count, "bodov.")
        elif identity_count > 0 and feature_code == None:
            print("V prvku s neznamym kodom zistena identickost bodov. Skor zamerane identicke body boli vymazane.")
        if identity_count > 0:
            if feature_type == 0:
                feature_ring = ogr.Geometry(ogr.wkbLineString)  #pre liniu
            elif feature_type == 1:
                feature_ring = ogr.Geometry(ogr.wkbLinearRing)  #pre polygon (najprv ring)
            i = None
            for point_coor in points:
                if point_coor == []:
                    continue
                feature_ring.AddPoint(point_coor[0], point_coor[1], point_coor[2])
                if i == None:
                    i = points.index(point_coor)
            feature_ring.AddPoint(points[i][0], points[i][1], points[i][2])
    return identity_count, feature_ring
        


#######################################################################
## CESTY A NAZVY
point_layer_path = r"D:\Praca\SAHI\Kosice\geodezia\plan_pre_mirku\data\L1_points_fixed.shp"   #cesta k bodovej vrstve
output_folder = r"D:\Praca\SAHI\Kosice\geodezia\plan_pre_mirku\data\script_outds"  #cesta k priecinku, kde sa ulozi vysledok
output_file = r"L1_objekty_hroby_update3"   #nazov vystupneho suboru
line_file_suffix = r"_lines"    #pripona suboru so zvlast liniovymi prvkami
point_file_suffix = r"_points"  #pripona suboru so zvlast bodovymi prvkami

## NASTAVENIA
feature_type = 1 #typ vysledku, 0 = linia, 1 = polygon
line_ring = 1 #uzavretie linie, 1 = ano, 0 = nie (nepouzitelne pri polygone)
feature_description = 1 #precitanie kodu bodu a jeho pridelenie vytvorenemu prvku, 1 = ano, 0 = nie
keep_point_crs = 0 #vystupna vrstva ma suradnicovy system ako vstupna bodova, ano = 1, nie, nastavim EPSG noveho SS = 0
EPSG = 5514 #EPSG kod (suradnicovy system) vystupnej vrstvy
duplicite_feature = 0   #duplicitne prvky s totoznym kodom, 0 = ponechat vsetky duplicitne prvky, 1 = ponechanie iba prvych vyhodnotenych duplicitnych prvkov, 2 = nahradit skorsie vyhodnotene duplicitne prvky neskorsimi
use_point_heights = 1   #zakomponovanie vysok bodov do prvkov, 0 = nie, 1 = ano
save_lines = 0 #ulozit dvojbodove prvky do zvlast liniovej vrstvy, 1 = ano, 0 = nie
save_points = 1 #ulozit jednobodove prvky do zvlast bodovej vrstvy, 1 = ano, 0 = nie
identic_points_check = 2    #kontrola zamerania identickych bodov dvakrat vramci jedneho prvku (v premennych nastavenie identic_points_distance), 0 = bez kontroly, 1 = s kontrolou a oznamenim kodu prvku, kde je potvrdena identickost, 2 = s kontrolou, oznamenim a vymazanim prveho z dvojice identickych bodov (druhe meranie sa povazuje za spravne)


## PREMENNE
include_features = ('OBJ','HROB')   #zadanie retazcov kodov/casti kodov prvkov, ktore budu vo vystupe. Napr. ('OBJ','HROB','Obj','H')
exclude_features = ('VB','kera','FTG','SHL','bronz','Foto','foto','rez','SON','Tele')   #zadanie retazcov kodov/casti kodov prvkov, ktore nebudu vo vystupe. Napr. ('VB','kera','FTG','SHL','PROF')
code_position = 5   #cislo atributu s kodmi bodov podla poradia
new_field_name = "Kod"  #nazov noveho pola s popisom/kodom prvku
identic_points_distance = 0.06 #vzdialenost medzi bodmi, do ktorej budu povazovane za identicke


#############################################################################
## HLAVNA CAST KODU

#uistenie sa, ze v pripade polygonov je nastavene uzavretie linie
if feature_type == 1:
    line_ring = 1
#uistenie sa, ze ak je zapnute vyhladanie identickych bodov a nie je nastavena vzdialenost, tak sa defaultne nastavi
if identic_points_check > 0 and identic_points_distance == 0:
    identic_points_distance = 0.05


# import bodovej vrstvy
point_ds = ogr.Open(point_layer_path, 0) #1 = editing, 0 = read only. Datasource
# bodova vrstva
point_layer = point_ds.GetLayer()
# ziskanie poctu bodov vo vrstve
point_count = point_layer.GetFeatureCount()


#definicia vystupnej vrstvy, zdroja, CRS
driver = ogr.GetDriverByName("ESRI Shapefile")
outds = driver.CreateDataSource(output_folder + "\\" + output_file + ".shp")
#ak sa aj dvoj alebo jednobodove prvky ukladaju tak sa im vytvori vrstva
if save_lines == 1:
    driver_lines = ogr.GetDriverByName("ESRI Shapefile")
    outds_lines = driver_lines.CreateDataSource(output_folder + "\\" + output_file + line_file_suffix + ".shp")
if save_points == 1:
    driver_points = ogr.GetDriverByName("ESRI Shapefile")
    outds_points = driver_points.CreateDataSource(output_folder + "\\" + output_file + point_file_suffix + ".shp")

# definicia referencneho systemu
srs = osr.SpatialReference()
if keep_point_crs == 0:
    srs.ImportFromEPSG(EPSG)    
elif keep_point_crs == 1:
    srs = point_layer.GetSpatialRef()
else:
    print("Zle nastavena hodnota keep_point_crs.")
    exit()
outlayer = outds.CreateLayer(output_file, srs)

#pre dvoj alebo jednobodove prvky
if save_lines == 1:
    outlayer_lines = outds_lines.CreateLayer(output_file + line_file_suffix, srs, ogr.wkbLineString)
if save_points == 1:
    outlayer_points = outds_points.CreateLayer(output_file + point_file_suffix, srs, ogr.wkbPoint)

#vytvorenie noveho atributoveho pola s popisom prvku
if feature_description == 1:
    new_field = ogr.FieldDefn(new_field_name, ogr.OFTString)
    new_field.SetWidth(32)
    outlayer.CreateField(new_field)
    #aj pre bodovu vrstvu
    if save_lines == 1:
        outlayer_lines.CreateField(new_field)
    if save_points == 1:
        outlayer_points.CreateField(new_field)

#zoznam kodov pre kontrolu duplicity
code_register = []
code_register_lines = []
code_register_points = []
#poradie bodu v linii/polygone
feature_point_count = 0

print("\nKONTROLA POCTU BODOV VYTVARANYCH PRVKOV")
warn_count = 0
#cyklus citania atributov kazdeho bodu
for point_number in range(0,point_count):
    # ziskanie konkretneho bodu
    point_feature = point_layer.GetFeature(point_number)
    # ziskanie geometrie bodu, X a Y suradnice (odpovedajuce smeru a orientacii osi v QGISe)
    point_geom = point_feature.GetGeometryRef()
    X_coor_point = point_geom.GetX()
    Y_coor_point = point_geom.GetY()
    if use_point_heights == 0:  #bez pouzitia vysok automaticke definovanie nulovej vysky
        Z_coor_point = 0.0
    if use_point_heights == 1:  #zakomponovanie vysok
        Z_coor_point = point_geom.GetZ()
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
        feature_ring.AddPoint(X_coor_point, Y_coor_point, Z_coor_point)
        #ulozenie suradnice prveho bodu pre neskorsie uzavretie
        if line_ring == 1 and feature_point_count == 1:
            end_ring_X = X_coor_point
            end_ring_Y = Y_coor_point
            end_ring_Z = Z_coor_point
        
        #rozpoznanie posledneho bodu prvku
        if point_code != point_layer.GetFeature(point_number+1).GetField(code_position-1):
            #kontrola poctu bodov pre novovytvarane prvky
            if feature_point_count == 2 and line_ring == 1:
                warn_count += 1
                if save_lines == 1:    #v pripade ukladania dvojbodovych linii do separe vrstvy vratenie sa na prvy bod prvku a ulozenie
                    feature_ring = None
                    feature_ring = ogr.Geometry(ogr.wkbLinearRing)
                    for point_number_in_lines in (point_number-1,point_number):
                        # ziskanie konkretneho bodu
                        point_feature = point_layer.GetFeature(point_number_in_lines)
                        # ziskanie geometrie bodu, X a Y suradnice (odpovedajuce smeru a orientacii osi v QGISe)
                        point_geom = point_feature.GetGeometryRef()
                        X_coor_point = point_geom.GetX()
                        Y_coor_point = point_geom.GetY()
                        if use_point_heights == 0:  #bez pouzitia vysok automaticke definovanie nulovej vysky
                            Z_coor_point = 0.0
                        if use_point_heights == 1:  #zakomponovanie vysok
                            Z_coor_point = point_geom.GetZ()
                        #priradenie suradnice
                        feature_ring.AddPoint(X_coor_point, Y_coor_point, Z_coor_point)
                    # pridanie dvojbodovej linie do feature a jej ulozenie do zvlast vystupnej vrstvy
                    feature_lines = ogr.Feature(outlayer_lines.GetLayerDefn())
                    feature_lines.SetGeometry(feature_ring)
                    outlayer_lines.CreateFeature(feature_lines)
                    if feature_description == 1:
                        feature_lines.SetField(new_field_name, point_code)   #priradenie kodu prvku
                        outlayer_lines.SetFeature(feature_lines)    #update prvku vo vrstve
                    print("Dvojbodovy prvok s kodom", point_code, " bol ulozeny do zvlast liniovej vrstvy.")
                    feature_ring = feature_lines = None
                    feature_point_count = 0
                    code_register_lines.append(point_code)
                    continue
                elif save_lines == 0:   #pripad, kde sa neukladaju linie do zvlast vrstvy
                    print("Prvok ", point_code, " pozostava len z 2 bodov. Uzavrety prvok vytvoreny nebol.")
                    feature_ring = None
                    feature_point_count = 0
                    continue

            if feature_point_count == 1:
                warn_count += 1
                if save_points == 1:    #v pripade ukladania bodovych prvkov do separe vrstvy vratenie sa na prvy bod prvku a ulozenie
                    feature_ring = None
                    #feature_ring = ogr.Geometry(ogr.wkbLinearRing)
                    # ziskanie konkretneho bodu
                    point_feature = point_layer.GetFeature(point_number)
                    # ziskanie geometrie bodu, X a Y suradnice (odpovedajuce smeru a orientacii osi v QGISe)
                    point_geom = point_feature.GetGeometryRef()
                    # pridanie bodu do feature a jeho ulozenie do zvlast vystupnej vrstvy
                    feature_points = ogr.Feature(outlayer_points.GetLayerDefn())
                    feature_points.SetGeometry(point_geom)
                    outlayer_points.CreateFeature(feature_points)
                    if feature_description == 1:
                        feature_points.SetField(new_field_name, point_code)   #priradenie kodu prvku
                        outlayer_points.SetFeature(feature_points)    #update prvku vo vrstve
                    print("Jednobodovy prvok s kodom", point_code, " bol ulozeny do zvlast bodovej vrstvy.")
                    feature_points = None
                    feature_point_count = 0
                    code_register_points.append(point_code)
                    continue
                elif save_points == 0:  #pripad, kde sa neukladaju body do zvlast vrstvy
                    print("Prvok ", point_code, " pozostava len z 1 bodu. Prvok vytvoreny nebol.")
                    feature_ring = None
                    feature_point_count = 0
                    continue

            #pridanie kodu do zoznamu
            code_register.append(point_code)

            #uzavretie ring
            if line_ring == 1:
                feature_ring.AddPoint(end_ring_X, end_ring_Y, end_ring_Z)
            # vytvorenie linie
            if feature_type == 0:
                # pridanie linie do feature a jej ulozenie do vystupnej vrstvy
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
if warn_count == 0:
    print("Pocet bodov vsetkych prvkov OK.")
print("\n")


##############################################################################################
#KONTROLA DUPLICITY SPOJENYCH PRVKOV
print("KONTROLA DUPLICITY SPOJENYCH PRVKOV HLAVNEJ VRSTVY")
warn_count = 0
#spocitanie prvkov s rovnakym kodom a vytvorenie matice s nazvami kodov a ich poctom (opakujuce sa)
codes_count = [code_register]
if save_lines == 1:
    codes_count.append(code_register_lines)
if save_points == 1:
    codes_count.append(code_register_points)
for i in range(0,len(codes_count)):
    codes_count.append([])
for j in range(0,int(len(codes_count)/2)):
    for code in codes_count[j]:
        codes_count[j+int(len(codes_count)/2)].append(codes_count[j].count(code))

#Vysporiadanie sa s duplicitou
#duplicita sa ponecha, no oznami sa pocet duplicit
if duplicite_feature == 0:
    for j in range(0,int(len(codes_count)/2)):
        i = 0
        repeating_codes = []
        for code in codes_count[j]:
            if codes_count[j+int(len(codes_count)/2)][i] > 1:
                warn_count += 1
                if code in repeating_codes: #kotrola ci uz kod nebol spomenuty ako duplicitny (inak by sa spomenul tolkokrat, kolkokrat sa kod vyskytuje)
                    i += 1
                    continue
                print("Prvok s kodom", code, "sa vyskytuje", codes_count[j+int(len(codes_count)/2)][i], "krat.")
                repeating_codes.append(code)
            i += 1

#Mazanie neskorsich duplicitnych prvkov
elif duplicite_feature == 1:
    not_first_time_codes = [[],[]]   #vektor so zoznamom kodov a vyskytov prvkov po prvom opakovani
    duplicite_rows = [] #vektor s poradiami prvkov, ktore sa vymazu
    #pridelenie hodnot vektoru
    for i in range(0,len(codes_count[int(len(codes_count)/2)])):
        if codes_count[int(len(codes_count)/2)][i] > 1:
            warn_count += 1
            if codes_count[0][i] in not_first_time_codes[0]:
                duplicite_rows.append(i)
            elif codes_count[0][i] not in not_first_time_codes[0]:
                not_first_time_codes[0].append(codes_count[0][i])
                not_first_time_codes[1].append(codes_count[int(len(codes_count)/2)][i])
    #mazanie prvkov
    for row in duplicite_rows:
        outlayer.DeleteFeature(row)
    for i in range(0,len(not_first_time_codes[0])): #vypisanie spravy o vymazanych duplicitnych prvkoch iba raz
        print("Neskorsie duplicitne prvky s kodom", not_first_time_codes[0][i],"boli vymazane", not_first_time_codes[1][i]-1,"krat.")
    if save_lines == 1 or save_points == 1:
        print("Duplicita prvkov zvlast bodovej/liniovej vrstvy neopravena.")

#Mazanie skorsich duplicitnych prvkov a ponechanie posledneho
elif duplicite_feature == 2:
    last_time_code = [[],[]]   #vektor so zoznamom kodov a vyskytov prvkov pred poslednym opakovanim
    first_time_codes = []
    duplicite_rows = [] #vektor s poradiami prvkov, ktore sa vymazu
    #pridelenie hodnot vektoru
    for i in range(0,len(codes_count[int(len(codes_count)/2)])):
        if codes_count[int(len(codes_count)/2)][i] > 1:
            warn_count += 1
            if codes_count[0][i] not in last_time_code[0]:
                duplicite_rows.append(i)
                first_time_codes.append(codes_count[0][i])
                if codes_count[int(len(codes_count)/2)][i] == (first_time_codes.count(codes_count[0][i])+1):
                    last_time_code[0].append(codes_count[0][i])
                    last_time_code[1].append(codes_count[int(len(codes_count)/2)][i])
            else:
                continue
    #mazanie prvkov
    for row in duplicite_rows:
        outlayer.DeleteFeature(row)
    for i in range(0,len(last_time_code[0])): #vypisanie spravy o vymazanych duplicitnych prvkoch iba raz
        print("Skorsie duplicitne prvky s kodom", last_time_code[0][i],"boli vymazane", last_time_code[1][i]-1,"krat.")
    print("Duplicita prvkov zvlast bodovej/liniovej vrstvy neopravena.")
if warn_count == 0:
    print("Ziadna duplicita.")
print("\n")


##############################################################################################
#KONTROLA GEOMETRIE SPOJENYCH PRVKOV
print("KONTROLA GEOMETRIE SPOJENYCH PRVKOV HLAVNEJ VRSTVY")
warn_count = 0
for feature in outlayer:
    geom = feature.GetGeometryRef()
    if feature_type == 1:   #jednoduchsi pripad polygonov
        buffer = geom.Buffer(0)
    elif feature_type == 0:   #pri liniach treba urobit najprv polygon a az z neho buffer
        if line_ring == 0: #pre pripad nastavenia neuzavretych linii, kde nie je mozna kontrola geometrie nizsim sposobom
            warn_count += 1
            print("Kontrola geometrie neuzavretych linii nemozna.")
            break

        #Cerpanie bodov z geometrie
        wkt = geom.ExportToWkt()
        wkt_edited = wkt.replace("LINESTRING (","")
        wkt_edited2 = wkt_edited.replace(")","")
        coor_list = list(wkt_edited2.split(","))
        coor_list2 = []
        for i in range(0,len(coor_list)):
            coor_list2.append(coor_list[i].split(" "))
        linear_ring = ogr.Geometry(ogr.wkbLinearRing)
        for i in range(0,len(coor_list2)):
            linear_ring.AddPoint(float(coor_list2[i][0]), float(coor_list2[i][1]), float(coor_list2[i][2]))
        feature_polygon = ogr.Geometry(ogr.wkbPolygon)  #docasny polygon pre buffer
        feature_polygon.AddGeometry(linear_ring)    #vlozenie ringu
        feature2 = ogr.Feature(outlayer.GetLayerDefn())
        feature2.SetGeometry(feature_polygon)
        geom_polygon = feature2.GetGeometryRef()
        buffer = geom_polygon.Buffer(0) #buffer prijme iba polygon, nie liniu, preto transformacia LINESTRING na LINEARRING a potom na POLYGON
        feature2 = linear_ring = feature_polygon = None
    
    #kontrola pozostava z porovnania plochy prvku a plochy bufferu s nastavenou vzdialenostou 0
    if abs(geom.GetArea() - buffer.GetArea()) > 0.000001:   #pri liniach vyjde aj pri spravnej geometrii trocha rozdielna plocha buffera, preto tolerancia 1 mm2
        print("Geometria prvku s kodom", feature.GetField(new_field_name), "nie je v poriadku. Je odporucana kontrola.")
        warn_count += 1
if warn_count == 0:
    print("Geometria prvkov OK.")
print("\n")


##############################################################################################
#KONTROLA IDENTICKOSTI BODOV V RAMCI UZAVRETYCH PRVKOV (POLYGONY A UZAVRETE LINIE)
if identic_points_check > 0:
    warn_count = 0
    print("KONTROLA IDENTICKOSTI BODOV V RAMCI UZAVRETYCH PRVKOV")
    feature_count = outlayer.GetFeatureCount()
    for feature_number in range(0,feature_count):
        feature = outlayer.GetFeature(feature_number)
        if feature_description == 1:
            feature_code = feature.GetField(0)
        elif feature_description == 0:
            feature_code = None
        identity_count, feature_ring = identity_check(feature,identic_points_check,identic_points_distance,feature_code,feature_type)
        warn_count += identity_count
        if identic_points_check == 2:
            if identity_count > 0:
                #vymazanie povodnej feature a jej vytvorenie na konci zoznamu prvkov
                outlayer.DeleteFeature(feature_number)
                # vytvorenie linie
                if feature_type == 0:
                    # pridanie linie do feature a jej ulozenie do vystupnej vrstvy
                    feature = ogr.Feature(outlayer.GetLayerDefn())
                    feature.SetGeometry(feature_ring)
                    outlayer.CreateFeature(feature)
                    if feature_description == 1:
                        feature.SetField(new_field_name, feature_code)   #priradenie kodu prvku
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
                        feature.SetField(new_field_name, feature_code)   #priradenie kodu prvku
                        outlayer.SetFeature(feature)    #update prvku vo vrstve
                    feature_polygon = feature = None

    if warn_count == 0:
        print("Identickost bodov nezistena.")


#zavretie suboru
outds = outds_lines = outds_points = outlayer = outlayer_lines = outlayer_points = None