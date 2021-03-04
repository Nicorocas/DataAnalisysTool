import os
from arcpy import env
import arcpy
import pickle

arcpy.env.overwriteOutput = True
env.overwriteOutput = True
#Se define el wrokspace de la carpeta donde se va a iterar
miworkspace= arcpy.GetParameterAsText(0) #variable carpeta donde estan los archivos
env.workspace= miworkspace
arcpy.env.overwriteOutput = True
#Se crea una GDB a la que iran los archivos que se van a sacar#
gdb_origen =  arcpy.GetParameterAsText(1) #variable donde se va a almacenar la GDB
nombre_GDB=  arcpy.GetParameterAsText(2) #Nombre de la GDB que se va a crear
NuevaGDB = arcpy.CreateFileGDB_management(gdb_origen, nombre_GDB)
NombreGDB = os.path.join(gdb_origen,nombre_GDB)
#la idea va ser añadir los archivos que se llamen rt_tramo_vial.shp y rt_nodoctra_p.shp a esa GDB#
### REFERENCIA ESPACIAL MALDITO DESASTREE###
#Codigo etrs89= 25830  WGS = 4326
etrs89 = arcpy.SpatialReference(25830)
wgs = arcpy.SpatialReference(3857)

#para hacerlo necesito el resultado de iterar en las carpetas dentro de la carpeta en dos bucles y en los nombres de cada archivo,
#un ListWorkspace para cada nivel
ListaCarpetas= arcpy.ListWorkspaces(workspace_type="Folder")

#y un ListfeatureClasses para cada workspace
ListasFeatureClass = arcpy.ListFeatureClasses(feature_type="Polyline")

#con estos dos elementos tenemos todos los nombres, hay que sacar la logica de iterar hasta el nivel de shapefile
for carpeta in ListaCarpetas: #cadaProvincia
    miNuevoWorkspace = carpeta
    env.workspace = miNuevoWorkspace  # se cambia el workspace
    arcpy.AddMessage(carpeta)
    arcpy.AddMessage("iterando en carpeta")

    ListaCarpetas = arcpy.ListWorkspaces(workspace_type="Folder")
    for carpetas in ListaCarpetas: #cada Tipo de Archivos
        miNuevoWorkspace = carpetas
        env.workspace = miNuevoWorkspace
        ListasFeatureClass = arcpy.ListFeatureClasses()

        #ListfeatureClasses para rt_tramo_vial.shp y ahora para los nodos rt_nodoctra_p.shp
        #ListfeatureClasses en cada carpeta y si es el correcto se añade a la GDB
        for FeatureClass in ListasFeatureClass:
            if FeatureClass == "rt_tramo_vial.shp":
                arcpy.FeatureClassToGeodatabase_conversion(FeatureClass,NuevaGDB)
                arcpy.AddMessage("cargando rt_tramo_vial a GDB")
            if FeatureClass == "rt_nodoctra_p.shp":
                arcpy.FeatureClassToGeodatabase_conversion(FeatureClass, NuevaGDB)
                arcpy.AddMessage("cargando rt_nodoctra_p.shp a GDB")
#ya estan las FC en la GDB, ahora vamos a unirlas en un merge para luego tener que manejar sola una FC en la GDB
arcpy.env.overwriteOutput = True
arcpy.env.overwriteOutput = True
env.workspace = NombreGDB

#primero listamos las lineas rt_tramo_vial
listaGDB_lineas = arcpy.ListFeatureClasses(feature_type="Polyline")
arcpy.AddMessage(listaGDB_lineas)
#añadimos los archivos listados en la nueva GDB
FC = arcpy.CreateFeatureclass_management(NuevaGDB,"Rt_definitivo","POLYLINE")
arcpy.Merge_management(listaGDB_lineas, FC)

#Ahora lo mismo pero para la clase de entidad de nodo
listaGDB_puntos = arcpy.ListFeatureClasses(feature_type="Point")
arcpy.AddMessage(listaGDB_puntos)
#listamos los archivos incorporados en la nueva GDB
FC = arcpy.CreateFeatureclass_management(NuevaGDB,"Rt_nodo_definitivo","POINT")
arcpy.Merge_management(listaGDB_puntos, FC)
NuevaFC = "Rt_definitivo.shp"
NuevaFCNodo = "Rt_nodo_definitivo.shp"
arcpy.AddMessage("Merge completado tutobenne")

#reproyectar las capas a WGS84 para hacerla compatible con el resto del proyecto en ArcgisOnline, y borrar datos sobrantes
env.workspace = NombreGDB
NuevaFCa = arcpy.ListFeatureClasses()
for fc in NuevaFCa:
    if fc == "Rt_definitivo":
        arcpy.Project_management(fc, "Rt_definitivo1", wgs)
        arcpy.AddMessage("capa reproyectada")
        arcpy.Delete_management(fc)
        arcpy.AddMessage(fc+" Borrada")
    if fc == "Rt_nodo_definitivo":
        arcpy.Project_management(fc, "Rt_nodo_definitivo1", wgs)
        arcpy.AddMessage("capa reproyectada")
        arcpy.Delete_management(fc)
        arcpy.AddMessage(fc + " Borrada")
    else:
        #borrar datos sobrantes
        arcpy.Delete_management(fc)
        arcpy.AddMessage(fc+" borrada")

NuevaFC = "Rt_definitivo1"
#Para Addfield tenemos que establecer unas variables y rellenar los campos en la capa de lineas

#Los diccionarios necesarios están guardados (con el módulo pickle). Los abrimos con pickle también:
with open('diccionarios/campos.pkl', 'rb') as f:
    campos = pkl.loads(f.read())
    
with open('diccionarios/expresiones.pkl', 'rb') as f:
    expresiones = pkl.loads(f.read())
    
with open('diccionarios/mensajes.pkl', 'rb') as f:
    mensajes = pkl.loads(f.read())
    
with open('diccionarios/codigos.pkl', 'rb') as f:
    codigos = pkl.loads(f.read())

#Field type
Field_type_text ="TEXT"
Field_type_Numero = "DOUBLE"


#hay que añadir 7 campos asique seran 7 addfields cada uno con su config, e ir añadiendo el CalculatedField.
# Para aligerar el código, crearemos una función general a la que llamar 7 veces.
def funcion_campos(campo, tipo_campo, expresion, codigo, mensaje, tipo_expresion = "PYTHON3", tabla = NuevaFC):
    arcpy.AddField_management(tabla, campo, tipo_campo)
    arcpy.CalculateField_management(tabla, campo, expresion, tipo_expresion, codigo, tipo_campo)
    arcpy.AddMessage(mensaje)

#Campo 0 Velocidad coches
funcion_campos(campos[0], Field_type_Numero, expresiones[0], codigos[0], mensajes[0])

#Campo 1 Velocidad ciclomotor
funcion_campos(campos[1], Field_type_Numero, expresiones[1], codigos[1], mensajes[1])

#Campo2 prohibido coches
funcion_campos(campos[2], Field_type_text, expresiones[2], codigos[2], mensajes[2])

#Campo3 prohibido bicis
funcion_campos(campos[3], Field_type_text, expresiones[3], codigos[3], mensajes[3])

#campo4 tiempo en coche
funcion_campos(campos[4], Field_type_Numero, expresiones[4], codigos[4], mensajes[4])

#campo5 tiempo ciclomotor
funcion_campos(campos[5], Field_type_Numero, expresiones[5], codigos[5], mensajes[5])

#Campo6 consumo coche
funcion_campos(campos[6], Field_type_Numero, expresiones[6], codigos[6], mensajes[6])

#Campo7 consumo moto
funcion_campos(campos[7], Field_type_Numero, expresiones[7], codigos[7], mensajes[7])



#Ya estas los campos nuevos añadidos y calculados al nuevo shape de Rt_definitivo1,
# con esta Feature class y con la de rtnodos es con la que haremos el network dataset y posteriormente construiremos la red
# para ello necesitamis 1. Un Feature dataset, 2. Un netowrk Dataset construido con Rt_definitivo1 y rt_nodos_definitivo1
# 1. Feature Dataset#

NuevaFC = "Rt_definitivo1"
NuevaFCNodo = "Rt_nodo_definitivo1"
Salida_dataset = NombreGDB
Nombre = "FeatureDataset"
#Referencia_espacial = "opcional"
arcpy.CreateFeatureDataset_management(Salida_dataset,Nombre,wgs)
arcpy.AddMessage("se ha creado el Feature dataset")
#Feature class to Feature Dataset, para introducir Rt-definitivo a un feature dataset
GDB = Salida_dataset
arcpy.env.workspace = GDB

#introducimos las capas de lineas y nodos
FeatureDataset = os.path.join(GDB,Nombre)
Clase_entrada = os.path.join(GDB,NuevaFC)
Clase_entrada1 = os.path.join(GDB,NuevaFCNodo)
FeatureDataset_destino = FeatureDataset
arcpy.FeatureClassToGeodatabase_conversion([Clase_entrada,Clase_entrada1],FeatureDataset_destino)
arcpy.AddMessage("El pájaro esta en nido")
#comprobar si la FC esta en el feature Dataset
#Crear el network dataset
Name = "NetworkDataset"
arcpy.env.workspace= FeatureDataset
nueva_clase_lineas= "Rt_definitivo1_1"
nueva_clase_nodos= "Rt_nodo_definitivo1_1"
arcpy.CreateNetworkDataset_na(FeatureDataset,Name,[nueva_clase_nodos,nueva_clase_lineas])
arcpy.AddMessage("Se ha creado el NetworkDataset")


