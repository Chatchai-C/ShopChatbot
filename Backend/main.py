from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import db_sql
app = FastAPI()

@app.post("/")
async def handle_request(request: Request):
    # Retrieve the JSON data from the request
    payload = await request.json()

    # Extract the necessary information from the payload
    # based on the structure of the WebhookRequest from Dialogflow
    intent = payload['queryResult']['intent']['displayName']
    parameters = payload['queryResult']['parameters']
    output_contexts = payload['queryResult']['outputContexts']

    if intent == "Tracking.Order.Num - context ongoing-tracking":
        response = track_order(parameters)
        return response 
        


def track_order(parameters: dict):
    order_id = int(parameters['number'])
    order_status = db_sql.get_order_status(order_id)

    if order_status:
        fulfillment_text = f"หมายเลข {order_id} มีสถานะ {order_status}"
    else :
        fulfillment_text = f"ไม่มีหมายเลข {order_id}"

    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })
