from fastapi import FastAPI
from src.dtos.ISayHelloDto import ISayHelloDto
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import JSONResponse
import configparser
from typing import List, Optional
import json
from pydantic import BaseModel
from types import SimpleNamespace

# Import your Graph class
from configparser import SectionProxy
from azure.identity import DeviceCodeCredential
from msgraph import GraphServiceClient
from msgraph.generated.users.item.user_item_request_builder import UserItemRequestBuilder
from msgraph.generated.users.item.mail_folders.item.messages.messages_request_builder import MessagesRequestBuilder
from msgraph.generated.users.item.send_mail.send_mail_post_request_body import SendMailPostRequestBody
from msgraph.generated.models.message import Message
from msgraph.generated.models.item_body import ItemBody
from msgraph.generated.models.body_type import BodyType
from msgraph.generated.models.recipient import Recipient
from msgraph.generated.models.email_address import EmailAddress
from msgraph.generated.models.o_data_errors.o_data_error import ODataError
from contextlib import redirect_stdout
import io


app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}


@app.post("/hello")
async def hello_message(dto: ISayHelloDto):
    return {"message": f"Hello {dto.message}"}

class Graph:
    settings: SectionProxy
    device_code_credential: DeviceCodeCredential
    user_client: GraphServiceClient

    def __init__(self, config: SectionProxy):
        self.settings = config
        client_id = self.settings['clientId']
        tenant_id = self.settings['tenantId']
        graph_scopes = self.settings['graphUserScopes'].split(' ')

        self.device_code_credential = DeviceCodeCredential(client_id, tenant_id=tenant_id)
        self.user_client = GraphServiceClient(self.device_code_credential, graph_scopes)

    async def get_user_token(self):
        graph_scopes = self.settings['graphUserScopes']
        access_token = self.device_code_credential.get_token(graph_scopes)
        return access_token.token

    async def get_user(self):
        query_params = UserItemRequestBuilder.UserItemRequestBuilderGetQueryParameters(
            select=['displayName', 'mail', 'userPrincipalName']
        )
    
        request_config = UserItemRequestBuilder.UserItemRequestBuilderGetRequestConfiguration(
            query_parameters=query_params
        )
    
        user = await self.user_client.me.get(request_configuration=request_config)
        return user
        
    async def make_graph_call(self):
        
        result = await self.user_client.drives.by_drive_id('b!Z6EVscpHQEa9NYpEGca-3TCUyTn_KBVDqRpPGBVbP-4bdxAn1NAFRqS9njceDBLv').items.by_drive_item_id('01LC476HLXFFRL5MXOCRHKZ4ZQ6GGE3LQE').children.get()
        #print(result)
        d = await self.user_client.drives.by_drive_id('b!Z6EVscpHQEa9NYpEGca-3TCUyTn_KBVDqRpPGBVbP-4bdxAn1NAFRqS9njceDBLv').items.by_drive_item_id('01LC476HKOFRDFH4JBEVGLPU6FVYKCE376').get()
        print(d)
        return result
        
    async def make_graph_call_content(self,item_id):
        
        result = await self.user_client.drives.by_drive_id('b!Z6EVscpHQEa9NYpEGca-3TCUyTn_KBVDqRpPGBVbP-4bdxAn1NAFRqS9njceDBLv').items.by_drive_item_id(item_id).get()
        #print(result)
        result = {"url":result.additional_data}
        return result
        
    async def list_inbox(self):
        # Implement inbox listing functionality
        try:
            query_params = MessagesRequestBuilder.MessagesRequestBuilderGetQueryParameters(
                select=['subject', 'receivedDateTime', 'from'],
                top=25,
                order_by=['receivedDateTime DESC']
            )
            
            request_config = MessagesRequestBuilder.MessagesRequestBuilderGetRequestConfiguration(
                query_parameters=query_params
            )
            
            messages = await self.user_client.me.mail_folders.by_mail_folder_id('inbox').messages.get(
                request_configuration=request_config
            )
            return messages
        except Exception as e:
            raise Exception(f"Error listing inbox: {str(e)}")

    async def send_email(self, subject: str, body: str, to_recipients: List[str]):
        try:
            message = Message()
            message.subject = subject
            
            message.body = ItemBody()
            message.body.content_type = BodyType.HTML
            message.body.content = body
            
            message.to_recipients = []
            for email in to_recipients:
                recipient = Recipient()
                recipient.email_address = EmailAddress()
                recipient.email_address.address = email
                message.to_recipients.append(recipient)
                
            request_body = SendMailPostRequestBody()
            request_body.message = message
            
            await self.user_client.me.send_mail.post(request_body)
            return True
        except Exception as e:
            raise Exception(f"Error sending email: {str(e)}")

# Global Graph client (initialized before FastAPI starts)
graph_client = None

# Pydantic models for request/response validation
class UserInfo(BaseModel):
    display_name: Optional[str] = None
    email: Optional[str] = None
    user_principal_name: Optional[str] = None

class EmailRequest(BaseModel):
    subject: str
    body: str
    to_recipients: List[str]

# Initialize Graph client and authenticate
async def initialize_graph():
    try:
        # Load settings
        # config = configparser.ConfigParser()
        # config.read(['config.cfg', 'config.dev.cfg'])
        # azure_settings = config['azure']
        azure_settings = {
            'clientId': '0e8e54e4-c386-4a78-a465-5d9f7aaf376d',
            'tenantId': 'a2f14507-fab7-4185-9f8d-bbb265ce04e5',
            'graphUserScopes': 'Files.Read'
        }
        
        # Convert to object with attribute access
        settings = SimpleNamespace(**azure_settings)
        client = Graph(settings)
        
        # # Force authentication by getting a token
        # token = await client.get_user_token()
        # print("Authentication successful. Token acquired.")
        
        # # Get user info to verify connection
        # user = await client.get_user()
        # print(f"Connected as: {user.display_name} ({user.mail or user.user_principal_name})")
        
        return client
    except Exception as e:
        print(f"Error during authentication: {str(e)}")
        raise e

# Dependency to get Graph client
def get_graph():
    global graph_client
    if graph_client is None:
        raise HTTPException(status_code=500, detail="Graph client not initialized")
    return graph_client

# Handle OData errors in a consistent way
def handle_odata_error(e: ODataError):
    if e.error:
        detail = f"{e.error.code}: {e.error.message}"
    else:
        detail = str(e)
    return HTTPException(status_code=400, detail=detail)

def parse_drive_item_response(response):
    """
    Parse a DriveItemCollectionResponse object from Microsoft Graph into a 
    JSON-serializable format.
    
    Args:
        response: DriveItemCollectionResponse object from Microsoft Graph
        
    Returns:
        dict: JSON-serializable dictionary with the parsed response
    """
    # Create base structure with metadata
    result = {
        "context": response.additional_data.get('@odata.context'),
        "nextLink": response.odata_next_link,
        "count": response.odata_count,
        "items": []
    }
    
    # Process each drive item in the collection
    for item in response.value:
        # Extract all properties from additional_data
        item_data = {}
        if hasattr(item, 'additional_data') and item.additional_data:
            item_data.update(item.additional_data)
        
        # Extract all standard properties from the DriveItem object
        standard_properties = [
            'id', 'name', 'size', 'web_url', 'created_date_time', 
            'last_modified_date_time', 'file', 'folder', 'parent_reference'
        ]
        
        for prop in standard_properties:
            if hasattr(item, prop) and getattr(item, prop) is not None:
                prop_value = getattr(item, prop)
                
                # Handle nested objects
                if hasattr(prop_value, 'to_dict'):
                    item_data[prop] = prop_value.to_dict()
                else:
                    item_data[prop] = prop_value
        
        # Add to items list
        result["items"].append(item_data)
    
    return result
    
# # Create FastAPI app
# app = FastAPI(title="Microsoft Graph API", 
#               description="A REST API for Microsoft Graph integration",
#               version="1.0.0")

# API endpoints
@app.get("/")
async def root():
    return {"message": "Microsoft Graph API"}

@app.get("/token", response_model=dict)
async def get_token(graph: Graph = Depends(get_graph)):
    try:
        token = await graph.get_user_token()
        return {"token": token}
    except ODataError as e:
        raise handle_odata_error(e)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/me", response_model=UserInfo)
async def get_me(graph: Graph = Depends(get_graph)):
    try:
        user = await graph.get_user()
        return {
            "display_name": user.display_name,
            "email": user.mail,
            "user_principal_name": user.user_principal_name
        }
    except ODataError as e:
        raise handle_odata_error(e)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


        
@app.get("/drive-contents")
async def get_drive_contents(graph: Graph = Depends(get_graph)):
    try:
        result = await graph.make_graph_call()
        #print(result)
        #parsed_response = parse_drive_item_response(result)
        
        # Convert the result to a JSON-serializable format
        return {"items": [{"id":item.id,"name":item.name} for item in result.value]}
    except ODataError as e:
        raise handle_odata_error(e)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/content/{item_id}")
async def get_drive_contents(item_id: str, graph: Graph = Depends(get_graph)):
    try:
        # Use the item_id in your graph call
        result = await graph.make_graph_call_content(item_id=item_id)
        return result
    except ODataError as e:
        raise handle_odata_error(e)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
@app.get("/inbox")
async def get_inbox(graph: Graph = Depends(get_graph)):
    try:
        messages = await graph.list_inbox()
        # Convert to a serializable format
        return {"messages": [msg.to_dict() for msg in messages.value]}
    except ODataError as e:
        raise handle_odata_error(e)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/send-email")
async def send_email(email: EmailRequest, graph: Graph = Depends(get_graph)):
    try:
        result = await graph.send_email(
            subject=email.subject,
            body=email.body,
            to_recipients=email.to_recipients
        )
        return {"message": "Email sent successfully"}
    except ODataError as e:
        raise handle_odata_error(e)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/init")
async def root_init():
    global graph_client
    graph_client = await initialize_graph()
    return {"message": "initialized"}
    
# global graph_client
# # Initialize Graph client once
# graph_client = await initialize_graph()
