claude_4_sonnet_models = [   # Sonnet 4
    {
        "bedrock_region": "ap-northeast-2", 
        "model_type": "claude",
        "model_id": "apac.anthropic.claude-sonnet-4-20250514-v1:0"
    }
]

claude_3_7_sonnet_models = [   # Sonnet 3.7
    {
        "bedrock_region": "ap-northeast-2", 
        "model_type": "claude",
        "model_id": "apac.anthropic.claude-3-7-sonnet-20250219-v1:0"
    }
]

claude_3_5_sonnet_v2_models = [   # Sonnet 3.5 V1
    {
        "bedrock_region": "ap-northeast-2", 
        "model_type": "claude",
        "model_id": "anthropic.claude-3-5-sonnet-20241022-v2:0"
    }
]

claude_3_5_sonnet_v1_models = [   # Sonnet 3.5 V2
    {
        "bedrock_region": "ap-northeast-2", 
        "model_type": "claude",
        "model_id": "anthropic.claude-3-5-sonnet-20240620-v1:0"
    }
]

claude_3_0_sonnet_models = [   # Sonnet 3.0
    {
        "bedrock_region": "ap-northeast-2", 
        "model_type": "claude",
        "model_id": "apac.anthropic.claude-3-sonnet-20240229-v1:0"
    }
]

def get_model_info(model_name):
    models = []

    if model_name == "Claude 3.7 Sonnet":
        models = claude_3_7_sonnet_models
    elif model_name == "Claude 3.0 Sonnet":
        models = claude_3_0_sonnet_models
    elif model_name == "Claude 3.5 Sonnet":
        models = claude_3_5_sonnet_v2_models
    elif model_name == "Claude 4 Sonnet":
        models = claude_4_sonnet_models

    return models

STOP_SEQUENCE_CLAUDE = "\n\nHuman:" 
STOP_SEQUENCE_NOVA = '"\n\n<thinking>", "\n<thinking>", " <thinking>"'

def get_stop_sequence(model_name):
    models = get_model_info(model_name)

    model_type = models[0]["model_type"]

    if model_type == "claude":
        return STOP_SEQUENCE_CLAUDE
    elif model_type == "nova":
        return STOP_SEQUENCE_NOVA
    else:
        return ""
