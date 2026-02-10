from flask import Flask, request, jsonify, send_from_directory
import os
import json
import math
import uuid
import re
from datetime import datetime

app = Flask(__name__, static_folder='public', static_url_path='')

# ============================================================
# IN-MEMORY STORAGE
# ============================================================
vehicles_db = {}
reports_db = {}
comps_db = {}

# ============================================================
# SERVE FRONTEND
# ============================================================
@app.route('/')
def index():
    return send_from_directory('public', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    if os.path.exists(os.path.join('public', path)):
        return send_from_directory('public', path)
    return send_from_directory('public', 'index.html')

# ============================================================
# HEALTH CHECK
# ============================================================
@app.route('/api/health')
def health():
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '2.0.0',
        'features': ['vision_intake', 'comp_discovery', 'daily_probability_curve']
    })

# ============================================================
# FEATURE 1: VISION INTAKE — Vehicle Identification
# ============================================================
@app.route('/api/vision/identify', methods=['POST'])
def vision_identify():
    """
    Accepts image description or listing URL and returns
    vehicle identification with confidence scoring.
    
    In production, this would connect to a computer vision API.
    Currently uses intelligent pattern matching on provided descriptions.
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    image_description = data.get('description', '')
    listing_url = data.get('url', '')
    image_base64 = data.get('image_base64', '')

    if not image_description and not listing_url and not image_base64:
        return jsonify({'error': 'Provide description, url, or image_base64'}), 400

    # --- Vision Analysis Engine ---
    identification = analyze_vehicle_identity(image_description, listing_url)

    return jsonify({
        'message': 'Vehicle identification complete',
        'identification': identification,
        'next_step': 'Confirm or correct the identification, then submit for full analysis.'
    })


def analyze_vehicle_identity(description, url):
    """
    Analyzes text description or URL to identify vehicle.
    In production: replace with actual CV model integration.
    Currently: intelligent keyword/pattern extraction.
    """
    text = (description + ' ' + url).lower()

    # --- Make Detection ---
    makes = {
        'toyota': ['toyota', 'trd', 'camry', 'corolla', 'rav4', 'tacoma', 'tundra', 'highlander', '4runner', 'prius', 'avalon', 'supra', 'sienna', 'venza'],
        'honda': ['honda', 'civic', 'accord', 'cr-v', 'crv', 'hr-v', 'hrv', 'pilot', 'odyssey', 'ridgeline', 'passport', 'fit'],
        'ford': ['ford', 'f-150', 'f150', 'mustang', 'explorer', 'escape', 'bronco', 'ranger', 'edge', 'expedition', 'maverick', 'fusion'],
        'chevrolet': ['chevrolet', 'chevy', 'silverado', 'equinox', 'traverse', 'tahoe', 'suburban', 'camaro', 'corvette', 'blazer', 'malibu', 'colorado', 'trax'],
        'nissan': ['nissan', 'altima', 'sentra', 'rogue', 'pathfinder', 'murano', 'frontier', 'titan', 'maxima', 'versa', 'kicks', 'armada'],
        'hyundai': ['hyundai', 'elantra', 'sonata', 'tucson', 'santa fe', 'palisade', 'kona', 'venue', 'ioniq'],
        'kia': ['kia', 'forte', 'optima', 'k5', 'sportage', 'sorento', 'telluride', 'soul', 'seltos', 'carnival', 'stinger'],
        'bmw': ['bmw', 'bimmer', '3 series', '5 series', 'x3', 'x5', 'x1', 'm3', 'm5', '330i', '530i', 'x7'],
        'mercedes': ['mercedes', 'benz', 'mb', 'c-class', 'e-class', 's-class', 'glc', 'gle', 'gls', 'amg', 'c300', 'e350'],
        'audi': ['audi', 'a3', 'a4', 'a6', 'q3', 'q5', 'q7', 'q8', 'e-tron', 'rs', 's4', 's5'],
        'lexus': ['lexus', 'rx', 'es', 'nx', 'is', 'gx', 'lx', 'ux', 'ls', 'rc'],
        'subaru': ['subaru', 'outback', 'forester', 'crosstrek', 'impreza', 'wrx', 'legacy', 'ascent', 'brz'],
        'volkswagen': ['volkswagen', 'vw', 'jetta', 'passat', 'tiguan', 'atlas', 'golf', 'gti', 'id.4', 'taos', 'arteon'],
        'mazda': ['mazda', 'cx-5', 'cx5', 'cx-9', 'cx9', 'mazda3', 'mazda6', 'cx-30', 'cx30', 'cx-50', 'mx-5', 'miata'],
        'gmc': ['gmc', 'sierra', 'yukon', 'acadia', 'terrain', 'canyon', 'denali'],
        'jeep': ['jeep', 'wrangler', 'grand cherokee', 'cherokee', 'compass', 'renegade', 'gladiator', 'wagoneer'],
        'dodge': ['dodge', 'ram', 'charger', 'challenger', 'durango', 'hornet'],
        'tesla': ['tesla', 'model 3', 'model y', 'model s', 'model x', 'cybertruck'],
        'acura': ['acura', 'mdx', 'rdx', 'tlx', 'integra', 'ilx'],
        'infiniti': ['infiniti', 'q50', 'q60', 'qx50', 'qx60', 'qx80'],
        'volvo': ['volvo', 'xc40', 'xc60', 'xc90', 's60', 's90', 'v60'],
        'cadillac': ['cadillac', 'escalade', 'xt4', 'xt5', 'xt6', 'ct4', 'ct5', 'lyriq'],
        'lincoln': ['lincoln', 'navigator', 'aviator', 'corsair', 'nautilus'],
        'buick': ['buick', 'encore', 'envision', 'enclave'],
        'chrysler': ['chrysler', 'pacifica', '300'],
        'genesis': ['genesis', 'g70', 'g80', 'g90', 'gv70', 'gv80'],
        'land rover': ['land rover', 'range rover', 'defender', 'discovery', 'evoque', 'velar'],
        'porsche': ['porsche', 'cayenne', 'macan', '911', 'taycan', 'panamera', 'boxster', 'cayman'],
    }

    detected_make = None
    make_confidence = 0
    detected_model = None

    for make, keywords in makes.items():
        for kw in keywords:
            if kw in text:
                # Direct make name = higher confidence
                if kw == make:
                    if make_confidence < 90:
                        detected_make = make
                        make_confidence = 90
                else:
                    # Model name found = we know both make and model
                    if make_confidence < 85:
                        detected_make = make
                        detected_model = kw
                        make_confidence = 85

    # --- Year Detection ---
    year_pattern = re.findall(r'20[0-2][0-9]|19[89][0-9]', text)
    detected_year = None
    year_confidence = 0
    if year_pattern:
        detected_year = int(year_pattern[0])
        year_confidence = 90

    # --- Trim Detection ---
    trim_keywords = {
        'se': 'SE', 'le': 'LE', 'xle': 'XLE', 'xse': 'XSE', 'trd': 'TRD',
        'limited': 'Limited', 'platinum': 'Platinum', 'sport': 'Sport',
        'touring': 'Touring', 'ex': 'EX', 'ex-l': 'EX-L', 'lx': 'LX',
        'sr': 'SR', 'sv': 'SV', 'sl': 'SL', 's': 'S', 'sxt': 'SXT',
        'gt': 'GT', 'gt-line': 'GT-Line', 'premium': 'Premium',
        'sel': 'SEL', 'limited': 'Limited', 'base': 'Base',
        'rs': 'RS', 'st': 'ST', 'raptor': 'Raptor', 'trail': 'Trail',
        'off-road': 'Off-Road', 'pro': 'Pro', 'nightshade': 'Nightshade',
        'denali': 'Denali', 'at4': 'AT4', 'slt': 'SLT',
        'laredo': 'Laredo', 'overland': 'Overland', 'rubicon': 'Rubicon',
        'sahara': 'Sahara', 'willys': 'Willys',
    }

    detected_trim = None
    for kw, label in trim_keywords.items():
        # Use word boundary matching to avoid false positives
        if re.search(r'\b' + re.escape(kw) + r'\b', text):
            detected_trim = label
            break

    # --- Body Style Detection ---
    body_styles = {
        'sedan': ['sedan', '4 door', '4-door', 'four door'],
        'suv': ['suv', 'crossover', 'sport utility'],
        'truck': ['truck', 'pickup', 'crew cab', 'double cab', 'regular cab', 'extended cab'],
        'coupe': ['coupe', '2 door', '2-door', 'two door'],
        'hatchback': ['hatchback', 'hatch', '5 door', '5-door'],
        'wagon': ['wagon', 'estate'],
        'van': ['van', 'minivan'],
        'convertible': ['convertible', 'cabriolet', 'roadster', 'spider', 'spyder'],
    }

    detected_body = None
    for style, keywords_list in body_styles.items():
        for kw in keywords_list:
            if kw in text:
                detected_body = style
                break

    # --- Color Detection ---
    colors = ['white', 'black', 'silver', 'gray', 'grey', 'red', 'blue', 'green',
              'brown', 'beige', 'gold', 'orange', 'yellow', 'purple', 'burgundy',
              'champagne', 'bronze', 'pearl', 'midnight', 'lunar', 'celestial',
              'magnetic', 'iconic', 'platinum', 'cement', 'army', 'cavalry']

    detected_color = None
    for c in colors:
        if c in text:
            detected_color = c.title()
            break

    # --- Overall Confidence ---
    scores = [make_confidence, year_confidence]
    if detected_model:
        scores.append(85)
    if detected_trim:
        scores.append(70)
    if detected_body:
        scores.append(60)

    overall_confidence = sum(scores) / len(scores) if scores else 0

    if overall_confidence >= 75:
        conf_level = 'HIGH'
    elif overall_confidence >= 50:
        conf_level = 'MEDIUM'
    else:
        conf_level = 'LOW'

    # --- Missing Data Flags ---
    missing = []
    if not detected_make:
        missing.append('Make not identified — need badge, logo, or explicit mention')
    if not detected_model:
        missing.append('Model not identified — need rear badge or listing text')
    if not detected_year:
        missing.append('Year not identified — need listing data or generation cues')
    if not detected_trim:
        missing.append('Trim not identified — need badge detail or window sticker')
    if not detected_color:
        missing.append('Color not confirmed from description')

    return {
        'identified': {
            'year': detected_year,
            'make': detected_make.title() if detected_make else None,
            'model': detected_model.title() if detected_model else None,
            'trim': detected_trim,
            'body_style': detected_body,
            'color': detected_color,
        },
        'confidence': {
            'level': conf_level,
            'percent': round(overall_confidence),
            'make_confidence': make_confidence,
            'year_confidence': year_confidence,
        },
        'missing_data': missing,
        'recommendation': 'Proceed with structured input for highest accuracy.' if conf_level != 'HIGH' else 'High-confidence identification. Ready for analysis.'
    }


# ============================================================
# FEATURE 2: COMP DISCOVERY ENGINE
# ============================================================
@app.route('/api/comps/discover', methods=['POST'])
def discover_comps():
    """
    Generates market comps based on vehicle parameters.
    In production: connects to auction APIs, dealer listing feeds, etc.
    Currently: generates realistic statistical comp data based on inputs.
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    year = int(data.get('year', 0))
    make = str(data.get('make', ''))
    model = str(data.get('model', ''))
    trim = str(data.get('trim', ''))
    mileage = int(data.get('mileage', 0))
    list_price = float(data.get('list_price', 0))
    comp_low = float(data.get('comp_low', 0))
    comp_high = float(data.get('comp_high', 0))
    competing_units = int(data.get('competing_units', 0))
    zip_code = str(data.get('zip_code', ''))

    if not year or not make or not model:
        return jsonify({'error': 'Year, make, and model are required'}), 400

    comps = generate_comp_analysis(year, make, model, trim, mileage, list_price, comp_low, comp_high, competing_units)

    return jsonify({
        'message': 'Comp discovery complete',
        'comp_analysis': comps
    })


@app.route('/api/comps/override', methods=['POST'])
def override_comps():
    """
    Accepts manual comp data and merges/compares with automated findings.
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    manual_comps = data.get('manual_comps', [])
    auto_comps = data.get('auto_comps', {})

    if not manual_comps:
        return jsonify({'error': 'Provide manual_comps array'}), 400

    # Process manual comps
    manual_prices = [float(c.get('price', 0)) for c in manual_comps if c.get('price')]
    manual_days = [int(c.get('days_to_sale', 0)) for c in manual_comps if c.get('days_to_sale')]

    manual_median = sorted(manual_prices)[len(manual_prices) // 2] if manual_prices else 0
    manual_avg_days = sum(manual_days) / len(manual_days) if manual_days else 0

    # Compare with auto
    auto_median = auto_comps.get('median_sale_price', 0)
    discrepancy = abs(manual_median - auto_median) if auto_median else 0
    discrepancy_pct = (discrepancy / auto_median * 100) if auto_median else 0

    if discrepancy_pct > 10:
        weight_recommendation = 'MANUAL_WEIGHTED'
        weight_explanation = f'Manual comps diverge {discrepancy_pct:.1f}% from automated data. Manual data likely reflects more current or localized conditions. Weighting manual comps at 70%.'
        blended_median = (manual_median * 0.7) + (auto_median * 0.3) if auto_median else manual_median
    elif discrepancy_pct > 5:
        weight_recommendation = 'BLENDED'
        weight_explanation = f'Moderate {discrepancy_pct:.1f}% discrepancy. Blending equally for balanced estimate.'
        blended_median = (manual_median + auto_median) / 2 if auto_median else manual_median
    else:
        weight_recommendation = 'AUTO_CONFIRMED'
        weight_explanation = 'Manual comps confirm automated findings. High confidence in automated data.'
        blended_median = auto_median if auto_median else manual_median

    return jsonify({
        'message': 'Comp override processed',
        'comparison': {
            'manual_median': round(manual_median),
            'auto_median': round(auto_median) if auto_median else None,
            'discrepancy_dollars': round(discrepancy),
            'discrepancy_percent': round(discrepancy_pct, 1),
            'weight_recommendation': weight_recommendation,
            'weight_explanation': weight_explanation,
            'blended_median': round(blended_median),
            'manual_comp_count': len(manual_comps),
            'manual_avg_days_to_sale': round(manual_avg_days) if manual_avg_days else None
        }
    })


def generate_comp_analysis(year, make, model, trim, mileage, list_price, comp_low, comp_high, competing_units):
    """
    Generates realistic comp analysis based on vehicle parameters.
    In production: this pulls from real auction + listing APIs.
    """
    import random
    random.seed(hash(f"{year}{make}{model}{mileage}"))

    # Use provided comp range or estimate
    if comp_low and comp_high:
        price_low = comp_low
        price_high = comp_high
    elif list_price:
        price_low = list_price * 0.88
        price_high = list_price * 1.05
    else:
        return {'error': 'Insufficient data for comp analysis'}

    comp_mid = (price_low + price_high) / 2
    comp_range = price_high - price_low
    num_comps = competing_units if competing_units > 0 else random.randint(8, 25)

    # Generate individual comps
    completed_sales = []
    active_listings = []

    for i in range(min(num_comps, 12)):
        price_var = random.gauss(0, comp_range * 0.15)
        sale_price = round(comp_mid + price_var, -2)
        mile_var = random.randint(-8000, 12000)
        comp_mileage = max(5000, mileage + mile_var)
        days_on_market = max(3, int(random.gauss(35, 15)))

        completed_sales.append({
            'price': sale_price,
            'mileage': comp_mileage,
            'days_on_market': days_on_market,
            'source': random.choice(['Auction', 'Retail - Delisted', 'Dealer Retail']),
            'distance_miles': random.randint(5, 95)
        })

    for i in range(min(num_comps - len(completed_sales), 8)):
        price_var = random.gauss(comp_range * 0.05, comp_range * 0.15)
        active_price = round(comp_mid + price_var, -2)
        mile_var = random.randint(-5000, 15000)
        comp_mileage = max(5000, mileage + mile_var)
        days_listed = random.randint(1, 65)

        active_listings.append({
            'price': active_price,
            'mileage': comp_mileage,
            'days_listed': days_listed,
            'source': random.choice(['AutoTrader', 'Cars.com', 'CarGurus', 'Dealer Website']),
            'distance_miles': random.randint(5, 95)
        })

    # Statistics
    all_sale_prices = [c['price'] for c in completed_sales]
    all_sale_prices.sort()
    all_days = [c['days_on_market'] for c in completed_sales]

    median_price = all_sale_prices[len(all_sale_prices) // 2] if all_sale_prices else comp_mid
    avg_price = sum(all_sale_prices) / len(all_sale_prices) if all_sale_prices else comp_mid
    median_days = sorted(all_days)[len(all_days) // 2] if all_days else 35
    avg_days = sum(all_days) / len(all_days) if all_days else 35

    # Supply/demand assessment
    active_count = len(active_listings)
    if active_count > 15:
        supply_pressure = 'HIGH'
        supply_detail = f'{active_count} active listings create significant buyer leverage.'
    elif active_count > 8:
        supply_pressure = 'MODERATE'
        supply_detail = f'{active_count} active listings — competitive but manageable.'
    else:
        supply_pressure = 'LOW'
        supply_detail = f'Only {active_count} active listings — supply scarcity favors sellers.'

    # Velocity assessment
    if median_days <= 25:
        velocity = 'FAST'
        velocity_detail = f'Median {median_days} days to sale — high-velocity segment.'
    elif median_days <= 45:
        velocity = 'NORMAL'
        velocity_detail = f'Median {median_days} days to sale — standard velocity.'
    else:
        velocity = 'SLOW'
        velocity_detail = f'Median {median_days} days to sale — sluggish segment.'

    return {
        'vehicle_searched': f'{year} {make} {model} {trim}'.strip(),
        'comp_count': {
            'completed_sales': len(completed_sales),
            'active_listings': len(active_listings),
            'total': len(completed_sales) + len(active_listings)
        },
        'price_analysis': {
            'median_sale_price': round(median_price),
            'average_sale_price': round(avg_price),
            'price_range_low': round(min(all_sale_prices)) if all_sale_prices else round(price_low),
            'price_range_high': round(max(all_sale_prices)) if all_sale_prices else round(price_high),
            'price_std_dev': round(std_dev(all_sale_prices)) if len(all_sale_prices) > 1 else 0
        },
        'days_to_sale': {
            'median': round(median_days),
            'average': round(avg_days),
            'fastest': min(all_days) if all_days else 0,
            'slowest': max(all_days) if all_days else 0
        },
        'supply_demand': {
            'supply_pressure': supply_pressure,
            'supply_detail': supply_detail,
            'velocity': velocity,
            'velocity_detail': velocity_detail,
            'active_inventory_count': active_count
        },
        'completed_sales': completed_sales[:8],
        'active_listings': active_listings[:8],
        'data_freshness': 'Simulated — production version uses live market feeds',
        'generated_at': datetime.utcnow().isoformat()
    }


def std_dev(values):
    if len(values) < 2:
        return 0
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
    return math.sqrt(variance)


# ============================================================
# VEHICLE ENDPOINTS
# ============================================================
@app.route('/api/vehicles', methods=['GET'])
def get_vehicles():
    vehicle_list = list(vehicles_db.values())
    vehicle_list.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    return jsonify({'count': len(vehicle_list), 'vehicles': vehicle_list})

@app.route('/api/vehicles', methods=['POST'])
def add_vehicle():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    required = ['year', 'make', 'model', 'acquisition_cost', 'list_price']
    for field in required:
        if field not in data or not data[field]:
            return jsonify({'error': f'Missing required field: {field}'}), 400

    vehicle_id = str(uuid.uuid4())
    vehicle = build_vehicle_record(vehicle_id, data)
    vehicles_db[vehicle_id] = vehicle
    return jsonify({'message': 'Vehicle added', 'vehicle': vehicle}), 201

@app.route('/api/vehicles/<vehicle_id>', methods=['GET'])
def get_vehicle(vehicle_id):
    vehicle = vehicles_db.get(vehicle_id)
    if not vehicle:
        return jsonify({'error': 'Vehicle not found'}), 404
    return jsonify({'vehicle': vehicle})

@app.route('/api/vehicles/<vehicle_id>', methods=['PUT'])
def update_vehicle(vehicle_id):
    if vehicle_id not in vehicles_db:
        return jsonify({'error': 'Vehicle not found'}), 404
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    vehicle = build_vehicle_record(vehicle_id, data)
    vehicles_db[vehicle_id] = vehicle
    return jsonify({'message': 'Vehicle updated', 'vehicle': vehicle})

@app.route('/api/vehicles/<vehicle_id>', methods=['DELETE'])
def delete_vehicle(vehicle_id):
    if vehicle_id not in vehicles_db:
        return jsonify({'error': 'Vehicle not found'}), 404
    del vehicles_db[vehicle_id]
    return jsonify({'message': 'Vehicle deleted'})

@app.route('/api/vehicles/<vehicle_id>/analyze', methods=['POST'])
def analyze_vehicle_endpoint(vehicle_id):
    vehicle = vehicles_db.get(vehicle_id)
    if not vehicle:
        return jsonify({'error': 'Vehicle not found'}), 404

    analysis = analyze_vehicle(vehicle)
    report_id = str(uuid.uuid4())
    reports_db[report_id] = {
        'id': report_id,
        'vehicle_id': vehicle_id,
        'vehicle_title': f"{vehicle['year']} {vehicle['make']} {vehicle['model']} {vehicle.get('trim', '')}".strip(),
        'analysis': analysis,
        'created_at': datetime.utcnow().isoformat()
    }
    return jsonify({'message': 'Analysis complete', 'report': reports_db[report_id]})


# ============================================================
# DIRECT ANALYSIS (no save required)
# ============================================================
@app.route('/api/analyze', methods=['POST'])
def analyze_direct():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    required = ['year', 'make', 'model', 'acquisition_cost', 'list_price']
    for field in required:
        if field not in data or not data[field]:
            return jsonify({'error': f'Missing required field: {field}'}), 400

    vehicle = build_vehicle_record(None, data)
    analysis = analyze_vehicle(vehicle)

    return jsonify({
        'message': 'Analysis complete',
        'report': {
            'id': str(uuid.uuid4()),
            'vehicle_title': f"{vehicle['year']} {vehicle['make']} {vehicle['model']} {vehicle.get('trim', '')}".strip(),
            'analysis': analysis,
            'created_at': datetime.utcnow().isoformat()
        }
    })


# ============================================================
# REPORTS
# ============================================================
@app.route('/api/reports', methods=['GET'])
def get_reports():
    report_list = list(reports_db.values())
    report_list.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    return jsonify({'count': len(report_list), 'reports': report_list})

@app.route('/api/reports/<report_id>', methods=['GET'])
def get_report(report_id):
    report = reports_db.get(report_id)
    if not report:
        return jsonify({'error': 'Report not found'}), 404
    return jsonify({'report': report})


# ============================================================
# DASHBOARD
# ============================================================
@app.route('/api/dashboard/summary', methods=['GET'])
def dashboard_summary():
    active = [v for v in vehicles_db.values() if v.get('status') == 'active']
    total_invested = sum(v['acquisition_cost'] + v['recon_cost'] for v in active)
    total_list = sum(v['list_price'] for v in active)
    avg_days = sum(v['days_in_inventory'] for v in active) / len(active) if active else 0
    daily_burn = sum(
        (v['acquisition_cost'] + v['recon_cost']) * v['floorplan_rate'] / 100 / 365 for v in active
    )
    healthy = len([v for v in active if v['days_in_inventory'] <= 30])
    at_risk = len([v for v in active if 30 < v['days_in_inventory'] <= 60])
    danger = len([v for v in active if v['days_in_inventory'] > 60])

    return jsonify({
        'summary': {
            'total_vehicles': len(active),
            'total_invested': round(total_invested),
            'total_list_value': round(total_list),
            'total_potential_gross': round(total_list - total_invested),
            'avg_days_in_inventory': round(avg_days),
            'daily_floorplan_burn': round(daily_burn, 2),
            'monthly_floorplan_burn': round(daily_burn * 30),
            'aging_breakdown': {'healthy': healthy, 'at_risk': at_risk, 'danger': danger}
        }
    })


# ============================================================
# HELPER: Build Vehicle Record
# ============================================================
def build_vehicle_record(vehicle_id, data):
    return {
        'id': vehicle_id or str(uuid.uuid4()),
        'year': int(data.get('year', 0)),
        'make': str(data.get('make', '')),
        'model': str(data.get('model', '')),
        'trim': str(data.get('trim', '')),
        'mileage': int(data.get('mileage', 0)),
        'ext_color': str(data.get('ext_color', '')),
        'int_color': str(data.get('int_color', '')),
        'vin': str(data.get('vin', '')),
        'equipment': str(data.get('equipment', '')),
        'acquisition_cost': float(data.get('acquisition_cost', 0)),
        'recon_cost': float(data.get('recon_cost', 0)),
        'list_price': float(data.get('list_price', 0)),
        'floorplan_rate': float(data.get('floorplan_rate', 7.25)),
        'wholesale_price': float(data.get('wholesale_price', 0)),
        'min_gross': float(data.get('min_gross', 2000)),
        'days_in_inventory': int(data.get('days_in_inventory', 0)),
        'price_changes': int(data.get('price_changes', 0)),
        'days_since_price_change': int(data.get('days_since_price_change', 0)),
        'comp_low': float(data.get('comp_low', 0)),
        'comp_high': float(data.get('comp_high', 0)),
        'competing_units': int(data.get('competing_units', 0)),
        'demand_signal': str(data.get('demand_signal', 'moderate')),
        'seasonal_notes': str(data.get('seasonal_notes', '')),
        'views_7': int(data.get('views_7', 0)),
        'views_30': int(data.get('views_30', 0)),
        'leads_7': int(data.get('leads_7', 0)),
        'leads_30': int(data.get('leads_30', 0)),
        'test_drives_7': int(data.get('test_drives_7', 0)),
        'test_drives_30': int(data.get('test_drives_30', 0)),
        'sales_notes': str(data.get('sales_notes', '')),
        'status': 'active',
        'created_at': datetime.utcnow().isoformat()
    }


# ============================================================
# CORE ANALYSIS ENGINE (with Daily Probability Curve)
# ============================================================
def analyze_vehicle(d):
    analysis = {}

    # --- CORE FINANCIALS ---
    total_invested = d['acquisition_cost'] + d['recon_cost']
    potential_gross = d['list_price'] - total_invested
    daily_floorplan = (total_invested * (d['floorplan_rate'] / 100)) / 365
    floorplan_accrued = daily_floorplan * d['days_in_inventory']
    current_net_gross = potential_gross - floorplan_accrued
    wholesale_net_today = d['wholesale_price'] - total_invested - floorplan_accrued

    analysis['financials'] = {
        'total_invested': r2(total_invested),
        'potential_gross_at_sticker': r2(potential_gross),
        'daily_floorplan_cost': r2(daily_floorplan),
        'floorplan_accrued_to_date': r2(floorplan_accrued),
        'current_net_gross': r2(current_net_gross),
        'wholesale_net_today': r2(wholesale_net_today)
    }

    # --- MARKET POSITION ---
    comp_range = d['comp_high'] - d['comp_low']
    market_position = ((d['list_price'] - d['comp_low']) / comp_range) if comp_range > 0 else 0.5

    if market_position > 0.75:
        mp_label = 'Top Quartile — Overpriced Risk'
    elif market_position > 0.5:
        mp_label = 'Above Mid-Market'
    elif market_position > 0.25:
        mp_label = 'Mid-Market'
    else:
        mp_label = 'Value Position'

    analysis['market_position'] = {
        'percentile': round(market_position * 100),
        'label': mp_label,
        'comp_range': {'low': d['comp_low'], 'high': d['comp_high']},
        'competing_units': d['competing_units'],
        'demand_signal': d['demand_signal']
    }

    # --- ENGAGEMENT ---
    avg_weekly_views = d['views_30'] / 4.3 if d['views_30'] > 0 else 0
    view_trend = ((d['views_7'] - avg_weekly_views) / avg_weekly_views * 100) if avg_weekly_views > 0 else 0
    view_trend_label = 'Accelerating' if view_trend > 10 else ('Stable' if view_trend > -10 else 'Declining')
    lead_to_view = (d['leads_30'] / d['views_30'] * 100) if d['views_30'] > 0 else 0
    td_to_lead = (d['test_drives_30'] / d['leads_30'] * 100) if d['leads_30'] > 0 else 0
    engagement_score = (d['leads_7'] * 3) + (d['test_drives_7'] * 10) + (d['views_7'] * 0.2)

    analysis['engagement'] = {
        'views_7': d['views_7'], 'views_30': d['views_30'],
        'leads_7': d['leads_7'], 'leads_30': d['leads_30'],
        'test_drives_7': d['test_drives_7'], 'test_drives_30': d['test_drives_30'],
        'view_trend_pct': round(view_trend),
        'view_trend_label': view_trend_label,
        'lead_to_view_rate': r2(lead_to_view),
        'test_drive_to_lead_rate': r2(td_to_lead),
        'engagement_score': r2(engagement_score)
    }

    # --- PROBABILITY MODEL FACTORS ---
    demand_mult = 1.2 if d['demand_signal'] == 'high' else (0.75 if d['demand_signal'] == 'soft' else 1.0)
    cu = d['competing_units']
    comp_factor = 1.3 if cu <= 5 else (1.1 if cu <= 10 else (0.9 if cu <= 20 else 0.7))
    di = d['days_in_inventory']
    aging_factor = 1.2 if di <= 20 else (1.0 if di <= 40 else (0.85 if di <= 60 else (0.65 if di <= 90 else 0.45)))
    eng_factor = 1.2 if engagement_score > 25 else (1.0 if engagement_score > 12 else (0.8 if engagement_score > 5 else 0.6))
    price_factor = 0.7 if market_position > 0.8 else (0.85 if market_position > 0.6 else (1.0 if market_position > 0.4 else (1.15 if market_position > 0.2 else 1.25)))

    composite = demand_mult * comp_factor * aging_factor * eng_factor * price_factor

    prob30 = clamp(0.35 * composite, 0.05, 0.95)
    prob60 = clamp(0.55 * composite * 1.1, 0.10, 0.97)
    prob90 = clamp(0.72 * composite * 1.15, 0.20, 0.98)

    # --- FEATURE 3: DAILY PROBABILITY CURVE ---
    daily_curve = generate_daily_probability_curve(prob30, prob60, prob90, di, composite)

    # Factors
    factors_30 = []
    factors_60 = []
    factors_90 = []

    if market_position > 0.65:
        factors_30.append('Priced in upper range of comps — limits buyer pool.')
        factors_60.append('Extended exposure at high price depletes interested buyers.')
    if cu > 12:
        factors_30.append(f'{cu} competing units give buyers alternatives and time.')
    if engagement_score < 10:
        factors_30.append('Low engagement — insufficient buyer interest at current positioning.')
    elif engagement_score > 20:
        factors_30.append('Solid engagement — conversion rate is the key lever.')
    if di > 40:
        factors_60.append('Many local buyers have already seen and passed on this listing.')
        factors_90.append('Remaining buyer pool is thin. Price is the only lever left.')
    if view_trend < -15:
        factors_30.append('View trend declining sharply — losing visibility.')
    if d['demand_signal'] == 'high':
        factors_30.append('High regional demand supports faster absorption.')
    elif d['demand_signal'] == 'soft':
        factors_30.append('Soft demand extends expected time to sale.')
    if not factors_60:
        factors_60.append('Standard market dynamics. Price and marketing effort are primary levers.')
    if not factors_90:
        factors_90.append('Near-certain retail exit if priced correctly, but margin erosion makes timing critical.')

    # Curve insights
    # Find acceleration and decay points
    accel_end_day = 0
    decay_start_day = 0
    prev_daily = 0
    for point in daily_curve:
        if point['daily_probability'] >= prev_daily:
            accel_end_day = point['day']
        elif decay_start_day == 0 and point['daily_probability'] < prev_daily:
            decay_start_day = point['day']
        prev_daily = point['daily_probability']

    curve_insights = {
        'acceleration_phase': f'Days 1–{accel_end_day}: Probability builds as listing gains exposure.',
        'peak_probability_day': accel_end_day,
        'decay_begins': f'Day {decay_start_day}: Daily sell probability begins declining as buyer pool depletes.',
        'decay_start_day': decay_start_day,
        'critical_insight': f'The window between day {accel_end_day} and day {decay_start_day + 15} is when this vehicle is most likely to sell. Marketing and pricing actions have maximum impact during this window.'
    }

    analysis['sale_probability'] = {
        'prob_30_day': round(prob30 * 100),
        'prob_60_day': round(prob60 * 100),
        'prob_90_day': round(prob90 * 100),
        'factors_30': factors_30,
        'factors_60': factors_60,
        'factors_90': factors_90,
        'daily_curve': daily_curve,
        'curve_insights': curve_insights
    }

    # --- AGING & EROSION ---
    if di <= 30:
        aging_zone = 'HEALTHY'
        aging_detail = 'Within target velocity window.'
    elif di <= 60:
        aging_zone = 'AT-RISK'
        aging_detail = 'Approaching danger zone. Active intervention required.'
    else:
        aging_zone = 'DANGER'
        aging_detail = 'Past target velocity. Immediate action needed.'

    erosion_table = []
    for add_days in [0, 30, 60, 90]:
        total_days = di + add_days
        fp_total = daily_floorplan * total_days
        gross_sticker = potential_gross - fp_total
        erosion_table.append({
            'additional_days': add_days,
            'total_days': total_days,
            'floorplan_accrued': r2(fp_total),
            'gross_at_sticker': r2(gross_sticker),
            'realistic_gross_low': r2(gross_sticker - 1000),
            'realistic_gross_high': r2(gross_sticker - 500)
        })

    irrational_day = di
    for day in range(di, di + 150):
        fp = daily_floorplan * day
        retail_net = (potential_gross - fp) - 750
        day_prob = clamp(prob30 * (0.98 ** (day - di)), 0.05, 0.95)
        pw_retail = retail_net * day_prob
        ws_at_day = d['wholesale_price'] - total_invested - fp
        if pw_retail < max(ws_at_day, wholesale_net_today) or retail_net < 0:
            irrational_day = day
            break
        irrational_day = day

    days_until_irrational = max(0, irrational_day - di)

    analysis['aging'] = {
        'zone': aging_zone, 'zone_detail': aging_detail,
        'days_in_inventory': di,
        'erosion_table': erosion_table,
        'irrationality_threshold': {
            'day': irrational_day,
            'days_remaining': days_until_irrational,
            'explanation': f'Beyond day {irrational_day}, holding becomes economically irrational. ~{days_until_irrational} days remain.'
        }
    }

    # --- PRICING ---
    optimal_pos = 0.45
    optimal_price = (d['comp_low'] + (comp_range * optimal_pos)) if comp_range > 0 else d['list_price']
    price_diff = d['list_price'] - optimal_price

    if market_position > 0.65 and di > 30:
        price_action = 'REDUCE'
        raw_cut = round(price_diff / 100) * 100
        change_amount = max(300, min(raw_cut, round(potential_gross * 0.35 / 100) * 100))
        new_price = d['list_price'] - change_amount
        reasoning = f"At {round(market_position*100)}th percentile with {di} days aging. ${change_amount:,} reduction to ${new_price:,.0f} repositions to mid-market with negotiation room."
    elif market_position < 0.25 and di < 20 and engagement_score > 20:
        price_action = 'INCREASE'
        raw_raise = round(abs(price_diff) * 0.5 / 100) * 100
        change_amount = min(raw_raise, 800)
        new_price = d['list_price'] + change_amount
        reasoning = 'Strong engagement at below-market price. Room to capture additional gross.'
    elif market_position > 0.55 and di > 45:
        price_action = 'REDUCE'
        change_amount = max(300, round(price_diff * 0.7 / 100) * 100)
        new_price = d['list_price'] - change_amount
        reasoning = f"Slightly over-positioned and aging at {di} days. ${change_amount:,} cut improves competitive stance."
    else:
        price_action = 'HOLD'
        change_amount = 0
        new_price = d['list_price']
        reasoning = 'Price and engagement balanced. Hold and monitor.'

    exp_trans_low = new_price - 1000
    exp_trans_high = new_price - 500
    exp_gross_low = exp_trans_low - total_invested
    exp_gross_high = exp_trans_high - total_invested

    if cu > 15:
        elasticity = 'HIGH'
        elast_detail = f'{cu} competing units. Buyers are highly price-aware. Price directly impacts search visibility.'
    elif cu > 8:
        elasticity = 'MODERATE-HIGH'
        elast_detail = 'Meaningful competition. Price changes impact lead volume.'
    elif cu > 4:
        elasticity = 'MODERATE'
        elast_detail = 'Moderate competition. Vehicle attributes also matter.'
    else:
        elasticity = 'LOW'
        elast_detail = 'Limited competition. Stronger pricing power.'

    # Expected probability change from price action
    if price_action == 'REDUCE':
        prob_boost = min(15, round(change_amount / 100 * 2))
        gross_impact = -change_amount
    elif price_action == 'INCREASE':
        prob_boost = -min(8, round(change_amount / 100 * 1.5))
        gross_impact = change_amount
    else:
        prob_boost = 0
        gross_impact = 0

    analysis['pricing'] = {
        'action': price_action,
        'change_amount': change_amount,
        'current_list_price': d['list_price'],
        'new_list_price': new_price,
        'reasoning': reasoning,
        'timing': 'Execute today.' if price_action != 'HOLD' else 'No action needed.',
        'elasticity': {'level': elasticity, 'detail': elast_detail},
        'expected_transaction_range': {'low': r2(exp_trans_low), 'high': r2(exp_trans_high)},
        'expected_gross_range': {'low': r2(exp_gross_low), 'high': r2(exp_gross_high)},
        'probability_impact': {
            'estimated_prob_change_pct': prob_boost,
            'estimated_gross_impact': gross_impact,
            'explanation': f"Price {'reduction' if price_action == 'REDUCE' else 'increase' if price_action == 'INCREASE' else 'hold'} expected to {'increase' if prob_boost > 0 else 'decrease' if prob_boost < 0 else 'maintain'} 30-day sell probability by ~{abs(prob_boost)} percentage points."
        }
    }

    # --- EXIT PATH ---
    retail_exp_gross = ((exp_gross_low + exp_gross_high) / 2) - (daily_floorplan * 20)
    retail_prob_weighted = retail_exp_gross * prob30

    if retail_prob_weighted > wholesale_net_today and exp_gross_low > d['min_gross'] * 0.5:
        optimal_exit = 'RETAIL'
        exit_reasoning = f'Retail-wholesale spread ~${round(retail_exp_gross - wholesale_net_today):,} justifies continued retail. Wholesale is the backstop.'
    elif wholesale_net_today > -500:
        optimal_exit = 'WHOLESALE'
        exit_reasoning = 'Probability-weighted retail no longer justifies holding costs.'
    else:
        optimal_exit = 'RETAIL'
        exit_reasoning = 'Wholesale produces significant loss. Aggressive retail pricing required immediately.'

    reassess_day = di + 14

    analysis['exit_path'] = {
        'optimal': optimal_exit,
        'reasoning': exit_reasoning,
        'paths': [
            {
                'path': 'RETAIL', 'recommended': optimal_exit == 'RETAIL',
                'expected_gross_low': r2(exp_gross_low), 'expected_gross_high': r2(exp_gross_high),
                'expected_days': '12-25 days' if price_action != 'HOLD' else '20-40 days',
                'probability': f'{round(prob30*100)}%-{round(prob60*100)}%'
            },
            {
                'path': 'WHOLESALE', 'recommended': optimal_exit == 'WHOLESALE',
                'expected_gross_low': r2(wholesale_net_today), 'expected_gross_high': r2(wholesale_net_today),
                'expected_days': '3-7 days', 'probability': '~95%'
            },
            {
                'path': 'DEALER_TRADE', 'recommended': False,
                'expected_gross_low': 0, 'expected_gross_high': 300,
                'expected_days': '7-21 days', 'probability': 'Low'
            }
        ],
        'decision_trigger': {
            'reassess_at_day': reassess_day,
            'condition': f'If <2 test drives by day {reassess_day}, wholesale immediately.'
        }
    }

    # --- ACTION PLAN ---
    actions = []

    if price_action == 'REDUCE':
        actions.append({
            'priority': 1, 'title': f'Execute ${change_amount:,} price reduction',
            'timing': 'TODAY',
            'detail': f'Reduce from ${d["list_price"]:,.0f} to ${new_price:,.0f}. Estimated +{prob_boost}% sell probability. Daily hold cost: ${daily_floorplan:.2f}.',
            'purpose': 'Reposition competitively and trigger platform re-indexing.'
        })
    elif price_action == 'INCREASE':
        actions.append({
            'priority': 1, 'title': f'Increase price by ${change_amount:,}',
            'timing': 'TODAY',
            'detail': f'Raise to ${new_price:,.0f}. Strong engagement supports it.',
            'purpose': 'Capture available gross.'
        })
    else:
        actions.append({
            'priority': 1, 'title': 'Hold price — monitor 7 days',
            'timing': 'THIS WEEK',
            'detail': f'Maintain ${d["list_price"]:,.0f}. Reassess if views drop >15%.',
            'purpose': 'Avoid disrupting momentum.'
        })

    actions.append({
        'priority': 2, 'title': 'Audit and upgrade listing',
        'timing': 'TODAY',
        'detail': f'30+ photos. Highlight: {d.get("equipment", "key features")}. Video walkaround. Verify feature filters.',
        'purpose': 'Maximize conversion from traffic.'
    })

    if d['leads_30'] > 0:
        actions.append({
            'priority': 3, 'title': f'Re-engage all {d["leads_30"]} leads',
            'timing': 'BY WEDNESDAY',
            'detail': f'Phone first, text, email. {d["leads_7"]} recent leads within 4 hours.',
            'purpose': 'Re-engagement converts 2-3x cold inbound.'
        })

    actions.append({
        'priority': 4, 'title': 'Brief sales team',
        'timing': 'TOMORROW AM',
        'detail': f'Sticker: ${new_price:,.0f}. Floor: ${max(new_price - 500, total_invested + d["min_gross"]):,.0f}. No leading with concessions.',
        'purpose': 'Protect gross. Prevent demoralized selling.'
    })

    actions.append({
        'priority': 5, 'title': f'Hard wholesale date: Day {reassess_day}',
        'timing': 'CALENDAR NOW',
        'detail': f'<2 test drives by day {reassess_day} = wholesale. No extensions. WS net: ${wholesale_net_today:,.0f}.',
        'purpose': 'Remove emotional attachment to sunk costs.'
    })

    analysis['action_plan'] = actions

    # --- RISK & CONFIDENCE ---
    risks = []

    sn = d.get('seasonal_notes', '') or ''
    if 'compression' in sn.lower():
        risks.append({'factor': 'Incentive Compression', 'detail': 'Newer model incentives pulling ceiling down.', 'severity': 'HIGH'})
    if di > 45:
        risks.append({'factor': 'Stale Listing', 'detail': f'At {di} days, many buyers have passed.', 'severity': 'MEDIUM'})
    if cu > 12:
        risks.append({'factor': 'Heavy Supply', 'detail': f'{cu} units. Liquidation risk.', 'severity': 'MEDIUM'})
    if view_trend < -15:
        risks.append({'factor': 'Declining Views', 'detail': f'Down {abs(round(view_trend))}% WoW.', 'severity': 'HIGH'})
    if 'price' in (d.get('sales_notes', '') or '').lower():
        risks.append({'factor': 'Price Resistance', 'detail': 'Buyers pushing back per sales team.', 'severity': 'MEDIUM'})
    if not risks:
        risks.append({'factor': 'Standard Dynamics', 'detail': 'No critical risks.', 'severity': 'LOW'})

    data_points = [
        1 if d['views_30'] > 0 else 0, 1 if d['leads_30'] > 0 else 0,
        1 if d['comp_low'] > 0 else 0, 1 if d['competing_units'] > 0 else 0,
        1 if d['wholesale_price'] > 0 else 0, 1 if d.get('equipment') else 0,
        1 if d.get('sales_notes') else 0
    ]
    completeness = sum(data_points) / len(data_points)
    if completeness > 0.75:
        confidence = 'HIGH'
        conf_pct = 80 + round(completeness * 15)
    elif completeness > 0.5:
        confidence = 'MEDIUM'
        conf_pct = 50 + round(completeness * 20)
    else:
        confidence = 'LOW'
        conf_pct = 20 + round(completeness * 30)

    analysis['risk_and_confidence'] = {
        'risks': risks,
        'confidence': {'level': confidence, 'percent': conf_pct, 'data_completeness': round(completeness * 100)}
    }

    # --- SUMMARY ---
    analysis['summary'] = {
        'vehicle': f"{d['year']} {d['make']} {d['model']} {d.get('trim', '')}".strip(),
        'mileage': d['mileage'],
        'color': f"{d['ext_color']} / {d['int_color']}",
        'total_invested': r2(total_invested),
        'current_list': d['list_price'],
        'recommended_price': new_price,
        'price_action': price_action,
        'aging_zone': aging_zone,
        'optimal_exit': optimal_exit,
        'days_to_decision': days_until_irrational,
        'confidence': confidence,
        'generated_at': datetime.utcnow().isoformat()
    }

    return analysis


# ============================================================
# FEATURE 3: DAILY PROBABILITY CURVE GENERATOR
# ============================================================
def generate_daily_probability_curve(prob30, prob60, prob90, current_day, composite_factor):
    """
    Generates a day-by-day probability curve from Day 1 through Day 90.
    
    The model uses a modified logistic growth curve that accounts for:
    - Initial listing exposure ramp-up (days 1-10)
    - Peak probability window (days 10-35)
    - Gradual decay as buyer pool depletes (days 35+)
    - Steeper decay past 60 days
    
    Each day returns:
    - daily_probability: chance of selling ON that specific day
    - cumulative_probability: chance of having sold BY that day
    - remaining_gross: expected gross if sold on that day
    """
    curve = []
    cumulative = 0

    # Model parameters based on composite factor
    # Higher composite = faster ramp, higher peak, slower decay
    ramp_speed = 0.15 * min(composite_factor, 1.5)
    peak_day = max(8, min(30, round(20 / max(composite_factor, 0.3))))
    peak_height = min(0.045, 0.025 * composite_factor)
    decay_rate = 0.02 + (0.01 * (1 / max(composite_factor, 0.3)))

    for day in range(1, 91):
        # Ramp phase (logistic growth)
        if day <= peak_day:
            ramp = 1 / (1 + math.exp(-ramp_speed * (day - peak_day * 0.6)))
            daily_prob = peak_height * ramp
        # Decay phase
        else:
            days_past_peak = day - peak_day
            daily_prob = peak_height * math.exp(-decay_rate * days_past_peak)

        # Adjust for already-elapsed days
        if day <= current_day:
            # Days already passed — can't sell in the past
            daily_prob = 0

        # Ensure daily prob is reasonable
        daily_prob = max(0, min(0.06, daily_prob))

        # Accumulate
        # Probability of selling on this day = daily_prob * (1 - cumulative)
        # (Can only sell if not already sold)
        conditional_daily = daily_prob * (1 - cumulative)
        cumulative = min(0.98, cumulative + conditional_daily)

        curve.append({
            'day': day,
            'daily_probability': round(conditional_daily * 100, 2),
            'cumulative_probability': round(cumulative * 100, 1),
        })

    # Normalize to match our milestone probabilities
    # Find actual cumulative at days 30, 60, 90
    cum_30 = next((p['cumulative_probability'] for p in curve if p['day'] == 30), 0)
    cum_60 = next((p['cumulative_probability'] for p in curve if p['day'] == 60), 0)
    cum_90 = next((p['cumulative_probability'] for p in curve if p['day'] == 90), 0)

    # Scale curve to match our probability model
    target_30 = prob30 * 100
    target_60 = prob60 * 100
    target_90 = prob90 * 100

    if cum_90 > 0:
        scale = target_90 / cum_90
    elif cum_60 > 0:
        scale = target_60 / cum_60
    elif cum_30 > 0:
        scale = target_30 / cum_30
    else:
        scale = 1

    # Apply scaling
    scaled_cum = 0
    for point in curve:
        original_daily = point['daily_probability'] / 100
        scaled_daily = original_daily * scale
        scaled_daily = max(0, min(0.08, scaled_daily))
        scaled_cum = min(0.98, scaled_cum + scaled_daily)

        point['daily_probability'] = round(scaled_daily * 100, 2)
        point['cumulative_probability'] = round(scaled_cum * 100, 1)

    return curve


# ============================================================
# HELPERS
# ============================================================
def r2(n):
    return round(n * 100) / 100

def clamp(value, min_val, max_val):
    return max(min_val, min(max_val, value))


# ============================================================
# RUN
# ============================================================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
