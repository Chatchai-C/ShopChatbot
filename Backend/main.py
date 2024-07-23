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

    intent_handler_dict = {
        'Add.Order - context ongoing-order': add_to_order,
        #'Remove.Order - context ongoing-order': remove_from_order,
        #'Complete.Order - context ongoing-order': complete_order,
        'Tracking.Order.Num - context ongoing-tracking': track_order
    }

    return intent_handler_dict[intent](parameters)

def add_to_order(parameters: dict):
    item = parameters["Item"]
    quantities = parameters["number"]

    if len(item) != len(quantities):
        fulfillment_text = f"ขอโทษทีค่ะ ฉันไม่เข้าใจสิ่งที่คุณกำลังอธิบาย กรุณาบอกชื่อสินค้าและจำนวนชิ้นด้วยค่ะ"
    else:
        fulfillment_text = f"{item} และ {quantities} in backend"
    
    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })

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
