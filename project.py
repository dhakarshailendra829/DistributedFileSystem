from flask import Flask, request, jsonify
import hashlib

app = Flask(__name__)

# Simulated distributed storage
STORAGE_NODES = {
    "node1": {},
    "node2": {},
    "node3": {},
    "node4": {},
    "node5": {}
}

REPLICATION_FACTOR = 2  # Backup copies

# Function to generate file hash
def generate_hash(file_data):
    return hashlib.sha256(file_data).hexdigest()

# Upload a file and split into chunks
@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    filename = file.filename
    file_data = file.read()
    chunk_size = len(file_data) // 3
    chunks = [file_data[i * chunk_size:(i + 1) * chunk_size] for i in range(3)]
    
    for i, chunk in enumerate(chunks):
        primary_node = f"node{i+1}"
        STORAGE_NODES[primary_node][f"{filename}_chunk{i}"] = chunk
        
        # Replication
        backup_node = f"node{(i+1) % 3 + 1}"
        STORAGE_NODES[backup_node][f"{filename}_chunk{i}_backup"] = chunk
    
    return jsonify({"message": "File uploaded successfully!", "filename": filename})

# Upload multiple files
@app.route('/upload_multiple', methods=['POST'])
def upload_multiple():
    files = request.files.getlist('files')
    if not files:
        return jsonify({"error": "No files provided"}), 420
    
    uploaded_files = []
    for file in files:
        request.files = {'file': file}
        upload()
        uploaded_files.append(file.filename)
    
    return jsonify({"message": "Multiple files uploaded!", "files": uploaded_files})

# Download file
@app.route('/download/<filename>', methods=['GET'])
def download(filename):
    chunks = []
    for i in range(3):
        primary_node = f"node{i+1}"
        chunk_key = f"{filename}_chunk{i}"
        
        if chunk_key in STORAGE_NODES[primary_node]:
            chunks.append(STORAGE_NODES[primary_node][chunk_key])
        else:
            return jsonify({"error": f"Chunk {i} missing!"}), 500
    
    file_data = b''.join(chunks)
    return jsonify({"filename": filename, "data": file_data.decode()})

# Recover missing chunks
@app.route('/recover/<filename>', methods=['GET'])
def recover(filename):
    recovered_chunks = 0
    for i in range(3):
        primary_node = f"node{i+1}"
        chunk_key = f"{filename}_chunk{i}"
        backup_key = f"{filename}_chunk{i}_backup"
        
        if chunk_key not in STORAGE_NODES[primary_node]:
            backup_node = f"node{(i+1) % 3 + 1}"
            if backup_key in STORAGE_NODES[backup_node]:
                STORAGE_NODES[primary_node][chunk_key] = STORAGE_NODES[backup_node][backup_key]
                recovered_chunks += 1
    
    return jsonify({"message": f"{recovered_chunks} chunks recovered!"})

# Delete a file
@app.route('/delete/<filename>', methods=['DELETE'])
def delete(filename):
    deleted_chunks = 0
    for node in STORAGE_NODES:
        for key in list(STORAGE_NODES[node].keys()):
            if filename in key:
                del STORAGE_NODES[node][key]
                deleted_chunks += 1
    
    return jsonify({"message": f"Deleted {deleted_chunks} chunks of {filename}"})

# List all files
@app.route('/list_files', methods=['GET'])
def list_files():
    files = set()
    for node in STORAGE_NODES:
        files.update(key.split("_chunk")[0] for key in STORAGE_NODES[node].keys())
    return jsonify({"files": list(files)})

# Load balancing
@app.route('/balance_load', methods=['GET'])
def balance_load():
    node_sizes = {node: sum(len(data) for data in STORAGE_NODES[node].values()) for node in STORAGE_NODES}
    max_node = max(node_sizes, key=node_sizes.get)
    min_node = min(node_sizes, key=node_sizes.get)
    
    if node_sizes[max_node] - node_sizes[min_node] > 500:
        chunk_to_move = list(STORAGE_NODES[max_node].keys())[0]
        STORAGE_NODES[min_node][chunk_to_move] = STORAGE_NODES[max_node].pop(chunk_to_move)
        return jsonify({"message": f"Chunk {chunk_to_move} moved from {max_node} to {min_node}!"})
    
    return jsonify({"message": "Load is balanced!"})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000, debug=True)
