import json
import uuid
from datetime import datetime
from typing import Any


def convert_parameter(
    param: dict[str, Any],
    parameter_type: str,
    parent_id: str | None = None,
    tree_level: int = 0,
    tree_sort: int = 0,
) -> dict[str, Any]:
    """Convert a parameter from api_definition format to ToolDefinitionCreate format"""
    is_array = param.get("isArray", "false") == "true"
    tree_leaf = not param.get("properties", [])

    parameter = {
        "parent_id": parent_id,
        "parent_ids": str(parent_id) if parent_id else "",
        "tree_leaf": tree_leaf,
        "tree_level": tree_level,
        "tree_sort": tree_sort,
        "tree_sorts": str(tree_sort),
        "tree_names": param.get("name", param["code"]),
        "code": param["code"],
        "name": param.get("name", param["code"]),
        "value": "",
        "is_required": False,  # Default to False, adjust as needed
        "is_array": is_array,
        "data_type": param["dataType"].lower() if "dataType" in param else "string",
        "default_value": str(param.get("defaultValue", "")),
        "description": param.get("description", ""),
        "sort": tree_sort,
        "parameter_type": parameter_type,
        "parameter_location": None,
        "children": [],
        "id": hash(f"{param['code']}_{tree_level}_{tree_sort}"),  # Simple ID generation
        "function_id": "",
    }

    # Set parameter location if it's an input parameter
    if parameter_type == "input":
        if "location" in param:
            if param["location"] == "header":
                parameter["parameter_location"] = "header"
            elif param["location"] == "query_string":
                parameter["parameter_location"] = "query"
            elif param["location"] == "body":
                parameter["parameter_location"] = "body"

    # Process children recursively
    if "properties" in param:
        for i, child in enumerate(param["properties"], 1):
            child_param = convert_parameter(
                child,
                parameter_type,
                parent_id=parameter["id"],
                tree_level=tree_level + 1,
                tree_sort=i * 1000,  # Scale to allow inserting between items
            )
            parameter["children"].append(child_param)

    return parameter


def convert_api_definition(api_def: dict[str, Any]) -> list[dict[str, Any]]:
    """Convert API definition to ToolDefinitionCreate format"""
    # Create base tool definition
    tool_def = {
        "tool_code": f"tool_{api_def.get('endpoint', 'unknown').replace('/', '_').strip('_')}",
        "tool_type": "api_request",
        "tool_icon": "",
        "tool_name": api_def.get("endpoint", "Unnamed API")
        .split("/")[-1]
        .replace("_", " ")
        .title(),
        "tool_description": api_def.get("description", "No description provided"),
        "status": "1",
        "additional_settings": {
            "source": "swagger",
            "swagger_info": {
                "title": api_def.get("endpoint", "API")
                .split("/")[-1]
                .replace("_", " ")
                .title(),
                "version": "1.0.0",
            },
        },
        "settings": [],
        "functions": [],
    }

    # Add auth settings
    auth_setting = {
        "code": "authType",
        "name": "认证类型",
        "value": api_def.get("authType", "No_Auth"),
        "description": "两层的认证类型，示例：No_Auth、Api_Key、OAuth/Password、OAuth/Client_Credential",
        "type": None,
        "data_type": "string",
        "default_value": api_def.get("authType", "No_Auth"),
        "required": True,
        "sort": 1,
        "status": "1",
        "enum_values": [
            {"label": "No_Auth", "value": "No_Auth", "children": []},
            {"label": "Api_Key", "value": "Api_Key", "children": []},
            {
                "label": "OAuth",
                "value": "OAuth",
                "children": [
                    {"label": "Password", "value": "Password"},
                    {"label": "Client_Credential", "value": "Client_Credential"},
                ],
            },
        ],
        "children": [],
    }

    # Add auth parameters
    for i, auth_param in enumerate(api_def.get("authParams", []), 2):
        param_type = None
        if auth_param.get("location") == "header":
            param_type = "header"
        elif auth_param.get("location") == "query_string":
            param_type = "query_string"

        auth_setting["children"].append(
            {
                "code": auth_param.get("paramKey", ""),
                "name": auth_param.get("paramKey", "").replace("_", " ").title(),
                "value": auth_param.get("paramValue", ""),
                "description": f"{auth_param.get('paramKey', '')} for authentication",
                "type": param_type,
                "data_type": "string",
                "default_value": auth_param.get("paramValue", ""),
                "required": True,
                "sort": i,
                "status": "1",
                "children": [],
            }
        )

    tool_def["settings"].append(auth_setting)

    # Create function
    function = {
        "function_code": f"{api_def['method'].lower()}_{api_def['endpoint'].replace('/', '_').strip('_')}",
        "function_name": api_def.get("description", "Unnamed Function").split("，")[
            0
        ],  # Use first sentence as name
        "function_url": api_def["endpoint"],
        "function_method": api_def["method"],
        "function_description": api_def.get("description", "No description provided"),
        "status": "1",
        "parameters": [],
    }

    # Add headers
    for i, header in enumerate(api_def.get("headers", []), 1):
        param = convert_parameter(header, "input")
        param["parameter_location"] = "header"
        param["sort"] = i
        param["tree_sort"] = i * 1000
        param["tree_sorts"] = str(i * 1000)
        function["parameters"].append(param)

    # Add query params
    for i, param_def in enumerate(api_def.get("params", []), 1):
        param = convert_parameter(param_def, "input")
        param["parameter_location"] = "query"
        param["sort"] = i + len(api_def.get("headers", []))
        param["tree_sort"] = (i + len(api_def.get("headers", []))) * 1000
        param["tree_sorts"] = str((i + len(api_def.get("headers", []))) * 1000)
        function["parameters"].append(param)

    # Add body params
    if "body" in api_def:
        body_param = convert_parameter(api_def["body"], "input")
        body_param["parameter_location"] = "body"
        body_param["sort"] = (
            1 + len(api_def.get("headers", [])) + len(api_def.get("params", []))
        )
        body_param["tree_sort"] = body_param["sort"] * 1000
        body_param["tree_sorts"] = str(body_param["sort"] * 1000)
        function["parameters"].append(body_param)

    # Add response params
    if "result" in api_def:
        result_param = convert_parameter(api_def["result"], "output")
        result_param["sort"] = 1
        result_param["tree_sort"] = 1
        result_param["tree_sorts"] = "1"
        result_param["code"] = "response." + result_param["code"]  # Add response prefix
        function["parameters"].append(result_param)

    tool_def["functions"].append(function)

    return [tool_def]


def add_missing_fields(data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # 生成顶层ID和时间戳
    tool_id = str(uuid.uuid4())
    now = datetime.now().isoformat() + "Z"

    for tool in data:
        # 添加顶层字段
        tool["id"] = tool_id
        tool["created_at"] = now
        tool["updated_at"] = now

        # 处理settings
        if "settings" in tool:
            for setting in tool["settings"]:
                setting_id = str(uuid.uuid4())
                setting["id"] = setting_id
                setting["tool_id"] = tool_id

                # 处理嵌套的children
                if "children" in setting:
                    for child in setting["children"]:
                        child_id = str(uuid.uuid4())
                        child["id"] = child_id
                        child["tool_id"] = tool_id

        # 处理functions
        if "functions" in tool:
            for func in tool["functions"]:
                func_id = str(uuid.uuid4())
                func["id"] = func_id
                func["tool_id"] = tool_id

                # 处理function中的parameters
                if "parameters" in func:
                    for param in func["parameters"]:
                        if "id" not in param or not param["id"]:
                            param["id"] = str(uuid.uuid4())
                        if "function_id" not in param or not param["function_id"]:
                            param["function_id"] = func_id

    return data


def execute_convert_api_definition():
    # Load the API definition
    with open("tests/fixtures/data/api/api_definition.json", encoding="utf-8") as f:
        api_definition = json.load(f)

    # Convert the definition
    tool_definitions = convert_api_definition(api_definition)

    # Save the result
    with open(
        "tests/fixtures/data/api/api_tool_definition.json",
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(tool_definitions, f, ensure_ascii=False, indent=2)

    print(
        "Conversion completed. Output saved to tests/fixtures/data/api/api_tool_definition.json"
    )


def execute_add_missing_fields():
    # 读取原始JSON文件
    with open(
        "tests/fixtures/data/api/api_tool_definition.json", encoding="utf-8"
    ) as f:
        data = json.load(f)

    # 添加缺失的字段
    updated_data = add_missing_fields(data)

    # 保存更新后的JSON文件
    with open(
        "tests/fixtures/data/api/api_tool_definition_updated.json",
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(updated_data, f, ensure_ascii=False, indent=2)

    print(
        "已生成更新后的JSON文件: tests/fixtures/data/api/api_tool_definition_updated.json"
    )


if __name__ == "__main__":
    # execute_convert_api_definition()
    execute_add_missing_fields()
