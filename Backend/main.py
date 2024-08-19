from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import db_sql
import session_iden

app = FastAPI()
inprogress_orders = {}

@app.post("/")
async def handle_request(request: Request):
    # Retrieve the JSON data from the request
    payload = await request.json()

    # Extract the necessary information from the payload
    # based on the structure of the WebhookRequest from Dialogflow
    intent = payload['queryResult']['intent']['displayName']
    parameters = payload['queryResult']['parameters']
    output_contexts = payload['queryResult']['outputContexts']

    session_id = session_iden.extract_session_id(output_contexts[0]['name'])

    intent_handler_dict = {
        'Add.Order - context ongoing-order': add_to_order,
        #'Remove.Order - context ongoing-order': remove_from_order,
        'Complete.Order - context ongoing-order': complete_order,
        'Tracking.Order.Num - context ongoing-tracking': track_order
    }

    return intent_handler_dict[intent](parameters, session_id)

def add_to_order(parameters: dict,session_id: str):
    item = parameters["Item"]
    quantities = parameters["number"]

    if len(item) != len(quantities):
        fulfillment_text = f"ขอโทษทีค่ะ ฉันไม่เข้าใจสิ่งที่คุณกำลังอธิบาย กรุณาบอกชื่อสินค้าและจำนวนชิ้นให้ชัดเจนด้วยค่ะ"
    else:
        new_item = dict(zip(item, quantities))

        if session_id in inprogress_orders:
            current_item = inprogress_orders[session_id]
            current_item.update(new_item)
            inprogress_orders[session_id] = current_item
        else:
            inprogress_orders[session_id] = new_item

        order_str = session_iden.get_str_from_food_dict(inprogress_orders[session_id])
        fulfillment_text = f"ตอนนี้ในคำสั่งซื้อมีสิ้นค้าดังนี้ {order_str} คุณต้องการอะไรเพิ่มหรือไม่"
    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })

def complete_order(parameters: dict,session_id: str):
    if session_id not in inprogress_orders:
        fulfillment_text = f"ขออภัยด้วยค่ะ ฉันไม่สามารถหา order ของคุณได้ กรุณาทำการสั่งซื้อใหม่ค่ะ"
    else:
        order = inprogress_orders[session_id]
        order_id = saveto_db(order)

        if order_id == -1:
            fulfillment_text = f"ขออภัยด้วยค่ะ ฉันไม่สามารถเตรียมคำสั่งซื้อของคุณได้เนื่องจากเกิดปัญหา กรุณาทำการสั่งซื้อใหม่ค่ะ"

        else:
            order_total = db_sql.get_total_order_price(order_id)
            fulfillment_text = f"เรียบร้อยค่ะ เราได้รับคำสั่งซื้อของคุณแล้ว " \
                f"นี่คือเลข Tracking ID ของคุณ # {order_id}. " \
                f"รวมทั้งหมด {order_total} บาท โดยคุณสามารถจ่ายเงินได้เมื่อของถึงปลายทาง"
    
        return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })


def saveto_db(order: dict):
    next_order_id = db_sql.get_next_order_id()

    for item,quantity in order.items():
        rcode = db_sql.insert_order_item(
            item,
            quantity,
            next_order_id
        )

        if rcode == -1:
            return -1
        
    db_sql.insert_order_tracking(next_order_id, "กำลังดำเนินการ")
        
    return next_order_id

def track_order(parameters: dict,session_id: str):
    order_id = int(parameters['number'])
    order_status = db_sql.get_order_status(order_id)

    if order_status:
        fulfillment_text = f"หมายเลข {order_id} มีสถานะ {order_status}"
    else :
        fulfillment_text = f"ไม่มีหมายเลข {order_id}"

    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })
