from flask import Flask, render_template, jsonify, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)

# Configure SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy with the app
db = SQLAlchemy(app)

product_controls = db.Table('product_controls',
    db.Column('product_id', db.Integer, db.ForeignKey('products.id'), primary_key=True),
    db.Column('control_id', db.Integer, db.ForeignKey('controls.id'), primary_key=True)
)

# Define Control Model
class Control(db.Model):
    __tablename__ = 'controls'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    
# Define Product model
class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    vendor = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    business_unit = db.Column(db.String(50), nullable=False)
    app_owner = db.Column(db.String(50), nullable=True)
    licensed_users = db.Column(db.Float, nullable=False)
    data_sources = db.Column(db.String(200), nullable=False)
    risk_score = db.Column(db.Float, nullable=False)
    data_privacy_status = db.Column(db.String(50), nullable=False)
    explainability = db.Column(db.String(50), nullable=False)
    cost_monthly = db.Column(db.Float, nullable=False)
    foundation_model = db.Column(db.String(50), nullable=False)
    data_ownership = db.Column(db.String(50), nullable=False)
    nth_party_risk = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    controls = db.relationship('Control', secondary=product_controls, backref=db.backref('products', lazy='dynamic'))

# Create the database and tables
with app.app_context():
    db.create_all()



@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/products', methods=['GET'])
def get_products():
    products = Product.query.all()
    product_list = []
    for product in products:
        product_dict = {
            'id': product.id,
            'name': product.name,
            'vendor': product.vendor,
            'category': product.category,
            'business_unit': product.business_unit,
            'app_owner': product.app_owner,
	    'licensed_users': product.licensed_users,
            'data_sources': product.data_sources,
            'risk_score': product.risk_score,
            'data_privacy_status': product.data_privacy_status,
            'explainability': product.explainability,
            'cost_monthly': product.cost_monthly,
            'foundation_model': product.foundation_model,
            'data_ownership': product.data_ownership,
            'nth_party_risk': product.nth_party_risk,
            'status': product.status,
            'last_updated': product.last_updated.isoformat()
        }
        product_list.append(product_dict)
    return jsonify(product_list)

@app.route('/api/kpi', methods=['GET'])
def get_kpi():
    total_integrations = Product.query.count()
    high_risk_count = Product.query.filter(Product.risk_score > 7).count()
    monthly_costs = [product.cost_monthly for product in Product.query.all()]
    total_monthly_costs = sum(monthly_costs)

    # Calculate average risk score
    risk_scores = [product.risk_score for product in Product.query.all()]
    avg_risk_score = sum(risk_scores) / len(risk_scores)

    kpi_data = {
        'total_integrations': total_integrations,
        'high_risk_count': high_risk_count,
        'avg_risk_score': avg_risk_score,
	'total_monthly_costs': total_monthly_costs
    }

    return jsonify(kpi_data)

@app.route('/api/chart_data', methods=['GET'])
def get_chart_data():
    # Fetch risk score data for each month (assuming you have a timestamp field)
    product_query = Product.query.with_entities(
        db.extract('month', Product.last_updated).label('month'),
        db.func.avg(Product.risk_score).label('average_risk')
    ).group_by(db.extract('month', Product.last_updated))

    risk_data = {entry.month: entry.average_risk for entry in product_query}

    # Fetch cost data for each month
    cost_query = Product.query.with_entities(
        db.extract('month', Product.last_updated).label('month'),
        db.func.sum(Product.cost_monthly).label('total_cost')
    ).group_by(db.extract('month', Product.last_updated))

    cost_data = {entry.month: entry.total_cost for entry in cost_query}

    chart_data = {
        'risk_trend': risk_data,
        'cost_trend': cost_data
    }

    return jsonify(chart_data)

@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        name = request.form['name']
        vendor = request.form['vendor']
        category = request.form['category']
        business_unit = request.form['business_unit']
        app_owner = request.form['app_owner']
        licensed_users = request.form['licensed_users']
        data_sources = request.form['data_sources']
        risk_score = float(request.form['risk_score'])
        data_privacy_status = request.form['data_privacy_status']
        explainability = request.form['explainability']
        foundation_model = request.form['foundation_model']
        cost_monthly = float(request.form['cost_monthly'])
        data_ownership = request.form['data_ownership']
        nth_party_risk = request.form['nth_party_risk']
        status = request.form['status']

        new_product = Product(
            name=name,
            vendor=vendor,
            category=category,
            business_unit=business_unit,
	    app_owner=app_owner,
            licensed_users=licensed_users,
            data_sources=data_sources,
            risk_score=risk_score,
            data_privacy_status=data_privacy_status,
            explainability=explainability,
            foundation_model=foundation_model,
            cost_monthly=cost_monthly,
            data_ownership=data_ownership,
            nth_party_risk=nth_party_risk,
            status=status
        )

        db.session.add(new_product)
        db.session.commit()

              # Add selected controls to the product
        selected_controls = request.form.getlist('controls')
        for control_name in selected_controls:
            # Find or create the control if it doesn't exist yet
            control = Control.query.filter_by(name=control_name).first()
            if not control:
                control = Control(name=control_name)
                db.session.add(control)
                db.session.commit()

            new_product.controls.append(control)

        db.session.commit()
        return redirect(url_for('index'))

    controls = Control.query.all()  # Fetch existing controls for the form
    return render_template('add_product.html', controls=controls)

@app.route('/api/product/<int:id>', methods=['GET'])
def get_product(id):
    product = Product.query.get_or_404(id)
    product_dict = {
            'id': product.id,
            'name': product.name,
            'vendor': product.vendor,
            'category': product.category,
            'business_unit': product.business_unit,
            'app_owner': product.app_owner,
	    'licensed_users': product.licensed_users,
            'data_sources': product.data_sources,
            'risk_score': product.risk_score,
            'data_privacy_status': product.data_privacy_status,
            'explainability': product.explainability,
            'cost_monthly': product.cost_monthly,
            'foundation_model': product.foundation_model,
            'data_ownership': product.data_ownership,
            'nth_party_risk': product.nth_party_risk,
            'status': product.status,
            'last_updated': product.last_updated.isoformat()
        }
    return jsonify(product_dict)    

@app.route('/edit_product/<int:id>', methods=['GET', 'POST'])
def edit_product(id):
    if request.method == 'POST':
        product = Product.query.get_or_404(id)
        product.name = request.form['name']
        product.vendor = request.form['vendor']
        product.category = request.form['category']
        product.business_unit = request.form['business_unit']
        product.app_owner = request.form['app_owner']
        product.licensed_users = request.form['licensed_users']
        product.data_sources = request.form['data_sources']
        product.risk_score = float(request.form['risk_score'])
        product.data_privacy_status = request.form['data_privacy_status']
        product.explainability = request.form['explainability']
        product.foundation_model = request.form['foundation_model']
        product.cost_monthly = float(request.form['cost_monthly'])
        product.data_ownership = request.form['data_ownership']
        product.nth_party_risk = request.form['nth_party_risk']
        product.status = request.form['status']

        db.session.commit()

        return redirect(url_for('index'))

    product = Product.query.get_or_404(id)
    return render_template('edit_product.html', product=product)
    
@app.route('/product/<int:id>', methods=['GET'])
def product_details(id):
    product = Product.query.get_or_404(id)
    return render_template('product_details.html', product=product)

@app.route('/controls')
def manage_controls():
    controls = Control.query.all()
    return render_template('manage_controls.html', controls=controls)

@app.route('/add_control', methods=['POST'])
def add_control():
    name = request.form['name']
    new_control = Control(name=name)
    db.session.add(new_control)
    db.session.commit()

    return redirect(url_for('manage_controls'))
    
if __name__ == '__main__':
    app.run(debug=True)

