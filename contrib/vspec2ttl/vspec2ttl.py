#!/usr/bin/env python3

# (C) 2021 BMW Group - All rights reserved.
# AUTHOR: Daniel Wilms BMW Group;

#
#
#
# All files and artifacts in this repository are licensed under the
# provisions of the license provided by the LICENSE file in this repository.
#

#
# Convert vspec file to TTL
#
import os
import sys
import re

# Add path to main py vspec  parser
myDir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(myDir, "../.."))

from anytree import RenderTree, PreOrderIter

import vspec
import getopt

from vspec.model.vsstree import VSSNode, VSSType, VSSDataType
from vspec.model.constants import VSSConstant

from rdflib import Graph, Literal, RDF, URIRef, Namespace
from rdflib.namespace import RDFS, XSD, OWL, XMLNS, RDF, FOAF, SKOS, SDO, NamespaceManager
from enum import Enum

from vssotypes import VssoConcepts, DataTypes, DataUnits, Namespaces


def usage():
    print(f"""
Usage: {sys.argv[0]} [options] vspec_file ttl_file

  where [options] are:

  -I include_dir       Add include directory to search for included vspec
                       files. Can be used multiple timees.

  vspec_file           The vehicle specification file to parse.

  ttl_file             The file to output the ttl data to.
""")
    sys.exit(255)


def setup_graph():
    # create a Graph
    g = Graph()

    ontology = VssoConcepts.EMPTY.uri
    g.add((ontology, RDF.type, OWL.Ontology))
    g.add((ontology, OWL.versionInfo, Literal("1.0.0")))
    g.add((ontology, RDFS.label, Literal("COVESA VSS ontology", lang="en")))
    g.add((ontology, OWL.imports, URIRef("http://purl.oclc.org/NET/ssnx/qu/qu-rec20")))

    belongsTo = VssoConcepts.BELONGS_TO.uri
    g.add((belongsTo, RDF.type, OWL.ObjectProperty))
    g.add((belongsTo, RDFS.subPropertyOf, OWL.topObjectProperty))
    g.add((belongsTo, RDFS.label, Literal(VssoConcepts.BELONGS_TO.value, lang="en")))
    g.add((belongsTo, RDFS.range, VssoConcepts.VEHICLE_COMP.uri))
    g.add((belongsTo, RDFS.domain, VssoConcepts.VEHICLE_PROP.uri))

    # holdsValue = VssoConcepts.HOLDS_VALUE.uri
    # g.add((holdsValue, RDF.type, OWL.DatatypeProperty))
    # g.add((holdsValue,RDFS.subPropertyOf, OWL.topDataProperty))
    # g.add((holdsValue,RDFS.domain, VssoConcepts.VEHICLE_PROP.uri))
    # g.add((holdsValue,RDFS.label, Literal(VssoConcepts.HOLDS_VALUE.value,lang="en")))

    # partOfVehicle = VssoConcepts.PART_OF_VEHICLE.uri
    # g.add((partOfVehicle, RDF.type, OWL.ObjectProperty))
    # g.add((partOfVehicle,RDFS.subPropertyOf, OWL.topObjectProperty))
    # g.add((partOfVehicle,RDFS.domain, VssoConcepts.VEHICLE_COMP.uri))
    # g.add((partOfVehicle,RDFS.range, VssoConcepts.VEHICLE.uri))
    # g.add((partOfVehicle,RDFS.label, Literal(VssoConcepts.PART_OF_VEHICLE.value,lang="en")))

    unit = VssoConcepts.UNIT.uri
    g.add((unit, RDF.type, OWL.ObjectProperty))
    g.add((unit, RDFS.subPropertyOf, OWL.topObjectProperty))
    g.add((unit, RDFS.domain, VssoConcepts.VEHICLE_PROP_NUM.uri))
    g.add((unit, RDFS.range, URIRef(Namespaces["unit"] + "Unit")))
    g.add((unit, RDFS.label, Literal(VssoConcepts.UNIT.value, lang="en")))

    dataType = VssoConcepts.DATA_TYPE.uri
    g.add((dataType, RDF.type, OWL.ObjectProperty))
    g.add((dataType, RDFS.subPropertyOf, OWL.topObjectProperty))
    g.add((dataType, RDFS.domain, VssoConcepts.VEHICLE_PROP_NUM.uri))
    g.add((dataType, RDFS.range, RDFS.Datatype))
    g.add((dataType, RDFS.label, Literal(VssoConcepts.DATA_TYPE.value, lang="en")))

    baseDataType = VssoConcepts.BASE_DATA_TYPE.uri
    g.add((baseDataType, RDF.type, OWL.ObjectProperty))
    g.add((baseDataType, RDFS.subPropertyOf, OWL.topObjectProperty))
    g.add((baseDataType, RDFS.domain, VssoConcepts.ARRAY_TYPE.uri))
    g.add((baseDataType, RDFS.range, RDFS.Datatype))
    g.add((baseDataType, RDFS.label, Literal(VssoConcepts.BASE_DATA_TYPE.value, lang="en")))

    hasEnumerationValue = VssoConcepts.HAS_ENUM_VALUE.uri
    g.add((hasEnumerationValue, RDF.type, OWL.ObjectProperty))
    g.add((hasEnumerationValue, RDFS.subPropertyOf, OWL.topObjectProperty))
    g.add((hasEnumerationValue, RDFS.domain, VssoConcepts.VEHICLE_PROP_ENUM.uri))
    g.add((hasEnumerationValue, RDFS.range, VssoConcepts.ENUM_VALUE.uri))
    g.add((hasEnumerationValue, RDFS.label, Literal(VssoConcepts.HAS_ENUM_VALUE.value, lang="en")))

    hasDefaultEnumerationValue = VssoConcepts.HAS_ENUM_DEF.uri
    g.add((hasDefaultEnumerationValue, RDF.type, OWL.ObjectProperty))
    g.add((hasDefaultEnumerationValue, RDFS.subPropertyOf, OWL.topObjectProperty))
    g.add((hasDefaultEnumerationValue, RDFS.domain, VssoConcepts.VEHICLE_PROP_ENUM.uri))
    g.add((hasDefaultEnumerationValue, RDFS.range, VssoConcepts.ENUM_VALUE.uri))
    g.add((hasDefaultEnumerationValue, RDFS.label, Literal(VssoConcepts.HAS_ENUM_DEF.value, lang="en")))

    partOfVehicleComponent = VssoConcepts.PART_OF_VEH_COMP.uri
    g.add((partOfVehicleComponent, RDF.type, OWL.ObjectProperty))
    g.add((partOfVehicleComponent,RDFS.subPropertyOf, OWL.topObjectProperty))
    g.add((partOfVehicleComponent,RDFS.domain, VssoConcepts.VEHICLE_COMP.uri))
    g.add((partOfVehicleComponent,RDFS.range, VssoConcepts.VEHICLE_COMP.uri))
    g.add((partOfVehicleComponent,RDFS.label, Literal(VssoConcepts.PART_OF_VEH_COMP.value,lang="en")))

    vehiclePropertyName = VssoConcepts.VEHICLE_PROP_NAME.uri
    g.add((vehiclePropertyName, RDF.type, OWL.DatatypeProperty))
    g.add((vehiclePropertyName, RDFS.subPropertyOf, OWL.topDataProperty))
    g.add((vehiclePropertyName, RDFS.label, Literal(VssoConcepts.VEHICLE_PROP_NAME.value,lang="en")))
    g.add((vehiclePropertyName, RDFS.domain, VssoConcepts.VEHICLE_PROP.uri))
    g.add((vehiclePropertyName, RDFS.range, XSD.string))

    vehicleComponentName = VssoConcepts.VEHICLE_COMP_NAME.uri
    g.add((vehicleComponentName, RDF.type, OWL.DatatypeProperty))
    g.add((vehicleComponentName, RDFS.subPropertyOf, OWL.topDataProperty))
    g.add((vehicleComponentName, RDFS.label, Literal(VssoConcepts.VEHICLE_COMP_NAME.value,lang="en")))
    g.add((vehicleComponentName, RDFS.domain, VssoConcepts.VEHICLE_COMP.uri))
    g.add((vehicleComponentName, RDFS.range, XSD.string))

    minValue = VssoConcepts.MIN.uri
    g.add((minValue, RDF.type, OWL.DatatypeProperty))
    g.add((minValue, RDFS.subPropertyOf, OWL.topDataProperty))
    g.add((minValue, RDFS.label, Literal(VssoConcepts.MIN.value, lang="en")))
    g.add((minValue, RDFS.domain, VssoConcepts.VEHICLE_PROP_NUM.uri))
    g.add((minValue, RDFS.range, XSD.double))

    maxValue = VssoConcepts.MAX.uri
    g.add((maxValue, RDF.type, OWL.DatatypeProperty))
    g.add((maxValue, RDFS.subPropertyOf, OWL.topDataProperty))
    g.add((maxValue, RDFS.label, Literal(VssoConcepts.MAX.value, lang="en")))
    g.add((maxValue, RDFS.domain, VssoConcepts.VEHICLE_PROP_NUM.uri))
    g.add((maxValue, RDFS.range, XSD.double))

    resolution = VssoConcepts.RES.uri
    g.add((resolution, RDF.type, OWL.DatatypeProperty))
    g.add((resolution, RDFS.subPropertyOf, OWL.topDataProperty))
    g.add((resolution, RDFS.label, Literal(VssoConcepts.RES.value, lang="en")))
    g.add((resolution, RDFS.domain, VssoConcepts.VEHICLE_PROP_NUM.uri))
    g.add((resolution, RDFS.range, XSD.double))

    enumerationName = VssoConcepts.ENUM_NAME.uri
    g.add((enumerationName, RDF.type, OWL.DatatypeProperty))
    g.add((enumerationName, RDFS.subPropertyOf, OWL.topDataProperty))
    g.add((enumerationName, RDFS.label, Literal(VssoConcepts.ENUM_NAME.value, lang="en")))
    g.add((enumerationName, RDFS.domain, VssoConcepts.ENUM_VALUE.uri))
    g.add((enumerationName, RDFS.range, XSD.string))

    enumerationDescription = VssoConcepts.ENUM_DESC.uri
    g.add((enumerationDescription, RDF.type, OWL.DatatypeProperty))
    g.add((enumerationDescription, RDFS.subPropertyOf, OWL.topDataProperty))
    g.add((enumerationDescription, RDFS.label, Literal(VssoConcepts.ENUM_DESC.value, lang="en")))
    g.add((enumerationDescription, RDFS.domain, VssoConcepts.ENUM_VALUE.uri))
    g.add((enumerationDescription, RDFS.range, XSD.string))

    # hasComponentInstance = VssoConcepts.HAS_COMP_INST.uri
    # g.add((hasComponentInstance, RDF.type, OWL.DatatypeProperty))
    # g.add((hasComponentInstance,RDFS.subPropertyOf, OWL.topDataProperty))
    # g.add((hasComponentInstance,RDFS.label, Literal(VssoConcepts.HAS_COMP_INST.value,lang="en")))

    # hasAttribute = VssoConcepts.HAS_ATTRIBUTE.uri
    # g.add((hasAttribute, RDF.type, OWL.ObjectProperty))
    # g.add((hasAttribute,RDFS.subPropertyOf, OWL.topObjectProperty))
    # g.add((hasAttribute, RDFS.domain, VssoConcepts.VEHICLE.uri))
    # g.add((hasAttribute, RDFS.range, VssoConcepts.VEHICLE_STAT.uri))
    # g.add((hasAttribute, RDFS.label, Literal(VssoConcepts.HAS_ATTRIBUTE.value,lang="en")))
    #
    # hasDynProp = VssoConcepts.HAS_SIGNAL.uri
    # g.add((hasDynProp, RDF.type, OWL.ObjectProperty))
    # g.add((hasDynProp,RDFS.subPropertyOf, OWL.topObjectProperty))
    # g.add((hasDynProp, RDFS.domain, VssoConcepts.VEHICLE.uri))
    # g.add((hasDynProp, RDFS.range, VssoConcepts.VEHICLE_PROP.uri))
    # g.add((hasDynProp, RDFS.label, Literal(VssoConcepts.HAS_SIGNAL.value,lang="en")))

    ##
    # Classes
    ##
    # vehicle = VssoConcepts.VEHICLE.uri
    # g.add((vehicle, RDF.type, OWL.Class))
    # g.add((vehicle, RDF.type, RDFS.Class))
    # g.add((vehicle,RDFS.label, Literal(VssoConcepts.VEHICLE.value,lang="en")))

    vehicleProperty = VssoConcepts.VEHICLE_PROP.uri
    g.add((vehicleProperty, RDF.type, OWL.Class))
    g.add((vehicleProperty, RDFS.label, Literal(VssoConcepts.VEHICLE_PROP.value, lang="en")))

    dynamicVehicleProperty = VssoConcepts.VEHICLE_PROP_DYN.uri
    g.add((dynamicVehicleProperty, RDF.type, OWL.Class))
    g.add((dynamicVehicleProperty, RDFS.subClassOf, vehicleProperty))
    g.add((dynamicVehicleProperty, RDFS.label, Literal(VssoConcepts.VEHICLE_PROP_DYN.value, lang="en")))

    staticVehicleProperty = VssoConcepts.VEHICLE_PROP_STAT.uri
    g.add((staticVehicleProperty, RDF.type, OWL.Class))
    g.add((staticVehicleProperty, RDFS.subClassOf, vehicleProperty))
    g.add((staticVehicleProperty, RDFS.label, Literal(VssoConcepts.VEHICLE_PROP_STAT.value, lang="en")))

    numericVehicleProperty = VssoConcepts.VEHICLE_PROP_NUM.uri
    g.add((numericVehicleProperty, RDF.type, OWL.Class))
    g.add((numericVehicleProperty, RDFS.subClassOf, vehicleProperty))
    g.add((numericVehicleProperty, RDFS.label, Literal(VssoConcepts.VEHICLE_PROP_NUM.value, lang="en")))

    enumeratedVehicleProperty = VssoConcepts.VEHICLE_PROP_ENUM.uri
    g.add((enumeratedVehicleProperty, RDF.type, OWL.Class))
    g.add((enumeratedVehicleProperty, RDFS.subClassOf, vehicleProperty))
    g.add((enumeratedVehicleProperty, RDFS.label, Literal(VssoConcepts.VEHICLE_PROP_ENUM.value, lang="en")))

    enumerationValue = VssoConcepts.ENUM_VALUE.uri
    g.add((enumerationValue, RDF.type, OWL.Class))
    g.add((enumerationValue, RDFS.label, Literal(VssoConcepts.ENUM_VALUE.value, lang="en")))

    vehicleComp = VssoConcepts.VEHICLE_COMP.uri
    g.add((vehicleComp, RDF.type, OWL.Class))
    g.add((vehicleComp, RDFS.label, Literal(VssoConcepts.VEHICLE_COMP.value, lang="en")))

    vehicleSignal = VssoConcepts.VEHICLE_SIGNAL.uri
    g.add((vehicleSignal, RDF.type, OWL.Class))
    g.add((vehicleSignal, RDFS.subClassOf, VssoConcepts.VEHICLE_PROP_DYN.uri))
    g.add((vehicleSignal, RDFS.label, Literal(VssoConcepts.VEHICLE_SIGNAL.value, lang="en")))

    vehicleAct = VssoConcepts.VEHICLE_ACT.uri
    g.add((vehicleAct, RDF.type, OWL.Class))
    g.add((vehicleAct, RDFS.subClassOf, VssoConcepts.VEHICLE_PROP_DYN.uri))
    g.add((vehicleAct, RDFS.label, Literal(VssoConcepts.VEHICLE_ACT.value, lang="en")))

    # Datatype extension
    arrayType = VssoConcepts.ARRAY_TYPE.uri
    g.add((arrayType, RDF.type, OWL.Class))
    g.add((arrayType, RDFS.subClassOf, RDFS.Datatype))
    g.add((arrayType, RDFS.label, Literal(VssoConcepts.ARRAY_TYPE.value, lang="en")))

    # Bind the FOAF namespace to a prefix for more readable output
    g.bind("vsso", VssoConcepts.EMPTY.uri)
    g.bind("rdfs", RDFS)
    g.bind("rdf", RDF)
    g.bind("owl", OWL)
    g.bind("skos", SKOS)
    g.bind("schema", SDO)
    g.bind("xsd", XSD)
    g.bind("unit", URIRef(Namespaces["unit"]))
    g.bind("cdt", URIRef(Namespaces["cdt"]))

    # print all the data in the Notation3 format
    print("--- printing mboxes ---")
    print(g.serialize(format='ttl'))

    return g


array_types = {}


def to_array_type(name: str, g: Graph):
    baseuri = DataTypes[name.strip("[]")]
    uri = URIRef(VssoConcepts.EMPTY.uri_string + baseuri.split("#")[1] + "Array")
    if name not in array_types:
        array_types[name] = uri
        g.add((uri, RDF.type, VssoConcepts.ARRAY_TYPE.uri))
        g.add((uri, VssoConcepts.BASE_DATA_TYPE.uri, baseuri))
    return uri


def set_ttl_name(node, name_dict):
    if node.ttl_name:
        return node.ttl_name
    if node.name == "Vehicle":
        ttl_name = "VehicleEntity"
    elif node.parent and node.parent.name != "Vehicle" and name_dict[node.name]>1:
        ttl_name = node.parent.name + node.name
        print(f"** Warning: replace {node.name} with {ttl_name} ({node.qualified_name('.')})")
    else:
        ttl_name = node.name
    node.ttl_name = ttl_name
    return ttl_name


def print_ttl_content(file, tree):
    tree_node: VSSNode
    name_dict = {}
    types = {}
    units = {}
    enums = 0

    graph = setup_graph()

    # iterate once for node names to see which has duplicates for set_ttl_name
    for tree_node in PreOrderIter(tree):
        if tree_node.name not in name_dict:
            name_dict[tree_node.name] =1
        else:
            name_dict[tree_node.name] +=1

    for tree_node in PreOrderIter(tree):

        name = set_ttl_name(tree_node, name_dict)

        name_space = VssoConcepts.EMPTY.uri_string

        node = URIRef(name_space + name)

        # not needed, in case we use classes
        # if VSSType.ATTRIBUTE == tree_node.type:
        #     node = URIRef(f"{VssoConcepts.EMPTY.uri_string}has{name}")

        graph.add((node, RDFS.label, Literal(name, "en")))
        graph.add((node, SKOS.altLabel, Literal(tree_node.qualified_name('.'), "en")))
        graph.add((node, RDFS.comment, Literal(tree_node.description, "en")))

        parent_name_space = VssoConcepts.EMPTY.uri_string

        # branch nodes (incl. instance handling)
        if VSSType.BRANCH == tree_node.type:
            graph.add((node, RDF.type, VssoConcepts.VEHICLE_COMP.uri))
            graph.add((node, VssoConcepts.VEHICLE_COMP_NAME.uri, Literal(name, "en")))
            if tree_node.parent:
                graph.add((node, VssoConcepts.PART_OF_VEH_COMP.uri, URIRef(parent_name_space + set_ttl_name(tree_node.parent, name_dict))))
        # leafs (incl. restrictions)
        else:
            graph.add((node, VssoConcepts.BELONGS_TO.uri, URIRef(parent_name_space + set_ttl_name(tree_node.parent, name_dict))))
            graph.add((node, VssoConcepts.VEHICLE_PROP_NAME.uri, Literal(name, "en")))

            if type(tree_node.data_type)==VSSDataType:
                dt = tree_node.data_type.value
                if "[]" in dt:
                    graph.add((node, VssoConcepts.DATA_TYPE.uri, to_array_type(dt, graph)))
                else:
                    graph.add((node, VssoConcepts.DATA_TYPE.uri, DataTypes[dt]))

            if hasattr(tree_node, "unit"):
                graph.add((node, VssoConcepts.UNIT.uri, DataUnits[tree_node.unit.value]))
                graph.add((node, RDF.type, VssoConcepts.VEHICLE_PROP_NUM.uri))
                if tree_node.unit in units.keys():
                    units[tree_node.unit] += 1
                else:
                    units[tree_node.unit] = 1

            if type(tree_node.enum) == list:
                graph.add((node, RDF.type, VssoConcepts.VEHICLE_PROP_ENUM.uri))
                for item in tree_node.enum:
                    enum_name = tree_node.name + "_" + re.sub(r'[^\w]', '', item)
                    enum_item = URIRef(name_space + enum_name)
                    graph.add((enum_item, RDF.type, VssoConcepts.ENUM_VALUE.uri))
                    graph.add((enum_item, RDFS.label, Literal(item, "en")))
                    graph.add((enum_item, VssoConcepts.ENUM_NAME.uri, Literal(item, "en")))
                    graph.add((node, VssoConcepts.HAS_ENUM_VALUE.uri, enum_item))

            if tree_node.min != "":
                graph.add((node, VssoConcepts.MIN.uri, Literal(tree_node.min, datatype=XSD.int)))

            if tree_node.max != "":
                graph.add((node, VssoConcepts.MAX.uri, Literal(tree_node.max, datatype=XSD.int)))

            if VSSType.ATTRIBUTE == tree_node.type:
                graph.add((node, RDF.type, VssoConcepts.VEHICLE_PROP_STAT.uri))
                graph.add((node, RDFS.label, Literal(tree_node.name, "en")))

            else:

                if tree_node.data_type in types.keys():
                    types[tree_node.data_type] += 1
                else:
                    types[tree_node.data_type] = 1

                graph.add((node, RDF.type, VssoConcepts.VEHICLE_SIGNAL.uri))

                if VSSType.ACTUATOR == tree_node.type:
                    graph.add((node, RDF.type, VssoConcepts.VEHICLE_ACT.uri))

            if tree_node.enum:
                enums += 1

    file.write(graph.serialize(format='ttl'))

    print(name_dict)
    print(types)
    print(units)
    print(enums)


if __name__ == "__main__":
    #
    # Check that we have the correct arguments
    #
    opts, args = getopt.getopt(sys.argv[1:], "I:")

    # Always search current directory for include_file
    include_dirs = ["."]
    for o, a in opts:
        if o == "-I":
            include_dirs.append(a)
        else:
            usage()

    if len(args) != 2:
        usage()

    try:
        tree = vspec.load_tree(args[0], include_dirs, False, expand_inst=False)
        ttl_out = open(args[1], "w")
        print_ttl_content(ttl_out, tree)
        ttl_out.write("\n")
        ttl_out.close()
    except vspec.VSpecError as e:
        print(f"Error: {e}")
        exit(255)
