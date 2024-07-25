from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(filename='/var/log/server-monitor-app.log', level=logging.INFO,
                    format='%(asctime)s %(levelname)s:%(message)s')

app = Flask(__name__)
app.config.from_object('config.Config')

db = SQLAlchemy(app)

class AgentData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    server_name = db.Column(db.String(50))  # Removed unique constraint
    server_ip = db.Column(db.String(15), unique=True)  # Make server_ip unique
    network_status = db.Column(db.String(10))
    cpu_usage = db.Column(db.Float)
    memory_usage = db.Column(db.Float)
    disk_usage = db.Column(db.Float)

@app.route('/api/agent', methods=['POST'])
def receive_agent_data():
    try:
        data = request.json
        existing_server = AgentData.query.filter_by(server_ip=data['server_ip']).first()
        if existing_server:
            # Update existing server's status
            existing_server.server_name = data['server_name']
            existing_server.network_status = data['network_status']
            existing_server.cpu_usage = data['cpu_usage']
            existing_server.memory_usage = data['memory_usage']
            existing_server.disk_usage = data['disk_usage']
            existing_server.timestamp = datetime.utcnow()
            db.session.commit()
            logging.info(f"Updated data for server: {data['server_ip']}")
        else:
            # Add new server
            new_data = AgentData(
                server_name=data['server_name'],
                server_ip=data['server_ip'],
                network_status=data['network_status'],
                cpu_usage=data['cpu_usage'],
                memory_usage=data['memory_usage'],
                disk_usage=data['disk_usage']
            )
            db.session.add(new_data)
            db.session.commit()
            logging.info(f"Received data: {data}")
        return jsonify({'message': 'Data received'}), 201
    except Exception as e:
        logging.error(f"Error processing request: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500

@app.route('/api/agent/<int:id>', methods=['GET'])
def get_agent_data(id):
    data = AgentData.query.get_or_404(id)
    result = {
        'timestamp': data.timestamp,
        'server_name': data.server_name,
        'server_ip': data.server_ip,
        'network_status': data.network_status,
        'cpu_usage': data.cpu_usage,
        'memory_usage': data.memory_usage,
        'disk_usage': data.disk_usage
    }
    return jsonify(result)

@app.route('/api/servers', methods=['GET'])
def get_servers():
    # Query all data and sort by timestamp in descending order
    servers = AgentData.query.order_by(AgentData.timestamp.desc()).all()
    seen_ips = set()
    unique_servers = []
    for server in servers:
        if server.server_ip not in seen_ips:
            seen_ips.add(server.server_ip)
            unique_servers.append(server)

    result = [
        {
            'id': server.id,
            'server_name': server.server_name,
            'server_ip': server.server_ip,
            'network_status': server.network_status,
            'cpu_usage': server.cpu_usage,
            'memory_usage': server.memory_usage,
            'disk_usage': server.disk_usage,
        }
        for server in unique_servers
    ]
    return jsonify(result)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000)
