from flask import Flask, abort, jsonify
from flask_cors import CORS
import json

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

def read_data():
    with open('data.json') as json_file:
        datas = json.load(json_file)
    return datas

#initialize the data with the file data
datas = read_data()

@app.errorhandler(404)
def resource_not_found(e):
    return jsonify(error=str(e)), 404

@app.route('/')
def hello_world():
    return 'Hello to POPS Validator data API endpoint!'

@app.route('/networks/harmony')
def harmony_data():
    try:
        datas = read_data()
        return datas["networks"][0]
    except:
        abort(404, description="Harmony ressource not found")

@app.route('/networks/solana')
def solana_data():
    try:
        datas = read_data()
        return datas["networks"][1]
    except:
        abort(404, description="Solana ressource not found")

@app.route('/networks/avalanche')
def avalanche_data():
    try:
        datas = read_data()
        return datas["networks"][2]
    except:
        abort(404, description="Avalanche ressource not found")

@app.route('/networks/thegraph')
def thegraph_data():
    try:
        datas = read_data()
        return datas["networks"][3]
    except:
        abort(404, description="The Graph ressource not found")

@app.route('/networks/stafi')
def stafi_data():
    try:
        datas = read_data()
        return datas["networks"][4]
    except:
        abort(404, description="Stafi ressource not found")

@app.route('/global/akash')
def akash_data():
    try:
        datas = read_data()
        return datas["networks"][5]
    except:
        abort(404, description="Akash resource not found")

@app.route('/networks_total_delegation')
def networks_total_delegation():
    try:
        datas = read_data()
        return jsonify(datas["global"]["networks_total_delegation"])
    except:
        abort(404, description="Error reading networks_total_delegation")
      
@app.route('/networks')
def all():
    try:
        datas = read_data()["networks"]
        response = jsonify(datas)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return jsonify(datas)
    except:
        abort(404, description="Networks ressource not found")

