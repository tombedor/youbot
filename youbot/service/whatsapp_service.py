from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def handle_requests():
    if request.method == 'POST':
        data = request.get_json()
        # Process the data as needed
        return jsonify({'message': 'POST request received', 'received_data': data}), 200
    else:
        return jsonify({'message': 'GET request received'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)