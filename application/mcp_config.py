import logging
import sys
import utils
import os
import json
import boto3

logging.basicConfig(
    level=logging.INFO,  # Default to INFO level
    format='%(filename)s:%(lineno)d | %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger("mcp-config")

script_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(script_dir, "config.json")

config = utils.load_config()
logger.info(f"config: {config}")

region = config["region"] if "region" in config else "us-west-2"
projectName = config["projectName"] if "projectName" in config else "mcp"
workingDir = os.path.dirname(os.path.abspath(__file__))
# 상위 디렉토리의 contents 폴더 경로 추가
parent_dir = os.path.dirname(workingDir)
contents_dir = os.path.join(parent_dir, "contents")
logger.info(f"workingDir: {workingDir}")
logger.info(f"contents_dir: {contents_dir}")

mcp_user_config = {}    

def get_secret_value(secret_name):
    session = boto3.Session()
    client = session.client('secretsmanager', region_name=region)
    
    try:
        response = client.get_secret_value(SecretId=secret_name)
        return response['SecretString']
    except client.exceptions.ResourceNotFoundException:
        logger.info(f"Secret not found, creating new secret: {secret_name}")
        try:
            # Create secret value with bearer_key 
            secret_value = {
                "key": secret_name,
                "value": "need to update"
            }
            
            # Convert to JSON string
            secret_string = json.dumps(secret_value)

            client.create_secret(
                Name=secret_name,
                SecretString=secret_string,  
                Description=f"secret key and token for {secret_name}"
            )
            logger.info(f"Secret created: {secret_name}. Please update it with the actual value.")
            return None
        except Exception as create_error:
            logger.error(f"Failed to create secret: {create_error}")
            return None
    except Exception as e:
        logger.error(f"Error getting secret value: {e}")
        return None

def load_config(mcp_type):
    if mcp_type == "code interpreter":
        mcp_type = "repl_coder"
    elif mcp_type == "knowledge base":
        mcp_type = "kb-retriever"
    elif mcp_type == "AWS Sentral (Employee)":
        mcp_type = "aws_sentral"
    elif mcp_type == "AWS Outlook (Employee)":
        mcp_type = "aws_outlook"

    if mcp_type == "basic":
        return {
            "mcpServers": {
                "search": {
                    "command": "python",
                    "args": [
                        f"{workingDir}/mcp_server_basic.py"
                    ]
                }
            }
        }
    
    elif mcp_type == "tavily":
        return {
            "mcpServers": {
                "tavily-search": {
                    "command": "python",
                    "args": [
                        f"{workingDir}/mcp_server_tavily.py"
                    ]
                }
            }
        }
        
    elif mcp_type == "use-aws": 
        return {
            "mcpServers": {
                "use-aws": {
                    "command": "python",
                    "args": [
                        f"{workingDir}/mcp_server_use_aws.py"
                    ]
                }
            }
        }
    
    elif mcp_type == "kb-retriever":
        return {
            "mcpServers": {
                "kb_retriever": {
                    "command": "python",
                    "args": [f"{workingDir}/mcp_server_retrieve.py"]
                }
            }
        }
    
    elif mcp_type == "repl_coder":
        return {
            "mcpServers": {
                "repl_coder": {
                    "command": "python",
                    "args": [
                        f"{workingDir}/mcp_server_repl_coder.py"
                    ]
                }
            }
        }    

    elif mcp_type == "terminal (MAC)":
        return {
            "mcpServers": {
                "iterm-mcp": {
                    "command": "npx",
                    "args": [
                        "-y",
                        "iterm-mcp"
                    ]
                }
            }
        }
    
    elif mcp_type == "terminal (linux)":
        return {
            "mcpServers": {
                "terminal-control": {
                    "command": "terminal-control-mcp",
                    "args": [],
                    "env": {
                        "TERMINAL_CONTROL_SECURITY_LEVEL": "low"  # "off", "low", "medium", "high" 중 선택
                    }
                }
            }
        }    
    
    elif mcp_type == "filesystem":
        parent_dir = os.path.dirname(workingDir)
        contents_dir = os.path.join(parent_dir, "contents")
        return {
            "mcpServers": {
                "filesystem": {
                    "command": "npx",
                    "args": [
                        "-y",
                        "@modelcontextprotocol/server-filesystem",
                        f"{parent_dir}",
                        f"{workingDir}",
                        f"{contents_dir}"
                    ]
                }
            }
        }    
    
    elif mcp_type == "aws_documentation":
        return {
            "mcpServers": {
                "awslabs.aws-documentation-mcp-server": {
                    "command": "uvx",
                    "args": ["awslabs.aws-documentation-mcp-server@latest"],
                    "env": {
                        "FASTMCP_LOG_LEVEL": "ERROR"
                    }
                }
            }
        }

    elif mcp_type == "trade_info":
        return {
            "mcpServers": {
                "trade_info": {
                    "command": "python",
                    "args": [
                        f"{workingDir}/mcp_server_trade_info.py"
                    ]
                }
            }
        }
        
    elif mcp_type == "drawio":
        return {
            "mcpServers": {
                "drawio": {
                "command": "npx",
                "args": ["@drawio/mcp"]
                }
            }
        }
    
    elif mcp_type == "web_fetch":
        return {
            "mcpServers": {
                "web_fetch": {
                    "command": "npx",
                    "args": ["-y", "mcp-server-fetch-typescript"]
                }
            }
        }
    
    elif mcp_type == "text_extraction":
        return {
            "mcpServers": {
                "text_extraction": {
                    "command": "python",
                    "args": [f"{workingDir}/mcp_server_text_extraction.py"]
                }
            }
        }

    elif mcp_type == "outlook":
        secret_name = f"outlook-mcp-user-email"
        secret_value = json.loads(get_secret_value(secret_name))
        OUTLOOK_MCP_USER_EMAIL = secret_value['value']
        if not OUTLOOK_MCP_USER_EMAIL:
            logger.info(f"No outlook user email found in secret manager")
            return {}
        else:
            logger.info(f"outlook user email: {OUTLOOK_MCP_USER_EMAIL}")
            return {
                "mcpServers": {
                    "outlook": {
                        "command": f"{workingDir}/outlook-mac/outlook_mcp.py",
                        "env":{
                            "USER_EMAIL":OUTLOOK_MCP_USER_EMAIL,
                            "OUTLOOK_MCP_LOG_LEVEL":"INFO"
                        }
                    }
                }
            }
    
    elif mcp_type == "notion":
        return {
            "mcpServers": {
                "notionApi": {
                    "command": "npx",
                    "args": ["-y", "@notionhq/notion-mcp-server"],
                    "env": {
                        "NOTION_TOKEN": utils.notion_api_key
                    }
                }
            }
        }   

    elif mcp_type == "slack":
        return {
            "mcpServers": {
                "slack": {
                    "command": "npx",
                    "args": [
                        "-y",
                        "@modelcontextprotocol/server-slack"
                    ],
                    "env": {
                        "SLACK_BOT_TOKEN": os.environ["SLACK_BOT_TOKEN"],
                        "SLACK_TEAM_ID": os.environ["SLACK_TEAM_ID"]
                    }
                }
            }
        }

    elif mcp_type == "gog":
        return {
            "mcpServers": {
                "gog": {
                    "command": "python",
                    "args": [f"{workingDir}/mcp_server_gog.py"]
                }
            }
        }

    elif mcp_type == "aws_sentral":
        return {
            "mcpServers": {
                "aws_sentral": {
                "command": os.path.expanduser("~/.toolbox/bin/aws-sentral-mcp"),
                "args": []
                }
            }
        }

    elif mcp_type == "aws_outlook":
        return {
            "mcpServers": {
                "aws_outlook": {
                    "command": os.path.expanduser("~/.toolbox/bin/aws-outlook-mcp"),
                    "args": []
                }
            }
        }   

    elif mcp_type == "사용자 설정":
        return mcp_user_config

def load_selected_config(mcp_servers: dict):
    logger.info(f"mcp_servers: {mcp_servers}")
    
    loaded_config = {}
    for server in mcp_servers:
        config = load_config(server)
        if config:
            loaded_config.update(config["mcpServers"])
    return {
        "mcpServers": loaded_config
    }