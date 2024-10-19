'''Synchronous Function Part A'''

# from flask import Flask, request, jsonify
# from flask_cors import CORS
# import time
# import random
# from typing import Dict



# app = Flask(__name__)
# CORS(app)



# def mock_model_predict(input: str) -> Dict[str, str]:
#    time.sleep(random.randint(10, 17)) # Simulate processing delay
#    result = str(random.randint(1000, 20000))
#    output = {"input": input, "result": result}
#    return output

# @app.route('/predict', methods=['POST'])
# def predict():
#   try:
#     data = request.json
#     text_input = data['text']
#     prediction = mock_model_predict(text_input)
#     response = {
#         'prediction': prediction
#     }
#     return jsonify(response),200
#   except Exception as e:
#      return jsonify({"error": str(e)}),500
  

# if __name__ == '__main__':
#     app.run(host='localhost', port=8080,debug=True)

'''Asynchronous Modified version Part B'''

from flask import Flask, request, jsonify
from flask_cors import CORS
import asyncio
import random
import uuid
import json
import redis



app = Flask(__name__)
CORS(app) # help when you are deploying on cloud(Cross Platform)



try:
  
    connection = redis.StrictRedis(host='redis', port=6379, db=0, decode_responses=True) # establish connection with redis at port 6379
    connection.ping() # check for connection 
    print("Connected to Redis successfully!")
except redis.ConnectionError as e:
    print("Could not connect to Redis:", e)
RESULTS_KEY = "prediction" # a key to the redis DB that for this task
async def mock_model_predict(input: str) -> dict: 
    asyncio.sleep(random.randint(10, 17))   
    result = str(random.randint(1000, 20000))
    output = {"input": input, "result": result}
    return output

# route for the prediction
@app.route('/predict', methods=['POST'])
async def predict():
    try:
        
        data = request.json
        text_input = data['text']
        async_mode = request.headers.get('Async-Mode', 'false').lower() == 'true' #if async mode is in header it will return true else return defalt false

        if async_mode:
            #  a unique prediction_id
            prediction_id = str(uuid.uuid4())      
            response = {
                'message': 'Request received. Processing asynchronously',
                'prediction_id': prediction_id
            }
            # immediate response
            asyncio.create_task(process_async_task(text_input, prediction_id)) # create a task and return the immediate response
            return jsonify(response), 202

        else: #if not async mode
            prediction = await mock_model_predict(text_input)
            response = {
                'prediction': prediction
            }
            return jsonify(response), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


async def process_async_task(input_data, prediction_id): #Flask has built in async function 
    connection.hset(RESULTS_KEY, prediction_id, 'on_progress')    #initially it stores on_progress then it override  
    result = await mock_model_predict(input_data) # waiting for the function's result
    connection.hset(RESULTS_KEY, prediction_id, json.dumps(result))
    print(f"Stored result for prediction_id {prediction_id}: {result}")

@app.route('/predict/<prediction_id>', methods=['GET'])
async def get_prediction_result(prediction_id):
    try:
        result = connection.hget(RESULTS_KEY, prediction_id)
        if not result:
            return jsonify({"error": "Prediction ID not found."}), 404
        elif result=='on_progress':
            return jsonify({"error": "Prediction is still being processed"}), 400
            
        else:
            return jsonify({
                "prediction_id": prediction_id,"Output": json.loads(result)}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Run the Flask application
if __name__ == '__main__':
    app.run(host='localhost', port=8080, debug=True)


# I did have taken help from stackoverflow and documentation for redis and docker 
