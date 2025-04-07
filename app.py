from flask import Flask, jsonify, request, render_template
import sqlite3
from werkzeug.exceptions import BadRequest

app = Flask(__name__)

# Initialisation de la base de données
def init_db():
    conn = sqlite3.connect('students.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            matricule TEXT PRIMARY KEY,
            nom TEXT NOT NULL,
            prenom TEXT NOT NULL,
            moyenne REAL NOT NULL,
            section TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Calcul de la mention
def calculate_mention(moyenne):
    if moyenne >= 16: return "Très Bien"
    elif moyenne >= 14: return "Bien"
    elif moyenne >= 12: return "Assez Bien"
    elif moyenne >= 10: return "Passable"
    else: return "Insuffisant"

# Routes API
@app.route('/api/students', methods=['GET'])
def get_students():
    section = request.args.get('section')
    conn = sqlite3.connect('students.db')
    cursor = conn.cursor()
    
    if section:
        cursor.execute('SELECT * FROM students WHERE section = ? ORDER BY moyenne DESC', (section,))
    else:
        cursor.execute('SELECT * FROM students ORDER BY moyenne DESC')
    
    students = []
    for row in cursor.fetchall():
        mention = calculate_mention(row[3])
        students.append({
            'matricule': row[0],
            'nom': row[1],
            'prenom': row[2],
            'moyenne': row[3],
            'section': row[4],
            'mention': mention
        })
    
    conn.close()
    return jsonify(students)

@app.route('/api/students/major', methods=['GET'])
def get_major():
    section = request.args.get('section')
    if not section:
        raise BadRequest("Le paramètre 'section' est requis")
    
    conn = sqlite3.connect('students.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM students 
        WHERE section = ? 
        ORDER BY moyenne DESC 
        LIMIT 1
    ''', (section,))
    
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return jsonify({'error': 'Aucun étudiant trouvé'}), 404
    
    mention = calculate_mention(row[3])
    return jsonify({
        'matricule': row[0],
        'nom': row[1],
        'prenom': row[2],
        'moyenne': row[3],
        'section': row[4],
        'mention': mention
    })

@app.route('/api/students/count/bien', methods=['GET'])
def count_bien():
    conn = sqlite3.connect('students.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM students WHERE moyenne >= 14 AND moyenne < 16')
    count = cursor.fetchone()[0]
    conn.close()
    return jsonify({'count': count})

@app.route('/api/students/passable', methods=['DELETE'])
def delete_passable():
    conn = sqlite3.connect('students.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM students WHERE moyenne >= 10 AND moyenne < 12')
    affected_rows = cursor.rowcount
    conn.commit()
    conn.close()
    return jsonify({'deleted': affected_rows})

@app.route('/api/students', methods=['POST'])
def add_student():
    data = request.json
    required_fields = ['matricule', 'nom', 'prenom', 'moyenne', 'section']
    
    if not all(field in data for field in required_fields):
        raise BadRequest("Tous les champs sont requis")
    
    try:
        conn = sqlite3.connect('students.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO students (matricule, nom, prenom, moyenne, section)
            VALUES (?, ?, ?, ?, ?)
        ''', (data['matricule'], data['nom'], data['prenom'], float(data['moyenne']), data['section']))
        conn.commit()
        conn.close()
        return jsonify({'success': True}), 201
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Matricule déjà existant'}), 400

# Route pour l'interface
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    init_db()
    app.run(debug=True)