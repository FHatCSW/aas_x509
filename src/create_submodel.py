import requests
from basyx.aas import model
import json
import basyx.aas.adapter.json
from datetime import datetime

def defineAssetSubmodel(id):
    asset_information = model.AssetInformation(
        asset_kind=model.AssetKind.INSTANCE,
        global_asset_id=f'http://acplt.org/{id}'
    )

    aas_identifier = f'https://acplt.org/{id}AAS'
    digital_identity_aas = model.AssetAdministrationShell(
        id_=aas_identifier,
        asset_information=asset_information
    )

    submodel_identifier = f'https://acplt.org/{id}Submodel'
    digital_identity_submodel = model.Submodel(
        id_=submodel_identifier,
        id_short=id
    )

    return digital_identity_aas, digital_identity_submodel


def convert_to_datetime(value):
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")

def convert_to_boolean(value):
    return bool(value.lower() == "true")

def assembleSubmodel(submodel, json_file_path):
    with open(json_file_path, 'r') as file:
        json_template = json.load(file)
        for entity, properties in json_template.items():
            entity_element_collection = model.SubmodelElementCollection(id_short=entity)

            for prop_name, prop_value in properties.items():
                # Convert property names to camel case (if needed)
                # prop_name_camel_case = ''.join(word.capitalize() for word in prop_name.split('_'))

                # Extract value from dictionary if it's a dictionary
                if isinstance(prop_value, dict):
                    sub_entity_element_collection = model.SubmodelElementCollection(id_short=prop_name)
                    prop = model.Property(id_short="file", value_type=model.datatypes.String,
                                          value=prop_value.get('file', ''))
                    sub_entity_element_collection.add_referable(prop)
                    entity_element_collection.add_referable(sub_entity_element_collection)
                else:
                    # Handle specific property types
                    value_type = model.datatypes.String
                    if prop_name in ["validFrom", "validTill"]:
                        prop_value = convert_to_datetime(prop_value)
                        value_type = model.datatypes.DateTime
                    elif prop_name in ["available"]:
                        prop_value = convert_to_boolean(prop_value)
                        value_type = model.datatypes.Boolean

                    # Add properties to the submodel element collection
                    prop = model.Property(id_short=prop_name, value_type=value_type, value=prop_value)
                    entity_element_collection.add_referable(prop)

            submodel.submodel_element.add(entity_element_collection)

    return submodel

def update_model_type(obj):
    if isinstance(obj, list):
        for i in range(len(obj)):
            obj[i] = update_model_type(obj[i])
        return obj
    elif isinstance(obj, dict):
        if "modelType" in obj:
            if obj["modelType"] == "Property":
                obj["modelType"] = {"name": "Property"}
            elif obj["modelType"] == "SubmodelElementCollection":
                obj["modelType"] = {"name": "SubmodelElementCollection"}
            elif obj["modelType"] == "Submodel":
                obj["modelType"] = {"name": "Submodel"}
        for key, value in obj.items():
            obj[key] = update_model_type(value)
        return obj
    else:
        return obj

def migrateApiV2(json_input):
    obj = json.loads(json_input)
    updated_json = update_model_type(obj)

    identification = {
        "id": "Digital Identity",
        "idType": "IRI",
    }

    updated_json["identification"] = identification

    return updated_json


def update_aas_submodel(id_short, updated_json_string, device_id):
    url = f"http://localhost:4001/aasServer/shells/{device_id}/aas/submodels/{id_short}"

    headers = {
        "Content-Type": "application/json",
    }

    response = requests.put(url, headers=headers, data=updated_json_string)

    print(f"Status Code: {response.status_code}")
    print("Response:")
    print(response.text)

def main(json_template, submodel_id, device_id):

    digital_identity_aas, digital_identity_submodel = defineAssetSubmodel(submodel_id)

    updated_submodel = assembleSubmodel(digital_identity_submodel, json_template)

    submodel_json = json.dumps(updated_submodel, cls=basyx.aas.adapter.json.AASToJsonEncoder, indent=2)

    submodel_json = migrateApiV2(submodel_json)

    updated_json_string = json.dumps(submodel_json, indent=2)

    update_aas_submodel(submodel_id, updated_json_string, device_id)


if __name__ == "__main__":
    submodel_id = "Digitalidentity"
    json_template = 'template.json'
    device_id = "industrial_device"
    main(json_template, submodel_id, device_id)
